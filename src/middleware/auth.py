"""Authentication and authorization middleware."""
from jose import jwt
from datetime import datetime, timedelta
from typing import Callable, Optional, List

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.core.logging import get_logger, log_security_event
from src.middleware.error_handling import AuthenticationException, AuthorizationException
from src.middleware.request_id import get_request_id

logger = get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication and authorization middleware."""
    
    # Routes that don't require authentication
    PUBLIC_ROUTES = {
        "/",
        "/health",
        "/health/",
        "/health/ready",
        "/health/live",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
    
    # Routes that require authentication but have special handling
    AUTH_ROUTES = {
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/refresh",
        "/api/v1/auth/register",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
    }
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Authenticate and authorize requests."""
        
        # Skip authentication for public routes
        if self._is_public_route(request.url.path):
            return await call_next(request)
        
        try:
            # Extract and validate token
            token = self._extract_token(request)
            
            if not token:
                # Check if this is an auth route that allows anonymous access
                if request.url.path in self.AUTH_ROUTES:
                    return await call_next(request)
                raise AuthenticationException("Authentication token required")
            
            # Validate and decode token
            user_info = await self._validate_token(token)
            
            if not user_info:
                raise AuthenticationException("Invalid authentication token")
            
            # Set user context
            request.state.user_id = user_info["user_id"]
            request.state.user_email = user_info.get("email")
            request.state.user_role = user_info.get("role", "user")
            request.state.user_permissions = user_info.get("permissions", [])
            request.state.tenant_id = user_info.get("tenant_id")
            request.state.token_type = user_info.get("token_type", "access")
            
            # Check if user is active
            if not user_info.get("is_active", True):
                raise AuthenticationException("User account is not active")
            
            # Check authorization for protected routes
            await self._check_authorization(request, user_info)
            
            # Process request
            response = await call_next(request)
            
            # Add user context to response headers (for debugging in dev)
            if settings.APP_DEBUG:
                response.headers["X-User-ID"] = user_info["user_id"]
                response.headers["X-User-Role"] = user_info.get("role", "user")
            
            return response
            
        except (AuthenticationException, AuthorizationException):
            raise
        except Exception as e:
            logger.error(
                "Auth middleware error",
                error=str(e),
                request_id=get_request_id(),
                url=str(request.url)
            )
            raise AuthenticationException("Authentication processing failed")
    
    def _is_public_route(self, path: str) -> bool:
        """Check if route is public (no auth required)."""
        
        # Exact matches
        if path in self.PUBLIC_ROUTES:
            return True
        
        # Pattern matches
        if path.startswith("/health"):
            return True
        
        if path.startswith("/static"):
            return True
        
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract authentication token from request."""
        
        # Method 1: Authorization header (Bearer token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        # Method 2: Cookie (for web sessions)
        token = request.cookies.get("access_token")
        if token:
            return token
        
        # Method 3: Query parameter (for development/webhooks)
        if settings.APP_DEBUG:
            token = request.query_params.get("token")
            if token:
                return token
        
        # Method 4: Custom header
        token = request.headers.get("X-Auth-Token")
        if token:
            return token
        
        return None
    
    async def _validate_token(self, token: str) -> Optional[dict]:
        """Validate and decode JWT token."""
        
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                log_security_event("token_expired", token_type="access")
                return None
            
            # Extract user information
            user_id = payload.get("sub")  # Subject (user ID)
            if not user_id:
                return None
            
            # Get additional user info from database
            user_info = await self._get_user_info(user_id)
            if not user_info:
                return None
            
            # Merge token payload with user info
            return {
                "user_id": user_id,
                "tenant_id": payload.get("tenant_id"),
                "email": user_info.get("email"),
                "role": user_info.get("role"),
                "permissions": user_info.get("permissions", []),
                "is_active": user_info.get("is_active", True),
                "token_type": payload.get("type", "access"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
            }
            
        except jwt.ExpiredSignatureError:
            log_security_event("token_expired", token_type="access")
            return None
        except jwt.InvalidTokenError as e:
            log_security_event("invalid_token", error=str(e))
            return None
        except Exception as e:
            logger.error("Token validation failed", error=str(e))
            return None
    
    async def _get_user_info(self, user_id: str) -> Optional[dict]:
        """Get user information from database."""
        
        try:
            from src.core.database import db
            from src.models.user import User
            from sqlalchemy import select
            
            async with db.get_session() as session:
                query = select(User).where(User.id == user_id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                
                if not user:
                    return None
                
                return {
                    "email": user.email_hash,  # This would be the actual email in real implementation
                    "role": user.role,
                    "permissions": user.permissions,
                    "is_active": user.is_active,
                    "tenant_id": str(user.tenant_id),
                    "last_login": user.last_login_at,
                }
                
        except Exception as e:
            logger.error("Failed to get user info", user_id=user_id, error=str(e))
            return None
    
    async def _check_authorization(self, request: Request, user_info: dict):
        """Check if user is authorized for the requested resource."""
        
        path = request.url.path
        method = request.method
        user_role = user_info.get("role", "user")
        permissions = user_info.get("permissions", [])
        
        # Admin users have access to everything
        if user_role == "admin":
            return
        
        # Check role-based access
        if path.startswith("/api/v1/admin"):
            if user_role not in ["admin", "manager"]:
                raise AuthorizationException("Admin access required")
        
        if path.startswith("/api/v1/management"):
            if user_role not in ["admin", "manager"]:
                raise AuthorizationException("Management access required")
        
        # Check permission-based access
        required_permission = self._get_required_permission(path, method)
        if required_permission and required_permission not in permissions:
            if user_role not in ["admin", "manager"]:  # Admins/managers bypass permission checks
                raise AuthorizationException(f"Permission '{required_permission}' required")
        
        # Check resource-level access (e.g., tenant isolation)
        await self._check_resource_access(request, user_info)
    
    def _get_required_permission(self, path: str, method: str) -> Optional[str]:
        """Get required permission for endpoint."""
        
        # Map endpoints to permissions
        permission_map = {
            ("/api/v1/documents", "POST"): "documents:create",
            ("/api/v1/documents", "DELETE"): "documents:delete",
            ("/api/v1/sources", "POST"): "sources:create",
            ("/api/v1/sources", "PUT"): "sources:update",
            ("/api/v1/sources", "DELETE"): "sources:delete",
            ("/api/v1/experts", "POST"): "experts:create",
            ("/api/v1/experts", "PUT"): "experts:update",
            ("/api/v1/feedback", "POST"): "feedback:create",
            ("/api/v1/analytics", "GET"): "analytics:read",
            ("/api/v1/experiments", "POST"): "experiments:create",
            ("/api/v1/experiments", "PUT"): "experiments:update",
        }
        
        # Check exact matches
        for (endpoint_path, endpoint_method), permission in permission_map.items():
            if path.startswith(endpoint_path) and method == endpoint_method:
                return permission
        
        # Default permissions for common operations
        if method == "GET":
            return None  # Read access generally allowed
        elif method in ["POST", "PUT", "PATCH"]:
            return "content:write"
        elif method == "DELETE":
            return "content:delete"
        
        return None
    
    async def _check_resource_access(self, request: Request, user_info: dict):
        """Check access to specific resources (tenant isolation, ownership, etc.)."""
        
        user_tenant_id = user_info.get("tenant_id")
        request_tenant_id = getattr(request.state, 'tenant_id', None)
        
        # Ensure user can only access their tenant's resources
        if user_tenant_id and request_tenant_id:
            if user_tenant_id != request_tenant_id:
                log_security_event(
                    "cross_tenant_access_attempt",
                    user_id=user_info["user_id"],
                    user_tenant=user_tenant_id,
                    requested_tenant=request_tenant_id
                )
                raise AuthorizationException("Access denied to resources outside your tenant")


def get_current_user_id(request: Request) -> Optional[str]:
    """Get current user ID from request state."""
    return getattr(request.state, 'user_id', None)


def get_current_user_role(request: Request) -> str:
    """Get current user role from request state."""
    return getattr(request.state, 'user_role', 'user')


def get_current_user_permissions(request: Request) -> List[str]:
    """Get current user permissions from request state."""
    return getattr(request.state, 'user_permissions', [])


def require_permission(permission: str):
    """Decorator to require specific permission."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            permissions = get_current_user_permissions(request)
            user_role = get_current_user_role(request)
            
            # Admins bypass permission checks
            if user_role == "admin":
                return await func(request, *args, **kwargs)
            
            if permission not in permissions:
                raise AuthorizationException(f"Permission '{permission}' required")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role: str):
    """Decorator to require specific role."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user_role = get_current_user_role(request)
            
            # Define role hierarchy
            role_hierarchy = {
                "user": 0,
                "analyst": 1,
                "manager": 2,
                "admin": 3
            }
            
            user_level = role_hierarchy.get(user_role, 0)
            required_level = role_hierarchy.get(role, 0)
            
            if user_level < required_level:
                raise AuthorizationException(f"Role '{role}' or higher required")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def create_access_token(user_id: str, tenant_id: str, additional_claims: dict = None) -> str:
    """Create JWT access token."""
    
    now = datetime.utcnow()
    expires = now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    payload = {
        "sub": user_id,  # Subject (user ID)
        "tenant_id": tenant_id,
        "type": "access",
        "iat": now.timestamp(),
        "exp": expires.timestamp(),
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, tenant_id: str) -> str:
    """Create JWT refresh token."""
    
    now = datetime.utcnow()
    expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)
    
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "type": "refresh",
        "iat": now.timestamp(),
        "exp": expires.timestamp(),
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)