"""
Metrics and Observability Module for RAG + Redis Cache.
Tracks exact hits, semantic hits, LLM calls, hit rates, and estimated cost/token savings.
"""

from app.cache.redis_client import redis_client
from app.utils.logger import logger

STATS_PREFIX = "metrics:rag_cache"


def record_event(event_type: str):
    """
    Increments metrics counters in Redis.
    event_type can be: 'exact_hit', 'semantic_hit', 'rag_call', 'refusal_skipped'
    """
    try:
        redis_client.incr(f"{STATS_PREFIX}:{event_type}")
        redis_client.incr(f"{STATS_PREFIX}:total_queries")
    except Exception as e:
        logger.warning(f"⚠️ Metrics recording error: {e}")


def get_cache_stats() -> dict:
    """
    Returns current cache performance statistics and analytics.
    """
    try:
        total = int(redis_client.get(f"{STATS_PREFIX}:total_queries") or 0)
        exact = int(redis_client.get(f"{STATS_PREFIX}:exact_hit") or 0)
        semantic = int(redis_client.get(f"{STATS_PREFIX}:semantic_hit") or 0)
        rag_calls = int(redis_client.get(f"{STATS_PREFIX}:rag_call") or 0)

        total_hits = exact + semantic
        hit_rate = (total_hits / total * 100) if total > 0 else 0.0

        # Average tokens per LLM query estimate (~500 tokens answer + ~2000 context = ~2500 tokens)
        tokens_saved = total_hits * 2500

        return {
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
