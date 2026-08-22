import os
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.utils.logger import logger

app = FastAPI(
    title="RAG + Redis + Semantic Cache API Platform",
    description="Production-grade Retrieval-Augmented Generation API enhanced with multi-layer Redis caching, FlashRank cross-encoder reranking, and multilingual intent routing.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurable CORS origins for production security
raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-cache-status", "x-latency-ms"]
)

# Global Production Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Unhandled API Error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": request.url.path
        }
    )

# Attach API routes
app.include_router(api_router)


@app.on_event("startup")
def startup_event():
    logger.info("🚀 Starting Production FastAPI RAG Server...")
    logger.info("📄 Interactive API Documentation available at http://localhost:8000/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True)
