"""
Pydantic schemas for quiz system
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class QuizClothingItemBase(BaseModel):
    """Base schema for quiz clothing items"""
    name: str = Field(..., min_length=1, max_length=255)
    image_url: str = Field(..., min_length=1, max_length=500)
    gender: str = Field(..., pattern="^(male|female)$")
    category: str = Field(..., min_length=1, max_length=50)
    features: List[str] = Field(default_factory=list)


class QuizClothingItemCreate(QuizClothingItemBase):
    """Schema for creating quiz clothing items"""
    pass


class QuizClothingItemUpdate(BaseModel):
    """Schema for updating quiz clothing items"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    image_url: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    features: Optional[List[str]] = None
    auto_extracted_features: Optional[List[str]] = None
    feature_confidence_scores: Optional[Dict[str, float]] = None
    is_active: Optional[bool] = None


class QuizClothingItem(QuizClothingItemBase):
    """Schema for quiz clothing item response"""
    id: uuid.UUID
    auto_extracted_features: Optional[List[str]] = None
    feature_confidence_scores: Optional[Dict[str, float]] = None
    selection_count: int
    satisfaction_score: Optional[Decimal] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StyleCategoryBase(BaseModel):
    """Base schema for style categories"""
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., pattern="^(male|female)$")
    features: List[str] = Field(default_factory=list)
    ai_theme_prompt: Optional[str] = None
    description: Optional[str] = None


class StyleCategoryCreate(StyleCategoryBase):
    """Schema for creating style categories"""
    pass


class StyleCategoryUpdate(BaseModel):
    """Schema for updating style categories"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    features: Optional[List[str]] = None
    ai_theme_prompt: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class StyleCategory(StyleCategoryBase):
    """Schema for style category response"""
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuizResponseItemCreate(BaseModel):
    """Schema for creating quiz response items"""
    item_id: uuid.UUID
    category: str = Field(..., min_length=1, max_length=50)
    weight: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)


class QuizResponseCreate(BaseModel):
    """Schema for creating quiz responses"""
    gender: str = Field(..., pattern="^(male|female)$")
    selected_items: Dict[str, str] = Field(..., min_length=1)  # Accept strings, convert internally
    weights: Optional[Dict[str, float]] = None

    @field_validator('selected_items')
    @classmethod
    def validate_selected_items(cls, v):
        """Validate selected items structure and convert string UUIDs"""
        required_categories = {'top', 'bottom', 'shoes', 'layering', 'accessory', 'complete_outfit'}
        provided_categories = set(v.keys())
        
        if not required_categories.issubset(provided_categories):
            missing = required_categories - provided_categories
            raise ValueError(f"Missing required categories: {missing}")
        
        # Validate that all values are valid UUID strings
        for category, item_id in v.items():
            try:
                uuid.UUID(item_id)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid UUID format for {category}: {item_id}")
        
        return v


class QuizResponseFeedback(BaseModel):
    """Schema for quiz response feedback"""
    satisfaction_rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = Field(None, max_length=1000)


class QuizResponse(BaseModel):
    """Schema for quiz response"""
    id: uuid.UUID
    user_id: uuid.UUID
    selected_item_ids: List[str]
    calculated_scores: Dict[str, float]
    assigned_category: str
    assigned_category_id: Optional[uuid.UUID] = None
    confidence_score: Optional[Decimal] = None
    user_satisfaction_rating: Optional[int] = None
    user_feedback_text: Optional[str] = None
    completed_at: datetime

    class Config:
        from_attributes = True


class QuizResponseWithItems(QuizResponse):
    """Schema for quiz response with selected items"""
    selected_items: List[QuizClothingItem] = []
    assigned_category_obj: Optional[StyleCategory] = None


class EnhancedQuizResponse(QuizResponse):
    """Schema for enhanced quiz response with hybrid style detection"""
    selected_items: List[QuizClothingItem] = []
    assigned_category_obj: Optional[StyleCategory] = None
    is_hybrid: bool = False
    hybrid_styles: List[str] = []
    primary_score: Optional[float] = None
    style_message: Optional[str] = None  # User-friendly message about their style


class FeatureLearningDataCreate(BaseModel):
    """Schema for creating feature learning data"""
    feature_name: str = Field(..., min_length=1, max_length=100)
    item_id: uuid.UUID
    source: str = Field(..., pattern="^(manual|cv_auto|user_suggested|algorithm_discovered)$")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class FeatureLearningData(BaseModel):
    """Schema for feature learning data"""
    id: uuid.UUID
    feature_name: str
    item_id: uuid.UUID
    source: str
    confidence_score: Optional[Decimal] = None
    validation_count: int
    rejection_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class FeatureValidation(BaseModel):
    """Schema for feature validation"""
    is_valid: bool


class FeatureCorrelation(BaseModel):
    """Schema for feature correlation"""
    id: uuid.UUID
    feature_a: str
    feature_b: str
    correlation_strength: Optional[Decimal] = None
    co_occurrence_count: int
    total_occurrences: int
    updated_at: datetime

    class Config:
        from_attributes = True


class QuizClothingItemsResponse(BaseModel):
    """Schema for quiz clothing items response by category"""
    category: str
    items: List[QuizClothingItem]


class QuizQuestionsResponse(BaseModel):
    """Schema for complete quiz questions response"""
    gender: str
    questions: Dict[str, QuizClothingItemsResponse]


class StyleScores(BaseModel):
    """Schema for style calculation scores"""
    scores: Dict[str, float]
    best_match: str
    confidence: float


class QuizAnalytics(BaseModel):
    """Schema for quiz analytics"""
    total_responses: int
    category_distribution: Dict[str, int]
    average_confidence: float
    satisfaction_ratings: Dict[int, int]
    most_selected_items: List[Dict[str, Any]]
    feature_popularity: Dict[str, int]


class AdminQuizItemCreate(QuizClothingItemCreate):
    """Schema for admin creating quiz items with additional fields"""
    auto_extracted_features: Optional[List[str]] = None
    feature_confidence_scores: Optional[Dict[str, float]] = None


class BulkItemImport(BaseModel):
    """Schema for bulk importing quiz items"""
    items: List[AdminQuizItemCreate] = Field(..., min_length=1, max_length=100)


class FeatureSuggestion(BaseModel):
    """Schema for feature suggestions"""
    feature_name: str = Field(..., min_length=1, max_length=100)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    source: str
    reasoning: Optional[str] = None


class ItemFeatureSuggestions(BaseModel):
    """Schema for item feature suggestions"""
    item_id: uuid.UUID
    suggested_features: List[FeatureSuggestion]


class FeatureInsights(BaseModel):
    """Schema for feature learning insights"""
    pending_validations: int
    validated_features: int
    rejected_features: int
    top_correlations: List[FeatureCorrelation]
    accuracy_by_source: Dict[str, float]
    recent_discoveries: List[FeatureLearningData]


class StyleAssignmentFeedbackCreate(BaseModel):
    """Schema for creating style assignment feedback"""
    accuracy_rating: int = Field(..., ge=1, le=5)
    preferred_style: Optional[str] = Field(None, max_length=100)
    feedback_type: str = Field(..., pattern="^(too_broad|too_narrow|completely_wrong|mostly_right|perfect)$")
    feedback_text: Optional[str] = Field(None, max_length=1000)
    feature_feedback: Optional[Dict[str, Any]] = None


class StyleAssignmentFeedback(BaseModel):
    """Schema for style assignment feedback"""
    id: uuid.UUID
    quiz_response_id: uuid.UUID
    user_id: uuid.UUID
    accuracy_rating: int
    preferred_style: Optional[str] = None
    feedback_type: str
    feedback_text: Optional[str] = None
    feature_feedback: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlgorithmImprovementMetrics(BaseModel):
    """Schema for algorithm improvement metrics"""
    total_feedback_count: int
    average_accuracy_rating: float
    feedback_distribution: Dict[str, int]
    most_common_issues: List[Dict[str, Any]]
    improvement_suggestions: List[str]
    confidence_vs_accuracy: Dict[str, float]