import os
from typing import Optional
from fastapi import APIRouter, Query
from app.schemas import CacheStatsResponse, HealthResponse
from app.cache.metrics import get_cache_stats, reset_cache_stats
from app.cache.redis_client import redis_client

router = APIRouter(tags=["Metrics & Health"])


@router.get("/api/v1/cache/stats", response_model=CacheStatsResponse)
def cache_stats_endpoint(user_id: Optional[str] = Query(None)):
    """
    Returns live performance analytics dashboard metrics for a user or globally.
    """
    stats = get_cache_stats(user_id=user_id)
    return CacheStatsResponse(
        total_queries=stats.get("total_queries", 0),
        exact_redis_hits=stats.get("exact_redis_hits", 0),
        semantic_cache_hits=stats.get("semantic_cache_hits", 0),
        total_cache_hits=stats.get("total_cache_hits", 0),
        rag_llm_calls=stats.get("rag_llm_calls", 0),
        cache_hit_rate_pct=stats.get("cache_hit_rate_pct", 0.0),
        estimated_tokens_saved=stats.get("estimated_tokens_saved", 0),
        estimated_llm_calls_avoided=stats.get("estimated_llm_calls_avoided", 0)
    )


@router.post("/api/v1/cache/stats/reset")
def reset_stats_endpoint(user_id: Optional[str] = Query(None)):
    """
    Resets metrics counters to zero.
    """
    reset_cache_stats(user_id=user_id)
    return {"message": "Metrics reset successfully", "user_id": user_id or "global"}


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Readiness and Liveness probe endpoint.
    """
    redis_ok = False
    try:
        redis_ok = redis_client.ping()
    except Exception:
        pass

    groq_ok = bool(os.getenv("GROQ_API_KEY"))
    mistral_ok = bool(os.getenv("MISTRAL_API_KEY"))

    status = "healthy" if (redis_ok and groq_ok and mistral_ok) else "degraded"

    return HealthResponse(
        status=status,
        redis_connected=redis_ok,
        groq_configured=groq_ok,
        mistral_configured=mistral_ok
    )
