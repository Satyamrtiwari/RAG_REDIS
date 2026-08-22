from app.context import RequestContext
from app.utils.logger import logger
from app.utils.guardrails import should_cache_response

from app.cache.cache_services import (
    get_cached_answer,
    get_cached_answer_by_key,
    store_cached_answer,
    clear_document_cache
)

from app.cache.metrics import log_cache_stats
from app.rag.intent_router import route_intent
from app.rag.rag_service import ask_rag

from app.rag.semantic_cache import (
    delete_semantic_question,
    search_semantic_cache,
    store_semantic_question
)


def run_cli():
    # Simulating logged-in user context
    context = RequestContext(
        user_id="satyam",
        document_id="deep_learning"
    )

    logger.info("--------------- Options: 0 to Exit | /stats for Dashboard | /clear to Invalidate Cache ---------------")

    while True:
        try:
            query = input("\nEnter your question : ")
        except (EOFError, KeyboardInterrupt):
            logger.info("Exited")
            break

        clean_input = query.strip()

        if clean_input == "0":
            logger.info("Exited")
            break

        if clean_input == "/stats":
            log_cache_stats()
            continue

        if clean_input == "/clear":
            clear_document_cache(context)
            continue

        if not clean_input:
            continue

        # -------------------------------------------------
        # 0. Multilingual Dynamic Intent Router
        # -------------------------------------------------
        intent_res = route_intent(clean_input)
        if intent_res.get("is_greeting"):
            logger.info("----------------------------------------")
            logger.info(f"AI: {intent_res['response']}")
            continue

        # -------------------------------------------------
        # 1. Exact Redis Cache
        # -------------------------------------------------
        cached_answer = get_cached_answer(context, clean_input)
        if cached_answer:
            logger.info("----------------------------------------")
            logger.info("Redis Cache Hit ✅")
            logger.info(f"AI: {cached_answer}")
            continue

        # -------------------------------------------------
        # 2. Semantic Cache
        # -------------------------------------------------
        redis_key = search_semantic_cache(context, clean_input)
        if redis_key:
            cached_answer = get_cached_answer_by_key(redis_key)
            if cached_answer:
                logger.info("----------------------------------------")
                logger.info("Semantic Cache Hit ✅")
                logger.info(f"AI: {cached_answer}")
                continue

            logger.info("⚠️ Redis Cache Expired")
            delete_semantic_question(context, redis_key)
            logger.info("♻️ Rebuilding Cache...")

        # -------------------------------------------------
        # 3. Production RAG Pipeline (Query Rewriter + 2-Stage Reranking)
        # -------------------------------------------------
        response = ask_rag(clean_input, context)

        # -------------------------------------------------
        # 4. Guardrail Cache Quality Check
        # -------------------------------------------------
        if should_cache_response(response):
            store_cached_answer(context, clean_input, response)
            store_semantic_question(context, clean_input)
            logger.info("💾 Cached response successfully.")
        else:
            logger.warning("⚠️ Response was a refusal/failure. Skipped caching.")

        logger.info("----------------------------------------")
        logger.info(f"AI: {response}")


if __name__ == "__main__":
    run_cli()