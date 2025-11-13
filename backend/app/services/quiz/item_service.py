"""
Service for managing quiz items (clothing images)
"""
import uuid
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.quiz import QuizItem

logger = logging.getLogger(__name__)


class QuizItemService:
    """Service for CRUD operations on quiz items"""
    
    @staticmethod
    def get_quiz_questions(db: Session, gender: str) -> Dict[str, List[QuizItem]]:
        """
        Get all quiz questions organized by question type
        
        Args:
            db: Database session
            gender: 'female' or 'male'
            
        Returns:
            Dict with question types as keys and lists of QuizItems as values
            {
                'pants': [QuizItem, ...],
                'shirt': [QuizItem, ...],
                'shorts': [QuizItem, ...],
                'overlayer': [QuizItem, ...],
                'shoes': [QuizItem, ...]
            }
        """
        question_types = ['pants', 'shirt', 'shorts', 'overlayer', 'shoes']
        questions = {}
        
        for question_type in question_types:
            items = db.query(QuizItem).filter(
                and_(
                    QuizItem.gender == gender,
                    QuizItem.question_type == question_type,
                    QuizItem.is_active == True
                )
            ).order_by(QuizItem.display_order, QuizItem.created_at).all()
            
            questions[question_type] = items
            
            if len(items) != 10:
                logger.warning(
                    f"Expected 10 items for {gender} {question_type}, found {len(items)}"
                )
        
        return questions
    
    @staticmethod
    def get_item_by_id(db: Session, item_id: uuid.UUID) -> Optional[QuizItem]:
        """Get a quiz item by ID"""
        return db.query(QuizItem).filter(QuizItem.id == item_id).first()
    
    @staticmethod
    def get_items_by_ids(db: Session, item_ids: List[uuid.UUID]) -> List[QuizItem]:
        """Get multiple quiz items by their IDs"""
        return db.query(QuizItem).filter(QuizItem.id.in_(item_ids)).all()
    
    @staticmethod
    def create_item(
        db: Session,
        name: Optional[str],
        image_url: str,
        question_type: str,
        style_category: str,
        gender: str,
        display_order: Optional[int] = None
    ) -> QuizItem:
        """Create a new quiz item"""
        item = QuizItem(
            name=name,
            image_url=image_url,
            question_type=question_type,
            style_category=style_category,
            gender=gender,
            display_order=display_order
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    
    @staticmethod
    def update_item(
        db: Session,
        item_id: uuid.UUID,
        **updates
    ) -> Optional[QuizItem]:
        """Update a quiz item"""
        item = db.query(QuizItem).filter(QuizItem.id == item_id).first()
        
        if not item:
            return None
        
        for key, value in updates.items():
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)
        
        db.commit()
        db.refresh(item)
        return item
    
    @staticmethod
    def delete_item(db: Session, item_id: uuid.UUID) -> bool:
        """Soft delete a quiz item by setting is_active to False"""
        item = db.query(QuizItem).filter(QuizItem.id == item_id).first()
        
        if not item:
            return False
        
        item.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def get_all_items(
        db: Session,
        gender: Optional[str] = None,
        question_type: Optional[str] = None,
        style_category: Optional[str] = None,
        is_active: bool = True
    ) -> List[QuizItem]:
        """Get all quiz items with optional filters"""
        query = db.query(QuizItem)
        
        if gender:
            query = query.filter(QuizItem.gender == gender)
        if question_type:
            query = query.filter(QuizItem.question_type == question_type)
        if style_category:
            query = query.filter(QuizItem.style_category == style_category)
        if is_active is not None:
            query = query.filter(QuizItem.is_active == is_active)
        
        return query.order_by(QuizItem.question_type, QuizItem.display_order).all()
