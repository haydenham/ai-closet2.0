"""
Rate limiting decorators and utilities for API endpoints
"""
import logging
from functools import wraps
from typing import Callable, Optional

from fastapi import Request, HTTPException, status, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.security import SecurityConfig

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    "auth": "10/minute",           # Authentication endpoints
    "upload": "20/minute",         # File upload endpoints  
    "api": "100/minute",           # General API endpoints
    "search": "50/minute",         # Search endpoints
    "recommendation": "30/minute", # AI recommendation endpoints
}


def rate_limit(limit_type: str = "api"):
    """
    Rate limiting decorator for FastAPI endpoints
    
    Args:
        limit_type: Type of rate limit to apply (auth, upload, api, search, recommendation)
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        rate_limit_string = RATE_LIMITS.get(limit_type, RATE_LIMITS["api"])
        
        @wraps(func)
        @limiter.limit(rate_limit_string)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                return await func(request, *args, **kwargs)
            except RateLimitExceeded as e:
                logger.warning(
                    f"Rate limit exceeded for {get_remote_address(request)} "
                    f"on endpoint {request.url.path} (limit: {rate_limit_string})"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {rate_limit_string}",
                    headers={
                        "Retry-After": str(e.retry_after) if hasattr(e, 'retry_after') else "60"
                    }
                )
        
        return wrapper
    return decorator


def get_rate_limiter():
    """Get the configured rate limiter instance"""
    return limiter


def auth_rate_limit(request: Request):
    """Rate limit dependency for authentication endpoints"""
    return limiter.limit(RATE_LIMITS["auth"])(request)


def upload_rate_limit(request: Request):
    """Rate limit dependency for upload endpoints"""
    return limiter.limit(RATE_LIMITS["upload"])(request)


def search_rate_limit(request: Request):
    """Rate limit dependency for search endpoints"""
    return limiter.limit(RATE_LIMITS["search"])(request)


def recommendation_rate_limit(request: Request):
    """Rate limit dependency for recommendation endpoints"""
    return limiter.limit(RATE_LIMITS["recommendation"])(request)


# Custom rate limit exceeded handler
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors"""
    logger.warning(
        f"Rate limit exceeded for {get_remote_address(request)} "
        f"on endpoint {request.url.path}"
    )
    
    response = {
        "error": "Rate limit exceeded",
        "detail": f"Too many requests. Limit: {exc.detail}",
        "retry_after": getattr(exc, 'retry_after', 60)
    }
    
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=response,
        headers={
            "Retry-After": str(getattr(exc, 'retry_after', 60))
        }
    )