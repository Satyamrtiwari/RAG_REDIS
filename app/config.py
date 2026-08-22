import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", None)
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", None)

CACHE_TTL = 3600

MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-20b")

CHROMA_DB_PATH = "Chroma_deep_learning-DB"

SEARCH_TYPE = "similarity"

SEARCH_KWARGS = {
    "k": 15,
}