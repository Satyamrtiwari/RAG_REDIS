"""
Guardrails module for RAG + Redis Caching.
Provides validation logic to filter out non-cacheable responses and queries.
"""

REFUSAL_PHRASES = [
    "couldn't find the answer",
    "could not find the answer",
    "not mentioned in the document",
    "not mentioned in the context",
    "does not provide information",
    "don't have enough context",
    "cannot answer based on",
    "no information provided",
    "unable to find",
]

GREETINGS_AND_FILLERS = {
    "hi", "hello", "hii", "hiii", "hey", "heyy",
    "thanks", "thank you", "bye", "goodbye",
    "good morning", "good evening", "good afternoon",
    "who are you", "what can you do", "ok", "okay"
}


def should_cache_response(answer: str) -> bool:
    """
    Determines whether an LLM response should be cached.
    Rejects refusal/failure messages and empty responses.
    """
    if not answer or len(answer.strip()) < 10:
        return False

    lower_ans = answer.lower()
    for phrase in REFUSAL_PHRASES:
        if phrase in lower_ans:
            return False

    return True


def is_informational_query(query: str) -> bool:
    """
    Determines whether a query is an actual document question
    or just a greeting/small-talk filler.
    """
    if not query or len(query.strip()) < 2:
        return False

    normalized_query = query.strip().lower().rstrip(".!?")
    if normalized_query in GREETINGS_AND_FILLERS:
        return False

    return True
