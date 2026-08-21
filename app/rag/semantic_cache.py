from datetime import datetime
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.context import RequestContext
from app.rag.embeddings import embedding_model
from app.utils.logger import logger


def get_semantic_cache_store(context: RequestContext) -> Chroma:
    """
    Returns an isolated Chroma collection per user and document context.
    Collection format: semantic_cache_{user_id}_{document_id}
    """
    collection_name = f"semantic_cache_{context.user_id}_{context.document_id}"
    return Chroma(
        collection_name=collection_name,
        persist_directory="Semantic_Cache_DB",
        embedding_function=embedding_model
    )


def store_semantic_question(
    context: RequestContext,
    question: str
):
    """
    Store a question inside context-isolated semantic cache only if it
    doesn't already exist.
    """
    from app.cache.cache_services import get_cache_key

    cache_store = get_semantic_cache_store(context)
    redis_key = get_cache_key(context, question)

    # Check whether a similar question already exists in this context
    existing = cache_store.similarity_search_with_relevance_scores(
        query=question,
        k=1
    )

    if existing:
        document, score = existing[0]
        logger.info(f"Duplicate Check Score : {score:.3f}")

        if score >= 0.99:
            logger.info("⚠️ Question already exists in Semantic Cache")
            return

    document = Document(
        page_content=question,
        metadata={
            "redis_key": redis_key,
            "created_at": datetime.now().isoformat(),
            "user_id": context.user_id,
            "document_id": context.document_id,
            "question": question
        }
    )

    cache_store.add_documents([document])
    logger.info("✅ Stored in Semantic Cache")


def search_semantic_cache(
    context: RequestContext,
    question: str,
    threshold: float = 0.90
):
    """
    Search context-isolated semantic cache.
    Returns redis_key if a similar question exists.
    """
    cache_store = get_semantic_cache_store(context)

    results = cache_store.similarity_search_with_relevance_scores(
        query=question,
        k=1
    )

    if not results:
        return None

    document, score = results[0]
    logger.info(f"Semantic Score : {score:.3f}")

    if score >= threshold:
        logger.info("✅ Semantic Cache Hit")
        return document.metadata["redis_key"]

    return None


def delete_semantic_question(context: RequestContext, redis_key: str):
    """
    Delete a stale semantic cache entry from the context's isolated collection.
    """
    try:
        cache_store = get_semantic_cache_store(context)
        cache_store.delete(
            where={
                "redis_key": redis_key
            }
        )
        logger.info("🗑 Removed stale semantic cache entry")
    except Exception as e:
        logger.error(f"Semantic Delete Error : {e}")


def clear_semantic_cache_for_context(context: RequestContext):
    """
    Purges/resets the entire semantic cache collection for a specific user and document.
    """
    try:
        cache_store = get_semantic_cache_store(context)
        cache_store.delete_collection()
        logger.info(f"🧹 Purged Chroma semantic cache collection for {context.user_id}:{context.document_id}")
    except Exception as e:
        logger.warning(f"⚠️ Error purging Chroma semantic collection: {e}")