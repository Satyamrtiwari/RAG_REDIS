from langchain_core.prompts import ChatPromptTemplate
from app.rag.llm import model
from app.utils.logger import logger

rewriter_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert RAG Query Optimizer.
Your task is to rewrite a raw user question into a single, clean, search-optimized query for vector database retrieval.

Rules:
1. Fix any typos or spelling errors (e.g. "explainantio" -> "explanation").
2. Expand technical abbreviations when appropriate (e.g. "DL" -> "Deep Learning", "ANN" -> "Artificial Neural Network", "CNN" -> "Convolutional Neural Network").
3. Strip conversational noise or filler phrases (e.g. "give me depth", "can you tell me", "please explain me").
4. Output ONLY the refined query text. Do not include quotes, preambles, or markdown formatting.
"""),
    ("human", "Raw user query: {query}")
])


def rewrite_query(raw_query: str) -> str:
    """
    Rewrites and optimizes a raw user query for high-precision vector search.
    """
    if not raw_query or len(raw_query.strip()) < 3:
        return raw_query.strip()

    try:
        formatted_prompt = rewriter_prompt.invoke({"query": raw_query})
        response = model.invoke(formatted_prompt)
        cleaned_query = response.content.strip().strip('"').strip("'")
        logger.info(f"🔍 Query Rewritten: '{raw_query}' ➡️ '{cleaned_query}'")
        return cleaned_query
    except Exception as e:
        logger.warning(f"⚠️ Query Rewriter fallback: {e}")
        return raw_query
