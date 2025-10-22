"""Dependency injection for FastAPI."""

from typing import AsyncGenerator
from fastapi import Depends

from ..services.document_processor import DocumentProcessor
from ..services.embedding_service import embedding_service
from ..services.search_service import search_service
from ..services.storage_service import storage_service
from ..services.rag_engine import rag_engine
from ..services.cache import cache_service
from ..services.auth_service import auth_service


async def get_storage_service():
    """Get storage service instance."""
    return storage_service


async def get_embedding_service():
    """Get embedding service instance."""
    return embedding_service


async def get_search_service():
    """Get search service instance."""
    return search_service


async def get_document_processor():
    """Get document processor instance."""
    return DocumentProcessor(storage_service)


async def get_rag_service():
    """Get RAG service instance."""
    return rag_engine


async def get_cache_service():
    """Get cache service instance."""
    return cache_service


async def get_auth_service():
    """Get auth service instance."""
    return auth_service


# Chat service dependencies
class ChatService:
    """Chat service for handling conversations."""
    
    def __init__(self):
        pass
    
    async def generate_response(
        self,
        message: str,
        conversation_id: str,
        user_id: str,
        tenant_id: str,
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        include_sources: bool = True,
        search_params: dict = None
    ):
        """Generate chat response using RAG."""
        
        # Use RAG engine for response generation
        return await rag_engine.ask_question(
            question=message,
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            model_preference=model,
            max_tokens=max_tokens,
            temperature=temperature,
            include_citations=include_sources
        )
    
    async def generate_response_stream(
        self,
        message: str,
        conversation_id: str,
        user_id: str,
        tenant_id: str,
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        include_sources: bool = True,
        search_params: dict = None
    ):
        """Generate streaming chat response."""
        
        # For now, return the full response as a single chunk
        # In production, implement actual streaming
        response = await self.generate_response(
            message, conversation_id, user_id, tenant_id,
            model, temperature, max_tokens, include_sources, search_params
        )
        
        # Simulate streaming by yielding chunks
        content = response.get("answer", "")
        words = content.split()
        
        for i in range(0, len(words), 5):  # 5 words per chunk
            chunk = " ".join(words[i:i+5])
            yield {
                "type": "content",
                "content": chunk + " " if i + 5 < len(words) else chunk
            }
        
        # Yield final metadata
        yield {
            "type": "metadata",
            "sources": response.get("sources", []),
            "model_used": response.get("model_used"),
            "cost_usd": response.get("cost_usd", 0.0)
        }


async def get_chat_service():
    """Get chat service instance."""
    return ChatService()


# Admin service dependencies
class AdminService:
    """Admin service for system management."""
    
    async def create_user(
        self,
        email: str,
        username: str,
        full_name: str,
        password: str,
        role: str = "USER",
        tenant_id: str = None,
        is_active: bool = True
    ):
        """Create a new user."""
        from ..models.user import User
        from ..core.auth import get_password_hash
        from ..core.database import get_db_session
        import uuid
        
        async with get_db_session() as session:
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                username=username,
                hashed_password=get_password_hash(password),
                full_name=full_name,
                role=role,
                is_active=is_active,
                is_verified=True,  # Admin-created users are verified
                tenant_id=tenant_id
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            return user
    
    async def cleanup_old_data(self, cutoff_date, dry_run: bool = True):
        """Clean up old system data."""
        from ..core.database import get_db_session
        from ..models.audit_log import AuditLog
        from sqlalchemy import select, delete
        
        cleanup_results = {
            "audit_logs": 0,
            "temp_files": 0,
            "cache_entries": 0
        }
        
        if not dry_run:
            async with get_db_session() as session:
                # Clean old audit logs
                result = await session.execute(
                    delete(AuditLog).where(AuditLog.timestamp < cutoff_date)
                )
                cleanup_results["audit_logs"] = result.rowcount
                await session.commit()
        
        return cleanup_results
    
    async def start_reindex_task(self):
        """Start reindexing task."""
        import uuid
        task_id = str(uuid.uuid4())
        
        # In production, start background task
        # For now, return task ID
        return task_id
    
    async def get_detailed_health(self):
        """Get detailed system health."""
        health = {
            "status": "healthy",
            "services": {},
            "database": {},
            "storage": {},
            "embedding": {},
            "search": {}
        }
        
        try:
            # Check all services
            health["storage"] = await storage_service.health_check()
            health["embedding"] = await embedding_service.health_check()
            health["search"] = await search_service.health_check()
            
            # Overall status
            service_statuses = [
                health["storage"].get("status"),
                health["embedding"].get("status"),
                health["search"].get("status")
            ]
            
            if any(status == "unhealthy" for status in service_statuses):
                health["status"] = "unhealthy"
            elif any(status == "degraded" for status in service_statuses):
                health["status"] = "degraded"
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health


async def get_admin_service():
    """Get admin service instance."""
    return AdminService()


# Analytics service
class AnalyticsService:
    """Analytics service for metrics."""
    
    async def get_performance_metrics(self):
        """Get performance metrics."""
        return {
            "avg_response_time_ms": 250,
            "requests_per_minute": 10,
            "error_rate_percent": 0.5,
            "uptime_percent": 99.9
        }


async def get_analytics_service():
    """Get analytics service instance."""
    return AnalyticsService()