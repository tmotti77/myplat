"""Tenant isolation middleware for multi-tenancy."""
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.core.logging import get_logger
from src.middleware.error_handling import TenantException
from src.middleware.request_id import get_request_id

logger = get_logger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to handle tenant identification and isolation."""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Identify tenant and set context."""
        
        # Skip tenant handling for non-API routes
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        
        # Skip for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        try:
            # Identify tenant
            tenant_info = await self._identify_tenant(request)
            
            if not tenant_info:
                raise TenantException("Unable to identify tenant")
            
            # Set tenant context
            request.state.tenant_id = tenant_info["id"]
            request.state.tenant_name = tenant_info["name"]
            request.state.tenant_plan = tenant_info.get("plan", "basic")
            request.state.tenant_features = tenant_info.get("features", {})
            
            # Validate tenant status
            if tenant_info.get("status") != "active":
                raise TenantException("Tenant account is not active")
            
            # Check tenant limits
            await self._check_tenant_limits(request, tenant_info)
            
            # Process request
            response = await call_next(request)
            
            # Add tenant headers
            response.headers["X-Tenant-ID"] = tenant_info["id"]
            
            return response
            
        except TenantException:
            raise
        except Exception as e:
            logger.error(
                "Tenant middleware error",
                error=str(e),
                request_id=get_request_id(),
                url=str(request.url)
            )
            raise TenantException("Tenant processing failed")
    
    async def _identify_tenant(self, request: Request) -> Optional[dict]:
        """Identify tenant from request."""
        
        tenant_id = None
        
        # Method 1: From subdomain (e.g., tenant1.api.example.com)
        host = request.headers.get("host", "")
        if "." in host and not host.startswith("localhost"):
            subdomain = host.split(".")[0]
            if subdomain and subdomain != "api" and subdomain != "www":
                tenant_id = subdomain
        
        # Method 2: From custom header
        if not tenant_id:
            tenant_id = request.headers.get("X-Tenant-ID")
        
        # Method 3: From query parameter (for development)
        if not tenant_id and settings.APP_DEBUG:
            tenant_id = request.query_params.get("tenant_id")
        
        # Method 4: From JWT token (will be available after auth middleware)
        if not tenant_id and hasattr(request.state, 'tenant_id'):
            tenant_id = request.state.tenant_id
        
        if not tenant_id:
            # For single-tenant mode, use default tenant
            if not settings.MULTI_TENANT_MODE:
                tenant_id = "default"
            else:
                return None
        
        # Look up tenant information
        return await self._get_tenant_info(tenant_id)
    
    async def _get_tenant_info(self, tenant_id: str) -> Optional[dict]:
        """Get tenant information from database."""
        
        try:
            from src.core.database import db
            from src.models.tenant import Tenant
            
            async with db.get_session() as session:
                # Query tenant by ID or name
                from sqlalchemy import select, or_
                
                query = select(Tenant).where(
                    or_(
                        Tenant.id == tenant_id,
                        Tenant.name == tenant_id
                    )
                )
                
                result = await session.execute(query)
                tenant = result.scalar_one_or_none()
                
                if not tenant:
                    logger.warning("Tenant not found", tenant_id=tenant_id)
                    return None
                
                return {
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "display_name": tenant.display_name,
                    "plan": tenant.plan,
                    "status": tenant.status,
                    "features": tenant.features,
                    "config": tenant.config,
                    "max_documents": tenant.max_documents,
                    "max_queries_per_day": tenant.max_queries_per_day,
                    "daily_cost_limit_usd": tenant.daily_cost_limit_usd / 100,  # Convert from cents
                    "monthly_cost_limit_usd": tenant.monthly_cost_limit_usd / 100,
                }
                
        except Exception as e:
            logger.error("Failed to get tenant info", tenant_id=tenant_id, error=str(e))
            return None
    
    async def _check_tenant_limits(self, request: Request, tenant_info: dict):
        """Check if tenant is within usage limits."""
        
        # Check feature access
        path = request.url.path
        
        if path.startswith("/api/v1/ask") or path.startswith("/api/v1/search"):
            if not tenant_info["features"].get("api_access", True):
                raise TenantException("API access not enabled for this tenant")
        
        if path.startswith("/api/v1/experts"):
            if not tenant_info["features"].get("expert_system", False):
                raise TenantException("Expert system not enabled for this tenant")
        
        if path.startswith("/api/v1/analytics"):
            if not tenant_info["features"].get("advanced_analytics", False):
                raise TenantException("Advanced analytics not enabled for this tenant")
        
        # Check daily query limits
        if request.method == "POST" and path.startswith("/api/v1/ask"):
            await self._check_daily_query_limit(tenant_info["id"], tenant_info["max_queries_per_day"])
        
        # Check cost limits
        await self._check_cost_limits(tenant_info["id"], tenant_info)
    
    async def _check_daily_query_limit(self, tenant_id: str, max_queries: int):
        """Check daily query limit for tenant."""
        
        try:
            from src.services.cache import cache_service
            
            # Get current date key
            from datetime import datetime
            date_key = datetime.utcnow().strftime("%Y-%m-%d")
            cache_key = f"tenant:{tenant_id}:queries:{date_key}"
            
            # Get current count
            redis = await cache_service.get_client()
            current_count = await redis.get(cache_key)
            current_count = int(current_count) if current_count else 0
            
            if current_count >= max_queries:
                raise TenantException(f"Daily query limit of {max_queries} exceeded")
            
            # Increment counter
            await redis.incr(cache_key)
            await redis.expire(cache_key, 86400)  # Expire after 24 hours
            
        except TenantException:
            raise
        except Exception as e:
            logger.error("Failed to check query limit", tenant_id=tenant_id, error=str(e))
            # Don't block on cache failures
    
    async def _check_cost_limits(self, tenant_id: str, tenant_info: dict):
        """Check cost limits for tenant."""
        
        try:
            from src.services.cache import cache_service
            from datetime import datetime
            
            redis = await cache_service.get_client()
            
            # Check daily cost limit
            date_key = datetime.utcnow().strftime("%Y-%m-%d")
            daily_cost_key = f"tenant:{tenant_id}:cost:daily:{date_key}"
            
            daily_cost = await redis.get(daily_cost_key)
            daily_cost = float(daily_cost) if daily_cost else 0.0
            
            if daily_cost >= tenant_info["daily_cost_limit_usd"]:
                raise TenantException("Daily cost limit exceeded")
            
            # Check monthly cost limit
            month_key = datetime.utcnow().strftime("%Y-%m")
            monthly_cost_key = f"tenant:{tenant_id}:cost:monthly:{month_key}"
            
            monthly_cost = await redis.get(monthly_cost_key)
            monthly_cost = float(monthly_cost) if monthly_cost else 0.0
            
            if monthly_cost >= tenant_info["monthly_cost_limit_usd"]:
                raise TenantException("Monthly cost limit exceeded")
                
        except TenantException:
            raise
        except Exception as e:
            logger.error("Failed to check cost limits", tenant_id=tenant_id, error=str(e))
            # Don't block on cache failures


def get_current_tenant_id(request: Request) -> Optional[str]:
    """Get current tenant ID from request state."""
    return getattr(request.state, 'tenant_id', None)


def get_current_tenant_features(request: Request) -> dict:
    """Get current tenant features from request state."""
    return getattr(request.state, 'tenant_features', {})


def require_tenant_feature(feature: str):
    """Decorator to require specific tenant feature."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            features = get_current_tenant_features(request)
            if not features.get(feature, False):
                raise TenantException(f"Feature '{feature}' not enabled for this tenant")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator