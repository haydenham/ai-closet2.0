"""
Pydantic schemas for simplified quiz system
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# Style Category Schemas
class StyleCategoryBase(BaseModel):
    """Base schema for style categories"""
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., pattern="^(female|male)$")
    description: Optional[str] = None
    ai_theme_prompt: Optional[str] = None


class StyleCategoryCreate(StyleCategoryBase):
    """Schema for creating style categories"""
    pass


class StyleCategory(StyleCategoryBase):
    """Schema for style category response"""
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Quiz Item Schemas
class QuizItemBase(BaseModel):
    """Base schema for quiz items"""
    name: Optional[str] = None
    image_url: str = Field(..., min_length=1, max_length=500)
    question_type: str = Field(..., pattern="^(pants|shirt|shorts|overlayer|shoes)$")
    style_category: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., pattern="^(female|male)$")
    display_order: Optional[int] = None


class QuizItemCreate(QuizItemBase):
    """Schema for creating quiz items"""
    pass


class QuizItemUpdate(BaseModel):
    """Schema for updating quiz items"""
    name: Optional[str] = None
    image_url: Optional[str] = Field(None, min_length=1, max_length=500)
    question_type: Optional[str] = Field(None, pattern="^(pants|shirt|shorts|overlayer|shoes)$")
    style_category: Optional[str] = Field(None, min_length=1, max_length=100)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class QuizItem(QuizItemBase):
    """Schema for quiz item response"""
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Quiz Questions Response
class QuizQuestionsResponse(BaseModel):
    """Schema for complete quiz questions response"""
    gender: str
    questions: Dict[str, List[QuizItem]]  # {pants: [...], shirt: [...], ...}


# Quiz Submission Schemas
class QuizSubmission(BaseModel):
    """Schema for submitting quiz answers"""
    gender: str = Field(..., pattern="^(female|male)$")
    selections: Dict[str, str] = Field(
        ...,
        description="Selected item IDs for each question type"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "gender": "female",
                "selections": {
                    "pants": "uuid-here",
                    "shirt": "uuid-here",
                    "shorts": "uuid-here",
                    "overlayer": "uuid-here",
                    "shoes": "uuid-here"
                }
            }
        }


# Quiz Response Schemas
class QuizResponseBase(BaseModel):
    """Base schema for quiz responses"""
    gender: str
    selected_items: Dict[str, str]  # {pants: uuid, shirt: uuid, ...}
    primary_style: str
    secondary_style: Optional[str] = None
    style_message: str
    scores: Dict[str, int]  # {Bohemian: 3, Classic: 1, ...}


class QuizResponse(QuizResponseBase):
    """Schema for quiz response"""
    id: uuid.UUID
    user_id: uuid.UUID
    completed_at: datetime

    class Config:
        from_attributes = True


class QuizResultResponse(BaseModel):
    """Schema for quiz result with additional context"""
    id: uuid.UUID
    primary_style: str
    secondary_style: Optional[str] = None
    style_message: str
    scores: Dict[str, int]
    completed_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "uuid-here",
                "primary_style": "Bohemian",
                "secondary_style": "Classic",
                "style_message": "Bohemian with a hint of Classic",
                "scores": {
                    "Bohemian": 3,
                    "Classic": 1,
                    "Streetwear": 1
                },
                "completed_at": "2025-11-02T22:00:00Z"
            }
        }
