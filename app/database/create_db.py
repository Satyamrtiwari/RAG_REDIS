import os
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from app.config import CHROMA_DB_PATH
from app.rag.embeddings import embedding_model
from app.utils.logger import logger

# Default PDF path or accept from environment / command line argument
DEFAULT_PDF = os.path.join(os.path.dirname(__file__), "..", "..", "data", "deep_learning.pdf")
PDF_PATH = sys.argv[1] if len(sys.argv) > 1 else os.getenv("PDF_PATH", DEFAULT_PDF)

if not os.path.exists(PDF_PATH):
    # Check fallback path
    fallback_path = r"C:\Users\3star\Desktop\GenAI\RAG_Shreyainsh\document loaders\deep_learning.pdf"
    if os.path.exists(fallback_path):
        PDF_PATH = fallback_path

if not os.path.exists(PDF_PATH):
    logger.error(f"❌ PDF file not found at path: {PDF_PATH}")
    sys.exit(1)

logger.info(f"📄 Processing document from: {PDF_PATH}")
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

logger.info("✅ Chroma database created successfully.")