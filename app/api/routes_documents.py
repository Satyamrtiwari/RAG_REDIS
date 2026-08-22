import os
import re
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from app.context import RequestContext
from app.config import CHROMA_DB_PATH
from app.rag.embeddings import embedding_model
from app.rag.retriever import vector_store
from app.schemas import DocumentUploadResponse
from app.cache.cache_services import clear_document_cache
from app.utils.logger import logger

router = APIRouter(prefix="/api/v1/documents", tags=["Document Management"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".doc", ".md", ".txt")


def sanitize_id(raw_str: str) -> str:
    """Sanitizes document_id into clean slug format"""
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', raw_str.strip().lower())
    clean = re.sub(r'_+', '_', clean)
    return clean.strip('_') or "default_doc"


@router.get("")
def list_documents(user_id: str = "satyam"):
    """
    List all uploaded documents for a user.
    """
    documents_list = []
    clean_user = user_id.strip().lower()

    if os.path.exists(UPLOAD_DIR):
        for fname in os.listdir(UPLOAD_DIR):
            if "@@" in fname:
                parts = fname.split("@@")
                if len(parts) == 3 and parts[0] == clean_user:
                    documents_list.append({
                        "document_id": parts[1],
                        "filename": parts[2],
                        "stored_file": fname,
                        "user_id": clean_user
                    })

    return {
        "user_id": clean_user,
        "total_documents": len(documents_list),
        "has_documents": len(documents_list) > 0,
        "message": "Documents retrieved successfully." if documents_list else "No documents uploaded.",
        "documents": documents_list
    }


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form("satyam"),
    document_id: str = Form(None)
):
    """
    Upload and index a PDF, DOCX, MD, or TXT document into Chroma Vector Store.
    Automatically invalidates old cached answers for the target document_id.
    """
    filename_lower = file.filename.lower()
    if not filename_lower.endswith(SUPPORTED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    clean_user = user_id.strip().lower()
    raw_doc_id = document_id if document_id else file.filename.rsplit('.', 1)[0]
    clean_doc_id = sanitize_id(raw_doc_id)

    # Store file with robust @@ divider
    file_path = os.path.join(UPLOAD_DIR, f"{clean_user}@@{clean_doc_id}@@{file.filename}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Multi-Format Loader Selector
        if filename_lower.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif filename_lower.endswith((".docx", ".doc")):
            loader = Docx2txtLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")

        documents = loader.load()

        # Split document into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(documents)

        # Attach metadata
        for chunk in chunks:
            chunk.metadata["user_id"] = clean_user
            chunk.metadata["document_id"] = clean_doc_id
            chunk.metadata["source_filename"] = file.filename

        # Index into Chroma
        Chroma.from_documents(
            documents=chunks,
            embedding=embedding_model,
            persist_directory=CHROMA_DB_PATH
        )

        # Invalidate old cache for this document
        context = RequestContext(user_id=clean_user, document_id=clean_doc_id)
        clear_document_cache(context)

        logger.info(f"✅ Ingested '{file.filename}' into Chroma with {len(chunks)} chunks for {clean_user}:{clean_doc_id}")

        return DocumentUploadResponse(
            message="Document uploaded and indexed successfully.",
            filename=file.filename,
            user_id=clean_user,
            document_id=clean_doc_id,
            chunks_created=len(chunks)
        )

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {str(e)}")


@router.delete("/{document_id}")
def delete_document_completely(document_id: str, user_id: str = "satyam"):
    """
    Completely deletes a document:
    1. Removes uploaded PDF/DOCX/MD files from disk.
    2. Purges vector embeddings from Chroma.
    3. Clears Redis keys & Chroma semantic cache collections.
    """
    clean_user = user_id.strip().lower()
    clean_doc_id = sanitize_id(document_id)

    deleted_files = 0
    if os.path.exists(UPLOAD_DIR):
        for fname in os.listdir(UPLOAD_DIR):
            if fname.startswith(f"{clean_user}@@{clean_doc_id}@@") or fname.startswith(f"{clean_user}_{clean_doc_id}_"):
                try:
                    os.remove(os.path.join(UPLOAD_DIR, fname))
                    deleted_files += 1
                except Exception as e:
                    logger.warning(f"Failed to delete file {fname}: {e}")

    # Delete vector chunks from Chroma
    deleted_chunks = 0
    try:
        results = vector_store.get(where={"document_id": clean_doc_id})
        if results and results.get("ids"):
            deleted_chunks = len(results["ids"])
            vector_store.delete(ids=results["ids"])
            logger.info(f"🧹 Purged {deleted_chunks} vector chunks from Chroma for document '{clean_doc_id}'")
    except Exception as e:
        logger.warning(f"Chroma chunk deletion warning: {e}")

    # Invalidate cache
    context = RequestContext(user_id=clean_user, document_id=clean_doc_id)
    clear_document_cache(context)

    return {
        "message": f"Document '{clean_doc_id}' deleted completely.",
        "user_id": clean_user,
        "document_id": clean_doc_id,
        "files_deleted": deleted_files,
        "vector_chunks_deleted": deleted_chunks
    }
