"""
Tests for authentication service
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.auth_service import AuthService
from app.models.user import User, EmailVerificationToken, PasswordResetToken
from app.schemas.user import UserCreate, PasswordReset, PasswordResetConfirm


class TestAuthService:
    """Test cases for AuthService"""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance for testing"""
        return AuthService()
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user registration data"""
        return UserCreate(
            email="test@example.com",
            password="TestPassword123",
            first_name="John",
            last_name="Doe"
        )
    
    @pytest.fixture
    async def sample_user(self, async_session: AsyncSession, auth_service):
        """Create a sample user in the database"""
        # Create a proper bcrypt hash for testing
        password_hash = auth_service.hash_password("TestPassword123")
        # Use a unique email for each test to avoid conflicts
        import uuid
        unique_email = f"user-{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=unique_email,
            password_hash=password_hash,
            first_name="Jane",
            last_name="Smith",
            is_verified=True,
            is_active=True
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user
    
    def test_hash_password(self, auth_service):
        """Test password hashing"""
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are typically 60 characters
        assert hashed.startswith("$2b$")
    
    def test_verify_password(self, auth_service):
        """Test password verification"""
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)
        
        # Correct password should verify
        assert auth_service.verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert auth_service.verify_password("WrongPassword", hashed) is False
    
    def test_generate_verification_token(self, auth_service):
        """Test verification token generation"""
        token1 = auth_service.generate_verification_token()
        token2 = auth_service.generate_verification_token()
        
        assert len(token1) > 20  # Should be a reasonable length
        assert len(token2) > 20
        assert token1 != token2  # Should be unique
        assert isinstance(token1, str)
        assert isinstance(token2, str)
    
    def test_generate_password_reset_token(self, auth_service):
        """Test password reset token generation"""
        token1 = auth_service.generate_password_reset_token()
        token2 = auth_service.generate_password_reset_token()
        
        assert len(token1) > 20  # Should be a reasonable length
        assert len(token2) > 20
        assert token1 != token2  # Should be unique
        assert isinstance(token1, str)
        assert isinstance(token2, str)
    
    def test_create_access_token(self, auth_service):
        """Test JWT access token creation"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = auth_service.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long
        
        # Verify token can be decoded
        payload = auth_service.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload
    
    def test_create_refresh_token(self, auth_service):
        """Test JWT refresh token creation"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = auth_service.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
        
        # Verify token can be decoded and has correct type
        payload = auth_service.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "refresh"
        assert "exp" in payload
    
    def test_verify_token_invalid(self, auth_service):
        """Test token verification with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token("invalid_token")
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    async def test_register_user_success(self, auth_service, sample_user_data, async_session):
        """Test successful user registration"""
        user_response, verification_token = await auth_service.register_user(
            sample_user_data, async_session
        )
        
        # Check user response
        assert user_response.email == sample_user_data.email
        assert user_response.first_name == sample_user_data.first_name
        assert user_response.last_name == sample_user_data.last_name
        assert user_response.is_verified is False
        assert user_response.is_active is True
        
        # Check verification token
        assert isinstance(verification_token, str)
        assert len(verification_token) > 20
        
        # Verify user was created in database
        result = await async_session.execute(
            select(User).where(User.email == sample_user_data.email)
        )
        db_user = result.scalar_one_or_none()
        assert db_user is not None
        assert db_user.email == sample_user_data.email
        assert db_user.is_verified is False
        
        # Verify verification token was created
        result = await async_session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == db_user.id
            )
        )
        db_token = result.scalar_one_or_none()
        assert db_token is not None
        assert db_token.token == verification_token
    
    async def test_register_user_duplicate_email(self, auth_service, sample_user, async_session):
        """Test user registration with duplicate email"""
        duplicate_data = UserCreate(
            email=sample_user.email,
            password="TestPassword123",
            first_name="John",
            last_name="Doe"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user(duplicate_data, async_session)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    async def test_verify_email_success(self, auth_service, sample_user, async_session):
        """Test successful email verification"""
        # Create verification token
        verification_token = auth_service.generate_verification_token()
        token_expires = datetime.utcnow() + timedelta(hours=24)
        
        db_token = EmailVerificationToken(
            user_id=sample_user.id,
            token=verification_token,
            expires_at=token_expires
        )
        async_session.add(db_token)
        
        # Set user as unverified
        sample_user.is_verified = False
        await async_session.commit()
        
        # Verify email
        user_response = await auth_service.verify_email(verification_token, async_session)
        
        assert user_response.is_verified is True
        assert user_response.email == sample_user.email
        
        # Verify token was deleted
        result = await async_session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token == verification_token
            )
        )
        assert result.scalar_one_or_none() is None
    
    async def test_verify_email_invalid_token(self, auth_service, async_session):
        """Test email verification with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.verify_email("invalid_token", async_session)
        
        assert exc_info.value.status_code == 400
        assert "Invalid verification token" in str(exc_info.value.detail)
    
    async def test_verify_email_expired_token(self, auth_service, sample_user, async_session):
        """Test email verification with expired token"""
        # Create expired verification token
        verification_token = auth_service.generate_verification_token()
        token_expires = datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        
        db_token = EmailVerificationToken(
            user_id=sample_user.id,
            token=verification_token,
            expires_at=token_expires
        )
        async_session.add(db_token)
        await async_session.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.verify_email(verification_token, async_session)
        
        assert exc_info.value.status_code == 400
        assert "Verification token has expired" in str(exc_info.value.detail)
        
        # Verify expired token was deleted
        result = await async_session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token == verification_token
            )
        )
        assert result.scalar_one_or_none() is None
    
    async def test_authenticate_user_success(self, auth_service, async_session):
        """Test successful user authentication"""
        # Create user with known password
        password = "TestPassword123"
        hashed_password = auth_service.hash_password(password)
        
        user = User(
            email="auth@example.com",
            password_hash=hashed_password,
            first_name="Auth",
            last_name="User",
            is_verified=True,
            is_active=True
        )
        async_session.add(user)
        await async_session.commit()
        
        # Authenticate user
        authenticated_user = await auth_service.authenticate_user(
            "auth@example.com", password, async_session
        )
        
        assert authenticated_user is not None
        assert authenticated_user.email == "auth@example.com"
        assert authenticated_user.first_name == "Auth"
    
    async def test_authenticate_user_wrong_password(self, auth_service, sample_user, async_session):
        """Test authentication with wrong password"""
        authenticated_user = await auth_service.authenticate_user(
            sample_user.email, "WrongPassword", async_session
        )
        
        assert authenticated_user is None
    
    async def test_authenticate_user_nonexistent(self, auth_service, async_session):
        """Test authentication with nonexistent user"""
        authenticated_user = await auth_service.authenticate_user(
            "nonexistent@example.com", "password", async_session
        )
        
        assert authenticated_user is None
    
    async def test_create_user_tokens(self, auth_service, sample_user):
        """Test creating user tokens"""
        tokens = await auth_service.create_user_tokens(sample_user)
        
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in > 0
        
        # Verify tokens can be decoded
        access_payload = auth_service.verify_token(tokens.access_token)
        refresh_payload = auth_service.verify_token(tokens.refresh_token)
        
        assert access_payload["sub"] == str(sample_user.id)
        assert access_payload["email"] == sample_user.email
        assert refresh_payload["sub"] == str(sample_user.id)
        assert refresh_payload["email"] == sample_user.email
        assert refresh_payload["type"] == "refresh"
    
    async def test_get_current_user_success(self, auth_service, sample_user, async_session):
        """Test getting current user from valid token"""
        # Create token for user
        tokens = await auth_service.create_user_tokens(sample_user)
        
        # Get current user
        current_user = await auth_service.get_current_user(
            tokens.access_token, async_session
        )
        
        assert current_user.id == sample_user.id
        assert current_user.email == sample_user.email
    
    async def test_get_current_user_invalid_token(self, auth_service, async_session):
        """Test getting current user with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_current_user("invalid_token", async_session)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    async def test_get_current_user_nonexistent_user(self, auth_service, async_session):
        """Test getting current user when user doesn't exist"""
        # Create token with fake user ID
        fake_user_id = str(uuid.uuid4())
        token = auth_service.create_access_token({
            "sub": fake_user_id,
            "email": "fake@example.com"
        })
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_current_user(token, async_session)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)
    
    def test_create_access_token_with_custom_expiration(self, auth_service):
        """Test JWT access token creation with custom expiration"""
        from datetime import timedelta
        
        data = {"sub": "user123", "email": "test@example.com"}
        custom_expiration = timedelta(minutes=60)
        token = auth_service.create_access_token(data, expires_delta=custom_expiration)
        
        assert isinstance(token, str)
        assert len(token) > 50
        
        # Verify token can be decoded and has correct expiration
        payload = auth_service.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload
    
    def test_verify_token_expired(self, auth_service):
        """Test token verification with expired token"""
        from datetime import timedelta
        
        # Create an already expired token
        data = {"sub": "user123", "email": "test@example.com"}
        expired_token = auth_service.create_access_token(
            data, 
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token(expired_token)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    def test_refresh_token_properties(self, auth_service):
        """Test refresh token has correct properties"""
        data = {"sub": "user123", "email": "test@example.com"}
        refresh_token = auth_service.create_refresh_token(data)
        
        payload = auth_service.verify_token(refresh_token)
        
        # Refresh token should have longer expiration than access token
        import time
        refresh_exp = payload["exp"]
        current_time = time.time()
        
        # Should expire more than 1 day from now (refresh tokens are 7 days)
        assert refresh_exp > current_time + (24 * 60 * 60)
        assert payload["type"] == "refresh"
    
    async def test_get_current_user_token_without_sub(self, auth_service, async_session):
        """Test getting current user with token missing 'sub' claim"""
        # Create token without 'sub' claim
        from jose import jwt
        
        token_data = {"email": "test@example.com"}
        token = jwt.encode(token_data, auth_service.secret_key, algorithm=auth_service.algorithm)
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_current_user(token, async_session)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    @patch('app.services.email_service.email_service.send_password_reset_email')
    async def test_request_password_reset_success(self, mock_send_email, auth_service, sample_user, async_session):
        """Test successful password reset request"""
        mock_send_email.return_value = True
        
        result = await auth_service.request_password_reset(sample_user.email, async_session)
        
        assert result is True
        
        # Verify password reset token was created
        result = await async_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.user_id == sample_user.id)
        )
        db_token = result.scalar_one_or_none()
        assert db_token is not None
        assert len(db_token.token) > 20
        assert db_token.expires_at > datetime.utcnow()
        
        # Verify email was sent
        mock_send_email.assert_called_once_with(
            email=sample_user.email,
            first_name=sample_user.first_name,
            reset_token=db_token.token
        )
    
    @patch('app.services.email_service.email_service.send_password_reset_email')
    async def test_request_password_reset_nonexistent_user(self, mock_send_email, auth_service, async_session):
        """Test password reset request for nonexistent user"""
        mock_send_email.return_value = True
        
        result = await auth_service.request_password_reset("nonexistent@example.com", async_session)
        
        # Should return True to prevent email enumeration
        assert result is True
        
        # No email should be sent
        mock_send_email.assert_not_called()
        
        # No token should be created
        result = await async_session.execute(select(PasswordResetToken))
        tokens = result.scalars().all()
        assert len(tokens) == 0
    
    @patch('app.services.email_service.email_service.send_password_reset_email')
    async def test_request_password_reset_unverified_user(self, mock_send_email, auth_service, async_session):
        """Test password reset request for unverified user"""
        mock_send_email.return_value = True
        
        # Create unverified user
        password_hash = auth_service.hash_password("TestPassword123")
        user = User(
            email="unverified@example.com",
            password_hash=password_hash,
            first_name="Unverified",
            last_name="User",
            is_verified=False,
            is_active=True
        )
        async_session.add(user)
        await async_session.commit()
        
        result = await auth_service.request_password_reset(user.email, async_session)
        
        # Should return True to prevent information disclosure
        assert result is True
        
        # No email should be sent for unverified users
        mock_send_email.assert_not_called()
    
    @patch('app.services.email_service.email_service.send_password_reset_email')
    async def test_request_password_reset_inactive_user(self, mock_send_email, auth_service, async_session):
        """Test password reset request for inactive user"""
        mock_send_email.return_value = True
        
        # Create inactive user
        password_hash = auth_service.hash_password("TestPassword123")
        user = User(
            email="inactive@example.com",
            password_hash=password_hash,
            first_name="Inactive",
            last_name="User",
            is_verified=True,
            is_active=False
        )
        async_session.add(user)
        await async_session.commit()
        
        result = await auth_service.request_password_reset(user.email, async_session)
        
        # Should return True to prevent information disclosure
        assert result is True
        
        # No email should be sent for inactive users
        mock_send_email.assert_not_called()
    
    @patch('app.services.email_service.email_service.send_password_reset_email')
    async def test_request_password_reset_replaces_existing_token(self, mock_send_email, auth_service, sample_user, async_session):
        """Test that new password reset request replaces existing token"""
        mock_send_email.return_value = True
        
        # Create existing password reset token
        old_token = auth_service.generate_password_reset_token()
        old_db_token = PasswordResetToken(
            user_id=sample_user.id,
            token=old_token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        async_session.add(old_db_token)
        await async_session.commit()
        
        # Request new password reset
        result = await auth_service.request_password_reset(sample_user.email, async_session)
        
        assert result is True
        
        # Verify old token was deleted and new one created
        result = await async_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.user_id == sample_user.id)
        )
        tokens = result.scalars().all()
        assert len(tokens) == 1
        assert tokens[0].token != old_token
        
        # Verify email was sent with new token
        mock_send_email.assert_called_once()
    
    @patch('app.services.email_service.email_service.send_password_reset_email')
    async def test_request_password_reset_email_failure(self, mock_send_email, auth_service, sample_user, async_session):
        """Test password reset request when email sending fails"""
        mock_send_email.return_value = False
        
        result = await auth_service.request_password_reset(sample_user.email, async_session)
        
        # Should still return True even if email fails
        assert result is True
        
        # Token should still be created
        result = await async_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.user_id == sample_user.id)
        )
        db_token = result.scalar_one_or_none()
        assert db_token is not None
    
    async def test_reset_password_success(self, auth_service, sample_user, async_session):
        """Test successful password reset"""
        # Create password reset token
        reset_token = auth_service.generate_password_reset_token()
        token_expires = datetime.utcnow() + timedelta(hours=1)
        
        db_token = PasswordResetToken(
            user_id=sample_user.id,
            token=reset_token,
            expires_at=token_expires
        )
        async_session.add(db_token)
        await async_session.commit()
        
        # Store original password hash
        original_password_hash = sample_user.password_hash
        
        # Reset password
        reset_data = PasswordResetConfirm(
            token=reset_token,
            new_password="NewPassword123"
        )
        
        result = await auth_service.reset_password(reset_data, async_session)
        
        assert result is True
        
        # Verify password was changed
        await async_session.refresh(sample_user)
        assert sample_user.password_hash != original_password_hash
        assert auth_service.verify_password("NewPassword123", sample_user.password_hash)
        
        # Verify token was deleted
        result = await async_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == reset_token)
        )
        assert result.scalar_one_or_none() is None
    
    async def test_reset_password_invalid_token(self, auth_service, async_session):
        """Test password reset with invalid token"""
        reset_data = PasswordResetConfirm(
            token="invalid_token",
            new_password="NewPassword123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.reset_password(reset_data, async_session)
        
        assert exc_info.value.status_code == 400
        assert "Invalid or expired reset token" in str(exc_info.value.detail)
    
    async def test_reset_password_expired_token(self, auth_service, sample_user, async_session):
        """Test password reset with expired token"""
        # Create expired password reset token
        reset_token = auth_service.generate_password_reset_token()
        token_expires = datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        
        db_token = PasswordResetToken(
            user_id=sample_user.id,
            token=reset_token,
            expires_at=token_expires
        )
        async_session.add(db_token)
        await async_session.commit()
        
        reset_data = PasswordResetConfirm(
            token=reset_token,
            new_password="NewPassword123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.reset_password(reset_data, async_session)
        
        assert exc_info.value.status_code == 400
        assert "Reset token has expired" in str(exc_info.value.detail)
        
        # Verify expired token was deleted
        result = await async_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == reset_token)
        )
        assert result.scalar_one_or_none() is None
    
    async def test_reset_password_inactive_user(self, auth_service, async_session):
        """Test password reset for inactive user"""
        # Create inactive user
        password_hash = auth_service.hash_password("TestPassword123")
        user = User(
            email="inactive@example.com",
            password_hash=password_hash,
            first_name="Inactive",
            last_name="User",
            is_verified=True,
            is_active=False
        )
        async_session.add(user)
        await async_session.commit()
        
        # Create password reset token
        reset_token = auth_service.generate_password_reset_token()
        token_expires = datetime.utcnow() + timedelta(hours=1)
        
        db_token = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=token_expires
        )
        async_session.add(db_token)
        await async_session.commit()
        
        reset_data = PasswordResetConfirm(
            token=reset_token,
            new_password="NewPassword123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.reset_password(reset_data, async_session)
        
        assert exc_info.value.status_code == 403
        assert "Account is deactivated" in str(exc_info.value.detail)
    
    async def test_reset_password_nonexistent_user(self, auth_service, async_session):
        """Test password reset when user doesn't exist"""
        # Create password reset token with fake user ID
        fake_user_id = uuid.uuid4()
        reset_token = auth_service.generate_password_reset_token()
        token_expires = datetime.utcnow() + timedelta(hours=1)
        
        db_token = PasswordResetToken(
            user_id=fake_user_id,
            token=reset_token,
            expires_at=token_expires
        )
        async_session.add(db_token)
        await async_session.commit()
        
        reset_data = PasswordResetConfirm(
            token=reset_token,
            new_password="NewPassword123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.reset_password(reset_data, async_session)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)
    
    async def test_reset_password_removes_all_user_tokens(self, auth_service, sample_user, async_session):
        """Test that password reset removes all reset tokens for the user"""
        # Create multiple password reset tokens for the user
        tokens = []
        for i in range(3):
            reset_token = auth_service.generate_password_reset_token()
            token_expires = datetime.utcnow() + timedelta(hours=1)
            
            db_token = PasswordResetToken(
                user_id=sample_user.id,
                token=reset_token,
                expires_at=token_expires
            )
            async_session.add(db_token)
            tokens.append(reset_token)
        
        await async_session.commit()
        
        # Use the first token to reset password
        reset_data = PasswordResetConfirm(
            token=tokens[0],
            new_password="NewPassword123"
        )
        
        result = await auth_service.reset_password(reset_data, async_session)
        
        assert result is True
        
        # Verify all tokens were deleted
        result = await async_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.user_id == sample_user.id)
        )
        remaining_tokens = result.scalars().all()
        assert len(remaining_tokens) == 0