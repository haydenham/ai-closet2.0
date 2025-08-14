"""
Security-enhanced Pydantic schemas with comprehensive validation
"""
import uuid
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, EmailStr

from app.core.security import (
    SecurityValidator, 
    validate_no_sql_injection, 
    validate_no_xss,
    validate_safe_filename,
    validate_string_length,
    InputSanitizer
)


class SecureUserCreate(SecurityValidator):
    """Security-enhanced user creation schema"""
    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields"""
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError("Name contains invalid characters")
        
        return v.strip()
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength with comprehensive checks"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if len(v) > 128:
            raise ValueError('Password too long (max 128 characters)')
        
        # Check for common patterns
        if re.search(r'(.)\1{3,}', v):  # 4+ repeated characters
            raise ValueError('Password cannot contain repeated characters')
        
        if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', v.lower()):
            raise ValueError('Password cannot contain sequential characters')
        
        # Strength requirements
        has_upper = bool(re.search(r'[A-Z]', v))
        has_lower = bool(re.search(r'[a-z]', v))
        has_digit = bool(re.search(r'\d', v))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', v))
        
        strength_score = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength_score < 3:
            raise ValueError('Password must contain at least 3 of: uppercase, lowercase, digit, special character')
        
        # Check against common passwords
        common_passwords = {
            'password', '12345678', 'qwerty', 'abc123', 'password123',
            'admin', 'letmein', 'welcome', 'monkey', '1234567890'
        }
        
        if v.lower() in common_passwords:
            raise ValueError('Password is too common')
        
        return v


class SecureUserUpdate(SecurityValidator):
    """Security-enhanced user update schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields"""
        if v is None:
            return v
        
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError("Name contains invalid characters")
        
        return v.strip()


class SecureUserLogin(SecurityValidator):
    """Security-enhanced login schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=128, description="Password")
    
    @validator('password')
    def validate_password_format(cls, v):
        """Basic password validation for login"""
        # Don't reveal password requirements on login
        if len(v) > 128:
            raise ValueError('Invalid password format')
        return v


class SecurePasswordReset(SecurityValidator):
    """Security-enhanced password reset schema"""
    email: EmailStr = Field(..., description="User email address")


class SecurePasswordResetConfirm(SecurityValidator):
    """Security-enhanced password reset confirmation schema"""
    token: str = Field(..., min_length=1, max_length=500, description="Reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('token')
    def validate_token(cls, v):
        """Validate reset token format"""
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        # Token should be alphanumeric with possible hyphens/underscores
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Invalid token format')
        
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        # Reuse password validation from SecureUserCreate
        return SecureUserCreate.validate_password_strength(v)


class SecureClothingItemUpload(SecurityValidator):
    """Security-enhanced clothing item upload schema"""
    category: str = Field(..., min_length=1, max_length=100, description="Clothing category")
    category_id: Optional[str] = Field(None, description="Category UUID")
    color: Optional[str] = Field(None, max_length=50, description="Item color")
    brand: Optional[str] = Field(None, max_length=100, description="Brand name")
    size: Optional[str] = Field(None, max_length=20, description="Size")
    description: Optional[str] = Field(None, max_length=1000, description="Item description")
    tags: Optional[List[str]] = Field(default_factory=list, description="Item tags")
    
    @validator('category')
    def validate_category(cls, v):
        """Validate category field"""
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        # Only allow alphanumeric, spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Category contains invalid characters')
        
        return v.strip()
    
    @validator('category_id')
    def validate_category_id(cls, v):
        """Validate category ID as UUID"""
        if v is None:
            return v
        
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid category ID format')
    
    @validator('color', 'brand', 'size')
    def validate_text_fields(cls, v):
        """Validate text fields"""
        if v is None:
            return v
        
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        # Allow alphanumeric, spaces, common punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-_.,()&/]+$', v):
            raise ValueError('Field contains invalid characters')
        
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        """Validate description field"""
        if v is None:
            return v
        
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        # More permissive for descriptions but still safe
        v = InputSanitizer.sanitize_string(v, 1000)
        
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags list"""
        if not v:
            return []
        
        if len(v) > 50:  # Reasonable limit on number of tags
            raise ValueError('Too many tags (max 50)')
        
        validated_tags = []
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError('All tags must be strings')
            
            tag = validate_no_sql_injection(tag)
            tag = validate_no_xss(tag)
            
            # Tags should be simple alphanumeric with limited punctuation
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', tag):
                raise ValueError(f'Tag "{tag}" contains invalid characters')
            
            tag = tag.strip()
            if len(tag) > 50:
                raise ValueError(f'Tag "{tag}" too long (max 50 characters)')
            
            if tag and tag not in validated_tags:  # Remove duplicates
                validated_tags.append(tag)
        
        return validated_tags


class SecureOutfitRequest(SecurityValidator):
    """Security-enhanced outfit recommendation request schema"""
    gender: str = Field(..., description="User's gender")
    style: str = Field(..., description="Style preference")
    weather: str = Field(..., description="Weather condition")
    occasion: str = Field(..., description="Occasion type")
    user_request: str = Field(..., min_length=1, max_length=500, description="User's specific request")
    
    @validator('gender')
    def validate_gender(cls, v):
        """Validate gender field"""
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        valid_genders = {'men', 'women', 'unisex', 'male', 'female', 'non-binary'}
        if v.lower() not in valid_genders:
            raise ValueError('Invalid gender value')
        
        return v.lower()
    
    @validator('style', 'weather', 'occasion')
    def validate_enum_fields(cls, v):
        """Validate enumeration-like fields"""
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        # Only allow alphanumeric, spaces, hyphens
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Field contains invalid characters')
        
        return v.lower().strip()
    
    @validator('user_request')
    def validate_user_request(cls, v):
        """Validate user request text"""
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        # Sanitize but allow more natural language
        v = InputSanitizer.sanitize_string(v, 500)
        
        if not v.strip():
            raise ValueError('Request cannot be empty')
        
        return v.strip()


class SecureRecommendationFeedback(SecurityValidator):
    """Security-enhanced recommendation feedback schema"""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_type: str = Field(default="general", max_length=50, description="Type of feedback")
    comments: Optional[str] = Field(None, max_length=1000, description="Feedback comments")
    style_accuracy: Optional[int] = Field(None, ge=1, le=5, description="Style accuracy rating")
    item_matching: Optional[int] = Field(None, ge=1, le=5, description="Item matching rating")
    occasion_appropriateness: Optional[int] = Field(None, ge=1, le=5, description="Occasion appropriateness rating")
    feedback_tags: Optional[List[str]] = Field(default_factory=list, description="Feedback tags")
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        """Validate feedback type"""
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        valid_types = {
            'general', 'item_specific', 'style_mismatch', 
            'occasion_mismatch', 'color_preference', 'fit_issue'
        }
        
        if v not in valid_types:
            raise ValueError(f'Invalid feedback type. Must be one of: {valid_types}')
        
        return v
    
    @validator('comments')
    def validate_comments(cls, v):
        """Validate feedback comments"""
        if v is None:
            return v
        
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        v = InputSanitizer.sanitize_string(v, 1000)
        
        return v.strip() if v else None
    
    @validator('feedback_tags')
    def validate_feedback_tags(cls, v):
        """Validate feedback tags"""
        if not v:
            return []
        
        if len(v) > 20:
            raise ValueError('Too many feedback tags (max 20)')
        
        validated_tags = []
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError('All feedback tags must be strings')
            
            tag = validate_no_sql_injection(tag)
            tag = validate_no_xss(tag)
            
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', tag):
                raise ValueError(f'Feedback tag "{tag}" contains invalid characters')
            
            tag = tag.strip()
            if len(tag) > 30:
                raise ValueError(f'Feedback tag "{tag}" too long (max 30 characters)')
            
            if tag and tag not in validated_tags:
                validated_tags.append(tag)
        
        return validated_tags


class SecureSearchQuery(SecurityValidator):
    """Security-enhanced search query schema"""
    query: Optional[str] = Field(None, max_length=200, description="Search query")
    category: Optional[str] = Field(None, max_length=100, description="Category filter")
    color: Optional[str] = Field(None, max_length=50, description="Color filter")
    brand: Optional[str] = Field(None, max_length=100, description="Brand filter")
    size: Optional[str] = Field(None, max_length=20, description="Size filter")
    tags: Optional[List[str]] = Field(None, description="Tag filters")
    limit: int = Field(default=20, ge=1, le=100, description="Results limit")
    offset: int = Field(default=0, ge=0, description="Results offset")
    
    @validator('query', 'category', 'color', 'brand', 'size')
    def validate_search_fields(cls, v):
        """Validate search fields"""
        if v is None:
            return v
        
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        # Allow alphanumeric, spaces, common punctuation for search
        if not re.match(r'^[a-zA-Z0-9\s\-_.,()&/]+$', v):
            raise ValueError('Search field contains invalid characters')
        
        return v.strip()
    
    @validator('tags')
    def validate_search_tags(cls, v):
        """Validate search tags"""
        if not v:
            return []
        
        if len(v) > 10:
            raise ValueError('Too many search tags (max 10)')
        
        validated_tags = []
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError('All search tags must be strings')
            
            tag = validate_no_sql_injection(tag)
            tag = validate_no_xss(tag)
            
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', tag):
                raise ValueError(f'Search tag "{tag}" contains invalid characters')
            
            tag = tag.strip()
            if len(tag) > 50:
                raise ValueError(f'Search tag "{tag}" too long (max 50 characters)')
            
            if tag and tag not in validated_tags:
                validated_tags.append(tag)
        
        return validated_tags


class SecureFileUpload(SecurityValidator):
    """Security-enhanced file upload validation schema"""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File content type")
    file_size: int = Field(..., ge=1, description="File size in bytes")
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate and sanitize filename"""
        return validate_safe_filename(v)
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate content type"""
        allowed_types = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
            'image/webp', 'image/bmp', 'image/tiff'
        }
        
        if v not in allowed_types:
            raise ValueError(f'Invalid content type. Allowed: {allowed_types}')
        
        return v
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size"""
        max_size = 10 * 1024 * 1024  # 10MB
        if v > max_size:
            raise ValueError(f'File too large (max {max_size // 1024 // 1024}MB)')
        
        return v


class SecurityAuditLog(BaseModel):
    """Schema for security audit logging"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = Field(..., description="Type of security event")
    severity: str = Field(..., description="Event severity level")
    user_id: Optional[str] = Field(None, description="User ID if applicable")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    endpoint: Optional[str] = Field(None, description="API endpoint accessed")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RateLimitInfo(BaseModel):
    """Schema for rate limit information"""
    limit: int = Field(..., description="Rate limit maximum")
    remaining: int = Field(..., description="Remaining requests")
    reset_time: datetime = Field(..., description="When limit resets")
    window_minutes: int = Field(..., description="Time window in minutes")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }