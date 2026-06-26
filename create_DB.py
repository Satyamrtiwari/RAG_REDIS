from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

data = PyPDFLoader("C:\\Users\\3star\\Desktop\\GenAI\\RAG_Shreyainsh\\document loaders\\deep_learning.pdf")
docs = data.load()

splitter  = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

chunks = splitter.split_documents(docs)

embedding_model = MistralAIEmbeddings()

vector_store = Chroma.from_documents(
    documents = chunks,
    embedding = embedding_model,
    persist_directory="Chroma_deep_learning-DB"
)   