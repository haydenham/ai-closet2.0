"""
Security middleware for rate limiting, request validation, and monitoring
"""
import json
import logging
import time
from typing import Callable, Dict, Any, Optional
from datetime import datetime

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.security import RateLimiter, SecurityConfig, InputSanitizer
from app.schemas.security import SecurityAuditLog

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for:
    - Rate limiting
    - Request validation
    - Security monitoring
    - Audit logging
    """
    
    def __init__(
        self,
        app: ASGIApp,
        enable_rate_limiting: bool = True,
        enable_request_validation: bool = True,
        enable_audit_logging: bool = True,
        rate_limit_storage: Optional[Dict] = None
    ):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_request_validation = enable_request_validation
        self.enable_audit_logging = enable_audit_logging
        self.rate_limit_storage = rate_limit_storage or {}
        
        # Define rate limits for different endpoint types
        self.rate_limits = {
            '/auth/': SecurityConfig.AUTH_RATE_LIMIT,
            '/closet/upload': SecurityConfig.UPLOAD_RATE_LIMIT,
            'default': SecurityConfig.DEFAULT_RATE_LIMIT
        }
        
        # Suspicious patterns to monitor
        self.suspicious_patterns = [
            'admin', 'root', 'test', 'debug', 'config',
            '../', '..\\', '/etc/', '/var/', '/usr/',
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP',
            '<script', 'javascript:', 'vbscript:', 'onload=',
            'union', 'information_schema', 'sysobjects'
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method"""
        start_time = time.time()
        
        try:
            # Get client information
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get('user-agent', 'unknown')
            endpoint = request.url.path
            method = request.method
            
            # Security checks
            if self.enable_request_validation:
                await self._validate_request(request, client_ip)
            
            if self.enable_rate_limiting:
                await self._check_rate_limit(request, client_ip, endpoint)
            
            # Process request
            response = await call_next(request)
            
            # Log successful requests if needed
            if self.enable_audit_logging and self._should_audit_request(request):
                await self._log_security_event(
                    event_type="request_success",
                    severity="info",
                    ip_address=client_ip,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    details={
                        "method": method,
                        "status_code": response.status_code,
                        "processing_time": time.time() - start_time
                    }
                )
            
            # Add security headers
            self._add_security_headers(response)
            
            return response
            
        except HTTPException as e:
            # Log security-related HTTP exceptions
            if self.enable_audit_logging and e.status_code in [401, 403, 429]:
                await self._log_security_event(
                    event_type="security_exception",
                    severity="warning",
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get('user-agent', 'unknown'),
                    endpoint=request.url.path,
                    details={
                        "status_code": e.status_code,
                        "detail": e.detail,
                        "processing_time": time.time() - start_time
                    }
                )
            raise e
            
        except Exception as e:
            # Log unexpected errors
            if self.enable_audit_logging:
                await self._log_security_event(
                    event_type="server_error",
                    severity="error",
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get('user-agent', 'unknown'),
                    endpoint=request.url.path,
                    details={
                        "error": str(e),
                        "processing_time": time.time() - start_time
                    }
                )
            
            logger.error(f"Unexpected error in security middleware: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else 'unknown'
    
    async def _validate_request(self, request: Request, client_ip: str):
        """Validate incoming request for security threats"""
        
        # Check URL for suspicious patterns
        url_path = request.url.path.lower()
        query_string = str(request.url.query).lower()
        
        for pattern in self.suspicious_patterns:
            if pattern.lower() in url_path or pattern.lower() in query_string:
                await self._log_security_event(
                    event_type="suspicious_request",
                    severity="warning",
                    ip_address=client_ip,
                    endpoint=request.url.path,
                    details={
                        "pattern": pattern,
                        "url": str(request.url),
                        "method": request.method
                    }
                )
                
                # Block obviously malicious requests
                if pattern.lower() in ['../', '..\\', '/etc/', 'information_schema']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid request"
                    )
        
        # Validate headers
        await self._validate_headers(request, client_ip)
        
        # Validate request body if present
        if request.method in ['POST', 'PUT', 'PATCH']:
            await self._validate_request_body(request, client_ip)
    
    async def _validate_headers(self, request: Request, client_ip: str):
        """Validate request headers"""
        
        # Check for excessively long headers
        for name, value in request.headers.items():
            if len(value) > 8192:  # 8KB limit per header
                await self._log_security_event(
                    event_type="oversized_header",
                    severity="warning",
                    ip_address=client_ip,
                    endpoint=request.url.path,
                    details={"header": name, "size": len(value)}
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Request header too large"
                )
        
        # Check user agent
        user_agent = request.headers.get('user-agent', '')
        if len(user_agent) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user agent"
            )
        
        # Check for suspicious user agents
        suspicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'nessus',
            'burpsuite', 'owasp', 'w3af', 'havij'
        ]
        
        for agent in suspicious_agents:
            if agent.lower() in user_agent.lower():
                await self._log_security_event(
                    event_type="suspicious_user_agent",
                    severity="high",
                    ip_address=client_ip,
                    user_agent=user_agent,
                    endpoint=request.url.path,
                    details={"detected_tool": agent}
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
    
    async def _validate_request_body(self, request: Request, client_ip: str):
        """Validate request body content"""
        
        content_type = request.headers.get('content-type', '')
        
        # Check content length
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                length = int(content_length)
                max_size = 50 * 1024 * 1024  # 50MB for file uploads
                
                if length > max_size:
                    await self._log_security_event(
                        event_type="oversized_request",
                        severity="warning",
                        ip_address=client_ip,
                        endpoint=request.url.path,
                        details={"content_length": length, "max_allowed": max_size}
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Request too large"
                    )
            except ValueError:
                pass
        
        # For JSON requests, validate content
        if 'application/json' in content_type:
            try:
                # Read body (this might consume the stream, but FastAPI handles it)
                body = await request.body()
                if body:
                    # Basic JSON validation
                    try:
                        json_data = json.loads(body)
                        
                        # Check for deeply nested objects (JSON bomb protection)
                        def check_depth(obj, depth=0):
                            if depth > 20:  # Max depth limit
                                return False
                            if isinstance(obj, dict):
                                return all(check_depth(v, depth + 1) for v in obj.values())
                            elif isinstance(obj, list):
                                return all(check_depth(item, depth + 1) for item in obj)
                            return True
                        
                        if not check_depth(json_data):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Request structure too complex"
                            )
                        
                        # Check for suspicious content in JSON strings
                        def check_json_strings(obj):
                            if isinstance(obj, str):
                                if InputSanitizer.detect_sql_injection(obj) or InputSanitizer.detect_xss(obj):
                                    return False
                            elif isinstance(obj, dict):
                                return all(check_json_strings(v) for v in obj.values())
                            elif isinstance(obj, list):
                                return all(check_json_strings(item) for item in obj)
                            return True
                        
                        if not check_json_strings(json_data):
                            await self._log_security_event(
                                event_type="malicious_json_content",
                                severity="high",
                                ip_address=client_ip,
                                endpoint=request.url.path,
                                details={"content_preview": str(json_data)[:200]}
                            )
                            
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid request content"
                            )
                    
                    except json.JSONDecodeError:
                        # Invalid JSON will be handled by FastAPI
                        pass
                        
            except Exception as e:
                logger.error(f"Error validating request body: {e}")
    
    async def _check_rate_limit(self, request: Request, client_ip: str, endpoint: str):
        """Check rate limits for the request"""
        
        # Determine rate limit for this endpoint
        rate_limit = self.rate_limits['default']
        
        for pattern, limit in self.rate_limits.items():
            if pattern != 'default' and pattern in endpoint:
                rate_limit = limit
                break
        
        # Create identifier for rate limiting
        identifier = f"{client_ip}:{endpoint}"
        
        # Check if rate limited
        if RateLimiter.is_rate_limited(identifier, rate_limit, window_minutes=1):
            rate_info = RateLimiter.get_rate_limit_info(identifier, rate_limit, window_minutes=1)
            
            await self._log_security_event(
                event_type="rate_limit_exceeded",
                severity="warning",
                ip_address=client_ip,
                endpoint=endpoint,
                details={
                    "limit": rate_limit,
                    "window_minutes": 1,
                    "reset_time": rate_info['reset_time'].isoformat()
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": str(rate_info['remaining']),
                    "X-RateLimit-Reset": str(int(rate_info['reset_time'].timestamp())),
                    "Retry-After": "60"
                }
            )
    
    def _should_audit_request(self, request: Request) -> bool:
        """Determine if request should be audited"""
        
        # Always audit authentication endpoints
        if '/auth/' in request.url.path:
            return True
        
        # Audit file uploads
        if '/upload' in request.url.path:
            return True
        
        # Audit admin endpoints
        if '/admin/' in request.url.path:
            return True
        
        # Audit based on method
        if request.method in ['POST', 'PUT', 'DELETE']:
            return True
        
        return False
    
    async def _log_security_event(
        self,
        event_type: str,
        severity: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security event for monitoring and analysis"""
        
        try:
            audit_log = SecurityAuditLog(
                event_type=event_type,
                severity=severity,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                details=details or {}
            )
            
            # Log to application logger
            log_message = f"Security Event: {event_type} | Severity: {severity} | IP: {ip_address} | Endpoint: {endpoint}"
            
            if severity == "error":
                logger.error(log_message, extra=audit_log.dict())
            elif severity == "warning" or severity == "high":
                logger.warning(log_message, extra=audit_log.dict())
            else:
                logger.info(log_message, extra=audit_log.dict())
            
            # In production, you might want to send this to a SIEM system
            # or security monitoring service
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy (adjust based on your needs)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # HSTS (only for HTTPS)
        if hasattr(response, 'url') and str(response.url).startswith('https'):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """Middleware for IP whitelisting (useful for admin endpoints)"""
    
    def __init__(self, app: ASGIApp, allowed_ips: list = None, protected_paths: list = None):
        super().__init__(app)
        self.allowed_ips = set(allowed_ips or [])
        self.protected_paths = protected_paths or ['/admin/', '/debug/']
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check IP whitelist for protected paths"""
        
        if not self.allowed_ips:
            # If no whitelist configured, allow all
            return await call_next(request)
        
        # Check if path is protected
        path = request.url.path
        is_protected = any(protected in path for protected in self.protected_paths)
        
        if is_protected:
            client_ip = self._get_client_ip(request)
            
            if client_ip not in self.allowed_ips:
                logger.warning(f"IP {client_ip} attempted to access protected path: {path}")
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'