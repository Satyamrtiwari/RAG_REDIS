import os
import shutil
import tempfile
from typing import Optional, List
from fastapi import APIRouter, Header, UploadFile, File, Form, HTTPException, Response
from pydantic import BaseModel, Field

from app.enterprise.supabase_client import (
    create_client_record,
    get_client_by_api_key,
    record_knowledge_source,
    get_knowledge_sources,
    delete_knowledge_source_record
)
from app.enterprise.pinecone_service import ingest_text_to_pinecone
from app.enterprise.web_scraper import scrape_website_content
from app.enterprise.enterprise_rag import ask_enterprise_rag
from app.utils.logger import logger

from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader

router = APIRouter(prefix="/api/v1", tags=["Enterprise B2B Chatbot Platform"])

SUPERADMIN_SECRET_KEY = os.getenv("SUPERADMIN_SECRET_KEY", "superadmin_sec_7781b9e24fa10d")


# ==========================================
# PYDANTIC SCHEMAS
# ==========================================

class CreateClientRequest(BaseModel):
    client_name: str = Field(..., example="Acme Corp")
    allowed_domains: List[str] = Field(default=[], example=["https://acme.com", "http://localhost:3000"])
    rate_limit_per_day: int = Field(default=2000, example=2000)


class CreateClientResponse(BaseModel):
    status: str
    client_id: str
    client_name: str
    api_key: str
    allowed_domains: List[str]
    rate_limit_per_day: int


class IngestTextRequest(BaseModel):
    title: str = Field(..., example="Company Return Policy")
    content: str = Field(..., example="We accept returns within 30 days of purchase with full refund.")


class IngestUrlRequest(BaseModel):
    url: str = Field(..., example="https://example.com/about")


class IngestResponse(BaseModel):
    status: str
    source_type: str
    source_name: str
    chunks_indexed: int
    client_id: str


class EnterpriseChatRequest(BaseModel):
    api_key: str = Field(..., example="sk_live_...")
    question: str = Field(..., example="What is your return policy?")
    session_id: Optional[str] = Field(default=None, example="user_sess_123")


class EnterpriseChatResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    cache_hit: bool
    is_greeting: bool
    latency_ms: float


# ==========================================
# AUTH HELPER
# ==========================================

def authenticate_client(api_key: Optional[str], header_key: Optional[str] = None) -> dict:
    token = api_key or header_key
    if not token:
        raise HTTPException(status_code=401, detail="API Key is required. Pass in body or 'X-API-KEY' header.")
    
    client = get_client_by_api_key(token)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid or deactivated API Key.")
    return client


# ==========================================
# ENDPOINT 1: SUPERADMIN CREATE CLIENT
# ==========================================

@router.post("/admin/create-client", response_model=CreateClientResponse)
def admin_create_client(
    req: CreateClientRequest,
    x_superadmin_secret: Optional[str] = Header(None, alias="X-SuperAdmin-Secret")
):
    """
    SuperAdmin Endpoint: Registers a new business client and issues their unique API Key.
    Protected strictly by Master Secret Key.
    """
    if not x_superadmin_secret or x_superadmin_secret.strip() != SUPERADMIN_SECRET_KEY.strip():
        logger.warning("🚫 Unauthorized attempt on /api/v1/admin/create-client")
        raise HTTPException(status_code=401, detail="Invalid or missing X-SuperAdmin-Secret header.")

    try:
        client_data = create_client_record(
            client_name=req.client_name,
            allowed_domains=req.allowed_domains,
            rate_limit_per_day=req.rate_limit_per_day
        )
        return CreateClientResponse(
            status="created",
            client_id=str(client_data["id"]),
            client_name=client_data["client_name"],
            api_key=client_data["api_key"],
            allowed_domains=client_data.get("allowed_domains", []),
            rate_limit_per_day=client_data.get("rate_limit_per_day", 2000)
        )
    except Exception as e:
        logger.error(f"❌ Failed to create client: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ENDPOINT 2: INGEST RAW TEXT / FAQ
# ==========================================

@router.post("/enterprise/ingest/text", response_model=IngestResponse)
def ingest_text_endpoint(
    req: IngestTextRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY")
):
    """
    Client Ingestion: Pastes raw text, policies, product descriptions, or FAQs.
    """
    client = authenticate_client(api_key=None, header_key=x_api_key)
    client_id = str(client["id"])

    chunks_count = ingest_text_to_pinecone(
        client_id=client_id,
        text=req.content,
        source_name=req.title,
        source_type="text"
    )

    record_knowledge_source(
        client_id=client_id,
        source_type="text",
        source_name=req.title,
        chunk_count=chunks_count
    )

    return IngestResponse(
        status="indexed",
        source_type="text",
        source_name=req.title,
        chunks_indexed=chunks_count,
        client_id=client_id
    )


# ==========================================
# ENDPOINT 3: INGEST URL VIA WEB SCRAPER
# ==========================================

@router.post("/enterprise/ingest/url", response_model=IngestResponse)
def ingest_url_endpoint(
    req: IngestUrlRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY")
):
    """
    Client Ingestion: Crawls a public website URL, parses clean text, and indexes into Pinecone.
    """
    client = authenticate_client(api_key=None, header_key=x_api_key)
    client_id = str(client["id"])

    try:
        scraped = scrape_website_content(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Web scraping failed: {str(e)}")

    chunks_count = ingest_text_to_pinecone(
        client_id=client_id,
        text=scraped["content"],
        source_name=scraped["url"],
        source_type="url"
    )

    record_knowledge_source(
        client_id=client_id,
        source_type="url",
        source_name=scraped["url"],
        chunk_count=chunks_count
    )

    return IngestResponse(
        status="indexed",
        source_type="url",
        source_name=scraped["url"],
        chunks_indexed=chunks_count,
        client_id=client_id
    )


# ==========================================
# ENDPOINT 4: INGEST FILE (PDF/DOCX/TXT/MD)
# ==========================================

@router.post("/enterprise/ingest/file", response_model=IngestResponse)
def ingest_file_endpoint(
    file: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    api_key_form: Optional[str] = Form(None)
):
    """
    Client Ingestion: Uploads PDF, DOCX, TXT, or MD manuals & company documents.
    """
    client = authenticate_client(api_key=api_key_form, header_key=x_api_key)
    client_id = str(client["id"])

    filename = file.filename or "uploaded_file"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in (".pdf", ".docx", ".doc", ".txt", ".md"):
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOCX, TXT, or MD.")

    # Save to temp file for parsing
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Parse content
        if ext == ".pdf":
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            content = "\n\n".join(d.page_content for d in docs)
        elif ext in (".docx", ".doc"):
            loader = Docx2txtLoader(tmp_path)
            docs = loader.load()
            content = "\n\n".join(d.page_content for d in docs)
        else:
            loader = TextLoader(tmp_path, encoding="utf-8")
            docs = loader.load()
            content = "\n\n".join(d.page_content for d in docs)

        if not content.strip():
            raise HTTPException(status_code=400, detail="Uploaded file contained no readable text.")

        chunks_count = ingest_text_to_pinecone(
            client_id=client_id,
            text=content,
            source_name=filename,
            source_type="file"
        )

        record_knowledge_source(
            client_id=client_id,
            source_type="file",
            source_name=filename,
            chunk_count=chunks_count
        )

        return IngestResponse(
            status="indexed",
            source_type="file",
            source_name=filename,
            chunks_indexed=chunks_count,
            client_id=client_id
        )

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ==========================================
# ENDPOINT 5: PUBLIC WEBSITE CHATBOT API
# ==========================================

@router.post("/enterprise/chat", response_model=EnterpriseChatResponse)
def enterprise_chat_endpoint(req: EnterpriseChatRequest, response: Response):
    """
    Public Chatbot Endpoint: Called by website chat widgets or mobile apps.
    Powered by Intent Router -> Upstash Redis Cache -> Pinecone -> FlashRank Reranker -> Groq/Mistral LLM.
    """
    client = authenticate_client(api_key=req.api_key)
    client_id = str(client["id"])

    result = ask_enterprise_rag(client_id=client_id, question=req.question)

    response.headers["x-cache-status"] = "hit" if result.get("cache_hit") else "miss"
    response.headers["x-latency-ms"] = str(result.get("latency_ms", 0))

    return EnterpriseChatResponse(
        question=req.question,
        answer=result["answer"],
        sources=result["sources"],
        cache_hit=result["cache_hit"],
        is_greeting=result.get("is_greeting", False),
        latency_ms=result["latency_ms"]
    )


# ==========================================
# ENDPOINT 6: LIST CLIENT SOURCES
# ==========================================

@router.get("/enterprise/sources")
def list_client_sources(x_api_key: Optional[str] = Header(None, alias="X-API-KEY")):
    """
    Returns list of all indexed knowledge sources for the authenticated client.
    """
    client = authenticate_client(api_key=None, header_key=x_api_key)
    client_id = str(client["id"])
    sources = get_knowledge_sources(client_id)
    return {
        "client_name": client["client_name"],
        "client_id": client_id,
        "total_sources": len(sources),
        "sources": sources
    }
