from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = "localhost"
REDIS_PORT = 6379

CACHE_TTL = 3600

# MODEL_NAME = "mistral-small-2506"

MODEL_NAME = "llama-3.3-70b-versatile"

CHROMA_DB_PATH = "Chroma_deep_learning-DB"

SEARCH_TYPE = "mmr"

SEARCH_KWARGS = {
    "k": 4,
    "fetch_k": 10,
    "lambda_multi": 0.5,
}