from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from app.config import CHROMA_DB_PATH
from app.rag.embeddings import embedding_model

PDF_PATH = r"C:\Users\3star\Desktop\GenAI\RAG_Shreyainsh\document loaders\deep_learning.pdf"

loader = PyPDFLoader(PDF_PATH)

documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.split_documents(documents)

vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model,
    persist_directory=CHROMA_DB_PATH
)

print("✅ Chroma database created successfully.")