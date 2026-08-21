from datetime import datetime

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from app.context import RequestContext
from app.rag.embeddings import embedding_model
from app.cache.cache_services import get_cache_key


semantic_cache = Chroma(
    collection_name="semantic_cache",
    persist_directory="Semantic_Cache_DB",
    embedding_function=embedding_model
)


def store_semantic_question(
    context: RequestContext,
    question: str
):
    """
    Store a question inside semantic cache only if it
    doesn't already exist.
    """

    redis_key = get_cache_key(context, question)

    # Check whether a similar question already exists
    existing = semantic_cache.similarity_search_with_relevance_scores(
        query=question,
        k=1
    )

    if existing:

        document, score = existing[0]

        print(f"Duplicate Check Score : {score:.3f}")

        if score >= 0.99:

            print("⚠ Question already exists in Semantic Cache")

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

    semantic_cache.add_documents([document])

    print("✅ Stored in Semantic Cache")





def search_semantic_cache(
    context: RequestContext,
    question: str,
    threshold: float = 0.90
):
    """
    Search semantic cache.
    Returns redis_key if a similar question exists.
    """

    results = semantic_cache.similarity_search_with_relevance_scores(
        query=question,
        k=1
    )

    if not results:
        return None

    document, score = results[0]

    print(f"Semantic Score : {score:.3f}")

    if score >= threshold:

        print("✅ Semantic Cache Hit")

        return document.metadata["redis_key"]

    return None


def delete_semantic_question(redis_key: str):
    """
    Delete a stale semantic cache entry.
    """

    try:

        semantic_cache.delete(
            where={
                "redis_key": redis_key
            }
        )

        print("🗑 Removed stale semantic cache entry")

    except Exception as e:

        print(f"Semantic Delete Error : {e}")