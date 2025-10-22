"""Health check and status endpoints."""

import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from ..core.database import get_db
from ..core.config import settings
from ..middleware.dependencies import get_redis_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Readiness check for dependencies."""
    checks = {}
    overall_status = "ready"
    
    # Database check
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        checks["database"] = {
            "status": "healthy",
            "response_time_ms": 0  # Could add timing
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "not_ready"
    
    # Redis check
    try:
        await redis_client.ping()
        checks["redis"] = {
            "status": "healthy"
        }
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "not_ready"
    
    # Vector database check (Qdrant)
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.QDRANT_URL}/health")
            if response.status_code == 200:
                checks["vector_db"] = {
                    "status": "healthy"
                }
            else:
                checks["vector_db"] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                overall_status = "not_ready"
    except Exception as e:
        checks["vector_db"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "not_ready"
    
    if overall_status != "ready":
        raise HTTPException(status_code=503, detail={
            "status": overall_status,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    # This would normally return Prometheus format metrics
    # For now, return basic metrics in JSON format
    return {
        "http_requests_total": 0,
        "http_request_duration_seconds": 0,
        "active_connections": 0,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/version")
async def version_info():
    """Version and build information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "environment": settings.ENVIRONMENT,
        "python_version": "3.11+",
        "build_date": datetime.utcnow().isoformat(),
        "features": {
            "multi_tenancy": settings.MULTI_TENANT_MODE,
            "real_time_updates": settings.ENABLE_REAL_TIME_UPDATES,
            "advanced_analytics": settings.ENABLE_ADVANCED_ANALYTICS,
            "expert_system": settings.ENABLE_EXPERT_SYSTEM,
            "feedback_learning": settings.ENABLE_FEEDBACK_LEARNING
        }
    }