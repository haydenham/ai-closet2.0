"""
Pydantic schemas package

This package contains all Pydantic schemas for request/response validation.
"""

# Import all schemas
from .user import (
    UserBase, UserCreate, UserUpdate, UserResponse, UserLogin,
    PasswordReset, PasswordResetConfirm, EmailVerification,
    TokenResponse, RefreshTokenRequest
)

from .style_profile import (
    StyleProfileBase, StyleProfileCreate, StyleProfileUpdate, StyleProfileResponse,
    QuizQuestionBase, QuizQuestionCreate, QuizQuestionUpdate, QuizQuestionResponse,
    QuizSubmission, QuizResult
)

from .clothing_item import (
    ClothingCategoryBase, ClothingCategoryCreate, ClothingCategoryUpdate, ClothingCategoryResponse,
    ClothingItemBase, ClothingItemCreate, ClothingItemUpdate, ClothingItemResponse,
    ClothingItemUpload, ClothingItemSearch, ClothingItemStats, EmbeddingResponse
)

from .outfit_recommendation import (
    OutfitRecommendationBase, OutfitRecommendationCreate, OutfitRecommendationUpdate, OutfitRecommendationResponse,
    RecommendationFeedbackBase, RecommendationFeedbackCreate, RecommendationFeedbackUpdate, RecommendationFeedbackResponse,
    OutfitRecommendationRequest, OutfitRecommendationSearch, RecommendationStats
)

__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "PasswordReset", "PasswordResetConfirm", "EmailVerification",
    "TokenResponse", "RefreshTokenRequest",
    
    # Style profile schemas
    "StyleProfileBase", "StyleProfileCreate", "StyleProfileUpdate", "StyleProfileResponse",
    "QuizQuestionBase", "QuizQuestionCreate", "QuizQuestionUpdate", "QuizQuestionResponse",
    "QuizSubmission", "QuizResult",
    
    # Clothing item schemas
    "ClothingCategoryBase", "ClothingCategoryCreate", "ClothingCategoryUpdate", "ClothingCategoryResponse",
    "ClothingItemBase", "ClothingItemCreate", "ClothingItemUpdate", "ClothingItemResponse",
    "ClothingItemUpload", "ClothingItemSearch", "ClothingItemStats", "EmbeddingResponse",
    
    # Outfit recommendation schemas
    "OutfitRecommendationBase", "OutfitRecommendationCreate", "OutfitRecommendationUpdate", "OutfitRecommendationResponse",
    "RecommendationFeedbackBase", "RecommendationFeedbackCreate", "RecommendationFeedbackUpdate", "RecommendationFeedbackResponse",
    "OutfitRecommendationRequest", "OutfitRecommendationSearch", "RecommendationStats",
]