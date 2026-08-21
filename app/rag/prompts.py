from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", """ you are a helpful AI assistant .
     Use ONLY the provided context to answer the question.

    If the answwer is not in the context,
      say " I couldn't find the answer in the document"
    """),

("human", """
    this is the context : {context}
    this is the question : {question}
    """)
])   