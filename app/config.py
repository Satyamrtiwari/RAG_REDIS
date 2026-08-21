from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = "localhost"
REDIS_PORT = 6379

CACHE_TTL = 3600

# MODEL_NAME = "mistral-small-2506"

MODEL_NAME = "openai/gpt-oss-20b"

CHROMA_DB_PATH = "Chroma_deep_learning-DB"

SEARCH_TYPE = "similarity"

SEARCH_KWARGS = {
    "k": 15,
}