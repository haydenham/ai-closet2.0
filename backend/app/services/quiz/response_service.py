"""
Service for handling quiz submissions and responses
"""
import uuid
import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

from app.models.quiz import QuizResponse
from app.services.quiz.item_service import QuizItemService
from app.services.quiz.scoring_service import ScoringService

logger = logging.getLogger(__name__)


class ResponseService:
    """Service for managing quiz responses"""
    
    @staticmethod
    def submit_quiz(
        db: Session,
        user_id: uuid.UUID,
        gender: str,
        selections: Dict[str, str]  # {pants: uuid, shirt: uuid, ...}
    ) -> QuizResponse:
        """
        Submit a quiz and calculate style results
        
        Args:
            db: Database session
            user_id: UUID of the user submitting the quiz
            gender: 'female' or 'male'
            selections: Dict mapping question types to selected item UUIDs
            
        Returns:
            QuizResponse object with calculated results
            
        Raises:
            ValueError: If selections are invalid or items not found
        """
        # Validate selections structure
        errors = ScoringService.validate_selections(selections, gender)
        if errors:
            raise ValueError(f"Invalid selections: {'; '.join(errors)}")
        
        # Convert string UUIDs to UUID objects
        item_ids = [uuid.UUID(item_id) for item_id in selections.values()]
        
        # Fetch all selected items from database
        selected_items = QuizItemService.get_items_by_ids(db, item_ids)
        
        # Verify we got all items
        if len(selected_items) != 5:
            raise ValueError(
                f"Could not find all selected items. "
                f"Expected 5, found {len(selected_items)}"
            )
        
        # Verify all items match the gender
        wrong_gender = [
            item for item in selected_items
            if item.gender != gender
        ]
        if wrong_gender:
            raise ValueError(
                f"Selected items do not match gender '{gender}'"
            )
        
        # Calculate style scores
        result = ScoringService.calculate_style_scores(selected_items)
        
        # Create quiz response record
        quiz_response = QuizResponse(
            user_id=user_id,
            gender=gender,
            selected_items=selections,  # Store as dict
            primary_style=result['primary_style'],
            secondary_style=result['secondary_style'],
            style_message=result['style_message'],
            scores=result['scores']
        )
        
        db.add(quiz_response)
        db.commit()
        db.refresh(quiz_response)
        
        logger.info(
            f"Quiz submitted for user {user_id}: {result['primary_style']} "
            f"(secondary: {result['secondary_style']})"
        )
        
        return quiz_response
    
    @staticmethod
    def get_user_latest_response(
        db: Session,
        user_id: uuid.UUID
    ) -> Optional[QuizResponse]:
        """Get user's most recent quiz response"""
        return db.query(QuizResponse).filter(
            QuizResponse.user_id == user_id
        ).order_by(QuizResponse.completed_at.desc()).first()
    
    @staticmethod
    def get_user_quiz_history(
        db: Session,
        user_id: uuid.UUID,
        limit: int = 10
    ) -> List[QuizResponse]:
        """Get user's quiz response history"""
        return db.query(QuizResponse).filter(
            QuizResponse.user_id == user_id
        ).order_by(QuizResponse.completed_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_response_by_id(
        db: Session,
        response_id: uuid.UUID
    ) -> Optional[QuizResponse]:
        """Get a quiz response by ID"""
        return db.query(QuizResponse).filter(
            QuizResponse.id == response_id
        ).first()
