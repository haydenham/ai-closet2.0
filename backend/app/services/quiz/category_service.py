"""
Service for managing style categories
"""
import uuid
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.quiz import StyleCategory

logger = logging.getLogger(__name__)


class CategoryService:
    """Service for CRUD operations on style categories"""
    
    @staticmethod
    def get_all_categories(
        db: Session,
        gender: Optional[str] = None,
        is_active: bool = True
    ) -> List[StyleCategory]:
        """Get all style categories, optionally filtered by gender"""
        query = db.query(StyleCategory)
        
        if gender:
            query = query.filter(StyleCategory.gender == gender)
        if is_active is not None:
            query = query.filter(StyleCategory.is_active == is_active)
        
        return query.order_by(StyleCategory.name).all()
    
    @staticmethod
    def get_category_by_name(
        db: Session,
        name: str,
        gender: str
    ) -> Optional[StyleCategory]:
        """Get a style category by name and gender"""
        return db.query(StyleCategory).filter(
            and_(
                StyleCategory.name == name,
                StyleCategory.gender == gender
            )
        ).first()
    
    @staticmethod
    def get_category_by_id(
        db: Session,
        category_id: uuid.UUID
    ) -> Optional[StyleCategory]:
        """Get a style category by ID"""
        return db.query(StyleCategory).filter(
            StyleCategory.id == category_id
        ).first()
    
    @staticmethod
    def create_category(
        db: Session,
        name: str,
        gender: str,
        description: Optional[str] = None,
        ai_theme_prompt: Optional[str] = None
    ) -> StyleCategory:
        """Create a new style category"""
        category = StyleCategory(
            name=name,
            gender=gender,
            description=description,
            ai_theme_prompt=ai_theme_prompt
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def update_category(
        db: Session,
        category_id: uuid.UUID,
        **updates
    ) -> Optional[StyleCategory]:
        """Update a style category"""
        category = db.query(StyleCategory).filter(
            StyleCategory.id == category_id
        ).first()
        
        if not category:
            return None
        
        for key, value in updates.items():
            if hasattr(category, key) and value is not None:
                setattr(category, key, value)
        
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def delete_category(db: Session, category_id: uuid.UUID) -> bool:
        """Soft delete a category by setting is_active to False"""
        category = db.query(StyleCategory).filter(
            StyleCategory.id == category_id
        ).first()
        
        if not category:
            return False
        
        category.is_active = False
        db.commit()
        return True
