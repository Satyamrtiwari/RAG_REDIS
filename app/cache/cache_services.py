from app.cache.redis_client import redis_client
from app.config import CACHE_TTL
from app.context import RequestContext
from app.utils.logger import logger
from app.cache.metrics import record_event


def get_cache_key(
    context: RequestContext,
    question: str
):
    """
    Generate a unique Redis cache key using:
    user_id + document_id + question
    """
    return (
        f"{context.user_id}:"
        f"{context.document_id}:"
        f"{question.strip().lower()}"
    )


def get_cached_answer(
    context: RequestContext,
    question: str
):
    """
    Get answer from Redis using question.
    """
    cache_key = get_cache_key(context, question)

    try:
        answer = redis_client.get(cache_key)
        if answer:
            record_event("exact_hit", user_id=context.user_id)
        return answer
    except Exception as e:
        logger.error(f"Redis Read Error : {e}")
        return None


def get_cached_answer_by_key(redis_key: str, user_id: str = "global"):
    """
    Get answer directly using Redis key.
    Used by Semantic Cache.
    """
    try:
        answer = redis_client.get(redis_key)
        if answer:
            record_event("semantic_hit", user_id=user_id)
        return answer
    except Exception as e:
        logger.error(f"Redis Read Error : {e}")
        return None


def store_cached_answer(
    context: RequestContext,
    question: str,
    answer: str
):
    """
    Store answer in Redis.
    """
    cache_key = get_cache_key(context, question)

    try:
        redis_client.set(
            cache_key,
            answer,
            ex=CACHE_TTL
        )
    except Exception as e:
        logger.error(f"Redis Write Error : {e}")


def delete_cache(
    context: RequestContext,
    question: str
):
    """
    Delete a Redis cache entry.
    """
    cache_key = get_cache_key(context, question)

    try:
        redis_client.delete(cache_key)
    except Exception as e:
        logger.error(f"Redis Delete Error : {e}")


def clear_document_cache(context: RequestContext):
    """
    Document Invalidation Service:
    Purges all Redis key entries and Chroma semantic cache vectors
    belonging to a specific user_id and document_id.
    """
    from app.rag.semantic_cache import clear_semantic_cache_for_context

    pattern = f"{context.user_id}:{context.document_id}:*"
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"🧹 Flushed {len(keys)} Redis cache keys matching pattern '{pattern}'")
        else:
            logger.info(f"🧹 No Redis keys found matching pattern '{pattern}'")

        # Purge isolated Chroma semantic collection
        clear_semantic_cache_for_context(context)
        logger.info(f"✅ Document Cache Invalidation complete for {context.user_id}:{context.document_id}")

    except Exception as e:
        logger.error(f"Document Cache Invalidation Error: {e}")