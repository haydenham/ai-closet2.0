"""
Unit tests for User model and related models
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User, EmailVerificationToken, PasswordResetToken
from app.core.database import Base


class TestUserModel:
    """Test cases for User model"""
    
    def test_create_user(self, db_session: Session):
        """Test creating a new user"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.is_verified is False
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_full_name_property(self, db_session: Session):
        """Test user full_name property"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        
        assert user.full_name == "John Doe"
    
    def test_user_email_unique_constraint(self, db_session: Session):
        """Test that user email must be unique"""
        user1 = User(
            email="test@example.com",
            password_hash="hashed_password1",
            first_name="John",
            last_name="Doe"
        )
        
        user2 = User(
            email="test@example.com",
            password_hash="hashed_password2",
            first_name="Jane",
            last_name="Smith"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_repr(self, db_session: Session):
        """Test user string representation"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        expected_repr = f"<User(id={user.id}, email=test@example.com)>"
        assert repr(user) == expected_repr
    
    def test_user_relationships_initialization(self, db_session: Session):
        """Test that user relationships are properly initialized"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Test that relationships are accessible and empty initially
        assert user.style_profile is None
        assert len(user.clothing_items) == 0
        assert len(user.outfit_recommendations) == 0


class TestEmailVerificationToken:
    """Test cases for EmailVerificationToken model"""
    
    def test_create_email_verification_token(self, db_session: Session):
        """Test creating an email verification token"""
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
        
        # Create verification token
        expires_at = datetime.utcnow() + timedelta(hours=24)
        token = EmailVerificationToken(
            user_id=user.id,
            token="verification_token_123",
            expires_at=expires_at
        )
        
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)
        
        assert token.id is not None
        assert token.user_id == user.id
        assert token.token == "verification_token_123"
        assert token.expires_at == expires_at
        assert token.created_at is not None
    
    def test_email_verification_token_user_relationship(self, db_session: Session):
        """Test email verification token relationship with user"""
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
        
        # Create verification token
        expires_at = datetime.utcnow() + timedelta(hours=24)
        token = EmailVerificationToken(
            user_id=user.id,
            token="verification_token_123",
            expires_at=expires_at
        )
        
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)
        
        # Test relationship
        assert token.user.id == user.id
        assert token.user.email == "test@example.com"
    
    def test_email_verification_token_unique_constraint(self, db_session: Session):
        """Test that verification token must be unique"""
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
        
        # Create first token
        expires_at = datetime.utcnow() + timedelta(hours=24)
        token1 = EmailVerificationToken(
            user_id=user.id,
            token="same_token",
            expires_at=expires_at
        )
        
        # Create second token with same token string
        token2 = EmailVerificationToken(
            user_id=user.id,
            token="same_token",
            expires_at=expires_at
        )
        
        db_session.add(token1)
        db_session.commit()
        
        db_session.add(token2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_email_verification_token_repr(self, db_session: Session):
        """Test email verification token string representation"""
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
        
        # Create verification token
        expires_at = datetime.utcnow() + timedelta(hours=24)
        token = EmailVerificationToken(
            user_id=user.id,
            token="verification_token_123",
            expires_at=expires_at
        )
        
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)
        
        expected_repr = f"<EmailVerificationToken(id={token.id}, user_id={user.id})>"
        assert repr(token) == expected_repr


class TestPasswordResetToken:
    """Test cases for PasswordResetToken model"""
    
    def test_create_password_reset_token(self, db_session: Session):
        """Test creating a password reset token"""
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
        
        # Create reset token
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = PasswordResetToken(
            user_id=user.id,
            token="reset_token_123",
            expires_at=expires_at
        )
        
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)
        
        assert token.id is not None
        assert token.user_id == user.id
        assert token.token == "reset_token_123"
        assert token.expires_at == expires_at
        assert token.created_at is not None
    
    def test_password_reset_token_user_relationship(self, db_session: Session):
        """Test password reset token relationship with user"""
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
        
        # Create reset token
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = PasswordResetToken(
            user_id=user.id,
            token="reset_token_123",
            expires_at=expires_at
        )
        
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)
        
        # Test relationship
        assert token.user.id == user.id
        assert token.user.email == "test@example.com"
    
    def test_password_reset_token_repr(self, db_session: Session):
        """Test password reset token string representation"""
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
        
        # Create reset token
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = PasswordResetToken(
            user_id=user.id,
            token="reset_token_123",
            expires_at=expires_at
        )
        
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)
        
        expected_repr = f"<PasswordResetToken(id={token.id}, user_id={user.id})>"
        assert repr(token) == expected_repr