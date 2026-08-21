from app.cache.redis_client import redis_client
from app.config import CACHE_TTL
from app.context import RequestContext


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
        return redis_client.get(cache_key)

    except Exception as e:
        print(f"Redis Read Error : {e}")
        return None


def get_cached_answer_by_key(redis_key: str):
    """
    Get answer directly using Redis key.
    Used by Semantic Cache.
    """

    try:
        return redis_client.get(redis_key)

    except Exception as e:
        print(f"Redis Read Error : {e}")
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
        print(f"Redis Write Error : {e}")


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
        print(f"Redis Delete Error : {e}")