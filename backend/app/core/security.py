"""
Security utilities for input validation, sanitization, and protection
"""
import re
import html
import hashlib
import secrets
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.sql import text

logger = logging.getLogger(__name__)

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available. File type validation will use basic checks only.")

# Rate limiting storage (in production, use Redis)
_rate_limit_storage = defaultdict(list)

class SecurityConfig:
    """Security configuration constants"""
    
    # File upload security
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/webp', 'image/bmp', 'image/tiff'
    }
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    AUTH_RATE_LIMIT = 10     # auth requests per minute
    UPLOAD_RATE_LIMIT = 20   # upload requests per minute
    
    # Input validation
    MAX_STRING_LENGTH = 10000
    MAX_LIST_LENGTH = 1000
    MAX_DICT_DEPTH = 10
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(INFORMATION_SCHEMA|SYSOBJECTS|SYSCOLUMNS)",
        r"(\bxp_\w+|\bsp_\w+)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
    ]


class InputSanitizer:
    """Utility class for input sanitization"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input by removing/escaping dangerous characters
        
        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
            
        Raises:
            ValueError: If input is invalid
        """
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        # HTML escape to prevent XSS
        value = html.escape(value, quote=True)
        
        # Trim whitespace
        value = value.strip()
        
        # Check length
        if max_length and len(value) > max_length:
            raise ValueError(f"String too long (max {max_length} characters)")
        
        return value
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and other attacks
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not filename:
            raise ValueError("Filename cannot be empty")
        
        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Prevent reserved names on Windows
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
            'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in reserved_names:
            filename = f"file_{filename}"
        
        # Ensure minimum length
        if len(filename) < 1:
            filename = f"file_{secrets.token_hex(4)}"
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_len = 255 - len(ext) - 1 if ext else 255
            filename = f"{name[:max_name_len]}.{ext}" if ext else name[:255]
        
        return filename
    
    @staticmethod
    def detect_sql_injection(value: str) -> bool:
        """
        Detect potential SQL injection attempts
        
        Args:
            value: String to check
            
        Returns:
            True if potential SQL injection detected
        """
        value_upper = value.upper()
        
        for pattern in SecurityConfig.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def detect_xss(value: str) -> bool:
        """
        Detect potential XSS attempts
        
        Args:
            value: String to check
            
        Returns:
            True if potential XSS detected
        """
        for pattern in SecurityConfig.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def validate_and_sanitize_input(value: Any, field_name: str = "input") -> Any:
        """
        Comprehensive input validation and sanitization
        
        Args:
            value: Input value to validate
            field_name: Name of the field for error messages
            
        Returns:
            Sanitized value
            
        Raises:
            ValueError: If input is invalid or potentially malicious
        """
        if value is None:
            return None
        
        if isinstance(value, str):
            # Check for malicious patterns
            if InputSanitizer.detect_sql_injection(value):
                logger.warning(f"SQL injection attempt detected in {field_name}: {value[:100]}")
                raise ValueError(f"Invalid characters detected in {field_name}")
            
            if InputSanitizer.detect_xss(value):
                logger.warning(f"XSS attempt detected in {field_name}: {value[:100]}")
                raise ValueError(f"Invalid characters detected in {field_name}")
            
            # Sanitize the string
            return InputSanitizer.sanitize_string(value, SecurityConfig.MAX_STRING_LENGTH)
        
        elif isinstance(value, (list, tuple)):
            if len(value) > SecurityConfig.MAX_LIST_LENGTH:
                raise ValueError(f"List too long in {field_name} (max {SecurityConfig.MAX_LIST_LENGTH} items)")
            
            return [InputSanitizer.validate_and_sanitize_input(item, f"{field_name}[{i}]") 
                   for i, item in enumerate(value)]
        
        elif isinstance(value, dict):
            def count_depth(d, depth=0):
                if depth > SecurityConfig.MAX_DICT_DEPTH:
                    return depth
                if isinstance(d, dict):
                    return max(count_depth(v, depth + 1) for v in d.values()) if d else depth
                return depth
            
            if count_depth(value) > SecurityConfig.MAX_DICT_DEPTH:
                raise ValueError(f"Dictionary too deeply nested in {field_name}")
            
            return {
                InputSanitizer.validate_and_sanitize_input(k, f"{field_name}.key"): 
                InputSanitizer.validate_and_sanitize_input(v, f"{field_name}.{k}")
                for k, v in value.items()
            }
        
        elif isinstance(value, (int, float, bool)):
            return value
        
        else:
            # For other types, convert to string and sanitize
            return InputSanitizer.sanitize_string(str(value))


class FileValidator:
    """Utility class for file validation and security scanning"""
    
    @staticmethod
    def validate_file_type(file_data: bytes, filename: str, allowed_types: set) -> bool:
        """
        Validate file type using both extension and magic bytes
        
        Args:
            file_data: File content as bytes
            filename: Original filename
            allowed_types: Set of allowed MIME types
            
        Returns:
            True if file type is valid
        """
        try:
            # Check file extension
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            if f'.{file_ext}' not in SecurityConfig.ALLOWED_IMAGE_EXTENSIONS:
                return False
            
            # Check MIME type using python-magic if available
            if MAGIC_AVAILABLE:
                mime_type = magic.from_buffer(file_data, mime=True)
                return mime_type in allowed_types
            else:
                # Fallback: basic file signature checking
                return FileValidator._check_file_signature(file_data, file_ext)
            
        except Exception as e:
            logger.error(f"Error validating file type: {e}")
            return False
    
    @staticmethod
    def _check_file_signature(file_data: bytes, file_ext: str) -> bool:
        """
        Basic file signature checking when python-magic is not available
        
        Args:
            file_data: File content as bytes
            file_ext: File extension
            
        Returns:
            True if file signature matches extension
        """
        if not file_data:
            return False
        
        # Common image file signatures
        signatures = {
            'jpg': [b'\xff\xd8\xff'],
            'jpeg': [b'\xff\xd8\xff'],
            'png': [b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'],
            'gif': [b'GIF87a', b'GIF89a'],
            'bmp': [b'BM'],
            'webp': [b'RIFF', b'WEBP'],
            'tiff': [b'\x49\x49\x2a\x00', b'\x4d\x4d\x00\x2a']
        }
        
        file_ext = file_ext.lower()
        if file_ext not in signatures:
            return False
        
        for signature in signatures[file_ext]:
            if file_data.startswith(signature):
                return True
            # For WEBP, check for RIFF...WEBP pattern
            if file_ext == 'webp' and file_data.startswith(b'RIFF') and b'WEBP' in file_data[:12]:
                return True
        
        return False
    
    @staticmethod
    def scan_file_for_malware(file_data: bytes) -> bool:
        """
        Basic malware scanning for uploaded files
        
        Args:
            file_data: File content as bytes
            
        Returns:
            True if file appears safe
        """
        try:
            # Check for suspicious patterns in file headers
            suspicious_patterns = [
                b'<script',
                b'javascript:',
                b'vbscript:',
                b'<?php',
                b'<%',
                b'<html',
                b'<iframe',
                b'<object',
                b'<embed',
            ]
            
            # Check first 1KB for suspicious content
            header = file_data[:1024].lower()
            
            for pattern in suspicious_patterns:
                if pattern in header:
                    logger.warning(f"Suspicious pattern found in file: {pattern}")
                    return False
            
            # Check for executable signatures
            executable_signatures = [
                b'\x4d\x5a',  # PE executable
                b'\x7f\x45\x4c\x46',  # ELF executable
                b'\xfe\xed\xfa',  # Mach-O executable
            ]
            
            for sig in executable_signatures:
                if file_data.startswith(sig):
                    logger.warning("Executable file detected")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error scanning file for malware: {e}")
            return False
    
    @staticmethod
    def validate_image_file(file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Comprehensive image file validation
        
        Args:
            file_data: Image file content
            filename: Original filename
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ValueError: If file is invalid or potentially dangerous
        """
        # Check file size
        if len(file_data) > SecurityConfig.MAX_FILE_SIZE:
            raise ValueError(f"File too large (max {SecurityConfig.MAX_FILE_SIZE / 1024 / 1024}MB)")
        
        if len(file_data) == 0:
            raise ValueError("File is empty")
        
        # Validate filename
        safe_filename = InputSanitizer.sanitize_filename(filename)
        
        # Check file type
        if not FileValidator.validate_file_type(file_data, filename, SecurityConfig.ALLOWED_IMAGE_TYPES):
            raise ValueError("Invalid file type. Only image files are allowed.")
        
        # Scan for malware
        if not FileValidator.scan_file_for_malware(file_data):
            raise ValueError("File failed security scan")
        
        # Additional image-specific validation
        try:
            from PIL import Image
            import io
            
            # Try to open and validate the image
            image = Image.open(io.BytesIO(file_data))
            image.verify()  # Verify it's a valid image
            
            # Reset stream and get image info
            image = Image.open(io.BytesIO(file_data))
            width, height = image.size
            format_name = image.format
            
            # Check image dimensions (prevent zip bombs)
            max_pixels = 50 * 1024 * 1024  # 50 megapixels
            if width * height > max_pixels:
                raise ValueError("Image resolution too high")
            
            return {
                'safe_filename': safe_filename,
                'width': width,
                'height': height,
                'format': format_name,
                'size_bytes': len(file_data),
                'mime_type': magic.from_buffer(file_data, mime=True) if MAGIC_AVAILABLE else f'image/{format_name.lower()}'
            }
            
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            raise ValueError("Invalid or corrupted image file")


class RateLimiter:
    """Rate limiting utility"""
    
    @staticmethod
    def is_rate_limited(identifier: str, limit: int, window_minutes: int = 1) -> bool:
        """
        Check if identifier is rate limited
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            limit: Maximum requests allowed
            window_minutes: Time window in minutes
            
        Returns:
            True if rate limited
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old entries
        _rate_limit_storage[identifier] = [
            timestamp for timestamp in _rate_limit_storage[identifier]
            if timestamp > window_start
        ]
        
        # Check if limit exceeded
        if len(_rate_limit_storage[identifier]) >= limit:
            return True
        
        # Add current request
        _rate_limit_storage[identifier].append(now)
        return False
    
    @staticmethod
    def get_rate_limit_info(identifier: str, limit: int, window_minutes: int = 1) -> Dict[str, Any]:
        """
        Get rate limit information for identifier
        
        Args:
            identifier: Unique identifier
            limit: Maximum requests allowed
            window_minutes: Time window in minutes
            
        Returns:
            Dictionary with rate limit info
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old entries
        _rate_limit_storage[identifier] = [
            timestamp for timestamp in _rate_limit_storage[identifier]
            if timestamp > window_start
        ]
        
        current_requests = len(_rate_limit_storage[identifier])
        remaining = max(0, limit - current_requests)
        
        # Calculate reset time
        if _rate_limit_storage[identifier]:
            oldest_request = min(_rate_limit_storage[identifier])
            reset_time = oldest_request + timedelta(minutes=window_minutes)
        else:
            reset_time = now + timedelta(minutes=window_minutes)
        
        return {
            'limit': limit,
            'remaining': remaining,
            'reset_time': reset_time,
            'window_minutes': window_minutes
        }


def rate_limit(limit: int = SecurityConfig.DEFAULT_RATE_LIMIT, window_minutes: int = 1):
    """
    Decorator for rate limiting endpoints
    
    Args:
        limit: Maximum requests allowed
        window_minutes: Time window in minutes
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Use IP address as identifier (in production, consider user ID)
            client_ip = request.client.host if request.client else "unknown"
            identifier = f"{client_ip}:{func.__name__}"
            
            if RateLimiter.is_rate_limited(identifier, limit, window_minutes):
                rate_info = RateLimiter.get_rate_limit_info(identifier, limit, window_minutes)
                
                logger.warning(f"Rate limit exceeded for {client_ip} on {func.__name__}")
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": str(rate_info['remaining']),
                        "X-RateLimit-Reset": str(int(rate_info['reset_time'].timestamp())),
                        "Retry-After": str(window_minutes * 60)
                    }
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


class SecurityValidator(BaseModel):
    """Base class for security-enhanced Pydantic models"""
    
    class Config:
        # Enable validation on assignment
        validate_assignment = True
        # Use enum values
        use_enum_values = True
        # Validate default values
        validate_default = True
        # Extra fields are forbidden
        extra = "forbid"
    
    def __init__(self, **data):
        # Sanitize all input data before validation
        sanitized_data = {}
        for key, value in data.items():
            try:
                sanitized_data[key] = InputSanitizer.validate_and_sanitize_input(value, key)
            except ValueError as e:
                logger.warning(f"Input sanitization failed for {key}: {e}")
                raise ValueError(f"Invalid input for {key}: {str(e)}")
        
        super().__init__(**sanitized_data)


# Custom validators for common security checks
def validate_no_sql_injection(value: str) -> str:
    """Validator to prevent SQL injection"""
    if InputSanitizer.detect_sql_injection(value):
        raise ValueError("Invalid characters detected")
    return value


def validate_no_xss(value: str) -> str:
    """Validator to prevent XSS"""
    if InputSanitizer.detect_xss(value):
        raise ValueError("Invalid characters detected")
    return value


def validate_safe_filename(value: str) -> str:
    """Validator for safe filenames"""
    return InputSanitizer.sanitize_filename(value)


def validate_string_length(max_length: int):
    """Factory for string length validators"""
    def validator(value: str) -> str:
        if len(value) > max_length:
            raise ValueError(f"String too long (max {max_length} characters)")
        return value
    return validator