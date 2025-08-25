"""Minimal security utility module (stub).
Provides a lightweight replacement for the removed comprehensive security system
so existing imports and tests continue to function. Expand as needed.
"""
from __future__ import annotations
import re
import html
import hashlib
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# -------------------- Configuration --------------------
class SecurityConfig:
    AUTH_RATE_LIMIT = "10/minute"
    UPLOAD_RATE_LIMIT = "20/minute"
    DEFAULT_RATE_LIMIT = "100/minute"

# -------------------- Input Sanitization --------------------
class InputSanitizer:
    _SQL_PATTERN = re.compile(r"(union select|drop table|--|;\s*delete|or\s+1=1|information_schema)", re.IGNORECASE)
    _XSS_PATTERN = re.compile(r"(<script.*?>|javascript:|onerror=|onload=|<iframe|<object|<img .*?onerror=)", re.IGNORECASE)
    _FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._-]")
    _RESERVED = {"CON", "PRN", "AUX", "NUL"}

    @staticmethod
    def sanitize_string(value: str, max_length: int = 500) -> str:
        if len(value) > max_length:
            raise ValueError("String too long")
        # Remove control chars
        value = ''.join(ch for ch in value if 32 <= ord(ch) < 127)
        return html.escape(value)

    @staticmethod
    def sanitize_filename(name: str) -> str:
        if not name:
            raise ValueError("Filename cannot be empty")
        # Strip directory components
        name = name.replace('..', '').replace('/', '').replace('\\', '')
        name = InputSanitizer._FILENAME_SAFE.sub('', name)
        if not name:
            raise ValueError("Filename cannot be empty")
        stem = name.split('.')[0]
        if stem.upper() in InputSanitizer._RESERVED:
            name = f"file_{name}"
        return name[:255]

    @staticmethod
    def detect_sql_injection(value: str) -> bool:
        return bool(InputSanitizer._SQL_PATTERN.search(value))

    @staticmethod
    def detect_xss(value: str) -> bool:
        return bool(InputSanitizer._XSS_PATTERN.search(value))

# -------------------- File Validation --------------------
class FileValidator:
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    MAX_SIZE_BYTES = 10 * 1024 * 1024

    @staticmethod
    def validate_image_file(data: bytes, filename: str) -> Dict[str, Any]:
        safe = InputSanitizer.sanitize_filename(filename)
        ext = ('.' + safe.rsplit('.', 1)[-1].lower()) if '.' in safe else ''
        if ext not in FileValidator.ALLOWED_EXTENSIONS:
            raise ValueError("Unsupported file type")
        if len(data) > FileValidator.MAX_SIZE_BYTES:
            raise ValueError("File too large")
        # Very lightweight mime inference
        mime = 'image/' + ext.lstrip('.')
        return {
            'safe_filename': safe,
            'size_bytes': len(data),
            'mime_type': mime,
            'width': None,
            'height': None
        }

# -------------------- Rate Limiting (in-memory demo) --------------------
class RateLimiter:
    _hits: Dict[str, List[float]] = {}

    @classmethod
    def is_rate_limited(cls, key: str, limit: int, window_minutes: int = 1) -> bool:
        now = time.time()
        window = window_minutes * 60
        hits = cls._hits.setdefault(key, [])
        # prune
        cls._hits[key] = [t for t in hits if now - t < window]
        if len(cls._hits[key]) >= limit:
            return True
        cls._hits[key].append(now)
        return False

    @classmethod
    def get_rate_limit_info(cls, key: str, limit: int, window_minutes: int = 1) -> Dict[str, Any]:
        now = time.time()
        window = window_minutes * 60
        hits = cls._hits.get(key, [])
        remaining = max(0, limit - len(hits))
        reset_time = now + window if not hits else hits[0] + window
        return {
            'limit': limit,
            'remaining': remaining,
            'reset_time': time.localtime(reset_time)
        }

# -------------------- Validation helper functions --------------------

def validate_no_sql_injection(value: str) -> str:
    if InputSanitizer.detect_sql_injection(value):
        raise ValueError("Potential SQL injection detected")
    return value

def validate_no_xss(value: str) -> str:
    if InputSanitizer.detect_xss(value):
        raise ValueError("Potential XSS detected")
    return value

def validate_safe_filename(value: str) -> str:
    return InputSanitizer.sanitize_filename(value)

__all__ = [
    'SecurityConfig', 'InputSanitizer', 'FileValidator', 'RateLimiter',
    'validate_no_sql_injection', 'validate_no_xss', 'validate_safe_filename'
]
