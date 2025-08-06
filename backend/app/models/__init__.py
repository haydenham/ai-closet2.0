"""
Database models package

This package contains all SQLAlchemy models for the application.
"""

# Import all models to ensure they are registered with SQLAlchemy
from .user import User, EmailVerificationToken, PasswordResetToken
from .style_profile import StyleProfile, QuizQuestion
from .clothing_item import ClothingItem, ClothingCategory
from .outfit_recommendation import OutfitRecommendation, RecommendationFeedback, outfit_clothing_items
from .quiz_system import (
    QuizClothingItem, 
    StyleCategory, 
    QuizResponse, 
    QuizResponseItem,
    FeatureLearningData, 
    FeatureCorrelation
)

# Import base for convenience
from app.core.database import Base

__all__ = [
    "Base",
    "User",
    "EmailVerificationToken", 
    "PasswordResetToken",
    "StyleProfile",
    "QuizQuestion",
    "ClothingItem",
    "ClothingCategory", 
    "OutfitRecommendation",
    "RecommendationFeedback",
    "outfit_clothing_items",
    "QuizClothingItem",
    "StyleCategory",
    "QuizResponse",
    "QuizResponseItem",
    "FeatureLearningData",
    "FeatureCorrelation",
]