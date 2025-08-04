"""
Pydantic schemas for OutfitRecommendation model validation
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator


class OutfitRecommendationBase(BaseModel):
    """Base outfit recommendation schema"""
    prompt: str = Field(..., min_length=1)
    occasion: Optional[str] = Field(None, max_length=100)
    weather: Optional[str] = Field(None, max_length=50)
    season: Optional[str] = Field(None, max_length=20)


class OutfitRecommendationCreate(OutfitRecommendationBase):
    """Schema for outfit recommendation creation"""
    ai_model_used: str = Field(..., min_length=1, max_length=100)
    ai_response: str = Field(..., min_length=1)
    outfit_components: Optional[Dict[str, Any]] = Field(default_factory=dict)
    processing_time_ms: Optional[int] = Field(None, ge=0)
    similarity_scores: Optional[Dict[str, float]] = Field(default_factory=dict)
    
    @validator('season')
    def validate_season(cls, v):
        """Validate season value"""
        if v is not None:
            valid_seasons = ['spring', 'summer', 'fall', 'winter']
            if v.lower() not in valid_seasons:
                raise ValueError(f'Season must be one of: {valid_seasons}')
        return v.lower() if v else v


class OutfitRecommendationUpdate(BaseModel):
    """Schema for outfit recommendation updates"""
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    feedback_score: Optional[int] = Field(None, ge=1, le=5)
    feedback_comments: Optional[str] = None
    
    @validator('feedback_score')
    def validate_feedback_score(cls, v):
        """Validate feedback score range"""
        if v is not None and not (1 <= v <= 5):
            raise ValueError('Feedback score must be between 1 and 5')
        return v


class OutfitRecommendationResponse(OutfitRecommendationBase):
    """Schema for outfit recommendation response"""
    id: uuid.UUID
    user_id: uuid.UUID
    ai_response: str
    outfit_components: Optional[Dict[str, Any]]
    ai_model_used: str
    feedback_score: Optional[int]
    feedback_comments: Optional[str]
    is_favorite: bool
    is_archived: bool
    processing_time_ms: Optional[int]
    similarity_scores: Optional[Dict[str, float]]
    created_at: datetime
    updated_at: datetime
    
    # Related data
    recommended_items: List["ClothingItemResponse"] = Field(default_factory=list)
    item_count: int = 0
    categories_covered: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True
    
    @property
    def has_feedback(self) -> bool:
        """Check if recommendation has user feedback"""
        return self.feedback_score is not None


class RecommendationFeedbackBase(BaseModel):
    """Base recommendation feedback schema"""
    rating: int = Field(..., ge=1, le=5)
    feedback_type: str = Field(default="general", max_length=50)
    comments: Optional[str] = None
    style_accuracy: Optional[int] = Field(None, ge=1, le=5)
    item_matching: Optional[int] = Field(None, ge=1, le=5)
    occasion_appropriateness: Optional[int] = Field(None, ge=1, le=5)
    feedback_tags: Optional[List[str]] = Field(default_factory=list)


class RecommendationFeedbackCreate(RecommendationFeedbackBase):
    """Schema for recommendation feedback creation"""
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        """Validate feedback type"""
        valid_types = ['general', 'item_specific', 'style_mismatch', 'occasion_mismatch', 'color_preference']
        if v not in valid_types:
            raise ValueError(f'Feedback type must be one of: {valid_types}')
        return v
    
    @validator('feedback_tags')
    def validate_feedback_tags(cls, v):
        """Validate feedback tags"""
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError('Feedback tags must be a list')
        return list(set(tag.strip() for tag in v if tag and tag.strip()))


class RecommendationFeedbackUpdate(BaseModel):
    """Schema for recommendation feedback updates"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_type: Optional[str] = Field(None, max_length=50)
    comments: Optional[str] = None
    style_accuracy: Optional[int] = Field(None, ge=1, le=5)
    item_matching: Optional[int] = Field(None, ge=1, le=5)
    occasion_appropriateness: Optional[int] = Field(None, ge=1, le=5)
    feedback_tags: Optional[List[str]] = None


class RecommendationFeedbackResponse(RecommendationFeedbackBase):
    """Schema for recommendation feedback response"""
    id: uuid.UUID
    recommendation_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class OutfitRecommendationRequest(BaseModel):
    """Schema for outfit recommendation request"""
    prompt: str = Field(..., min_length=1, max_length=1000)
    occasion: Optional[str] = Field(None, max_length=100)
    weather: Optional[str] = Field(None, max_length=50)
    season: Optional[str] = Field(None, max_length=20)
    style_preferences: Optional[List[str]] = Field(default_factory=list)
    exclude_items: Optional[List[uuid.UUID]] = Field(default_factory=list)
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Validate prompt content"""
        if not v.strip():
            raise ValueError('Prompt cannot be empty or whitespace only')
        return v.strip()
    
    @validator('season')
    def validate_season(cls, v):
        """Validate season value"""
        if v is not None:
            valid_seasons = ['spring', 'summer', 'fall', 'winter']
            if v.lower() not in valid_seasons:
                raise ValueError(f'Season must be one of: {valid_seasons}')
        return v.lower() if v else v


class OutfitRecommendationSearch(BaseModel):
    """Schema for outfit recommendation search"""
    occasion: Optional[str] = None
    weather: Optional[str] = None
    season: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    has_feedback: Optional[bool] = None
    min_rating: Optional[int] = Field(None, ge=1, le=5)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class RecommendationStats(BaseModel):
    """Schema for recommendation statistics"""
    total_recommendations: int
    favorite_count: int
    archived_count: int
    average_rating: Optional[float]
    recommendations_by_occasion: Dict[str, int]
    recommendations_by_season: Dict[str, int]
    most_used_models: Dict[str, int]
    recent_recommendations: List[OutfitRecommendationResponse]
    
    class Config:
        from_attributes = True


# Import ClothingItemResponse for forward reference
from .clothing_item import ClothingItemResponse

# Update forward references
OutfitRecommendationResponse.model_rebuild()