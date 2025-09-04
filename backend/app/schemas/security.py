"""Security-related Pydantic schemas with lightweight validation.

These are NOT a full security framework – just enough logic to satisfy
existing tests for input validation (name/password/email strength etc.).
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr, field_validator
import re

_NAME_REGEX = re.compile(r"^[A-Za-z .,'-]{1,50}$")
_COMMON_PASSWORDS = {"password", "password1", "password123", "12345678", "qwerty", "letmein"}

def _validate_name(value: str) -> str:
    if not _NAME_REGEX.match(value):
        raise ValueError("Name contains invalid characters")
    return value

def _validate_password(pw: str) -> str:
    if len(pw) < 8:
        raise ValueError("Password must be at least 8 characters")
    if pw.lower() in _COMMON_PASSWORDS:
        raise ValueError("Password is too common")
    if not re.search(r"[A-Z]", pw) or not re.search(r"[a-z]", pw) or not re.search(r"[0-9]", pw):
        raise ValueError("Password must include upper, lower, and digit")
    return pw

class SecurityAuditLog(BaseModel):
    event_type: str
    severity: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

class SecureAuthRequest(BaseModel):
    username: str
    password: str

class SecureTokenRefresh(BaseModel):
    refresh_token: str

class SecurePasswordResetRequest(BaseModel):
    email: str

class SecurePasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class SecureClothingItemUpload(BaseModel):
    category: str
    category_id: Optional[str] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    size: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class SecureSearchQuery(BaseModel):
    query: str
    filters: Dict[str, Any] = Field(default_factory=dict)

class SecureOutfitRequest(BaseModel):
    occasion: str
    user_request: str  # The user's specific request/prompt
    color_preference: Optional[str] = None
    weather: str

class SecureRecommendationFeedback(BaseModel):
    recommendation_id: int
    feedback: str
    rating: Optional[int] = None

# Auth-specific schemas expected by auth API
class SecureUserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

    _validate_first = field_validator("first_name")(lambda cls, v: _validate_name(v))  # type: ignore[arg-type]
    _validate_last = field_validator("last_name")(lambda cls, v: _validate_name(v))  # type: ignore[arg-type]
    _validate_pw = field_validator("password")(lambda cls, v: _validate_password(v))  # type: ignore[arg-type]

class SecureUserLogin(BaseModel):
    email: EmailStr
    password: str

class SecurePasswordReset(BaseModel):
    email: EmailStr

class SecurePasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    _validate_pw = field_validator("new_password")(lambda cls, v: _validate_password(v))  # type: ignore[arg-type]

__all__ = [
    'SecurityAuditLog',
    'SecureAuthRequest', 'SecureTokenRefresh', 'SecurePasswordResetRequest', 'SecurePasswordResetConfirm',
    'SecureClothingItemUpload', 'SecureSearchQuery', 'SecureOutfitRequest', 'SecureRecommendationFeedback',
    'SecureUserCreate', 'SecureUserLogin', 'SecurePasswordReset', 'SecurePasswordResetConfirm'
]
