"""
Unit tests for OutfitRecommendation model and related models
"""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.clothing_item import ClothingItem
from app.models.outfit_recommendation import OutfitRecommendation, RecommendationFeedback


class TestOutfitRecommendationModel:
    """Test cases for OutfitRecommendation model"""
    
    def test_create_outfit_recommendation(self, db_session: Session):
        """Test creating a new outfit recommendation"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create outfit recommendation
        outfit_components = {
            "top": "casual shirt",
            "bottom": "jeans",
            "shoes": "sneakers"
        }
        
        similarity_scores = {
            "top": 0.85,
            "bottom": 0.92,
            "shoes": 0.78
        }
        
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit for weekend",
            ai_response="Here's a great casual outfit: blue shirt, dark jeans, white sneakers",
            outfit_components=outfit_components,
            ai_model_used="casual_model_v1",
            occasion="weekend",
            weather="mild",
            season="spring",
            processing_time_ms=1500,
            similarity_scores=similarity_scores
        )
        
        db_session.add(recommendation)
        db_session.commit()
        db_session.refresh(recommendation)
        
        assert recommendation.id is not None
        assert recommendation.user_id == user.id
        assert recommendation.prompt == "I need a casual outfit for weekend"
        assert recommendation.ai_response == "Here's a great casual outfit: blue shirt, dark jeans, white sneakers"
        assert recommendation.outfit_components == outfit_components
        assert recommendation.ai_model_used == "casual_model_v1"
        assert recommendation.occasion == "weekend"
        assert recommendation.weather == "mild"
        assert recommendation.season == "spring"
        assert recommendation.feedback_score is None
        assert recommendation.feedback_comments is None
        assert recommendation.is_favorite is False
        assert recommendation.is_archived is False
        assert recommendation.processing_time_ms == 1500
        assert recommendation.similarity_scores == similarity_scores
        assert recommendation.created_at is not None
        assert recommendation.updated_at is not None
    
    def test_outfit_recommendation_user_relationship(self, db_session: Session):
        """Test outfit recommendation relationship with user"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create outfit recommendation
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit",
            ai_response="Here's a casual outfit suggestion",
            ai_model_used="casual_model_v1"
        )
        
        db_session.add(recommendation)
        db_session.commit()
        db_session.refresh(recommendation)
        
        # Test relationships
        assert recommendation.user.id == user.id
        assert recommendation.user.email == "test@example.com"
        assert len(user.outfit_recommendations) == 1
        assert user.outfit_recommendations[0].id == recommendation.id
    
    def test_add_clothing_item(self, db_session: Session):
        """Test adding clothing item to recommendation"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt"
        )
        
        db_session.add(clothing_item)
        db_session.commit()
        db_session.refresh(clothing_item)
        
        # Create outfit recommendation
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit",
            ai_response="Here's a casual outfit suggestion",
            ai_model_used="casual_model_v1"
        )
        
        db_session.add(recommendation)
        db_session.commit()
        db_session.refresh(recommendation)
        
        # Add clothing item to recommendation
        initial_count = clothing_item.times_recommended
        recommendation.add_clothing_item(clothing_item)
        db_session.commit()
        
        # Test relationship
        assert len(recommendation.recommended_items) == 1
        assert recommendation.recommended_items[0].id == clothing_item.id
        assert clothing_item.times_recommended == initial_count + 1
        assert clothing_item.last_recommended is not None
        
        # Adding same item again should not duplicate
        recommendation.add_clothing_item(clothing_item)
        assert len(recommendation.recommended_items) == 1
    
    def test_remove_clothing_item(self, db_session: Session):
        """Test removing clothing item from recommendation"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt"
        )
        
        db_session.add(clothing_item)
        db_session.commit()
        db_session.refresh(clothing_item)
        
        # Create outfit recommendation
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit",
            ai_response="Here's a casual outfit suggestion",
            ai_model_used="casual_model_v1"
        )
        
        db_session.add(recommendation)
        db_session.commit()
        db_session.refresh(recommendation)
        
        # Add and then remove clothing item
        recommendation.add_clothing_item(clothing_item)
        db_session.commit()
        assert len(recommendation.recommended_items) == 1
        
        recommendation.remove_clothing_item(clothing_item)
        db_session.commit()
        assert len(recommendation.recommended_items) == 0
    
    def test_get_items_by_category(self, db_session: Session):
        """Test getting items by category"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing items
        shirt = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt"
        )
        
        pants = ClothingItem(
            user_id=user.id,
            filename="pants_001.jpg",
            original_filename="jeans.jpg",
            image_url="https://storage.example.com/pants_001.jpg",
            category="pants"
        )
        
        db_session.add_all([shirt, pants])
        db_session.commit()
        db_session.refresh(shirt)
        db_session.refresh(pants)
        
        # Create outfit recommendation
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit",
            ai_response="Here's a casual outfit suggestion",
            ai_model_used="casual_model_v1"
        )
        
        db_session.add(recommendation)
        db_session.commit()
        db_session.refresh(recommendation)
        
        # Add items to recommendation
        recommendation.add_clothing_item(shirt)
        recommendation.add_clothing_item(pants)
        db_session.commit()
        
        # Test getting items by category
        shirt_items = recommendation.get_items_by_category("shirt")
        pants_items = recommendation.get_items_by_category("pants")
        shoes_items = recommendation.get_items_by_category("shoes")
        
        assert len(shirt_items) == 1
        assert shirt_items[0].id == shirt.id
        assert len(pants_items) == 1
        assert pants_items[0].id == pants.id
        assert len(shoes_items) == 0
    
    def test_set_feedback(self, db_session: Session):
        """Test setting feedback for recommendation"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create outfit recommendation
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit",
            ai_response="Here's a casual outfit suggestion",
            ai_model_used="casual_model_v1"
        )
        
        db_session.add(recommendation)
        db_session.commit()
        
        # Set feedback
        recommendation.set_feedback(4, "Great recommendation!")
        assert recommendation.feedback_score == 4
        assert recommendation.feedback_comments == "Great recommendation!"
        assert recommendation.has_feedback is True
        
        # Test invalid feedback score
        with pytest.raises(ValueError, match="Feedback score must be between 1 and 5"):
            recommendation.set_feedback(0)
        
        with pytest.raises(ValueError, match="Feedback score must be between 1 and 5"):
            recommendation.set_feedback(6)
    
    def test_item_count_property(self, db_session: Session):
        """Test item count property"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing items
        shirt = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt"
        )
        
        pants = ClothingItem(
            user_id=user.id,
            filename="pants_001.jpg",
            original_filename="jeans.jpg",
            image_url="https://storage.example.com/pants_001.jpg",
            category="pants"
        )
        
        db_session.add_all([shirt, pants])
        db_session.commit()
        db_session.refresh(shirt)
        db_session.refresh(pants)
        
        # Create outfit recommendation
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit",
            ai_response="Here's a casual outfit suggestion",
            ai_model_used="casual_model_v1"
        )
        
        db_session.add(recommendation)
        db_session.commit()
        db_session.refresh(recommendation)
        
        # Test item count
        assert recommendation.item_count == 0
        
        recommendation.add_clothing_item(shirt)
        db_session.commit()
        assert recommendation.item_count == 1
        
        recommendation.add_clothing_item(pants)
        db_session.commit()
        assert recommendation.item_count == 2
    
    def test_categories_covered_property(self, db_session: Session):
        """Test categories covered property"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create clothing items
        shirt1 = ClothingItem(
            user_id=user.id,
            filename="shirt_001.jpg",
            original_filename="blue_shirt.jpg",
            image_url="https://storage.example.com/shirt_001.jpg",
            category="shirt"
        )
        
        shirt2 = ClothingItem(
            user_id=user.id,
            filename="shirt_002.jpg",
            original_filename="red_shirt.jpg",
            image_url="https://storage.example.com/shirt_002.jpg",
            category="shirt"
        )
        
        pants = ClothingItem(
            user_id=user.id,
            filename="pants_001.jpg",
            original_filename="jeans.jpg",
            image_url="https://storage.example.com/pants_001.jpg",
            category="pants"
        )
        
        db_session.add_all([shirt1, shirt2, pants])
        db_session.commit()
        db_session.refresh(shirt1)
        db_session.refresh(shirt2)
        db_session.refresh(pants)
        
        # Create outfit recommendation
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit",
            ai_response="Here's a casual outfit suggestion",
            ai_model_used="casual_model_v1"
        )
        
        db_session.add(recommendation)
        db_session.commit()
        db_session.refresh(recommendation)
        
        # Test categories covered
        assert recommendation.categories_covered == []
        
        recommendation.add_clothing_item(shirt1)
        recommendation.add_clothing_item(shirt2)
        db_session.commit()
        categories = recommendation.categories_covered
        assert len(categories) == 1
        assert "shirt" in categories
        
        recommendation.add_clothing_item(pants)
        db_session.commit()
        categories = recommendation.categories_covered
        assert len(categories) == 2
        assert "shirt" in categories
        assert "pants" in categories
    
    def test_outfit_recommendation_repr(self, db_session: Session):
        """Test outfit recommendation string representation"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create outfit recommendation
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit",
            ai_response="Here's a casual outfit suggestion",
            ai_model_used="casual_model_v1"
        )
        
        db_session.add(recommendation)
        db_session.commit()
        db_session.refresh(recommendation)
        
        expected_repr = f"<OutfitRecommendation(id={recommendation.id}, user_id={user.id}, model=casual_model_v1)>"
        assert repr(recommendation) == expected_repr


class TestRecommendationFeedbackModel:
    """Test cases for RecommendationFeedback model"""
    
    def test_create_recommendation_feedback(self, db_session: Session):
        """Test creating recommendation feedback"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create outfit recommendation
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit",
            ai_response="Here's a casual outfit suggestion",
            ai_model_used="casual_model_v1"
        )
        
        db_session.add(recommendation)
        db_session.commit()
        db_session.refresh(recommendation)
        
        # Create feedback
        feedback = RecommendationFeedback(
            recommendation_id=recommendation.id,
            user_id=user.id,
            rating=4,
            feedback_type="general",
            comments="Great recommendation, loved the style!",
            style_accuracy=5,
            item_matching=4,
            occasion_appropriateness=4,
            feedback_tags=["stylish", "comfortable"]
        )
        
        db_session.add(feedback)
        db_session.commit()
        db_session.refresh(feedback)
        
        assert feedback.id is not None
        assert feedback.recommendation_id == recommendation.id
        assert feedback.user_id == user.id
        assert feedback.rating == 4
        assert feedback.feedback_type == "general"
        assert feedback.comments == "Great recommendation, loved the style!"
        assert feedback.style_accuracy == 5
        assert feedback.item_matching == 4
        assert feedback.occasion_appropriateness == 4
        assert feedback.feedback_tags == ["stylish", "comfortable"]
        assert feedback.created_at is not None
    
    def test_recommendation_feedback_relationships(self, db_session: Session):
        """Test recommendation feedback relationships"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create outfit recommendation
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit",
            ai_response="Here's a casual outfit suggestion",
            ai_model_used="casual_model_v1"
        )
        
        db_session.add(recommendation)
        db_session.commit()
        db_session.refresh(recommendation)
        
        # Create feedback
        feedback = RecommendationFeedback(
            recommendation_id=recommendation.id,
            user_id=user.id,
            rating=4,
            feedback_type="general",
            comments="Great recommendation!"
        )
        
        db_session.add(feedback)
        db_session.commit()
        db_session.refresh(feedback)
        
        # Test relationships
        assert feedback.recommendation.id == recommendation.id
        assert feedback.user.id == user.id
        assert len(recommendation.feedback_entries) == 1
        assert recommendation.feedback_entries[0].id == feedback.id
    
    def test_recommendation_feedback_repr(self, db_session: Session):
        """Test recommendation feedback string representation"""
        # Create a user first
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create outfit recommendation
        recommendation = OutfitRecommendation(
            user_id=user.id,
            prompt="I need a casual outfit",
            ai_response="Here's a casual outfit suggestion",
            ai_model_used="casual_model_v1"
        )
        
        db_session.add(recommendation)
        db_session.commit()
        db_session.refresh(recommendation)
        
        # Create feedback
        feedback = RecommendationFeedback(
            recommendation_id=recommendation.id,
            user_id=user.id,
            rating=4,
            feedback_type="general"
        )
        
        db_session.add(feedback)
        db_session.commit()
        db_session.refresh(feedback)
        
        expected_repr = f"<RecommendationFeedback(id={feedback.id}, rating=4)>"
        assert repr(feedback) == expected_repr