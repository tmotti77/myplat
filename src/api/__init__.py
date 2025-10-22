"""API package initialization."""

from fastapi import APIRouter
from .auth import router as auth_router
from .documents import router as documents_router
from .search import router as search_router
from .chat import router as chat_router
from .admin import router as admin_router
from .health import router as health_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers with prefixes
api_router.include_router(
    health_router,
    tags=["health"]
)

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    documents_router,
    prefix="/documents",
    tags=["documents"]
)

api_router.include_router(
    search_router,
    prefix="/search",
    tags=["search"]
)

api_router.include_router(
    chat_router,
    prefix="/chat",
    tags=["chat"]
)

api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["admin"]
)

__all__ = ["api_router"]