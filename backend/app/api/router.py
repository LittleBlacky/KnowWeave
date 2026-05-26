from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.chunks import router as chunks_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.files import router as files_router
from app.api.v1.health import router as health_router
from app.api.v1.search import router as search_router
from app.api.v1.wiki import router as wiki_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(files_router)
api_router.include_router(chunks_router)
api_router.include_router(search_router)
api_router.include_router(chat_router)
api_router.include_router(wiki_router)
api_router.include_router(feedback_router)
