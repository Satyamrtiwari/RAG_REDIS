import re
import json
import time
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from app.rag.intent_router import route_intent
from app.rag.query_rewriter import rewrite_query
from app.rag.reranker import rerank_documents
from app.rag.llm import model
from app.cache.redis_client import redis_client
from app.enterprise.pinecone_service import query_pinecone_candidates
from app.utils.logger import logger

CACHE_TTL = 3600  # 1 hour

enterprise_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a professional, helpful, and accurate AI customer assistant for the company.
Answer the visitor's question based strictly on the provided Context below.

Guidelines:
1. Be polite, concise, professional, and welcoming.
2. If the answer is found in the Context, answer clearly and accurately.
3. If the answer is NOT mentioned or cannot be deduced from the Context, politely state:
   "I don't have specific details on that in our knowledge base. Please contact our support team for further assistance."
4. Never make up facts, pricing, or policies not present in the context.

Context:
{context}
"""),
    ("human", "{question}")
])


def normalize_query(q: str) -> str:
    """Normalizes query for exact Redis caching."""
    clean = re.sub(r'[^\w\s]', '', q.lower()).strip()
    return re.sub(r'\s+', ' ', clean)


def ask_enterprise_rag(client_id: str, question: str) -> Dict[str, Any]:
    """
    Full Enterprise RAG Pipeline:
    1. Multilingual Intent Check (Sub-50ms instant response)
    2. Upstash Redis Exact Match Cache Check (Sub-15ms)
    3. Query Rewriter
    4. Pinecone Multi-Tenant Vector Search (Top-15 candidates)
    5. FlashRank Cross-Encoder Reranking (Top-5 purest chunks)
    6. LLM Context Synthesis (Groq Llama 3.3 + Mistral fallback)
    7. Upstash Redis Cache Store
    """
    start_time = time.time()
    clean_q = normalize_query(question)

    # 1. Dynamic Multilingual Intent Router
    intent_res = route_intent(question)
    if intent_res.get("is_greeting") and intent_res.get("response"):
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "answer": intent_res["response"],
            "sources": [],
            "cache_hit": False,
            "is_greeting": True,
            "latency_ms": elapsed_ms
        }

    # 2. Tier-1 Upstash Redis Exact Query Cache
    cache_key = f"ent:cache:{client_id}:{clean_q}"
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                cached_obj = json.loads(cached_data)
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                logger.info(f"⚡ Redis Exact Cache Hit for client '{client_id}': '{clean_q}' ({elapsed_ms}ms)")
                return {
                    "answer": cached_obj.get("answer"),
                    "sources": cached_obj.get("sources", []),
                    "cache_hit": True,
                    "is_greeting": False,
                    "latency_ms": elapsed_ms
                }
        except Exception as e:
            logger.warning(f"⚠️ Redis cache read error: {e}")

    # 3. Query Rewriter
    rewritten_query = rewrite_query(question)

    # 4. Pinecone Multi-Tenant Candidate Retrieval (k=15)
    candidate_docs = query_pinecone_candidates(client_id=client_id, query=rewritten_query, top_k=15)

    if not candidate_docs:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.warning(f"⚠️ No knowledge base vectors found for client '{client_id}'.")
        return {
            "answer": "Our knowledge base does not have information on this topic yet. Please check back later or contact customer support.",
            "sources": [],
            "cache_hit": False,
            "is_greeting": False,
            "latency_ms": elapsed_ms
        }

    # 5. FlashRank Cross-Encoder Reranker (Top 15 -> Top 5)
    reranked_docs = rerank_documents(rewritten_query, candidate_docs, top_n=5)

    # Extract distinct source names
    sources = list({doc.metadata.get("source_name", "Knowledge Base") for doc in reranked_docs if doc.metadata})

    # Combine context
    context_str = "\n\n---\n\n".join(doc.page_content for doc in reranked_docs)

    # 6. LLM Context Synthesis (Groq Llama 3.3 + Mistral fallback)
    formatted_prompt = enterprise_prompt.invoke({
        "context": context_str,
        "question": question
    })

    llm_res = model.invoke(formatted_prompt)
    answer = llm_res.content.strip()

    # 7. Write to Upstash Redis Cache
    if redis_client:
        try:
            cache_payload = json.dumps({"answer": answer, "sources": sources})
            redis_client.setex(cache_key, CACHE_TTL, cache_payload)
        except Exception as e:
            logger.warning(f"⚠️ Redis cache write error: {e}")

    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    return {
        "answer": answer,
        "sources": sources,
        "cache_hit": False,
        "is_greeting": False,
        "latency_ms": elapsed_ms
    }
