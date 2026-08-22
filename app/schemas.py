from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., example="what is cnn?")
    user_id: str = Field(default="satyam", example="satyam")
    document_id: str = Field(default="deep_learning", example="deep_learning")
    bypass_cache: bool = Field(default=False, description="If true, bypasses Redis and Semantic Cache")


class ChatResponse(BaseModel):
    question: str
    answer: str
    cache_hit_type: str = Field(..., description="exact | semantic | none")
    is_greeting: bool = False
    latency_ms: float


class DocumentUploadResponse(BaseModel):
    message: str
    filename: str
    user_id: str
    document_id: str
    chunks_created: int


class CacheStatsResponse(BaseModel):
    total_queries: int
    exact_redis_hits: int
    semantic_cache_hits: int
    total_cache_hits: int
    rag_llm_calls: int
    cache_hit_rate_pct: float
    estimated_tokens_saved: int
    estimated_llm_calls_avoided: int


class HealthResponse(BaseModel):
    status: str
    redis_connected: bool
    groq_configured: bool
    mistral_configured: bool
