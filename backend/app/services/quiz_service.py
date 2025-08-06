"""
Quiz service for managing visual style assessment system
"""
import uuid
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.exc import IntegrityError

from app.models.quiz_system import (
    QuizClothingItem, 
    StyleCategory, 
    QuizResponse, 
    QuizResponseItem,
    FeatureLearningData, 
    FeatureCorrelation
)
from app.models.user import User


class QuizClothingItemService:
    """Service for managing quiz clothing items"""
    
    @staticmethod
    def create_clothing_item(
        db: Session,
        name: str,
        image_url: str,
        gender: str,
        category: str,
        features: List[str]
    ) -> QuizClothingItem:
        """Create a new quiz clothing item"""
        item = QuizClothingItem(
            name=name,
            image_url=image_url,
            gender=gender,
            category=category,
            features=features
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    
    @staticmethod
    def get_clothing_items_by_category(
        db: Session,
        gender: str,
        category: str,
        is_active: bool = True
    ) -> List[QuizClothingItem]:
        """Get clothing items by gender and category"""
        query = db.query(QuizClothingItem).filter(
            and_(
                QuizClothingItem.gender == gender,
                QuizClothingItem.category == category,
                QuizClothingItem.is_active == is_active
            )
        )
        return query.all()
    
    @staticmethod
    def get_clothing_item_by_id(
        db: Session,
        item_id: uuid.UUID
    ) -> Optional[QuizClothingItem]:
        """Get clothing item by ID"""
        return db.query(QuizClothingItem).filter(
            QuizClothingItem.id == item_id
        ).first()
    
    @staticmethod
    def update_clothing_item(
        db: Session,
        item_id: uuid.UUID,
        **updates
    ) -> Optional[QuizClothingItem]:
        """Update clothing item"""
        item = db.query(QuizClothingItem).filter(
            QuizClothingItem.id == item_id
        ).first()
        
        if not item:
            return None
        
        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        db.commit()
        db.refresh(item)
        return item
    
    @staticmethod
    def delete_clothing_item(
        db: Session,
        item_id: uuid.UUID
    ) -> bool:
        """Delete clothing item"""
        item = db.query(QuizClothingItem).filter(
            QuizClothingItem.id == item_id
        ).first()
        
        if not item:
            return False
        
        db.delete(item)
        db.commit()
        return True
    
    @staticmethod
    def add_feature_to_item(
        db: Session,
        item_id: uuid.UUID,
        feature: str
    ) -> Optional[QuizClothingItem]:
        """Add a feature to a clothing item"""
        item = db.query(QuizClothingItem).filter(
            QuizClothingItem.id == item_id
        ).first()
        
        if not item:
            return None
        
        item.add_feature(feature)
        flag_modified(item, "features")  # Mark the field as modified
        db.commit()
        db.refresh(item)
        return item
    
    @staticmethod
    def remove_feature_from_item(
        db: Session,
        item_id: uuid.UUID,
        feature: str
    ) -> Optional[QuizClothingItem]:
        """Remove a feature from a clothing item"""
        item = db.query(QuizClothingItem).filter(
            QuizClothingItem.id == item_id
        ).first()
        
        if not item:
            return None
        
        item.remove_feature(feature)
        flag_modified(item, "features")  # Mark the field as modified
        db.commit()
        db.refresh(item)
        return item
    
    @staticmethod
    def get_items_by_features(
        db: Session,
        gender: str,
        features: List[str],
        match_all: bool = False
    ) -> List[QuizClothingItem]:
        """Get items that have specific features"""
        query = db.query(QuizClothingItem).filter(
            and_(
                QuizClothingItem.gender == gender,
                QuizClothingItem.is_active == True
            )
        )
        
        # Get all items and filter in Python for SQLite compatibility
        all_items = query.all()
        filtered_items = []
        
        for item in all_items:
            item_features = set(item.features or [])
            search_features = set(features)
            
            if match_all:
                # All features must be present
                if search_features.issubset(item_features):
                    filtered_items.append(item)
            else:
                # Any feature can be present
                if search_features.intersection(item_features):
                    filtered_items.append(item)
        
        return filtered_items


class StyleCategoryService:
    """Service for managing style categories"""
    
    @staticmethod
    def create_style_category(
        db: Session,
        name: str,
        gender: str,
        features: List[str],
        ai_theme_prompt: Optional[str] = None,
        description: Optional[str] = None
    ) -> StyleCategory:
        """Create a new style category"""
        category = StyleCategory(
            name=name,
            gender=gender,
            features=features,
            ai_theme_prompt=ai_theme_prompt,
            description=description
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def get_categories_by_gender(
        db: Session,
        gender: str,
        is_active: bool = True
    ) -> List[StyleCategory]:
        """Get style categories by gender"""
        return db.query(StyleCategory).filter(
            and_(
                StyleCategory.gender == gender,
                StyleCategory.is_active == is_active
            )
        ).all()
    
    @staticmethod
    def get_category_by_id(
        db: Session,
        category_id: uuid.UUID
    ) -> Optional[StyleCategory]:
        """Get style category by ID"""
        return db.query(StyleCategory).filter(
            StyleCategory.id == category_id
        ).first()
    
    @staticmethod
    def update_category_features(
        db: Session,
        category_id: uuid.UUID,
        features: List[str]
    ) -> Optional[StyleCategory]:
        """Update category features"""
        category = db.query(StyleCategory).filter(
            StyleCategory.id == category_id
        ).first()
        
        if not category:
            return None
        
        category.features = features
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def calculate_style_scores(
        db: Session,
        selected_items: List[QuizClothingItem],
        gender: str
    ) -> Dict[str, float]:
        """Calculate style scores for selected items"""
        categories = StyleCategoryService.get_categories_by_gender(db, gender)
        scores = {}
        
        # Extract all features from selected items
        all_selected_features = []
        for item in selected_items:
            all_selected_features.extend(item.features or [])
        
        # Calculate scores for each category
        for category in categories:
            score = category.calculate_match_score(all_selected_features)
            scores[category.name] = score
        
        return scores
    
    @staticmethod
    def get_best_matching_category(
        db: Session,
        selected_items: List[QuizClothingItem],
        gender: str
    ) -> Tuple[Optional[StyleCategory], float]:
        """Get the best matching style category"""
        scores = StyleCategoryService.calculate_style_scores(db, selected_items, gender)
        
        if not scores:
            return None, 0.0
        
        best_category_name = max(scores, key=scores.get)
        best_score = scores[best_category_name]
        
        best_category = db.query(StyleCategory).filter(
            and_(
                StyleCategory.name == best_category_name,
                StyleCategory.gender == gender
            )
        ).first()
        
        return best_category, best_score


class QuizResponseService:
    """Service for managing quiz responses"""
    
    @staticmethod
    def create_quiz_response(
        db: Session,
        user_id: uuid.UUID,
        selected_item_ids: List[str],
        calculated_scores: Dict[str, float],
        assigned_category: str,
        assigned_category_id: Optional[uuid.UUID] = None,
        confidence_score: Optional[float] = None
    ) -> QuizResponse:
        """Create a new quiz response"""
        response = QuizResponse(
            user_id=user_id,
            selected_item_ids=selected_item_ids,
            calculated_scores=calculated_scores,
            assigned_category=assigned_category,
            assigned_category_id=assigned_category_id,
            confidence_score=Decimal(str(confidence_score)) if confidence_score else None
        )
        db.add(response)
        db.commit()
        db.refresh(response)
        return response
    
    @staticmethod
    def add_response_items(
        db: Session,
        quiz_response_id: uuid.UUID,
        item_selections: List[Dict[str, Any]]
    ) -> List[QuizResponseItem]:
        """Add selected items to quiz response"""
        response_items = []
        
        for selection in item_selections:
            response_item = QuizResponseItem(
                quiz_response_id=quiz_response_id,
                clothing_item_id=selection['item_id'],
                question_category=selection['category'],
                weight=Decimal(str(selection.get('weight', 1.0)))
            )
            db.add(response_item)
            response_items.append(response_item)
        
        db.commit()
        return response_items
    
    @staticmethod
    def get_user_quiz_responses(
        db: Session,
        user_id: uuid.UUID
    ) -> List[QuizResponse]:
        """Get all quiz responses for a user"""
        return db.query(QuizResponse).filter(
            QuizResponse.user_id == user_id
        ).order_by(desc(QuizResponse.completed_at)).all()
    
    @staticmethod
    def get_latest_user_response(
        db: Session,
        user_id: uuid.UUID
    ) -> Optional[QuizResponse]:
        """Get the latest quiz response for a user"""
        return db.query(QuizResponse).filter(
            QuizResponse.user_id == user_id
        ).order_by(desc(QuizResponse.completed_at)).first()
    
    @staticmethod
    def update_user_feedback(
        db: Session,
        response_id: uuid.UUID,
        satisfaction_rating: int,
        feedback_text: Optional[str] = None
    ) -> Optional[QuizResponse]:
        """Update user feedback for a quiz response"""
        response = db.query(QuizResponse).filter(
            QuizResponse.id == response_id
        ).first()
        
        if not response:
            return None
        
        response.user_satisfaction_rating = satisfaction_rating
        response.user_feedback_text = feedback_text
        
        db.commit()
        db.refresh(response)
        return response
    
    @staticmethod
    def process_complete_quiz(
        db: Session,
        user_id: uuid.UUID,
        gender: str,
        selected_items: Dict[str, uuid.UUID],
        weights: Optional[Dict[str, float]] = None
    ) -> QuizResponse:
        """Process a complete quiz submission"""
        # Default weights for different question types
        default_weights = {
            'top': 0.2,
            'bottom': 0.2,
            'shoes': 0.15,
            'layering': 0.1,
            'accessory': 0.05,
            'complete_outfit': 0.4
        }
        
        if weights:
            default_weights.update(weights)
        
        # Get selected clothing items
        item_ids = list(selected_items.values())
        items = db.query(QuizClothingItem).filter(
            QuizClothingItem.id.in_(item_ids)
        ).all()
        
        # Calculate style scores
        scores = StyleCategoryService.calculate_style_scores(db, items, gender)
        
        # Get best matching category
        best_category, confidence = StyleCategoryService.get_best_matching_category(
            db, items, gender
        )
        
        # Create quiz response
        response = QuizResponseService.create_quiz_response(
            db=db,
            user_id=user_id,
            selected_item_ids=[str(item_id) for item_id in item_ids],
            calculated_scores=scores,
            assigned_category=best_category.name if best_category else "Unknown",
            assigned_category_id=best_category.id if best_category else None,
            confidence_score=confidence
        )
        
        # Add response items with weights
        item_selections = []
        for category, item_id in selected_items.items():
            item_selections.append({
                'item_id': item_id,
                'category': category,
                'weight': default_weights.get(category, 1.0)
            })
        
        QuizResponseService.add_response_items(
            db, response.id, item_selections
        )
        
        # Update selection counts for items
        for item in items:
            item.increment_selection_count()
        
        db.commit()
        return response


class FeatureLearningService:
    """Service for smart feature learning system"""
    
    @staticmethod
    def add_feature_suggestion(
        db: Session,
        feature_name: str,
        item_id: uuid.UUID,
        source: str,
        confidence_score: Optional[float] = None
    ) -> FeatureLearningData:
        """Add a feature suggestion for learning"""
        learning_data = FeatureLearningData(
            feature_name=feature_name,
            item_id=item_id,
            source=source,
            confidence_score=Decimal(str(confidence_score)) if confidence_score else None
        )
        db.add(learning_data)
        db.commit()
        db.refresh(learning_data)
        return learning_data
    
    @staticmethod
    def validate_feature(
        db: Session,
        learning_data_id: uuid.UUID,
        is_valid: bool
    ) -> Optional[FeatureLearningData]:
        """Validate or reject a feature suggestion"""
        learning_data = db.query(FeatureLearningData).filter(
            FeatureLearningData.id == learning_data_id
        ).first()
        
        if not learning_data:
            return None
        
        if is_valid:
            learning_data.validation_count += 1
        else:
            learning_data.rejection_count += 1
        
        db.commit()
        db.refresh(learning_data)
        return learning_data
    
    @staticmethod
    def get_pending_validations(
        db: Session,
        source: Optional[str] = None,
        limit: int = 50
    ) -> List[FeatureLearningData]:
        """Get pending feature validations"""
        query = db.query(FeatureLearningData).filter(
            and_(
                FeatureLearningData.validation_count == 0,
                FeatureLearningData.rejection_count == 0
            )
        )
        
        if source:
            query = query.filter(FeatureLearningData.source == source)
        
        return query.limit(limit).all()
    
    @staticmethod
    def update_feature_correlation(
        db: Session,
        feature_a: str,
        feature_b: str,
        co_occurred: bool = True
    ) -> FeatureCorrelation:
        """Update feature correlation data"""
        # Ensure consistent ordering
        if feature_a > feature_b:
            feature_a, feature_b = feature_b, feature_a
        
        correlation = db.query(FeatureCorrelation).filter(
            and_(
                FeatureCorrelation.feature_a == feature_a,
                FeatureCorrelation.feature_b == feature_b
            )
        ).first()
        
        if not correlation:
            correlation = FeatureCorrelation(
                feature_a=feature_a,
                feature_b=feature_b,
                co_occurrence_count=0,
                total_occurrences=0
            )
            db.add(correlation)
        
        correlation.total_occurrences += 1
        if co_occurred:
            correlation.co_occurrence_count += 1
        
        # Calculate correlation strength
        correlation.correlation_strength = Decimal(str(correlation.co_occurrence_rate))
        
        db.commit()
        db.refresh(correlation)
        return correlation
    
    @staticmethod
    def get_feature_correlations(
        db: Session,
        feature: str,
        min_strength: float = 0.5
    ) -> List[FeatureCorrelation]:
        """Get correlations for a specific feature"""
        return db.query(FeatureCorrelation).filter(
            and_(
                or_(
                    FeatureCorrelation.feature_a == feature,
                    FeatureCorrelation.feature_b == feature
                ),
                FeatureCorrelation.correlation_strength >= Decimal(str(min_strength))
            )
        ).all()