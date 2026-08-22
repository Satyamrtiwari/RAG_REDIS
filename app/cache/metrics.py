"""
Metrics and Observability Module for RAG + Redis Cache.
Tracks exact hits, semantic hits, LLM calls, hit rates, and estimated cost/token savings per user.
"""

from typing import Optional
from app.cache.redis_client import redis_client
from app.utils.logger import logger

STATS_PREFIX = "metrics:rag_cache"


def record_event(event_type: str, user_id: Optional[str] = "global"):
    """
    Increments metrics counters in Redis per user and globally.
    event_type can be: 'exact_hit', 'semantic_hit', 'rag_call', 'refusal_skipped'
    """
    clean_user = user_id.strip().lower() if user_id else "global"
    try:
        # User-scoped counters
        redis_client.incr(f"{STATS_PREFIX}:{clean_user}:{event_type}")
        redis_client.incr(f"{STATS_PREFIX}:{clean_user}:total_queries")
        
        # Global fallback counters
        if clean_user != "global":
            redis_client.incr(f"{STATS_PREFIX}:global:{event_type}")
            redis_client.incr(f"{STATS_PREFIX}:global:total_queries")
    except Exception as e:
        logger.warning(f"⚠️ Metrics recording error: {e}")


def get_cache_stats(user_id: Optional[str] = None) -> dict:
    """
    Returns cache performance statistics for a specific user_id or globally.
    """
    clean_user = user_id.strip().lower() if user_id else "global"
    try:
        total = int(redis_client.get(f"{STATS_PREFIX}:{clean_user}:total_queries") or 0)
        exact = int(redis_client.get(f"{STATS_PREFIX}:{clean_user}:exact_hit") or 0)
        semantic = int(redis_client.get(f"{STATS_PREFIX}:{clean_user}:semantic_hit") or 0)
        rag_calls = int(redis_client.get(f"{STATS_PREFIX}:{clean_user}:rag_call") or 0)

        # Fallback to global if user has zero queries and user_id was not explicitly requested
        if total == 0 and not user_id:
            total = int(redis_client.get(f"{STATS_PREFIX}:global:total_queries") or 0)
            exact = int(redis_client.get(f"{STATS_PREFIX}:global:exact_hit") or 0)
            semantic = int(redis_client.get(f"{STATS_PREFIX}:global:semantic_hit") or 0)
            rag_calls = int(redis_client.get(f"{STATS_PREFIX}:global:rag_call") or 0)

        total_hits = exact + semantic
        hit_rate = (total_hits / total * 100) if total > 0 else 0.0

        # Average tokens per LLM query estimate (~500 tokens answer + ~2000 context = ~2500 tokens)
        tokens_saved = total_hits * 2500

        return {
            "user_id": clean_user,
            "total_queries": total,
            "exact_redis_hits": exact,
            "semantic_cache_hits": semantic,
            "total_cache_hits": total_hits,
            "rag_llm_calls": rag_calls,
            "cache_hit_rate_pct": round(hit_rate, 2),
            "estimated_tokens_saved": tokens_saved,
            "estimated_llm_calls_avoided": total_hits
        }
    except Exception as e:
        logger.warning(f"⚠️ Error reading cache stats: {e}")
        return {}


def reset_cache_stats(user_id: Optional[str] = None):
    """
    Resets metrics counters to zero for a specific user_id or globally.
    """
    clean_user = user_id.strip().lower() if user_id else "global"
    pattern = f"{STATS_PREFIX}:{clean_user}:*"
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"🧹 Reset metrics for user '{clean_user}' ({len(keys)} counters cleared)")
    except Exception as e:
        logger.warning(f"⚠️ Error resetting cache stats: {e}")


def log_cache_stats():
    """
    Logs formatted cache statistics.
    """
    stats = get_cache_stats()
    if not stats:
        return

    logger.info("==================================================")
    logger.info("📊 CACHE PERFORMANCE & METRICS DASHBOARD")
    logger.info(f" Total Queries Processed : {stats.get('total_queries', 0)}")
    logger.info(f" Exact Redis Hits        : {stats.get('exact_redis_hits', 0)}")
    logger.info(f" Semantic Cache Hits     : {stats.get('semantic_cache_hits', 0)}")
    logger.info(f" Full RAG LLM Calls      : {stats.get('rag_llm_calls', 0)}")
    logger.info(f" Cache Hit Rate          : {stats.get('cache_hit_rate_pct', 0.0)}%")
    logger.info(f" Estimated Tokens Saved  : {stats.get('estimated_tokens_saved', 0)}")
    logger.info("==================================================")
