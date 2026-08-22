import os
import redis
from urllib.parse import urlparse

from app.config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
    UPSTASH_REDIS_REST_URL,
    UPSTASH_REDIS_REST_TOKEN
)
from app.utils.logger import logger

def create_redis_client():
    """
    Creates a Redis client that seamlessly connects to:
    1. Local Docker Redis (localhost:6379)
    2. Upstash Cloud Redis (via REDIS_HOST/REDIS_PASSWORD or UPSTASH_REDIS_REST_URL)
    """
    # 1. Check if Upstash REST URL/Token provided
    if UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
        parsed = urlparse(UPSTASH_REDIS_REST_URL)
        host = parsed.netloc or parsed.path
        logger.info(f"🌐 Connecting to Upstash Cloud Redis: {host}")
        return redis.Redis(
            host=host,
            port=6379,
            password=UPSTASH_REDIS_REST_TOKEN,
            ssl=True,
            ssl_cert_reqs=None,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True
        )

    # 2. Check if REDIS_PASSWORD or cloud host provided
    if REDIS_PASSWORD or REDIS_HOST != "localhost":
        logger.info(f"🌐 Connecting to Cloud Redis: {REDIS_HOST}:{REDIS_PORT}")
        return redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            ssl=True if REDIS_PASSWORD else False,
            ssl_cert_reqs=None if REDIS_PASSWORD else "required",
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True
        )

    # 3. Fallback to Local Redis
    logger.info(f"💻 Connecting to Local Redis: {REDIS_HOST}:{REDIS_PORT}")
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_timeout=3.0,
        socket_connect_timeout=3.0,
        retry_on_timeout=True
    )


redis_client = create_redis_client()

try:
    redis_client.ping()
    logger.info("✅ Redis Connected Successfully")
except Exception as e:
    logger.error(f"❌ Redis Connection Error: {e}")