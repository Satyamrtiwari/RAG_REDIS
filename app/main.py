from app.context import RequestContext

from app.cache.cache_services import (
    get_cached_answer,
    get_cached_answer_by_key,
    store_cached_answer
)

from app.rag.rag_service import ask_rag

from app.rag.semantic_cache import (
    delete_semantic_question,
    search_semantic_cache,
    store_semantic_question
)


# Simulating logged-in user
context = RequestContext(
    user_id="satyam",
    document_id="deep_learning"
)


print("---------------to exit enter 0-------------------------")

while True:

    query = input("Enter your question : ")

    if query == "0":
        print("Exited")
        break

    # -------------------------------------------------
    # 1. Exact Redis Cache
    # -------------------------------------------------

    cached_answer = get_cached_answer(
        context,
        query
    )

    if cached_answer:

        print("----------------------------------------")
        print("Redis Cache Hit ✅")
        print("AI:", cached_answer)

        continue

    # -------------------------------------------------
    # 2. Semantic Cache
    # -------------------------------------------------

    redis_key = search_semantic_cache(
        context,
        query
    )

    if redis_key:

        cached_answer = get_cached_answer_by_key(
            redis_key
        )

        if cached_answer:

            print("----------------------------------------")
            print("Semantic Cache Hit ✅")
            print("AI:", cached_answer)

            continue

        print("⚠ Redis Cache Expired")

        delete_semantic_question(redis_key)

        print("♻ Rebuilding Cache...")

    # -------------------------------------------------
    # 3. RAG
    # -------------------------------------------------

    response = ask_rag(query)

    store_cached_answer(
        context,
        query,
        response
    )

    store_semantic_question(
        context,
        query
    )

    print("----------------------------------------")
    print("AI:", response)