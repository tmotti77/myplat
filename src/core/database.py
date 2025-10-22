"""Database connection and session management."""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings
from src.models.base import Base


class DatabaseManager:
    """Database connection and session manager."""
    
    def __init__(self):
        """Initialize database manager."""
        self._async_engine = None
        self._sync_engine = None
        self._async_session_factory = None
        self._sync_session_factory = None
        
    @property
    def async_engine(self):
        """Get async database engine."""
        if self._async_engine is None:
            # Convert PostgreSQL URL to async version
            async_url = str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")
            
            self._async_engine = create_async_engine(
                async_url,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                echo=settings.DATABASE_ECHO,
                future=True,
                # Connection pool settings
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections every hour
            )
            
        return self._async_engine
    
    @property
    def sync_engine(self):
        """Get sync database engine (for migrations and admin tasks)."""
        if self._sync_engine is None:
            self._sync_engine = create_engine(
                str(settings.DATABASE_URL),
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                echo=settings.DATABASE_ECHO,
                future=True,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
        return self._sync_engine
    
    @property
    def async_session_factory(self):
        """Get async session factory."""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
        return self._async_session_factory
    
    @property
    def sync_session_factory(self):
        """Get sync session factory."""
        if self._sync_session_factory is None:
            self._sync_session_factory = sessionmaker(
                bind=self.sync_engine,
                autoflush=True,
                autocommit=False,
            )
        return self._sync_session_factory
    
    async def create_tables(self):
        """Create all database tables."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self):
        """Drop all database tables."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with automatic cleanup."""
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @asynccontextmanager
    def get_sync_session(self) -> Session:
        """Get sync database session with automatic cleanup."""
        session = self.sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            async with self.get_session() as session:
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception:
            return False
    
    async def close(self):
        """Close database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        
        if self._sync_engine:
            self._sync_engine.dispose()


# Global database manager instance
db = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session in FastAPI."""
    async with db.get_session() as session:
        yield session

# Alias for compatibility with imports
get_db = get_db_session


def get_sync_db_session() -> Session:
    """Get sync database session for scripts and admin tasks."""
    return db.sync_session_factory()


# Database event listeners for logging and monitoring
@event.listens_for(pool.Pool, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set database pragmas on connection."""
    if "postgresql" in str(settings.DATABASE_URL):
        # PostgreSQL-specific settings
        with dbapi_connection.cursor() as cursor:
            # Set search path for multi-tenancy
            cursor.execute("SET search_path TO public")
            
            # Enable row level security
            cursor.execute("SET row_security = on")
            
            # Set timezone
            cursor.execute("SET timezone = 'UTC'")


@event.listens_for(pool.Pool, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log when connection is checked out from pool."""
    if settings.DATABASE_ECHO:
        print(f"Connection checked out: {id(dbapi_connection)}")


@event.listens_for(pool.Pool, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log when connection is checked back into pool."""
    if settings.DATABASE_ECHO:
        print(f"Connection checked in: {id(dbapi_connection)}")


# Context managers for database operations
@asynccontextmanager
async def database_transaction():
    """Context manager for database transactions."""
    async with db.get_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_database():
    """Initialize database with tables and basic data."""
    # Create tables
    await db.create_tables()
    
    # Insert default data if needed
    async with db.get_session() as session:
        # Check if we need to create default tenant
        from src.models.tenant import Tenant
        
        result = await session.execute("SELECT COUNT(*) FROM tenant")
        tenant_count = result.scalar()
        
        if tenant_count == 0:
            # Create default tenant
            default_tenant = Tenant(
                name="default",
                display_name="Default Tenant",
                description="Default tenant for single-tenant deployments",
                contact_email="admin@example.com",
            )
            session.add(default_tenant)
            await session.commit()


async def cleanup_database():
    """Cleanup database connections."""
    await db.close()


# Health check functions
async def check_database_health() -> dict:
    """Comprehensive database health check."""
    health_info = {
        "status": "unhealthy",
        "connection": False,
        "tables": False,
        "response_time_ms": 0,
    }
    
    try:
        import time
        start_time = time.time()
        
        # Test basic connection
        connection_ok = await db.health_check()
        health_info["connection"] = connection_ok
        
        if connection_ok:
            # Test table access
            async with db.get_session() as session:
                from src.models.tenant import Tenant
                
                result = await session.execute("SELECT COUNT(*) FROM tenant")
                count = result.scalar()
                health_info["tables"] = isinstance(count, int)
        
        end_time = time.time()
        health_info["response_time_ms"] = int((end_time - start_time) * 1000)
        
        if health_info["connection"] and health_info["tables"]:
            health_info["status"] = "healthy"
        
    except Exception as e:
        health_info["error"] = str(e)
    
    return health_info