from langchain_community.vectorstores import Chroma
from app.config import CHROMA_DB_PATH
from app.config import SEARCH_TYPE
from app.config import SEARCH_KWARGS
from app.rag.embeddings import embedding_model


vector_store = Chroma(
    persist_directory=CHROMA_DB_PATH,
    embedding_function=embedding_model,
)

retriever = vector_store.as_retriever(
    search_type=SEARCH_TYPE,
    search_kwargs=SEARCH_KWARGS
)