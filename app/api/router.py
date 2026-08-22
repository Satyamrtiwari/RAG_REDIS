from fastapi import APIRouter
from app.api.routes_chat import router as chat_router
from app.api.routes_documents import router as doc_router
from app.api.routes_metrics import router as metrics_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(doc_router)
api_router.include_router(metrics_router)
