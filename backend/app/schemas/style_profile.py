"""
Pydantic schemas for StyleProfile model validation
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator


class StyleProfileBase(BaseModel):
    """Base style profile schema"""
    assigned_model: str = Field(..., min_length=1, max_length=100)
    style_preferences: List[str] = Field(default_factory=list)
    fashion_goals: Optional[List[str]] = Field(default_factory=list)
    preferred_colors: Optional[List[str]] = Field(default_factory=list)
    body_type: Optional[str] = Field(None, max_length=50)
    lifestyle: Optional[str] = Field(None, max_length=100)
    budget_range: Optional[str] = Field(None, max_length=50)


class StyleProfileCreate(StyleProfileBase):
    """Schema for style profile creation"""
    quiz_responses: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('quiz_responses')
    def validate_quiz_responses(cls, v):
        """Validate quiz responses structure"""
        if not isinstance(v, dict):
            raise ValueError('Quiz responses must be a dictionary')
        return v


class StyleProfileUpdate(BaseModel):
    """Schema for style profile updates"""
    quiz_responses: Optional[Dict[str, Any]] = None
    assigned_model: Optional[str] = Field(None, min_length=1, max_length=100)
    style_preferences: Optional[List[str]] = None
    fashion_goals: Optional[List[str]] = None
    preferred_colors: Optional[List[str]] = None
    body_type: Optional[str] = Field(None, max_length=50)
    lifestyle: Optional[str] = Field(None, max_length=100)
    budget_range: Optional[str] = Field(None, max_length=50)


class StyleProfileResponse(StyleProfileBase):
    """Schema for style profile response"""
    id: uuid.UUID
    user_id: uuid.UUID
    quiz_responses: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuizQuestionBase(BaseModel):
    """Base quiz question schema"""
    question_key: str = Field(..., min_length=1, max_length=100)
    question_text: str = Field(..., min_length=1)
    question_type: str = Field(default="multiple_choice", max_length=50)
    category: str = Field(..., min_length=1, max_length=50)
    order_index: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)


class QuizQuestionCreate(QuizQuestionBase):
    """Schema for quiz question creation"""
    options: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    
    @validator('question_type')
    def validate_question_type(cls, v):
        """Validate question type"""
        valid_types = ['multiple_choice', 'single_choice', 'scale', 'text']
        if v not in valid_types:
            raise ValueError(f'Question type must be one of: {valid_types}')
        return v


class QuizQuestionUpdate(BaseModel):
    """Schema for quiz question updates"""
    question_text: Optional[str] = Field(None, min_length=1)
    question_type: Optional[str] = Field(None, max_length=50)
    options: Optional[List[Dict[str, Any]]] = None
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    order_index: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class QuizQuestionResponse(QuizQuestionBase):
    """Schema for quiz question response"""
    id: uuid.UUID
    options: Optional[List[Dict[str, Any]]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuizSubmission(BaseModel):
    """Schema for quiz submission"""
    responses: Dict[str, Any] = Field(..., min_length=1)
    
    @validator('responses')
    def validate_responses(cls, v):
        """Validate quiz responses"""
        if not isinstance(v, dict):
            raise ValueError('Responses must be a dictionary')
        if not v:
            raise ValueError('At least one response is required')
        return v


class QuizResult(BaseModel):
    """Schema for quiz result"""
    assigned_model: str
    style_preferences: List[str]
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    recommendations: Optional[List[str]] = Field(default_factory=list)