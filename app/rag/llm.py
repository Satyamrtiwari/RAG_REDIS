import os
import random
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from app.config import MODEL_NAME
from app.utils.logger import logger


def get_groq_api_keys() -> list[str]:
    """Retrieves list of Groq API keys from environment (supports comma-separated list)."""
    raw = os.getenv("GROQ_API_KEYS") or os.getenv("GROQ_API_KEY") or ""
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    return keys


def get_mistral_api_keys() -> list[str]:
    """Retrieves list of Mistral API keys from environment (supports comma-separated list)."""
    raw = os.getenv("MISTRAL_API_KEYS") or os.getenv("MISTRAL_API_KEY") or ""
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    return keys


class ResilientLLMWrapper:
    """
    Resilient LLM Wrapper:
    1. Rotates across multiple Groq API keys if rate limits or errors occur.
    2. Automatically falls back to Mistral AI if all Groq keys fail.
    """
    def __init__(self):
        self.groq_keys = get_groq_api_keys()
        self.mistral_keys = get_mistral_api_keys()

    def invoke(self, input_prompt):
        # 1. Try Groq Keys
        groq_keys = get_groq_api_keys()
        if groq_keys:
            # Shuffle keys to distribute load
            shuffled_keys = groq_keys.copy()
            random.shuffle(shuffled_keys)

            for key in shuffled_keys:
                try:
                    groq_model = ChatGroq(model=MODEL_NAME, groq_api_key=key)
                    response = groq_model.invoke(input_prompt)
                    return response
                except Exception as e:
                    logger.warning(f"⚠️ Groq Key fallback triggered (Key ending '...{key[-6:]}'): {e}")

        # 2. Fallback to Mistral AI if Groq fails or no Groq keys provided
        mistral_keys = get_mistral_api_keys()
        if mistral_keys:
            for key in mistral_keys:
                try:
                    logger.info("🔄 Falling back to Mistral AI provider...")
                    mistral_model = ChatMistralAI(model="mistral-small-2506", mistral_api_key=key)
                    response = mistral_model.invoke(input_prompt)
                    return response
                except Exception as e:
                    logger.warning(f"⚠️ Mistral Key fallback error: {e}")

        # 3. Final attempt with default environment configuration
        logger.info("⚡ Final attempt using default ChatGroq model...")
        default_groq = ChatGroq(model=MODEL_NAME)
        return default_groq.invoke(input_prompt)


model = ResilientLLMWrapper()