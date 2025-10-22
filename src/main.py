"""Main FastAPI application entry point."""
import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from src.core.config import settings
from src.core.database import cleanup_database, init_database
from src.core.logging import get_logger, log_error
from src.api import api_router
from src.middleware.auth import AuthMiddleware
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.request_id import RequestIDMiddleware
from src.middleware.tenant import TenantMiddleware
from src.middleware.error_handling import ErrorHandlingMiddleware
# Monitoring imports - health is provided via API router
# from src.monitoring.health import router as health_router
# from src.monitoring.metrics import setup_metrics


# Configure logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting RAG Platform", version=settings.APP_VERSION)
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized")
        
        # Setup monitoring (disabled - using API health endpoints)
        # setup_metrics()
        logger.info("Metrics setup completed")
        
        # Initialize services
        await initialize_services()
        logger.info("Services initialized")
        
        yield
        
    except Exception as e:
        log_error(e, {"phase": "startup"})
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down RAG Platform")
        
        try:
            await cleanup_services()
            await cleanup_database()
            logger.info("Cleanup completed")
        except Exception as e:
            log_error(e, {"phase": "shutdown"})


async def initialize_services():
    """Initialize application services."""
    
    # Initialize Redis connections
    from src.services.cache import cache_service
    await cache_service.initialize()
    
    # Initialize vector database
    from src.services.vector_store import vector_store_service
    await vector_store_service.initialize()
    
    # Initialize search service
    from src.services.search import search_service
    await search_service.initialize()
    
    # Initialize LLM router
    from src.services.llm_router import llm_router_service
    await llm_router_service.initialize()
    
    # Initialize embedding service
    from src.services.embedding import embedding_service
    await embedding_service.initialize()
    
    # Initialize object storage
    from src.services.storage import storage_service
    await storage_service.initialize()


async def cleanup_services():
    """Cleanup application services."""
    
    # Cleanup in reverse order
    try:
        from src.services.storage import storage_service
        await storage_service.cleanup()
    except Exception as e:
        log_error(e, {"service": "storage"})
    
    try:
        from src.services.embedding import embedding_service
        await embedding_service.cleanup()
    except Exception as e:
        log_error(e, {"service": "embedding"})
    
    try:
        from src.services.llm_router import llm_router_service
        await llm_router_service.cleanup()
    except Exception as e:
        log_error(e, {"service": "llm_router"})
    
    try:
        from src.services.search import search_service
        await search_service.cleanup()
    except Exception as e:
        log_error(e, {"service": "search"})
    
    try:
        from src.services.vector_store import vector_store_service
        await vector_store_service.cleanup()
    except Exception as e:
        log_error(e, {"service": "vector_store"})
    
    try:
        from src.services.cache import cache_service
        await cache_service.cleanup()
    except Exception as e:
        log_error(e, {"service": "cache"})


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        openapi_url="/openapi.json" if settings.APP_DEBUG else None,
    )
    
    # Add middleware (order matters!)
    setup_middleware(app)
    
    # Add routers
    setup_routers(app)
    
    # Setup monitoring
    setup_monitoring(app)
    
    # Add global exception handler
    setup_exception_handlers(app)
    
    return app


def setup_middleware(app: FastAPI):
    """Setup application middleware."""
    
    # Trusted host middleware (security)
    if not settings.APP_DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure properly in production
        )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(TenantMiddleware)
    app.add_middleware(AuthMiddleware)


def setup_routers(app: FastAPI):
    """Setup application routers."""
    
    # Health check routes (using API health endpoints instead)
    # app.include_router(health_router, prefix="/health", tags=["health"])
    
    # Main API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": settings.APP_DESCRIPTION,
            "status": "running"
        }


def setup_monitoring(app: FastAPI):
    """Setup monitoring and metrics."""
    
    # Prometheus metrics (only if available)
    if PROMETHEUS_AVAILABLE:
        instrumentator = Instrumentator(
            should_group_status_codes=False,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/health", "/metrics"],
            env_var_name="ENABLE_METRICS",
            inprogress_name="fastapi_inprogress",
            inprogress_labels=True,
        )
        
        instrumentator.instrument(app)
        instrumentator.expose(app, endpoint="/metrics")
    else:
        logger.warning("Prometheus instrumentator not available - metrics disabled")


def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers."""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler."""
        
        log_error(exc, {
            "url": str(request.url),
            "method": request.method,
            "client": request.client.host if request.client else "unknown",
        })
        
        # Don't expose internal errors in production
        if settings.APP_DEBUG:
            error_detail = str(exc)
        else:
            error_detail = "Internal server error"
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": error_detail,
                "type": "internal_error"
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle validation errors."""
        
        logger.warning("Validation error", error=str(exc), url=str(request.url))
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "detail": str(exc),
                "type": "validation_error"
            }
        )


# Create application instance
app = create_app()


if __name__ == "__main__":
    """Run the application directly."""
    
    logger.info(
        "Starting server",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        debug=settings.APP_DEBUG,
        reload=settings.APP_RELOAD,
    )
    
    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        use_colors=True,
        loop="asyncio",
    )