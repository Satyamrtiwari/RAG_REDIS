# from langchain_mistralai import ChatMistralAI
# from app.config import MODEL_NAME

# model = ChatMistralAI(model = MODEL_NAME)


from langchain_groq import ChatGroq
from app.config import MODEL_NAME

model = ChatGroq(model = MODEL_NAME)