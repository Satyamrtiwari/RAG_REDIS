import redis

from app.config import REDIS_HOST, REDIS_PORT
from app.utils.logger import logger

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

try:
    redis_client.ping()
    logger.info("✅ Redis Connected")

except Exception as e:
    logger.error(f"❌ Redis Not Available: {e}")