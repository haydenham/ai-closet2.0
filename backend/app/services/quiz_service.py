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
    FeatureCorrelation,
    StyleAssignmentFeedback
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
    def calculate_weighted_style_scores(
        db: Session,
        selected_items: Dict[str, QuizClothingItem],
        gender: str,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate weighted style scores based on question categories"""
        categories = StyleCategoryService.get_categories_by_gender(db, gender)
        
        # Default weights prioritizing complete outfit
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
        
        scores = {}
        
        for category in categories:
            category_score = 0.0
            total_weight = 0.0
            
            # Calculate weighted score for each selected item
            for question_category, item in selected_items.items():
                if item and question_category in default_weights:
                    weight = default_weights[question_category]
                    item_features = set(item.features or [])
                    category_features = set(category.features or [])
                    
                    # Calculate feature match percentage for this item
                    if item_features:
                        match_count = len(item_features.intersection(category_features))
                        item_score = (match_count / len(item_features)) * 100
                        category_score += item_score * weight
                        total_weight += weight
            
            # Normalize by total weight
            if total_weight > 0:
                scores[category.name] = category_score / total_weight
            else:
                scores[category.name] = 0.0
        
        return scores
    
    @staticmethod
    def calculate_confidence_score(
        scores: Dict[str, float],
        selected_items: Dict[str, QuizClothingItem]
    ) -> float:
        """Calculate confidence in style assignment based on score distribution"""
        if not scores:
            return 0.0
        
        sorted_scores = sorted(scores.values(), reverse=True)
        
        # If no clear winner, confidence is low
        if len(sorted_scores) < 2:
            return 0.0
        
        best_score = sorted_scores[0]
        second_best = sorted_scores[1]
        
        # Confidence based on gap between best and second-best scores
        if best_score == 0:
            return 0.0
        
        # Calculate confidence as the relative gap
        gap = best_score - second_best
        confidence = min(gap / best_score, 1.0) * 100
        
        # Boost confidence if complete outfit strongly matches
        complete_outfit_item = selected_items.get('complete_outfit')
        if complete_outfit_item and best_score > 60:
            confidence = min(confidence * 1.2, 100.0)
        
        return round(confidence, 2)
    
    @staticmethod
    def detect_hybrid_styles(
        scores: Dict[str, float],
        threshold: float = 15.0
    ) -> List[str]:
        """Detect if user has hybrid style preferences"""
        if not scores:
            return []
        
        # Find styles that are close to the top score
        max_score = max(scores.values())
        hybrid_styles = []
        
        for style, score in scores.items():
            if max_score - score <= threshold and score > 30:
                hybrid_styles.append(style)
        
        return sorted(hybrid_styles, key=lambda x: scores[x], reverse=True)
    
    @staticmethod
    def get_enhanced_style_assignment(
        db: Session,
        selected_items: Dict[str, QuizClothingItem],
        gender: str,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive style assignment with confidence and hybrid detection"""
        # Calculate weighted scores
        scores = StyleCategoryService.calculate_weighted_style_scores(
            db, selected_items, gender, weights
        )
        
        if not scores:
            return {
                'primary_style': None,
                'confidence': 0.0,
                'scores': {},
                'hybrid_styles': [],
                'is_hybrid': False
            }
        
        # Get primary style
        primary_style = max(scores, key=scores.get)
        primary_score = scores[primary_style]
        
        # Calculate confidence
        confidence = StyleCategoryService.calculate_confidence_score(scores, selected_items)
        
        # Detect hybrid styles
        hybrid_styles = StyleCategoryService.detect_hybrid_styles(scores)
        is_hybrid = len(hybrid_styles) > 1
        
        # Get category object
        primary_category = db.query(StyleCategory).filter(
            and_(
                StyleCategory.name == primary_style,
                StyleCategory.gender == gender
            )
        ).first()
        
        return {
            'primary_style': primary_style,
            'primary_category': primary_category,
            'primary_score': primary_score,
            'confidence': confidence,
            'scores': scores,
            'hybrid_styles': hybrid_styles,
            'is_hybrid': is_hybrid
        }
    
    @staticmethod
    def calculate_style_scores(
        db: Session,
        selected_items: List[QuizClothingItem],
        gender: str
    ) -> Dict[str, float]:
        """Calculate style scores for selected items (legacy method)"""
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
        """Get the best matching style category (legacy method)"""
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
        selected_items: Dict[str, str],  # Accept string UUIDs
        weights: Optional[Dict[str, float]] = None
    ) -> QuizResponse:
        """Process a complete quiz submission with enhanced matching algorithm"""
        # Convert string UUIDs to UUID objects
        converted_items = {}
        for category, item_id_str in selected_items.items():
            converted_items[category] = uuid.UUID(item_id_str)
        
        # Get selected clothing items
        item_ids = list(converted_items.values())
        items_list = db.query(QuizClothingItem).filter(
            QuizClothingItem.id.in_(item_ids)
        ).all()
        
        # Create items dictionary for enhanced processing
        items_dict = {}
        for category, item_id in converted_items.items():
            item = next((item for item in items_list if item.id == item_id), None)
            items_dict[category] = item
        
        # Get enhanced style assignment
        style_assignment = StyleCategoryService.get_enhanced_style_assignment(
            db, items_dict, gender, weights
        )
        
        # Prepare response data
        assigned_category = style_assignment['primary_style'] or "Unknown"
        assigned_category_id = (
            style_assignment['primary_category'].id 
            if style_assignment['primary_category'] else None
        )
        confidence_score = style_assignment['confidence']
        calculated_scores = style_assignment['scores']
        
        # Add hybrid style information to scores
        if style_assignment['is_hybrid']:
            calculated_scores['_hybrid_styles'] = style_assignment['hybrid_styles']
            calculated_scores['_is_hybrid'] = True
            calculated_scores['_primary_score'] = style_assignment['primary_score']
        
        # Create quiz response
        response = QuizResponseService.create_quiz_response(
            db=db,
            user_id=user_id,
            selected_item_ids=[str(item_id) for item_id in item_ids],
            calculated_scores=calculated_scores,
            assigned_category=assigned_category,
            assigned_category_id=assigned_category_id,
            confidence_score=confidence_score
        )
        
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
        for item in items_list:
            item.increment_selection_count()
        
        db.commit()
        return response


class StyleFeedbackService:
    """Service for managing style assignment feedback and algorithm improvement"""
    
    @staticmethod
    def create_style_feedback(
        db: Session,
        quiz_response_id: uuid.UUID,
        user_id: uuid.UUID,
        accuracy_rating: int,
        feedback_type: str,
        preferred_style: Optional[str] = None,
        feedback_text: Optional[str] = None,
        feature_feedback: Optional[Dict[str, Any]] = None
    ) -> "StyleAssignmentFeedback":
        """Create style assignment feedback"""
        from app.models.quiz_system import StyleAssignmentFeedback
        
        feedback = StyleAssignmentFeedback(
            quiz_response_id=quiz_response_id,
            user_id=user_id,
            accuracy_rating=accuracy_rating,
            feedback_type=feedback_type,
            preferred_style=preferred_style,
            feedback_text=feedback_text,
            feature_feedback=feature_feedback or {}
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
    
    @staticmethod
    def get_feedback_metrics(
        db: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get algorithm improvement metrics based on user feedback"""
        from app.models.quiz_system import StyleAssignmentFeedback
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        feedback_query = db.query(StyleAssignmentFeedback).filter(
            StyleAssignmentFeedback.created_at >= cutoff_date
        )
        
        all_feedback = feedback_query.all()
        
        if not all_feedback:
            return {
                'total_feedback_count': 0,
                'average_accuracy_rating': 0.0,
                'feedback_distribution': {},
                'most_common_issues': [],
                'improvement_suggestions': [],
                'confidence_vs_accuracy': {}
            }
        
        # Calculate metrics
        total_count = len(all_feedback)
        avg_rating = sum(f.accuracy_rating for f in all_feedback) / total_count
        
        # Feedback type distribution
        feedback_dist = {}
        for feedback in all_feedback:
            feedback_dist[feedback.feedback_type] = feedback_dist.get(feedback.feedback_type, 0) + 1
        
        # Most common issues
        issues = []
        for feedback_type, count in feedback_dist.items():
            if feedback_type in ['too_broad', 'too_narrow', 'completely_wrong']:
                issues.append({
                    'issue': feedback_type,
                    'count': count,
                    'percentage': (count / total_count) * 100
                })
        
        issues.sort(key=lambda x: x['count'], reverse=True)
        
        # Generate improvement suggestions
        suggestions = StyleFeedbackService._generate_improvement_suggestions(feedback_dist, avg_rating)
        
        return {
            'total_feedback_count': total_count,
            'average_accuracy_rating': round(avg_rating, 2),
            'feedback_distribution': feedback_dist,
            'most_common_issues': issues[:5],
            'improvement_suggestions': suggestions,
            'confidence_vs_accuracy': {}  # TODO: Implement confidence correlation
        }
    
    @staticmethod
    def _generate_improvement_suggestions(
        feedback_dist: Dict[str, int],
        avg_rating: float
    ) -> List[str]:
        """Generate algorithm improvement suggestions based on feedback patterns"""
        suggestions = []
        total_feedback = sum(feedback_dist.values())
        
        if avg_rating < 3.0:
            suggestions.append("Overall algorithm accuracy is low - consider retraining with more diverse data")
        
        if feedback_dist.get('too_broad', 0) / total_feedback > 0.3:
            suggestions.append("Many users find categories too broad - consider adding more specific subcategories")
        
        if feedback_dist.get('too_narrow', 0) / total_feedback > 0.3:
            suggestions.append("Categories may be too narrow - consider merging similar styles")
        
        if feedback_dist.get('completely_wrong', 0) / total_feedback > 0.2:
            suggestions.append("High rate of completely wrong assignments - review feature mappings")
        
        return suggestions
    
    @staticmethod
    def analyze_feature_accuracy(
        db: Session,
        feature_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze accuracy of a specific feature in style assignments"""
        from app.models.quiz_system import StyleAssignmentFeedback, QuizResponse, QuizResponseItem, QuizClothingItem
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get feedback for responses that included items with this feature
        feedback_with_feature = db.query(StyleAssignmentFeedback).join(
            QuizResponse, StyleAssignmentFeedback.quiz_response_id == QuizResponse.id
        ).join(
            QuizResponseItem, QuizResponse.id == QuizResponseItem.quiz_response_id
        ).join(
            QuizClothingItem, QuizResponseItem.clothing_item_id == QuizClothingItem.id
        ).filter(
            StyleAssignmentFeedback.created_at >= cutoff_date,
            QuizClothingItem.features.contains([feature_name])
        ).all()
        
        if not feedback_with_feature:
            return {
                'feature_name': feature_name,
                'sample_size': 0,
                'average_accuracy': 0.0,
                'accuracy_trend': 'insufficient_data'
            }
        
        avg_accuracy = sum(f.accuracy_rating for f in feedback_with_feature) / len(feedback_with_feature)
        
        return {
            'feature_name': feature_name,
            'sample_size': len(feedback_with_feature),
            'average_accuracy': round(avg_accuracy, 2),
            'accuracy_trend': 'improving' if avg_accuracy > 3.5 else 'needs_attention'
        }


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