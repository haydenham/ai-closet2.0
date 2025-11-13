"""
Service for creating a StyleProfile interface compatible with outfit recommendations.
This bridges the new quiz system with existing outfit recommendation logic.
"""
import uuid
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.quiz import QuizResponse, StyleCategory

logger = logging.getLogger(__name__)


class StyleProfile:
    """
    Compatibility layer that represents a user's style profile based on quiz responses.
    This replaces the old StyleProfile model with data from QuizResponse.
    """
    
    def __init__(self, quiz_response: QuizResponse):
        self.id = quiz_response.id
        self.user_id = quiz_response.user_id
        self.created_at = quiz_response.created_at
        self.updated_at = quiz_response.updated_at
        
        # Build quiz_responses dict in the format expected by outfit_recommendations
        self.quiz_responses = {
            "gender": quiz_response.gender,
            "assigned_category": quiz_response.primary_category.name if quiz_response.primary_category else None,
            "secondary_category": quiz_response.secondary_category.name if quiz_response.secondary_category else None,
            "selected_items": [str(item_id) for item_id in quiz_response.selected_item_ids],
            "submitted_at": quiz_response.created_at.isoformat() if quiz_response.created_at else None
        }


class StyleProfileService:
    """
    Service for retrieving user style profiles based on quiz responses.
    Compatible with outfit recommendation system.
    """
    
    @staticmethod
    def get_by_user_id(db: Session, user_id: uuid.UUID) -> Optional[StyleProfile]:
        """
        Get the most recent quiz response for a user and convert to StyleProfile format.
        
        Args:
            db: Database session
            user_id: User's UUID
            
        Returns:
            StyleProfile object or None if no quiz response found
        """
        # Get the most recent quiz response for this user
        quiz_response = (
            db.query(QuizResponse)
            .filter(QuizResponse.user_id == user_id)
            .order_by(QuizResponse.created_at.desc())
            .first()
        )
        
        if not quiz_response:
            logger.info(f"No quiz response found for user {user_id}")
            return None
        
        # Check if the quiz response has required data
        if not quiz_response.primary_category:
            logger.warning(f"Quiz response {quiz_response.id} missing primary_category")
            return None
        
        logger.info(
            f"Found style profile for user {user_id}: "
            f"{quiz_response.primary_category.name} ({quiz_response.gender})"
        )
        
        return StyleProfile(quiz_response)
    
    @staticmethod
    def get_by_id(db: Session, profile_id: uuid.UUID) -> Optional[StyleProfile]:
        """
        Get a specific quiz response by ID and convert to StyleProfile format.
        
        Args:
            db: Database session
            profile_id: Quiz response UUID
            
        Returns:
            StyleProfile object or None if not found
        """
        quiz_response = (
            db.query(QuizResponse)
            .filter(QuizResponse.id == profile_id)
            .first()
        )
        
        if not quiz_response or not quiz_response.primary_category:
            return None
        
        return StyleProfile(quiz_response)
    
    @staticmethod
    def has_completed_quiz(db: Session, user_id: uuid.UUID) -> bool:
        """
        Check if a user has completed the style quiz.
        
        Args:
            db: Database session
            user_id: User's UUID
            
        Returns:
            True if user has completed quiz, False otherwise
        """
        count = (
            db.query(QuizResponse)
            .filter(QuizResponse.user_id == user_id)
            .count()
        )
        return count > 0
    
    @staticmethod
    def get_style_summary(db: Session, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get a summary of user's style preferences.
        
        Args:
            db: Database session
            user_id: User's UUID
            
        Returns:
            Dictionary with style summary or None
        """
        profile = StyleProfileService.get_by_user_id(db, user_id)
        
        if not profile:
            return None
        
        return {
            "user_id": str(user_id),
            "primary_style": profile.quiz_responses.get("assigned_category"),
            "secondary_style": profile.quiz_responses.get("secondary_category"),
            "gender": profile.quiz_responses.get("gender"),
            "last_updated": profile.updated_at.isoformat() if profile.updated_at else None
        }
