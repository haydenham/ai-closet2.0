"""Minimal security schema stubs after removal of legacy security module.
These provide just enough structure for existing imports and tests.
Replace with real validation logic as needed.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

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
    name: str
    category: str
    color: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SecureSearchQuery(BaseModel):
    query: str
    filters: Dict[str, Any] = Field(default_factory=dict)

class SecureOutfitRequest(BaseModel):
    user_id: Optional[int] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)

class SecureRecommendationFeedback(BaseModel):
    recommendation_id: int
    feedback: str
    rating: Optional[int] = None

# Auth-specific schemas expected by auth API
class SecureUserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

class SecureUserLogin(BaseModel):
    email: str
    password: str

class SecurePasswordReset(BaseModel):
    email: str

class SecurePasswordResetConfirm(BaseModel):
    token: str
    new_password: str

__all__ = [
    'SecurityAuditLog',
    'SecureAuthRequest', 'SecureTokenRefresh', 'SecurePasswordResetRequest', 'SecurePasswordResetConfirm',
    'SecureClothingItemUpload', 'SecureSearchQuery', 'SecureOutfitRequest', 'SecureRecommendationFeedback'
]
