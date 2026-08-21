import json
from langchain_core.prompts import ChatPromptTemplate
from app.rag.llm import model
from app.utils.logger import logger

router_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a multilingual AI Intent Classifier and Assistant.
Analyze the user's input in ANY language (English, Hindi, Spanish, French, etc.) and classify its intent.

Classification Rules:
1. GREETING / SMALL TALK: Greetings, courtesies, pleasantries, questions about your identity, thanks, or farewells (e.g., "hi", "hello", "namaste", "bonjour", "kaise ho", "who are you", "thanks", "bye").
   -> For GREETING: Generate a polite, friendly conversational response in the SAME language as the user's input, offering assistance with their documents. Set "is_greeting": true.

2. DOCUMENT_QUERY: Informational questions asking for explanations, definitions, concepts, formulas, data, summaries, or details from a document.
   -> For DOCUMENT_QUERY: Set "is_greeting": false and "response": null.

Return JSON format strictly:
{{
  "is_greeting": boolean,
  "response": string or null
}}
"""),
    ("human", "{query}")
])


def route_intent(query: str) -> dict:
    """
    Classifies user query intent in any language.
    Returns dict: {"is_greeting": bool, "response": str | None}
    """
    if not query or len(query.strip()) == 0:
        return {"is_greeting": True, "response": "Hello! How can I help you today?"}

    try:
        formatted_prompt = router_prompt.invoke({"query": query})
        raw_res = model.invoke(formatted_prompt)
        content = raw_res.content.strip()

        # Clean JSON markdown if wrapped in ```json ... ```
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:].strip()

        result = json.loads(content)
        if result.get("is_greeting"):
            logger.info(f"💬 Dynamic Intent Router: Classified '{query}' as GREETING.")
        else:
            logger.info(f"📄 Dynamic Intent Router: Classified '{query}' as DOCUMENT_QUERY.")

        return result

    except Exception as e:
        logger.warning(f"⚠️ Intent Router fallback: {e}")
        return {"is_greeting": False, "response": None}
