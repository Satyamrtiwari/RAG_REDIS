from app.rag.retriever import retriever
from app.rag.prompts import prompt
from app.rag.llm import model


def ask_rag(question: str):
    docs = retriever.invoke(question)

    context = "".join(
    doc.page_content
    for doc in docs
    )

    final_prompt = prompt.invoke({
    "context": context,
    "question": question
    })

    response = model.invoke(final_prompt)

    return response.content