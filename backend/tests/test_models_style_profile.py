"""
Unit tests for StyleProfile model and related models
"""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.style_profile import StyleProfile, QuizQuestion


class TestStyleProfileModel:
    """Test cases for StyleProfile model"""
    
    def test_create_style_profile(self, db_session: Session):
        """Test creating a new style profile"""
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
        
        # Create style profile
        quiz_responses = {
            "style_preference": "casual",
            "color_preference": ["blue", "black"],
            "budget": "medium"
        }
        
        style_profile = StyleProfile(
            user_id=user.id,
            quiz_responses=quiz_responses,
            assigned_model="casual_model_v1",
            style_preferences=["casual", "comfortable"],
            fashion_goals=["versatile", "professional"],
            preferred_colors=["blue", "black", "white"],
            body_type="athletic",
            lifestyle="active",
            budget_range="$100-500"
        )
        
        db_session.add(style_profile)
        db_session.commit()
        db_session.refresh(style_profile)
        
        assert style_profile.id is not None
        assert style_profile.user_id == user.id
        assert style_profile.quiz_responses == quiz_responses
        assert style_profile.assigned_model == "casual_model_v1"
        assert style_profile.style_preferences == ["casual", "comfortable"]
        assert style_profile.fashion_goals == ["versatile", "professional"]
        assert style_profile.preferred_colors == ["blue", "black", "white"]
        assert style_profile.body_type == "athletic"
        assert style_profile.lifestyle == "active"
        assert style_profile.budget_range == "$100-500"
        assert style_profile.created_at is not None
        assert style_profile.updated_at is not None
    
    def test_style_profile_user_relationship(self, db_session: Session):
        """Test style profile relationship with user"""
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
        
        # Create style profile
        style_profile = StyleProfile(
            user_id=user.id,
            quiz_responses={"style": "casual"},
            assigned_model="casual_model_v1",
            style_preferences=["casual"]
        )
        
        db_session.add(style_profile)
        db_session.commit()
        db_session.refresh(style_profile)
        
        # Test relationship
        assert style_profile.user.id == user.id
        assert style_profile.user.email == "test@example.com"
        assert user.style_profile.id == style_profile.id
    
    def test_style_profile_unique_user_constraint(self, db_session: Session):
        """Test that each user can have only one style profile"""
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
        
        # Create first style profile
        style_profile1 = StyleProfile(
            user_id=user.id,
            quiz_responses={"style": "casual"},
            assigned_model="casual_model_v1",
            style_preferences=["casual"]
        )
        
        # Create second style profile for same user
        style_profile2 = StyleProfile(
            user_id=user.id,
            quiz_responses={"style": "formal"},
            assigned_model="formal_model_v1",
            style_preferences=["formal"]
        )
        
        db_session.add(style_profile1)
        db_session.commit()
        
        db_session.add(style_profile2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_get_quiz_response(self, db_session: Session):
        """Test getting specific quiz response"""
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
        
        # Create style profile
        quiz_responses = {
            "style_preference": "casual",
            "color_preference": ["blue", "black"],
            "budget": "medium"
        }
        
        style_profile = StyleProfile(
            user_id=user.id,
            quiz_responses=quiz_responses,
            assigned_model="casual_model_v1",
            style_preferences=["casual"]
        )
        
        db_session.add(style_profile)
        db_session.commit()
        
        # Test getting quiz responses
        assert style_profile.get_quiz_response("style_preference") == "casual"
        assert style_profile.get_quiz_response("color_preference") == ["blue", "black"]
        assert style_profile.get_quiz_response("budget") == "medium"
        assert style_profile.get_quiz_response("nonexistent") is None
    
    def test_update_quiz_response(self, db_session: Session):
        """Test updating quiz response"""
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
        
        # Create style profile
        style_profile = StyleProfile(
            user_id=user.id,
            quiz_responses={"style_preference": "casual"},
            assigned_model="casual_model_v1",
            style_preferences=["casual"]
        )
        
        db_session.add(style_profile)
        db_session.commit()
        
        # Update quiz response
        style_profile.update_quiz_response("style_preference", "formal")
        style_profile.update_quiz_response("new_question", "new_answer")
        
        assert style_profile.get_quiz_response("style_preference") == "formal"
        assert style_profile.get_quiz_response("new_question") == "new_answer"
    
    def test_has_preference(self, db_session: Session):
        """Test checking if user has specific preference"""
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
        
        # Create style profile
        style_profile = StyleProfile(
            user_id=user.id,
            quiz_responses={"style": "casual"},
            assigned_model="casual_model_v1",
            style_preferences=["casual", "comfortable"]
        )
        
        db_session.add(style_profile)
        db_session.commit()
        
        # Test preference checking
        assert style_profile.has_preference("casual") is True
        assert style_profile.has_preference("comfortable") is True
        assert style_profile.has_preference("formal") is False
    
    def test_add_preference(self, db_session: Session):
        """Test adding style preference"""
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
        
        # Create style profile
        style_profile = StyleProfile(
            user_id=user.id,
            quiz_responses={"style": "casual"},
            assigned_model="casual_model_v1",
            style_preferences=["casual"]
        )
        
        db_session.add(style_profile)
        db_session.commit()
        
        # Add preference
        style_profile.add_preference("comfortable")
        assert style_profile.has_preference("comfortable") is True
        assert len(style_profile.style_preferences) == 2
        
        # Adding duplicate should not increase count
        style_profile.add_preference("casual")
        assert len(style_profile.style_preferences) == 2
    
    def test_remove_preference(self, db_session: Session):
        """Test removing style preference"""
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
        
        # Create style profile
        style_profile = StyleProfile(
            user_id=user.id,
            quiz_responses={"style": "casual"},
            assigned_model="casual_model_v1",
            style_preferences=["casual", "comfortable"]
        )
        
        db_session.add(style_profile)
        db_session.commit()
        
        # Remove preference
        style_profile.remove_preference("comfortable")
        assert style_profile.has_preference("comfortable") is False
        assert len(style_profile.style_preferences) == 1
        
        # Removing non-existent preference should not error
        style_profile.remove_preference("formal")
        assert len(style_profile.style_preferences) == 1
    
    def test_style_profile_repr(self, db_session: Session):
        """Test style profile string representation"""
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
        
        # Create style profile
        style_profile = StyleProfile(
            user_id=user.id,
            quiz_responses={"style": "casual"},
            assigned_model="casual_model_v1",
            style_preferences=["casual"]
        )
        
        db_session.add(style_profile)
        db_session.commit()
        db_session.refresh(style_profile)
        
        expected_repr = f"<StyleProfile(id={style_profile.id}, user_id={user.id}, model=casual_model_v1)>"
        assert repr(style_profile) == expected_repr


class TestQuizQuestionModel:
    """Test cases for QuizQuestion model"""
    
    def test_create_quiz_question(self, db_session: Session):
        """Test creating a new quiz question"""
        options = [
            {"value": "casual", "label": "Casual"},
            {"value": "formal", "label": "Formal"},
            {"value": "trendy", "label": "Trendy"}
        ]
        
        question = QuizQuestion(
            question_key="style_preference",
            question_text="What is your preferred style?",
            question_type="single_choice",
            options=options,
            category="style",
            order_index=1
        )
        
        db_session.add(question)
        db_session.commit()
        db_session.refresh(question)
        
        assert question.id is not None
        assert question.question_key == "style_preference"
        assert question.question_text == "What is your preferred style?"
        assert question.question_type == "single_choice"
        assert question.options == options
        assert question.category == "style"
        assert question.order_index == 1
        assert question.is_active is True
        assert question.created_at is not None
        assert question.updated_at is not None
    
    def test_quiz_question_unique_key_constraint(self, db_session: Session):
        """Test that quiz question key must be unique"""
        question1 = QuizQuestion(
            question_key="style_preference",
            question_text="What is your preferred style?",
            question_type="single_choice",
            category="style"
        )
        
        question2 = QuizQuestion(
            question_key="style_preference",
            question_text="Different question text",
            question_type="multiple_choice",
            category="style"
        )
        
        db_session.add(question1)
        db_session.commit()
        
        db_session.add(question2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_quiz_question_repr(self, db_session: Session):
        """Test quiz question string representation"""
        question = QuizQuestion(
            question_key="style_preference",
            question_text="What is your preferred style?",
            question_type="single_choice",
            category="style"
        )
        
        db_session.add(question)
        db_session.commit()
        db_session.refresh(question)
        
        expected_repr = f"<QuizQuestion(id={question.id}, key=style_preference)>"
        assert repr(question) == expected_repr