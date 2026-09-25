import os
import uuid
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pinecone import Pinecone
from fastembed import TextEmbedding
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.utils.logger import logger

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "docuquery-enterprise")

_pinecone_index = None
_embedder_instance = None


def get_embedder() -> TextEmbedding:
    """Returns singleton FastEmbed model instance for BAAI/bge-small-en-v1.5 (384 dims)."""
    global _embedder_instance
    if _embedder_instance is None:
        logger.info("🧠 Loading FastEmbed model: BAAI/bge-small-en-v1.5 (384 dimensions)...")
        _embedder_instance = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _embedder_instance


def get_pinecone_index():
    """Returns singleton Pinecone index connection."""
    global _pinecone_index
    if _pinecone_index is None:
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is missing from environment variables.")
        pc = Pinecone(api_key=PINECONE_API_KEY)
        _pinecone_index = pc.Index(PINECONE_INDEX_NAME)
        logger.info(f"🌲 Connected to Pinecone Index: {PINECONE_INDEX_NAME}")
    return _pinecone_index


def ingest_text_to_pinecone(
    client_id: str,
    text: str,
    source_name: str,
    source_type: str = "text"
) -> int:
    """
    Chunks text into 1000-character segments (200 overlap), embeds them,
    and upserts into Pinecone under namespace = client_id.
    """
    if not text or not text.strip():
        return 0

    # Step 1: Chunking using identical 1000/200 parameters
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text(text)
    if not chunks:
        return 0

    logger.info(f"✂️ Split '{source_name}' into {len(chunks)} chunks for client '{client_id}'.")

    # Step 2: Generate 384-d embeddings
    embedder = get_embedder()
    embeddings = list(embedder.embed(chunks))

    # Step 3: Prepare vectors
    vectors = []
    for idx, (chunk, vec) in enumerate(zip(chunks, embeddings)):
        vec_id = f"{client_id}_{idx}_{uuid.uuid4().hex[:8]}"
        vectors.append({
            "id": vec_id,
            "values": vec.tolist(),
            "metadata": {
                "text": chunk,
                "source_name": source_name,
                "source_type": source_type,
                "client_id": client_id,
                "chunk_index": idx
            }
        })

    # Step 4: Batch upsert into Pinecone namespace
    index = get_pinecone_index()
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch, namespace=client_id)

    logger.info(f"✅ Upserted {len(vectors)} vectors into Pinecone namespace '{client_id}'.")
    return len(vectors)


def query_pinecone_candidates(
    client_id: str,
    query: str,
    top_k: int = 15
) -> List[Document]:
    """
    Embeds user query and searches Pinecone inside namespace = client_id.
    Returns list of LangChain Document objects (candidate pool of top_k=15).
    """
    if not query or not query.strip():
        return []

    embedder = get_embedder()
    query_vec = list(embedder.embed([query]))[0].tolist()

    index = get_pinecone_index()
    try:
        response = index.query(
            vector=query_vec,
            top_k=top_k,
            include_metadata=True,
            namespace=client_id
        )
    except Exception as e:
        logger.error(f"❌ Pinecone query failed for namespace '{client_id}': {e}")
        return []

    documents = []
    if response and hasattr(response, "matches"):
        for match in response.matches:
            if match.metadata and "text" in match.metadata:
                doc = Document(
                    page_content=match.metadata["text"],
                    metadata=match.metadata
                )
                documents.append(doc)

    logger.info(f"🌲 Pinecone Retrieval ({client_id}): Found {len(documents)} candidate chunks.")
    return documents


def clear_client_vectors(client_id: str) -> bool:
    """
    Cleans up all vectors under client's namespace.
    """
    try:
        index = get_pinecone_index()
        index.delete(delete_all=True, namespace=client_id)
        logger.info(f"🧹 Deleted all vectors for namespace '{client_id}'.")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Pinecone vector deletion error: {e}")
        return False
