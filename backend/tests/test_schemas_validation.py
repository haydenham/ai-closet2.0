"""
Unit tests for Pydantic schema validation
"""
import pytest
import uuid
from datetime import datetime
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserUpdate, UserLogin, PasswordReset
from app.schemas.style_profile import StyleProfileCreate, QuizSubmission
from app.schemas.clothing_item import ClothingItemCreate, ClothingItemUpdate
from app.schemas.outfit_recommendation import OutfitRecommendationCreate, RecommendationFeedbackCreate


class TestUserSchemas:
    """Test cases for User schema validation"""
    
    def test_user_create_valid(self):
        """Test valid user creation data"""
        user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePass123"
        }
        
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.password == "SecurePass123"
    
    def test_user_create_invalid_email(self):
        """Test user creation with invalid email"""
        user_data = {
            "email": "invalid-email",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePass123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        assert "value is not a valid email address" in str(exc_info.value)
    
    def test_user_create_weak_password(self):
        """Test user creation with weak password"""
        user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "weak"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        assert "String should have at least 8 characters" in str(exc_info.value)
    
    def test_user_create_password_missing_requirements(self):
        """Test user creation with password missing requirements"""
        # Missing uppercase
        user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "lowercase123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        assert "Password must contain at least one uppercase letter" in str(exc_info.value)
        
        # Missing lowercase
        user_data["password"] = "UPPERCASE123"
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        assert "Password must contain at least one lowercase letter" in str(exc_info.value)
        
        # Missing digit
        user_data["password"] = "UpperLower"
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        assert "Password must contain at least one digit" in str(exc_info.value)
    
    def test_user_update_partial(self):
        """Test partial user update"""
        update_data = {"first_name": "Jane"}
        
        user_update = UserUpdate(**update_data)
        assert user_update.first_name == "Jane"
        assert user_update.last_name is None
        assert user_update.email is None
    
    def test_user_login_valid(self):
        """Test valid user login data"""
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        user_login = UserLogin(**login_data)
        assert user_login.email == "test@example.com"
        assert user_login.password == "password123"


class TestStyleProfileSchemas:
    """Test cases for StyleProfile schema validation"""
    
    def test_style_profile_create_valid(self):
        """Test valid style profile creation"""
        profile_data = {
            "assigned_model": "casual_model_v1",
            "style_preferences": ["casual", "comfortable"],
            "quiz_responses": {
                "style_preference": "casual",
                "color_preference": ["blue", "black"]
            },
            "fashion_goals": ["versatile"],
            "preferred_colors": ["blue", "black"],
            "body_type": "athletic",
            "lifestyle": "active",
            "budget_range": "$100-500"
        }
        
        profile = StyleProfileCreate(**profile_data)
        assert profile.assigned_model == "casual_model_v1"
        assert profile.style_preferences == ["casual", "comfortable"]
        assert profile.quiz_responses == {"style_preference": "casual", "color_preference": ["blue", "black"]}
    
    def test_quiz_submission_valid(self):
        """Test valid quiz submission"""
        quiz_data = {
            "responses": {
                "style_preference": "casual",
                "color_preference": ["blue", "black"],
                "budget": "medium"
            }
        }
        
        quiz = QuizSubmission(**quiz_data)
        assert quiz.responses == quiz_data["responses"]
    
    def test_quiz_submission_empty_responses(self):
        """Test quiz submission with empty responses"""
        quiz_data = {"responses": {}}
        
        with pytest.raises(ValidationError) as exc_info:
            QuizSubmission(**quiz_data)
        
        assert "Dictionary should have at least 1 item" in str(exc_info.value)


class TestClothingItemSchemas:
    """Test cases for ClothingItem schema validation"""
    
    def test_clothing_item_create_valid(self):
        """Test valid clothing item creation"""
        item_data = {
            "original_filename": "blue_shirt.jpg",
            "category": "shirt",
            "color": "blue",
            "brand": "Nike",
            "size": "M",
            "description": "Comfortable cotton shirt",
            "tags": ["casual", "cotton"]
        }
        
        item = ClothingItemCreate(**item_data)
        assert item.original_filename == "blue_shirt.jpg"
        assert item.category == "shirt"
        assert item.color == "blue"
        assert item.brand == "Nike"
        assert item.size == "M"
        assert item.description == "Comfortable cotton shirt"
        assert set(item.tags) == {"casual", "cotton"}
    
    def test_clothing_item_create_tags_validation(self):
        """Test clothing item tags validation"""
        # Test with duplicate tags
        item_data = {
            "original_filename": "shirt.jpg",
            "category": "shirt",
            "tags": ["casual", "cotton", "casual", ""]
        }
        
        item = ClothingItemCreate(**item_data)
        # Should remove duplicates and empty strings
        assert set(item.tags) == {"casual", "cotton"}
    
    def test_clothing_item_update_partial(self):
        """Test partial clothing item update"""
        update_data = {
            "color": "red",
            "tags": ["formal", "silk"]
        }
        
        item_update = ClothingItemUpdate(**update_data)
        assert item_update.color == "red"
        assert set(item_update.tags) == {"formal", "silk"}
        assert item_update.category is None
        assert item_update.brand is None


class TestOutfitRecommendationSchemas:
    """Test cases for OutfitRecommendation schema validation"""
    
    def test_outfit_recommendation_create_valid(self):
        """Test valid outfit recommendation creation"""
        recommendation_data = {
            "prompt": "I need a casual outfit for weekend",
            "ai_model_used": "casual_model_v1",
            "ai_response": "Here's a great casual outfit suggestion",
            "occasion": "weekend",
            "weather": "mild",
            "season": "spring",
            "outfit_components": {
                "top": "casual shirt",
                "bottom": "jeans"
            },
            "processing_time_ms": 1500,
            "similarity_scores": {
                "top": 0.85,
                "bottom": 0.92
            }
        }
        
        recommendation = OutfitRecommendationCreate(**recommendation_data)
        assert recommendation.prompt == "I need a casual outfit for weekend"
        assert recommendation.ai_model_used == "casual_model_v1"
        assert recommendation.season == "spring"
        assert recommendation.processing_time_ms == 1500
    
    def test_outfit_recommendation_season_validation(self):
        """Test season validation"""
        recommendation_data = {
            "prompt": "I need an outfit",
            "ai_model_used": "model_v1",
            "ai_response": "Here's an outfit",
            "season": "SPRING"  # Should be converted to lowercase
        }
        
        recommendation = OutfitRecommendationCreate(**recommendation_data)
        assert recommendation.season == "spring"
        
        # Test invalid season
        recommendation_data["season"] = "invalid_season"
        with pytest.raises(ValidationError) as exc_info:
            OutfitRecommendationCreate(**recommendation_data)
        
        assert "Season must be one of" in str(exc_info.value)
    
    def test_recommendation_feedback_create_valid(self):
        """Test valid recommendation feedback creation"""
        feedback_data = {
            "rating": 4,
            "feedback_type": "general",
            "comments": "Great recommendation!",
            "style_accuracy": 5,
            "item_matching": 4,
            "occasion_appropriateness": 4,
            "feedback_tags": ["stylish", "comfortable"]
        }
        
        feedback = RecommendationFeedbackCreate(**feedback_data)
        assert feedback.rating == 4
        assert feedback.feedback_type == "general"
        assert feedback.comments == "Great recommendation!"
        assert feedback.style_accuracy == 5
    
    def test_recommendation_feedback_rating_validation(self):
        """Test feedback rating validation"""
        # Test invalid rating (too low)
        feedback_data = {
            "rating": 0,
            "feedback_type": "general"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RecommendationFeedbackCreate(**feedback_data)
        
        assert "Input should be greater than or equal to 1" in str(exc_info.value)
        
        # Test invalid rating (too high)
        feedback_data["rating"] = 6
        with pytest.raises(ValidationError) as exc_info:
            RecommendationFeedbackCreate(**feedback_data)
        
        assert "Input should be less than or equal to 5" in str(exc_info.value)
    
    def test_recommendation_feedback_type_validation(self):
        """Test feedback type validation"""
        feedback_data = {
            "rating": 4,
            "feedback_type": "invalid_type"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RecommendationFeedbackCreate(**feedback_data)
        
        assert "Feedback type must be one of" in str(exc_info.value)
    
    def test_recommendation_feedback_tags_validation(self):
        """Test feedback tags validation"""
        feedback_data = {
            "rating": 4,
            "feedback_type": "general",
            "feedback_tags": ["stylish", "comfortable", "stylish", ""]
        }
        
        feedback = RecommendationFeedbackCreate(**feedback_data)
        # Should remove duplicates and empty strings
        assert set(feedback.feedback_tags) == {"stylish", "comfortable"}