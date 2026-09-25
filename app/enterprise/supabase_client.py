import os
import json
import secrets
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client
from app.utils.logger import logger
from app.cache.redis_client import redis_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase_instance: Optional[Client] = None


def get_supabase() -> Client:
    """Returns singleton Supabase client instance."""
    global _supabase_instance
    if _supabase_instance is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL or SUPABASE_KEY is missing in environment variables.")
        _supabase_instance = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_instance


def create_client_record(
    client_name: str,
    allowed_domains: Optional[List[str]] = None,
    rate_limit_per_day: int = 1000
) -> Dict[str, Any]:
    """
    Creates a new client company workspace in Supabase with a secure API key.
    """
    sp = get_supabase()
    api_key = f"sk_live_{secrets.token_hex(20)}"
    allowed_domains = allowed_domains or []

    payload = {
        "client_name": client_name.strip(),
        "api_key": api_key,
        "allowed_domains": allowed_domains,
        "is_active": True,
        "rate_limit_per_day": rate_limit_per_day
    }

    res = sp.table("clients").insert(payload).execute()
    if not res.data:
        raise RuntimeError("Failed to create client in Supabase.")

    client_data = res.data[0]
    logger.info(f"🏢 Created Enterprise Client '{client_name}' (ID: {client_data['id']})")
    return client_data


def get_client_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Validates client API key against Supabase.
    Results are cached in Upstash Redis (TTL 300s) for sub-1ms authorization!
    """
    if not api_key:
        return None

    clean_key = api_key.strip()
    cache_key = f"auth:client:{clean_key}"

    # 1. Check Redis Cache
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"⚠️ Redis auth cache read error: {e}")

    # 2. Query Supabase
    try:
        sp = get_supabase()
        res = sp.table("clients").select("*").eq("api_key", clean_key).eq("is_active", True).limit(1).execute()
        if not res.data:
            return None

        client_data = res.data[0]

        # 3. Store in Redis Cache for 5 minutes (300 seconds)
        if redis_client:
            try:
                redis_client.setex(cache_key, 300, json.dumps(client_data))
            except Exception as e:
                logger.warning(f"⚠️ Redis auth cache write error: {e}")

        return client_data

    except Exception as e:
        logger.error(f"❌ Supabase API key validation error: {e}")
        return None


def record_knowledge_source(
    client_id: str,
    source_type: str,
    source_name: str,
    chunk_count: int,
    status: str = "ready"
) -> Dict[str, Any]:
    """
    Records an ingested document, URL, or raw text piece in Supabase.
    """
    sp = get_supabase()
    payload = {
        "client_id": client_id,
        "source_type": source_type,
        "source_name": source_name,
        "chunk_count": chunk_count,
        "status": status
    }
    res = sp.table("knowledge_sources").insert(payload).execute()
    return res.data[0] if res.data else payload


def get_knowledge_sources(client_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all indexed sources for a given client company.
    """
    sp = get_supabase()
    res = sp.table("knowledge_sources").select("*").eq("client_id", client_id).order("created_at", desc=True).execute()
    return res.data or []


def delete_knowledge_source_record(client_id: str, source_id: str) -> bool:
    """
    Deletes a source record from Supabase.
    """
    sp = get_supabase()
    res = sp.table("knowledge_sources").delete().eq("id", source_id).eq("client_id", client_id).execute()
    return bool(res.data)
