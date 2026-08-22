import time
from fastapi import APIRouter, Response, HTTPException

from app.context import RequestContext
from app.schemas import ChatRequest, ChatResponse
from app.utils.logger import logger
from app.utils.guardrails import should_cache_response

from app.cache.cache_services import (
    get_cached_answer,
    get_cached_answer_by_key,
    store_cached_answer
)

from app.rag.intent_router import route_intent
from app.rag.rag_service import ask_rag
from app.rag.retriever import vector_store

from app.rag.semantic_cache import (
    delete_semantic_question,
    search_semantic_cache,
    store_semantic_question
)

router = APIRouter(prefix="/api/v1", tags=["RAG Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, response_obj: Response):
    """
    RAG Query Endpoint with Multi-Layer Caching & Strict Document Validation.
    """
    start_time = time.time()
    context = RequestContext(user_id=req.user_id, document_id=req.document_id)
    query = req.question.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Dynamic Multilingual Intent Router
    intent_res = route_intent(query)
    if intent_res.get("is_greeting"):
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        response_obj.headers["x-cache-status"] = "none"
        response_obj.headers["x-latency-ms"] = str(elapsed_ms)
        return ChatResponse(
            question=query,
            answer=intent_res["response"],
            cache_hit_type="none",
            is_greeting=True,
            latency_ms=elapsed_ms
        )

    # 2. Document Existence Check: Verify PDF is indexed in Vector Store before Cache/RAG
    try:
        doc_check = vector_store.get(where={"document_id": req.document_id}, limit=1)
        if not doc_check or not doc_check.get("documents"):
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            response_obj.headers["x-cache-status"] = "none"
            response_obj.headers["x-latency-ms"] = str(elapsed_ms)
            return ChatResponse(
                question=query,
                answer=f"⚠️ No document found for '{req.document_id}'. Please upload a PDF document first!",
                cache_hit_type="none",
                is_greeting=False,
                latency_ms=elapsed_ms
            )
    except Exception as e:
        logger.warning(f"Document existence check error: {e}")

    # 3. Exact Redis Cache Check
    if not req.bypass_cache:
        cached_answer = get_cached_answer(context, query)
        if cached_answer:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            response_obj.headers["x-cache-status"] = "exact"
            response_obj.headers["x-latency-ms"] = str(elapsed_ms)
            return ChatResponse(
                question=query,
                answer=cached_answer,
                cache_hit_type="exact",
                is_greeting=False,
                latency_ms=elapsed_ms
            )

    # 4. Semantic Vector Cache Check
    if not req.bypass_cache:
        redis_key = search_semantic_cache(context, query)
        if redis_key:
            cached_answer = get_cached_answer_by_key(redis_key)
            if cached_answer:
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                response_obj.headers["x-cache-status"] = "semantic"
                response_obj.headers["x-latency-ms"] = str(elapsed_ms)
                return ChatResponse(
                    question=query,
                    answer=cached_answer,
                    cache_hit_type="semantic",
                    is_greeting=False,
                    latency_ms=elapsed_ms
                )
            # Self-healing stale key cleanup
            delete_semantic_question(context, redis_key)

    # 5. Production RAG Pipeline (Query Rewriting + 2-Stage Retrieval + Reranking)
    answer = ask_rag(query, context)

    # 6. Guardrail Cache Persistence
    if should_cache_response(answer):
        store_cached_answer(context, query, answer)
        store_semantic_question(context, query)

    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    response_obj.headers["x-cache-status"] = "none"
    response_obj.headers["x-latency-ms"] = str(elapsed_ms)

    return ChatResponse(
        question=query,
        answer=answer,
        cache_hit_type="none",
        is_greeting=False,
        latency_ms=elapsed_ms
    )
