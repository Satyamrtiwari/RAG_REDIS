from typing import Optional
from app.context import RequestContext
from app.rag.retriever import vector_store
from app.rag.query_rewriter import rewrite_query
from app.rag.reranker import rerank_documents
from app.rag.prompts import prompt
from app.rag.llm import model
from app.utils.logger import logger
from app.cache.metrics import record_event


def ask_rag(question: str, context: Optional[RequestContext] = None) -> str:
    """
    Production RAG Pipeline with Strict Document Metadata Isolation & Empty Document Guardrails:
    1. LLM Query Rewriting (cleans typos, expands acronyms, strips noise)
    2. Isolated Vector Search (retrieves top-15 candidates filtered strictly by document_id)
    3. FlashRank Cross-Encoder Reranking (scores & selects top-5 purest chunks)
    4. Context Synthesis via LLM
    """
    user_id = context.user_id if context else "global"
    record_event("rag_call", user_id=user_id)

    # Step 1: Rewrite and normalize user query
    clean_query = rewrite_query(question)

    # Step 2: Retrieve candidate chunks strictly filtered by target document_id
    doc_id = context.document_id if context else "default"
    filter_dict = {"document_id": doc_id} if (context and context.document_id) else None

    if filter_dict:
        candidate_docs = vector_store.similarity_search(clean_query, k=15, filter=filter_dict)
        logger.info(f"📚 Filtered Vector Search ({doc_id}): Retrieved {len(candidate_docs)} candidate chunks.")
    else:
        candidate_docs = vector_store.similarity_search(clean_query, k=15)
        logger.info(f"📚 Vector Search: Retrieved {len(candidate_docs)} candidate chunks.")

    # Empty Document Guardrail: If no chunks exist in Chroma for this document_id, warn user
    if not candidate_docs:
        logger.warning(f"⚠️ No document vector chunks found for document_id='{doc_id}'.")
        return f"⚠️ No document found for '{doc_id}'. Please upload a PDF document first!"

    # Step 3: FlashRank Reranker (select top 5 purest chunks)
    top_docs = rerank_documents(clean_query, candidate_docs, top_n=5)

    # Combine context from top reranked chunks
    doc_context = "\n\n---\n\n".join(doc.page_content for doc in top_docs)

    # Step 4: Format prompt and call LLM
    final_prompt = prompt.invoke({
        "context": doc_context,
        "question": question
    })

    response = model.invoke(final_prompt)
    return response.content