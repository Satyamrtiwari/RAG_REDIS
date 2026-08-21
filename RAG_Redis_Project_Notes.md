# RAG + Redis + Semantic Cache Project

## 1. Project Overview

This project is a production-oriented Retrieval-Augmented Generation (RAG) system enhanced with Redis caching and semantic caching.

The main goal is to reduce unnecessary LLM calls, improve response latency, control LLM/API costs, and create a foundation that can later support multiple users, multiple documents, authentication, APIs, and production deployment.

The current system works with documents such as PDFs. The document is processed into chunks, converted into embeddings, stored in Chroma, and retrieved when a user asks a question. The retrieved context is then passed to an LLM to generate the final answer.

Caching is added in two layers:

1. Exact Redis cache
2. Semantic cache using vector similarity

---

## 2. Why Are We Building This?

A basic RAG system sends many user questions through the full pipeline:

```text
User Question
    ↓
Embedding / Retrieval
    ↓
LLM
    ↓
Answer
```

This has several problems:

- Repeated questions cause repeated LLM calls.
- Similar questions can cause unnecessary LLM calls.
- LLM calls increase latency.
- LLM/API usage can become expensive.
- Repeated retrieval and generation waste compute.
- Cached answers can become stale when documents change.

This project solves these problems progressively.

The intended pipeline is:

```text
User Question
      ↓
Exact Redis Cache
      ↓
Semantic Cache
      ↓
RAG Retrieval
      ↓
LLM
      ↓
Store Answer in Cache
```

The system should use the LLM only when the answer cannot safely be reused from cache.

---

# 3. High-Level Architecture

```text
                         User
                          │
                          ▼
                    User Question
                          │
                          ▼
                ┌───────────────────┐
                │   Exact Redis     │
                │      Cache        │
                └─────────┬─────────┘
                          │
                    Cache Hit?
                     /       \
                   YES        NO
                    │          │
                    ▼          ▼
                 Answer   Semantic Cache
                              │
                       Similar Question?
                         /          \
                       YES           NO
                        │             │
                        ▼             ▼
                   Redis GET         RAG
                        │             │
                    Found?            ▼
                   /     \         Chroma
                 YES      NO          │
                  │        │          ▼
                  ▼        ▼       Context
                Answer   RAG          │
                           │          ▼
                           │         LLM
                           │          │
                           └────┬─────┘
                                ▼
                         Store in Redis
                                │
                                ▼
                       Store Semantic Entry
```

---

# 4. Technology Stack

## Current Stack

- Python
- UV for Python environment and dependency management
- Redis
- Docker
- Chroma
- LangChain
- Mistral embeddings
- Groq LLM API
- PyPDF
- Python dotenv

## Planned Production Stack

- FastAPI
- PostgreSQL
- Redis
- Chroma or another production vector database
- Docker
- Authentication / JWT
- Logging and monitoring
- Automated tests
- Load balancing

---

# 5. RAG Pipeline

The current RAG pipeline is:

```text
PDF
 ↓
PyPDFLoader
 ↓
Document chunks
 ↓
Embeddings
 ↓
Chroma Vector Database
 ↓
Retriever
 ↓
Relevant Context
 ↓
LLM
 ↓
Answer
```

## Document Processing

The document is loaded with `PyPDFLoader`.

Text is split using a recursive text splitter.

Current configuration:

```text
chunk_size = 1000
chunk_overlap = 200
```

The chunks are converted into embeddings and stored in Chroma.

---

# 6. Redis Exact Cache

Redis is the first cache layer.

The application first checks Redis before doing semantic search or calling the LLM.

Example:

```text
Question:
What is deep learning?

Redis:
what is deep learning
        ↓
Cached Answer
```

If the answer exists, the application immediately returns it.

This avoids:

- LLM calls
- Retrieval
- Embedding work
- Additional latency

---

# 7. Redis TTL

TTL means:

**Time To Live**

The current cache TTL is:

```text
3600 seconds
```

which equals:

```text
1 hour
```

When the TTL expires, Redis automatically removes the cached entry.

The application stores answers using an expiration time similar to:

```python
redis_client.set(
    cache_key,
    answer,
    ex=CACHE_TTL
)
```

TTL can be checked manually using Redis CLI:

```text
TTL key_name
```

---

# 8. Semantic Cache

Exact Redis caching only works when the same question is asked again.

For example:

```text
What is CNN?
```

and:

```text
What is CNN?
```

will match.

But these may not be exact matches:

```text
What is CNN?
```

```text
Explain CNN.
```

```text
Can you tell me about convolutional neural networks?
```

A semantic cache attempts to recognize that these questions have similar meanings.

The semantic cache uses embeddings and similarity scores.

Example:

```text
Question A
"What is CNN?"

        ↓

Embedding

        ↓

Semantic Cache

        ↓

Question B
"Explain CNN"

        ↓

High similarity
```

If the score exceeds the configured threshold, the system can reuse the Redis answer associated with the semantic entry.

---

# 9. Semantic Cache Threshold

The current semantic threshold has been around:

```text
0.90
```

Example:

```text
Semantic Score : 0.94
```

may result in:

```text
Semantic Cache Hit
```

while:

```text
Semantic Score : 0.60
```

does not.

Important:

**Semantic similarity is not the same as identical intent.**

For example:

```text
What is ANN?
```

and:

```text
What is ANN and CNN in points?
```

may be semantically similar but require different answers.

Therefore threshold tuning and intent-aware cache decisions are still future work.

---

# 10. Semantic Cache Metadata

Semantic cache entries currently contain metadata such as:

```text
redis_key
created_at
user_id
document_id
question
```

The Redis key acts as a reference from the semantic cache to the actual answer stored in Redis.

Conceptually:

```text
Semantic Cache

"What is CNN?"
      ↓
redis_key
      ↓
Redis
      ↓
Actual Answer
```

This is important because the semantic cache itself is primarily being used to find a similar question. Redis remains the source of the cached answer.

---

# 11. Duplicate Prevention

The system checks whether a very similar question already exists before inserting another semantic entry.

Current logic is approximately:

```text
Similarity >= 0.99
        ↓
Treat as duplicate
        ↓
Do not store another entry
```

Example:

```text
"What is CNN?"

and

"What is CNN?"
```

should not create two semantic entries.

---

# 12. Self-Healing Semantic Cache

There is an important interaction between semantic cache and Redis TTL.

Suppose:

```text
Semantic Cache
"What is deep learning?"
        ↓
Redis Key
```

But the Redis entry has expired.

The semantic cache may still contain the question even though its Redis answer no longer exists.

The current system handles this:

```text
Semantic Cache Hit
        ↓
Redis GET
        ↓
Redis entry missing
        ↓
Delete stale semantic entry
        ↓
Run RAG
        ↓
Generate new answer
        ↓
Store in Redis
        ↓
Store semantic entry again
```

This is a self-healing cache mechanism.

---

# 13. Multi-User Cache Design

The project has started introducing a `RequestContext`.

Conceptually:

```python
RequestContext(
    user_id="satyam",
    document_id="deep_learning"
)
```

The Redis key is designed around:

```text
user_id + document_id + question
```

For example:

```text
satyam:deep_learning:what is cnn
```

This prevents a basic cross-user cache collision.

Without namespacing:

```text
what is cnn
```

could potentially return another user's cached answer.

With namespacing:

```text
user_a:document_a:what is cnn
```

is different from:

```text
user_b:document_b:what is cnn
```

---

# 14. Current Multi-User Limitation

Redis cache namespacing has been implemented conceptually.

However, semantic cache isolation is not fully completed.

An attempt was made to filter Chroma semantic searches by:

```text
user_id
document_id
```

but the installed version:

```text
langchain-community==0.4.2
```

caused a Chroma wrapper conflict when using `where`.

Therefore, the metadata filtering approach was not continued.

The preferred future design is to isolate semantic cache data using separate collections/namespaces based on user/document context rather than relying on the problematic filtering approach.

---

# 15. Current Project Status

## Phase 1 — Basic RAG

Status: **DONE**

Completed:

- PDF loading
- Text splitting
- Embeddings
- Chroma database
- Retrieval
- LLM generation

---

## Phase 2 — Redis Cache + TTL

Status: **DONE**

Completed:

- Redis installation
- Docker Redis container
- Redis connection
- Exact cache
- Cache hit/miss
- TTL
- Redis exception handling

Current TTL:

```text
3600 seconds / 1 hour
```

---

## Phase 3 — Semantic Cache

Status: **MOSTLY DONE**

Completed:

- Semantic cache
- Similarity search
- Similarity threshold
- Redis key reference
- Duplicate prevention
- TTL-aware semantic cleanup
- Self-healing behavior

Remaining:

- Better cache-quality rules
- Better intent handling
- Avoid caching failed answers
- Avoid caching irrelevant/greeting questions
- Threshold evaluation

---

## Phase 4 — Multi-User / Multi-Document

Status: **STARTED, NOT COMPLETE**

Completed:

- RequestContext concept
- User/document-aware Redis key design

Remaining:

- Proper semantic cache isolation
- Real document IDs
- Multiple document support
- User-specific document ownership
- Proper upload workflow

---

## Phase 5 — Cache Quality and Invalidation

Status: **NOT COMPLETE**

Required:

### Do not cache failed answers

Currently the system can cache:

```text
I couldn't find the answer in the document.
```

This should normally not be cached.

Otherwise a later document upload may contain the answer while Redis continues returning the old failure until TTL expires.

### Do not cache greetings

Questions such as:

```text
hi
hello
hii
thanks
bye
```

do not need semantic cache entries.

### Better semantic decision logic

Similarity alone should not determine whether an answer can be reused.

The system should eventually consider:

- semantic similarity
- user/document scope
- query intent
- requested answer format
- additional constraints
- cache age

### Document invalidation

When a new document is uploaded or an existing document changes, related cache entries may become stale.

A simple first implementation can invalidate all cache entries associated with the affected document.

---

# 16. Important Current Problem: Failed Answers

Current behavior can be:

```text
User Question
     ↓
RAG
     ↓
"I couldn't find the answer..."
     ↓
Redis stores it
```

Then:

```text
Same Question
     ↓
Redis Cache Hit
     ↓
"I couldn't find the answer..."
```

This is undesirable.

The intended future behavior is:

```text
RAG
 ↓
Answer found?
 ├── YES → Store in Redis + Semantic Cache
 └── NO  → Return response but DO NOT CACHE
```

---

# 17. Important Current Problem: Semantic False Positives

Semantic caching can sometimes return an answer that is similar but not appropriate.

Example:

```text
Explain CNN.
```

versus:

```text
Explain CNN with examples and mathematical intuition.
```

These may have a high embedding similarity even though the second query requires additional information.

Therefore:

```text
Semantic similarity ≠ exact intent
```

The system needs more intelligent cache validation before using a semantic hit.

---

# 18. Current CLI Application

The current application is still CLI-based.

It runs using:

```text
python -m app.main
```

The user enters questions using:

```text
Enter your question:
```

This is useful for development and testing but is not the final production interface.

---

# 19. Planned FastAPI Architecture

The CLI will eventually be replaced or wrapped by an API.

Expected endpoints:

```text
POST /documents/upload
POST /chat
GET /health
```

Potential future endpoints:

```text
GET /documents
DELETE /documents/{document_id}
GET /cache/stats
```

---

# 20. Authentication

Authentication has not yet been implemented.

Future flow:

```text
User
 ↓
Login
 ↓
JWT
 ↓
user_id
 ↓
RequestContext
 ↓
RAG + Cache
```

The currently hardcoded development context:

```python
user_id="satyam"
```

will eventually come from authenticated user information.

---

# 21. Application Database

Redis is a cache, not the primary application database.

A future PostgreSQL database should store information such as:

```text
users
documents
document ownership
sessions
document metadata
processing status
```

Redis should remain responsible primarily for temporary cached answers and cache-related state.

---

# 22. Future Production Architecture

The intended production architecture is approximately:

```text
                       Internet
                           │
                           ▼
                    Load Balancer
                     /          \
                    /            \
                   ▼              ▼
              FastAPI 1       FastAPI 2
                   │              │
                   └──────┬───────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
            Redis                PostgreSQL
              │
              ▼
         Vector Database
              │
              ▼
             LLM
```

Docker will eventually be used to package the services.

---

# 23. Testing and Monitoring

Not yet implemented.

Future testing should include:

## RAG evaluation

- Retrieval quality
- Answer correctness
- Context relevance
- Hallucination checks

## Cache evaluation

- Exact cache hit rate
- Semantic cache hit rate
- False semantic hits
- Cache misses
- TTL expiration
- LLM calls avoided

## Performance

Track:

```text
response latency
retrieval latency
LLM latency
cache latency
```

Example target metric:

```text
Cache Hit Rate = cached requests / total requests
```

---

# 24. Current Folder Structure

The intended structure is:

```text
RAG_Redis/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── context.py
│   │
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── redis_client.py
│   │   └── cache_services.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   ├── retriever.py
│   │   ├── rag_service.py
│   │   └── semantic_cache.py
│   │
│   └── database/
│       ├── __init__.py
│       └── create_db.py
│
├── Chroma_deep_learning-DB/
├── Semantic_Cache_DB/
│
├── .env
├── pyproject.toml
└── uv.lock
```

---

# 25. Running the Project

The project uses UV and a `.venv` environment.

From the project root:

```powershell
cd C:\Users\3star\Desktop\RAG_Redis
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start Redis:

```powershell
docker start redis
```

Verify Redis:

```powershell
docker ps
```

Run the application:

```powershell
python -m app.main
```

Do not run the application from inside the `app` directory because imports use the `app.*` package structure.

---

# 26. Recreating the Chroma Database

The database creation script can be run with:

```powershell
python -m app.database.create_db
```

This should only be run when the Chroma database needs to be created or rebuilt.

It should not be necessary on every application startup.

---

# 27. Current Startup Sequence

Every time the project needs to be run:

```powershell
cd C:\Users\3star\Desktop\RAG_Redis

.\.venv\Scripts\Activate.ps1

docker start redis

python -m app.main
```

---

# 28. Immediate Next Task

The next recommended task is NOT FastAPI yet.

First finish cache correctness.

Priority:

```text
1. Stop caching failed answers
        ↓
2. Stop caching greetings/useless queries
        ↓
3. Test and tune semantic threshold
        ↓
4. Improve semantic cache decision logic
        ↓
5. Finish user/document semantic isolation
        ↓
6. Implement document cache invalidation
        ↓
7. Move to FastAPI
```

---

# 29. Complete Roadmap

```text
PHASE 1
Basic RAG
✅ DONE

        ↓

PHASE 2
Redis Exact Cache + TTL
✅ DONE

        ↓

PHASE 3
Semantic Cache
🟡 MOSTLY DONE

        ↓

PHASE 4
Multi-user + Multi-document
🟡 STARTED

        ↓

PHASE 5
Cache Quality + Invalidation
❌ NOT DONE

        ↓

PHASE 6
FastAPI Backend
❌ NOT DONE

        ↓

PHASE 7
Authentication + PostgreSQL
❌ NOT DONE

        ↓

PHASE 8
Docker + Deployment + Scaling
❌ NOT DONE

        ↓

PHASE 9
Testing + Evaluation + Monitoring
❌ NOT DONE
```

---

# 30. Project Goal

The final goal is not simply to build a chatbot.

The goal is to build a **production-oriented, multi-user RAG platform with intelligent caching** where:

- Documents can be uploaded by users.
- Documents are processed and embedded.
- Questions are answered using retrieved document context.
- Exact repeated questions are served from Redis.
- Semantically similar questions can reuse existing answers when safe.
- Cache entries expire automatically.
- Stale semantic entries self-heal.
- Users cannot access another user's cached answers.
- Document changes invalidate stale answers.
- LLM usage is minimized.
- The system exposes APIs through FastAPI.
- Authentication controls user/document access.
- The application can be containerized and scaled.
- Cache performance and RAG quality can be measured.

The key design principle is:

> **Use the LLM when necessary, not when it is unnecessary.**
