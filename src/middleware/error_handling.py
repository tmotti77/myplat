"""Global error handling middleware."""
import traceback
from typing import Callable

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from src.core.config import settings
from src.core.logging import get_logger, log_error, log_security_event
from src.middleware.request_id import get_request_id

logger = get_logger(__name__)


class RateLimitException(Exception):
    """Rate limit exceeded exception."""
    pass


class AuthenticationException(Exception):
    """Authentication failed exception."""
    pass


class AuthorizationException(Exception):
    """Authorization failed exception."""
    pass


class TenantException(Exception):
    """Tenant-related exception."""
    pass


class ValidationException(Exception):
    """Validation exception."""
    pass


class ServiceUnavailableException(Exception):
    """Service unavailable exception."""
    pass


class CostLimitException(Exception):
    """Cost limit exceeded exception."""
    pass


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware with proper logging and response formatting."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle all requests with comprehensive error handling."""
        
        request_id = get_request_id()
        
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # FastAPI HTTP exceptions - pass through
            return await self._handle_http_exception(request, e, request_id)
            
        except RateLimitException as e:
            return await self._handle_rate_limit_exception(request, e, request_id)
            
        except AuthenticationException as e:
            return await self._handle_auth_exception(request, e, request_id)
            
        except AuthorizationException as e:
            return await self._handle_authz_exception(request, e, request_id)
            
        except TenantException as e:
            return await self._handle_tenant_exception(request, e, request_id)
            
        except ValidationException as e:
            return await self._handle_validation_exception(request, e, request_id)
            
        except ServiceUnavailableException as e:
            return await self._handle_service_unavailable_exception(request, e, request_id)
            
        except CostLimitException as e:
            return await self._handle_cost_limit_exception(request, e, request_id)
            
        except Exception as e:
            return await self._handle_unexpected_exception(request, e, request_id)
    
    async def _handle_http_exception(self, request: Request, exc: HTTPException, request_id: str) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        
        logger.warning(
            "HTTP exception",
            request_id=request_id,
            status_code=exc.status_code,
            detail=exc.detail,
            url=str(request.url),
            method=request.method
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "detail": exc.detail,
                "status_code": exc.status_code,
                "request_id": request_id,
                "type": "http_error"
            },
            headers=exc.headers
        )
    
    async def _handle_rate_limit_exception(self, request: Request, exc: RateLimitException, request_id: str) -> JSONResponse:
        """Handle rate limit exceptions."""
        
        client_ip = self._get_client_ip(request)
        
        log_security_event(
            "rate_limit_exceeded",
            client_ip=client_ip,
            request_id=request_id,
            url=str(request.url),
            method=request.method
        )
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate Limit Exceeded",
                "detail": "Too many requests. Please try again later.",
                "request_id": request_id,
                "type": "rate_limit_error"
            },
            headers={
                "Retry-After": "60"  # Suggest retry after 60 seconds
            }
        )
    
    async def _handle_auth_exception(self, request: Request, exc: AuthenticationException, request_id: str) -> JSONResponse:
        """Handle authentication exceptions."""
        
        log_security_event(
            "authentication_failed",
            client_ip=self._get_client_ip(request),
            request_id=request_id,
            url=str(request.url),
            method=request.method,
            error=str(exc)
        )
        
        return JSONResponse(
            status_code=401,
            content={
                "error": "Authentication Required",
                "detail": "Authentication credentials were not provided or are invalid.",
                "request_id": request_id,
                "type": "authentication_error"
            },
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )
    
    async def _handle_authz_exception(self, request: Request, exc: AuthorizationException, request_id: str) -> JSONResponse:
        """Handle authorization exceptions."""
        
        log_security_event(
            "authorization_failed",
            client_ip=self._get_client_ip(request),
            request_id=request_id,
            url=str(request.url),
            method=request.method,
            error=str(exc)
        )
        
        return JSONResponse(
            status_code=403,
            content={
                "error": "Access Forbidden",
                "detail": "You do not have permission to access this resource.",
                "request_id": request_id,
                "type": "authorization_error"
            }
        )
    
    async def _handle_tenant_exception(self, request: Request, exc: TenantException, request_id: str) -> JSONResponse:
        """Handle tenant-related exceptions."""
        
        logger.warning(
            "Tenant error",
            request_id=request_id,
            error=str(exc),
            url=str(request.url),
            method=request.method
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "Tenant Error",
                "detail": str(exc),
                "request_id": request_id,
                "type": "tenant_error"
            }
        )
    
    async def _handle_validation_exception(self, request: Request, exc: ValidationException, request_id: str) -> JSONResponse:
        """Handle validation exceptions."""
        
        logger.warning(
            "Validation error",
            request_id=request_id,
            error=str(exc),
            url=str(request.url),
            method=request.method
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "detail": str(exc),
                "request_id": request_id,
                "type": "validation_error"
            }
        )
    
    async def _handle_service_unavailable_exception(self, request: Request, exc: ServiceUnavailableException, request_id: str) -> JSONResponse:
        """Handle service unavailable exceptions."""
        
        logger.error(
            "Service unavailable",
            request_id=request_id,
            error=str(exc),
            url=str(request.url),
            method=request.method
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service Unavailable",
                "detail": "The service is temporarily unavailable. Please try again later.",
                "request_id": request_id,
                "type": "service_unavailable_error"
            },
            headers={
                "Retry-After": "300"  # Suggest retry after 5 minutes
            }
        )
    
    async def _handle_cost_limit_exception(self, request: Request, exc: CostLimitException, request_id: str) -> JSONResponse:
        """Handle cost limit exceptions."""
        
        logger.warning(
            "Cost limit exceeded",
            request_id=request_id,
            error=str(exc),
            url=str(request.url),
            method=request.method
        )
        
        return JSONResponse(
            status_code=402,
            content={
                "error": "Cost Limit Exceeded",
                "detail": str(exc),
                "request_id": request_id,
                "type": "cost_limit_error"
            }
        )
    
    async def _handle_unexpected_exception(self, request: Request, exc: Exception, request_id: str) -> JSONResponse:
        """Handle unexpected exceptions."""
        
        # Get detailed error information
        error_info = {
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent"),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }
        
        # Log full error with stack trace
        log_error(exc, error_info)
        
        # Prepare response
        if settings.APP_DEBUG:
            # In debug mode, include traceback
            error_detail = {
                "message": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc()
            }
        else:
            # In production, generic message
            error_detail = "An unexpected error occurred. Please try again later."
        
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": error_detail,
                "request_id": request_id,
                "type": "internal_error"
            }
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        
        # Check for forwarded headers (load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (client)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"