"""
Tests for authentication API endpoints
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, EmailVerificationToken, PasswordResetToken
from app.services.auth_service import auth_service
from app.schemas.user import UserCreate


class TestAuthAPI:
    """Test cases for authentication API endpoints"""
    
    @pytest.fixture
    async def sample_user(self, async_session: AsyncSession):
        """Create a sample user in the database"""
        password_hash = auth_service.hash_password("TestPassword123")
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
    
    @pytest.fixture
    async def unverified_user(self, async_session: AsyncSession):
        """Create an unverified user in the database"""
        password_hash = auth_service.hash_password("TestPassword123")
        unique_email = f"unverified-{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=unique_email,
            password_hash=password_hash,
            first_name="John",
            last_name="Doe",
            is_verified=False,
            is_active=True
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user
    
    @pytest.fixture
    async def inactive_user(self, async_session: AsyncSession):
        """Create an inactive user in the database"""
        password_hash = auth_service.hash_password("TestPassword123")
        unique_email = f"inactive-{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=unique_email,
            password_hash=password_hash,
            first_name="Inactive",
            last_name="User",
            is_verified=True,
            is_active=False
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user
    
    async def test_login_success(self, async_client: AsyncClient, sample_user: User):
        """Test successful user login"""
        login_data = {
            "email": sample_user.email,
            "password": "TestPassword123"
        }
        
        response = await async_client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0
        
        # Verify tokens are valid
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        
        access_payload = auth_service.verify_token(access_token)
        refresh_payload = auth_service.verify_token(refresh_token)
        
        assert access_payload["sub"] == str(sample_user.id)
        assert access_payload["email"] == sample_user.email
        assert refresh_payload["sub"] == str(sample_user.id)
        assert refresh_payload["email"] == sample_user.email
        assert refresh_payload["type"] == "refresh"
    
    async def test_login_invalid_email(self, async_client: AsyncClient):
        """Test login with invalid email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "TestPassword123"
        }
        
        response = await async_client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Invalid email or password" in data["detail"]
    
    async def test_login_invalid_password(self, async_client: AsyncClient, sample_user: User):
        """Test login with invalid password"""
        login_data = {
            "email": sample_user.email,
            "password": "WrongPassword"
        }
        
        response = await async_client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Invalid email or password" in data["detail"]
    
    async def test_login_unverified_user(self, async_client: AsyncClient, unverified_user: User):
        """Test login with unverified user"""
        login_data = {
            "email": unverified_user.email,
            "password": "TestPassword123"
        }
        
        response = await async_client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "Email address not verified" in data["detail"]
    
    async def test_login_inactive_user(self, async_client: AsyncClient, inactive_user: User):
        """Test login with inactive user"""
        login_data = {
            "email": inactive_user.email,
            "password": "TestPassword123"
        }
        
        response = await async_client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "Account is deactivated" in data["detail"]
    
    async def test_login_invalid_data(self, async_client: AsyncClient):
        """Test login with invalid request data"""
        # Missing password
        response = await async_client.post("/auth/login", json={"email": "test@example.com"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing email
        response = await async_client.post("/auth/login", json={"password": "password"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Invalid email format
        response = await async_client.post("/auth/login", json={
            "email": "invalid-email",
            "password": "password"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_refresh_token_success(self, async_client: AsyncClient, sample_user: User):
        """Test successful token refresh"""
        # First login to get tokens
        login_data = {
            "email": sample_user.email,
            "password": "TestPassword123"
        }
        
        login_response = await async_client.post("/auth/login", json=login_data)
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Use refresh token to get new tokens
        refresh_data = {"refresh_token": refresh_token}
        response = await async_client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        # Verify new tokens are valid
        new_access_token = data["access_token"]
        new_refresh_token = data["refresh_token"]
        
        # Tokens should be valid (we don't check if they're different since 
        # they might be the same if generated at the same second in tests)
        
        access_payload = auth_service.verify_token(new_access_token)
        refresh_payload = auth_service.verify_token(new_refresh_token)
        
        assert access_payload["sub"] == str(sample_user.id)
        assert access_payload["email"] == sample_user.email
        assert refresh_payload["sub"] == str(sample_user.id)
        assert refresh_payload["email"] == sample_user.email
        assert refresh_payload["type"] == "refresh"
    
    async def test_refresh_token_invalid(self, async_client: AsyncClient):
        """Test token refresh with invalid refresh token"""
        refresh_data = {"refresh_token": "invalid_token"}
        response = await async_client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Could not validate credentials" in data["detail"]
    
    async def test_refresh_token_access_token_used(self, async_client: AsyncClient, sample_user: User):
        """Test token refresh using access token instead of refresh token"""
        # Login to get tokens
        login_data = {
            "email": sample_user.email,
            "password": "TestPassword123"
        }
        
        login_response = await async_client.post("/auth/login", json=login_data)
        login_data = login_response.json()
        access_token = login_data["access_token"]
        
        # Try to use access token for refresh (should fail)
        refresh_data = {"refresh_token": access_token}
        response = await async_client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Invalid token type" in data["detail"]
    
    async def test_refresh_token_missing(self, async_client: AsyncClient):
        """Test token refresh with missing refresh token"""
        response = await async_client.post("/auth/refresh", json={})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Refresh token is required" in data["detail"]
    
    async def test_refresh_token_nonexistent_user(self, async_client: AsyncClient):
        """Test token refresh with token for nonexistent user"""
        # Create token with fake user ID
        fake_user_id = str(uuid.uuid4())
        fake_refresh_token = auth_service.create_refresh_token({
            "sub": fake_user_id,
            "email": "fake@example.com"
        })
        
        refresh_data = {"refresh_token": fake_refresh_token}
        response = await async_client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "User not found" in data["detail"]
    
    async def test_get_current_user_success(self, async_client: AsyncClient, sample_user: User):
        """Test getting current user with valid token"""
        # Login to get access token
        login_data = {
            "email": sample_user.email,
            "password": "TestPassword123"
        }
        
        login_response = await async_client.post("/auth/login", json=login_data)
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.get("/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == str(sample_user.id)
        assert data["email"] == sample_user.email
        assert data["first_name"] == sample_user.first_name
        assert data["last_name"] == sample_user.last_name
        assert data["is_verified"] == sample_user.is_verified
        assert data["is_active"] == sample_user.is_active
        assert "created_at" in data
        assert "updated_at" in data
    
    async def test_get_current_user_no_token(self, async_client: AsyncClient):
        """Test getting current user without token"""
        response = await async_client.get("/auth/me")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_get_current_user_invalid_token(self, async_client: AsyncClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.get("/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Could not validate credentials" in data["detail"]
    
    async def test_get_current_user_malformed_header(self, async_client: AsyncClient):
        """Test getting current user with malformed authorization header"""
        # Missing Bearer prefix
        headers = {"Authorization": "invalid_token"}
        response = await async_client.get("/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_logout_success(self, async_client: AsyncClient):
        """Test logout endpoint"""
        response = await async_client.post("/auth/logout")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Successfully logged out" in data["message"]
    
    async def test_login_flow_integration(self, async_client: AsyncClient, sample_user: User):
        """Test complete login flow integration"""
        # 1. Login
        login_data = {
            "email": sample_user.email,
            "password": "TestPassword123"
        }
        
        login_response = await async_client.post("/auth/login", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        tokens = login_response.json()
        
        # 2. Use access token to get user info
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        me_response = await async_client.get("/auth/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK
        user_data = me_response.json()
        assert user_data["email"] == sample_user.email
        
        # 3. Refresh token
        refresh_data = {"refresh_token": tokens["refresh_token"]}
        refresh_response = await async_client.post("/auth/refresh", json=refresh_data)
        assert refresh_response.status_code == status.HTTP_200_OK
        new_tokens = refresh_response.json()
        
        # 4. Use new access token
        new_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
        me_response2 = await async_client.get("/auth/me", headers=new_headers)
        assert me_response2.status_code == status.HTTP_200_OK
        
        # 5. Logout
        logout_response = await async_client.post("/auth/logout")
        assert logout_response.status_code == status.HTTP_200_OK
    
    async def test_concurrent_login_attempts(self, async_client: AsyncClient, sample_user: User):
        """Test concurrent login attempts for the same user"""
        import asyncio
        
        login_data = {
            "email": sample_user.email,
            "password": "TestPassword123"
        }
        
        # Create multiple concurrent login requests
        tasks = [
            async_client.post("/auth/login", json=login_data)
            for _ in range(5)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
    
    async def test_token_expiration_handling(self, async_client: AsyncClient, sample_user: User):
        """Test handling of expired tokens"""
        # Create an expired token
        from datetime import datetime, timedelta
        expired_data = {"sub": str(sample_user.id), "email": sample_user.email}
        expired_token = auth_service.create_access_token(
            expired_data, 
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await async_client.get("/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Could not validate credentials" in data["detail"]
    
    @patch('app.services.email_service.email_service.send_password_reset_email')
    async def test_forgot_password_success(self, mock_send_email, async_client: AsyncClient, sample_user: User):
        """Test successful forgot password request"""
        mock_send_email.return_value = True
        
        request_data = {"email": sample_user.email}
        response = await async_client.post("/auth/forgot-password", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "If the email address exists" in data["message"]
        
        # Verify email was sent
        mock_send_email.assert_called_once()
    
    @patch('app.services.email_service.email_service.send_password_reset_email')
    async def test_forgot_password_nonexistent_email(self, mock_send_email, async_client: AsyncClient):
        """Test forgot password with nonexistent email"""
        mock_send_email.return_value = True
        
        request_data = {"email": "nonexistent@example.com"}
        response = await async_client.post("/auth/forgot-password", json=request_data)
        
        # Should return success to prevent email enumeration
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "If the email address exists" in data["message"]
        
        # No email should be sent
        mock_send_email.assert_not_called()
    
    @patch('app.services.email_service.email_service.send_password_reset_email')
    async def test_forgot_password_unverified_user(self, mock_send_email, async_client: AsyncClient, unverified_user: User):
        """Test forgot password with unverified user"""
        mock_send_email.return_value = True
        
        request_data = {"email": unverified_user.email}
        response = await async_client.post("/auth/forgot-password", json=request_data)
        
        # Should return success to prevent information disclosure
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "If the email address exists" in data["message"]
        
        # No email should be sent for unverified users
        mock_send_email.assert_not_called()
    
    @patch('app.services.email_service.email_service.send_password_reset_email')
    async def test_forgot_password_inactive_user(self, mock_send_email, async_client: AsyncClient, inactive_user: User):
        """Test forgot password with inactive user"""
        mock_send_email.return_value = True
        
        request_data = {"email": inactive_user.email}
        response = await async_client.post("/auth/forgot-password", json=request_data)
        
        # Should return success to prevent information disclosure
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "If the email address exists" in data["message"]
        
        # No email should be sent for inactive users
        mock_send_email.assert_not_called()
    
    async def test_forgot_password_invalid_email_format(self, async_client: AsyncClient):
        """Test forgot password with invalid email format"""
        request_data = {"email": "invalid-email"}
        response = await async_client.post("/auth/forgot-password", json=request_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_forgot_password_missing_email(self, async_client: AsyncClient):
        """Test forgot password with missing email"""
        response = await async_client.post("/auth/forgot-password", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_reset_password_success(self, async_client: AsyncClient, sample_user: User, async_session: AsyncSession):
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
        reset_data = {
            "token": reset_token,
            "new_password": "NewPassword123"
        }
        
        response = await async_client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Password has been reset successfully" in data["message"]
        
        # Verify password was changed
        await async_session.refresh(sample_user)
        assert sample_user.password_hash != original_password_hash
        assert auth_service.verify_password("NewPassword123", sample_user.password_hash)
        
        # Verify user can login with new password
        login_data = {
            "email": sample_user.email,
            "password": "NewPassword123"
        }
        login_response = await async_client.post("/auth/login", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK
    
    async def test_reset_password_invalid_token(self, async_client: AsyncClient):
        """Test password reset with invalid token"""
        reset_data = {
            "token": "invalid_token",
            "new_password": "NewPassword123"
        }
        
        response = await async_client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid or expired reset token" in data["detail"]
    
    async def test_reset_password_expired_token(self, async_client: AsyncClient, sample_user: User, async_session: AsyncSession):
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
        
        reset_data = {
            "token": reset_token,
            "new_password": "NewPassword123"
        }
        
        response = await async_client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Reset token has expired" in data["detail"]
    
    async def test_reset_password_weak_password(self, async_client: AsyncClient, sample_user: User, async_session: AsyncSession):
        """Test password reset with weak password"""
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
        
        # Try to reset with weak password
        reset_data = {
            "token": reset_token,
            "new_password": "weak"
        }
        
        response = await async_client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_reset_password_missing_fields(self, async_client: AsyncClient):
        """Test password reset with missing fields"""
        # Missing token
        response = await async_client.post("/auth/reset-password", json={"new_password": "NewPassword123"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing password
        response = await async_client.post("/auth/reset-password", json={"token": "some_token"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Empty request
        response = await async_client.post("/auth/reset-password", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_reset_password_inactive_user(self, async_client: AsyncClient, inactive_user: User, async_session: AsyncSession):
        """Test password reset for inactive user"""
        # Create password reset token
        reset_token = auth_service.generate_password_reset_token()
        token_expires = datetime.utcnow() + timedelta(hours=1)
        
        db_token = PasswordResetToken(
            user_id=inactive_user.id,
            token=reset_token,
            expires_at=token_expires
        )
        async_session.add(db_token)
        await async_session.commit()
        
        reset_data = {
            "token": reset_token,
            "new_password": "NewPassword123"
        }
        
        response = await async_client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "Account is deactivated" in data["detail"]
    
    async def test_password_reset_flow_integration(self, async_client: AsyncClient, sample_user: User, async_session: AsyncSession):
        """Test complete password reset flow integration"""
        with patch('app.services.email_service.email_service.send_password_reset_email') as mock_send_email:
            mock_send_email.return_value = True
            
            # 1. Request password reset
            request_data = {"email": sample_user.email}
            forgot_response = await async_client.post("/auth/forgot-password", json=request_data)
            assert forgot_response.status_code == status.HTTP_200_OK
            
            # 2. Get the reset token from database (simulating email click)
            result = await async_session.execute(
                select(PasswordResetToken).where(PasswordResetToken.user_id == sample_user.id)
            )
            db_token = result.scalar_one()
            reset_token = db_token.token
            
            # 3. Reset password using token
            reset_data = {
                "token": reset_token,
                "new_password": "NewPassword123"
            }
            reset_response = await async_client.post("/auth/reset-password", json=reset_data)
            assert reset_response.status_code == status.HTTP_200_OK
            
            # 4. Login with new password
            login_data = {
                "email": sample_user.email,
                "password": "NewPassword123"
            }
            login_response = await async_client.post("/auth/login", json=login_data)
            assert login_response.status_code == status.HTTP_200_OK
            
            # 5. Verify old password no longer works
            old_login_data = {
                "email": sample_user.email,
                "password": "TestPassword123"
            }
            old_login_response = await async_client.post("/auth/login", json=old_login_data)
            assert old_login_response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_reset_password_token_single_use(self, async_client: AsyncClient, sample_user: User, async_session: AsyncSession):
        """Test that password reset tokens are single-use"""
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
        
        # First reset should succeed
        reset_data = {
            "token": reset_token,
            "new_password": "NewPassword123"
        }
        
        first_response = await async_client.post("/auth/reset-password", json=reset_data)
        assert first_response.status_code == status.HTTP_200_OK
        
        # Second reset with same token should fail
        reset_data["new_password"] = "AnotherPassword123"
        second_response = await async_client.post("/auth/reset-password", json=reset_data)
        assert second_response.status_code == status.HTTP_400_BAD_REQUEST
        data = second_response.json()
        assert "Invalid or expired reset token" in data["detail"]
    
    async def test_multiple_password_reset_requests(self, async_client: AsyncClient, sample_user: User, async_session: AsyncSession):
        """Test multiple password reset requests replace previous tokens"""
        with patch('app.services.email_service.email_service.send_password_reset_email') as mock_send_email:
            mock_send_email.return_value = True
            
            request_data = {"email": sample_user.email}
            
            # First request
            response1 = await async_client.post("/auth/forgot-password", json=request_data)
            assert response1.status_code == status.HTTP_200_OK
            
            # Get first token
            result = await async_session.execute(
                select(PasswordResetToken).where(PasswordResetToken.user_id == sample_user.id)
            )
            first_token = result.scalar_one().token
            
            # Second request should replace first token
            response2 = await async_client.post("/auth/forgot-password", json=request_data)
            assert response2.status_code == status.HTTP_200_OK
            
            # Get second token
            result = await async_session.execute(
                select(PasswordResetToken).where(PasswordResetToken.user_id == sample_user.id)
            )
            tokens = result.scalars().all()
            assert len(tokens) == 1  # Only one token should exist
            second_token = tokens[0].token
            
            # Tokens should be different
            assert first_token != second_token
            
            # First token should no longer work
            reset_data = {
                "token": first_token,
                "new_password": "NewPassword123"
            }
            response = await async_client.post("/auth/reset-password", json=reset_data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            
            # Second token should work
            reset_data["token"] = second_token
            response = await async_client.post("/auth/reset-password", json=reset_data)
            assert response.status_code == status.HTTP_200_OK