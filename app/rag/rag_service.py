from app.rag.retriever import retriever
from app.rag.query_rewriter import rewrite_query
from app.rag.reranker import rerank_documents
from app.rag.prompts import prompt
from app.rag.llm import model
from app.utils.logger import logger
from app.cache.metrics import record_event


def ask_rag(question: str) -> str:
    """
    Production RAG Pipeline:
    1. LLM Query Rewriting (cleans typos, expands acronyms, strips noise)
    2. Vector Candidate Search (retrieves top-15 candidate chunks)
    3. FlashRank Cross-Encoder Reranking (scores & selects top-5 purest chunks)
    4. Context Synthesis via LLM
    """
    record_event("rag_call")

    # Step 1: Rewrite and normalize user query
    clean_query = rewrite_query(question)

    # Step 2: Retrieve candidate chunks from vector store
    candidate_docs = retriever.invoke(clean_query)
    logger.info(f"📚 Vector Search: Retrieved {len(candidate_docs)} candidate chunks.")

    # Step 3: FlashRank Reranker (select top 5 purest chunks)
    top_docs = rerank_documents(clean_query, candidate_docs, top_n=5)

    # Combine context from top reranked chunks
    context = "\n\n---\n\n".join(doc.page_content for doc in top_docs)

    # Step 4: Format prompt and call LLM
    final_prompt = prompt.invoke({
        "context": context,
        "question": question
    })

    response = model.invoke(final_prompt)
    return response.content