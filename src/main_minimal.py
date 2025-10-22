"""Minimal FastAPI application entry point for testing."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.core.config import settings
from src.core.database import cleanup_database, init_database
from src.core.logging import get_logger, log_error

# Configure logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting RAG Platform (Minimal Mode)", version=settings.APP_VERSION)
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized")
        
        yield
        
    except Exception as e:
        log_error(e, {"phase": "startup"})
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down RAG Platform")
        
        try:
            await cleanup_database()
            logger.info("Cleanup completed")
        except Exception as e:
            log_error(e, {"phase": "shutdown"})


def create_app() -> FastAPI:
    """Create and configure minimal FastAPI application."""
    
    app = FastAPI(
        title=settings.APP_NAME + " (Minimal)",
        description="Minimal version for testing",
        version=settings.APP_VERSION,
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Add basic CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.APP_NAME + " (Minimal)",
            "version": settings.APP_VERSION,
            "description": "Minimal version for testing",
            "status": "running"
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": "2025-10-19T00:00:00Z",
            "version": settings.APP_VERSION
        }
    
    # Test database endpoint
    @app.get("/test-db")
    async def test_db():
        """Test database connection."""
        try:
            from src.core.database import get_db_session
            async with get_db_session() as db:
                from sqlalchemy import text
                result = await db.execute(text("SELECT 1"))
                return {
                    "database": "connected",
                    "result": result.scalar()
                }
        except Exception as e:
            return {
                "database": "error",
                "error": str(e)
            }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler."""
        
        log_error(exc, {
            "url": str(request.url),
            "method": request.method,
        })
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc) if settings.APP_DEBUG else "Internal server error",
                "type": "internal_error"
            }
        )
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    """Run the application directly."""
    
    logger.info(
        "Starting minimal server",
        host="0.0.0.0",
        port=8000,
    )
    
    uvicorn.run(
        "src.main_minimal:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )