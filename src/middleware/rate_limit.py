"""Rate limiting middleware with Redis backend."""
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.core.logging import get_logger
from src.middleware.error_handling import RateLimitException
from src.middleware.request_id import get_request_id

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm."""
    
    def __init__(self, app):
        super().__init__(app)
        self._redis = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests."""
        
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Check rate limit
        if not await self._check_rate_limit(client_id, request):
            raise RateLimitException("Rate limit exceeded")
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        await self._add_rate_limit_headers(response, client_id, request)
        
        return response
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for client."""
        
        # Use authenticated user ID if available
        if hasattr(request.state, 'user_id') and request.state.user_id:
            return f"user:{request.state.user_id}"
        
        # Use tenant ID if available
        if hasattr(request.state, 'tenant_id') and request.state.tenant_id:
            return f"tenant:{request.state.tenant_id}"
        
        # Fall back to IP address
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def _check_rate_limit(self, client_id: str, request: Request) -> bool:
        """Check if request is within rate limits."""
        
        try:
            # Get Redis connection
            redis = await self._get_redis()
            if not redis:
                # If Redis is unavailable, allow request (fail open)
                logger.warning("Redis unavailable for rate limiting, allowing request")
                return True
            
            # Determine rate limits based on request type
            limits = self._get_rate_limits(request)
            
            # Check each time window
            for window_seconds, max_requests in limits.items():
                if not await self._check_window_limit(redis, client_id, window_seconds, max_requests):
                    logger.warning(
                        "Rate limit exceeded",
                        client_id=client_id,
                        window_seconds=window_seconds,
                        max_requests=max_requests,
                        request_id=get_request_id()
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.error("Rate limit check failed", error=str(e), client_id=client_id)
            # Fail open - allow request if rate limiting fails
            return True
    
    async def _check_window_limit(self, redis, client_id: str, window_seconds: int, max_requests: int) -> bool:
        """Check rate limit for specific time window using sliding window."""
        
        now = time.time()
        window_start = now - window_seconds
        
        # Redis key for this client and window
        key = f"rate_limit:{client_id}:{window_seconds}"
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = redis.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiration
            pipe.expire(key, window_seconds + 1)
            
            # Execute pipeline
            results = await pipe.execute()
            
            # Check if limit exceeded
            current_count = results[1]  # Result of zcard
            
            return current_count < max_requests
            
        except Exception as e:
            logger.error("Rate limit window check failed", error=str(e), key=key)
            return True  # Fail open
    
    def _get_rate_limits(self, request: Request) -> dict:
        """Get rate limits for request."""
        
        # Base limits
        limits = {
            60: settings.RATE_LIMIT_PER_MINUTE,  # Per minute
            3600: settings.RATE_LIMIT_PER_MINUTE * 60,  # Per hour
            86400: settings.RATE_LIMIT_PER_MINUTE * 60 * 24,  # Per day
        }
        
        # Adjust based on endpoint
        path = request.url.path
        
        if path.startswith("/api/v1/ask"):
            # Stricter limits for LLM queries
            limits[60] = min(limits[60], 10)  # Max 10 questions per minute
            limits[3600] = min(limits[3600], 100)  # Max 100 per hour
        elif path.startswith("/api/v1/ingest"):
            # Generous limits for document ingestion
            limits[60] = min(limits[60], 20)  # Max 20 uploads per minute
        elif path.startswith("/api/v1/search"):
            # Medium limits for search
            limits[60] = min(limits[60], 30)  # Max 30 searches per minute
        
        # Premium users get higher limits
        if hasattr(request.state, 'user_plan') and request.state.user_plan == 'premium':
            for window in limits:
                limits[window] *= 2
        
        return limits
    
    async def _add_rate_limit_headers(self, response: Response, client_id: str, request: Request):
        """Add rate limit information to response headers."""
        
        try:
            redis = await self._get_redis()
            if not redis:
                return
            
            limits = self._get_rate_limits(request)
            
            # Add headers for primary limit (per minute)
            window_seconds = 60
            max_requests = limits[window_seconds]
            
            key = f"rate_limit:{client_id}:{window_seconds}"
            
            # Get current usage
            now = time.time()
            window_start = now - window_seconds
            
            # Count requests in current window
            current_count = await redis.zcount(key, window_start, now)
            
            # Add headers
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(max(0, max_requests - current_count))
            response.headers["X-RateLimit-Reset"] = str(int(now + window_seconds))
            response.headers["X-RateLimit-Window"] = str(window_seconds)
            
        except Exception as e:
            logger.error("Failed to add rate limit headers", error=str(e))
    
    async def _get_redis(self):
        """Get Redis connection lazily."""
        
        if self._redis is None:
            try:
                from src.services.cache import cache_service
                self._redis = await cache_service.get_client()
            except Exception as e:
                logger.error("Failed to get Redis connection for rate limiting", error=str(e))
                return None
        
        return self._redis