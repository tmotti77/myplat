"""Request ID middleware for tracking requests across services."""
import contextvars
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import get_logger

logger = get_logger(__name__)

# Context variable for request ID
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('request_id')


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request."""
    
    def __init__(self, app, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with unique ID."""
        
        # Get request ID from header or generate new one
        request_id = request.headers.get(self.header_name)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Set in context variable for logging
        request_id_var.set(request_id)
        
        # Add to request state for access in route handlers
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers[self.header_name] = request_id
            
            return response
            
        except Exception as e:
            logger.error(
                "Request processing failed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                error=str(e),
                exc_info=True
            )
            raise
        
        finally:
            # Clean up context
            try:
                request_id_var.delete()
            except LookupError:
                pass


def get_request_id() -> str:
    """Get current request ID from context."""
    try:
        return request_id_var.get()
    except LookupError:
        return "no-request-id"