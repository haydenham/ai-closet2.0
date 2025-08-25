"""
Authentication service for user registration, login, and email verification
"""
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.models.user import User, EmailVerificationToken, PasswordResetToken
from app.schemas.user import UserCreate, UserResponse, TokenResponse, PasswordReset, PasswordResetConfirm


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def generate_verification_token(self) -> str:
        """Generate a secure random token for email verification"""
        return secrets.token_urlsafe(32)
    
    def generate_password_reset_token(self) -> str:
        """Generate a secure random token for password reset"""
        return secrets.token_urlsafe(32)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create a JWT refresh token with longer expiration"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def register_user(
        self, 
        user_data: UserCreate, 
        db: AsyncSession
    ) -> Tuple[UserResponse, str]:
        """
        Register a new user and create email verification token
        
        Args:
            user_data: User registration data
            db: Database session
            
        Returns:
            Tuple of (UserResponse, verification_token)
            
        Raises:
            HTTPException: If email already exists or other validation errors
        """
        # Check if user already exists
        existing_user = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = self.hash_password(user_data.password)
        
        # Create user
        db_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_verified=False,
            is_active=True
        )
        
        try:
            db.add(db_user)
            await db.flush()  # Flush to get the user ID
            
            # Create email verification token
            verification_token = self.generate_verification_token()
            token_expires = datetime.utcnow() + timedelta(hours=24)  # 24 hours to verify
            
            db_token = EmailVerificationToken(
                user_id=db_user.id,
                token=verification_token,
                expires_at=token_expires
            )
            
            db.add(db_token)
            await db.commit()
            
            # Return user response and verification token
            user_response = UserResponse.model_validate(db_user)
            return user_response, verification_token
            
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )

    async def create_user(
        self,
        user_data: "UserCreate | dict",
        db: AsyncSession,
        *,
        verified: bool = False,
        active: bool = True
    ) -> User:
        """Lightweight user creation helper (used in tests).

        NOTE: This bypasses email verification token creation and email sending.

        Args:
            user_data: UserCreate schema instance or dict with keys email, password, first_name, last_name.
            db: Async session.
            verified: Whether to mark the user as verified immediately (tests convenience).
            active: Whether account is active.

        Returns:
            The persisted User model instance.

        Raises:
            HTTPException 400 if email already exists.
            HTTPException 500 for unexpected persistence errors.
        """
        # Normalize input
        if isinstance(user_data, dict):
            email = user_data.get("email")
            password = user_data.get("password")
            first_name = user_data.get("first_name")
            last_name = user_data.get("last_name")
        else:  # Pydantic model
            email = user_data.email
            password = user_data.password
            first_name = user_data.first_name
            last_name = user_data.last_name

        # Basic existence check
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_password = self.hash_password(password)
        db_user = User(
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
            is_verified=verified,
            is_active=active,
        )
        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    async def verify_email(self, token: str, db: AsyncSession) -> UserResponse:
        """
        Verify user email using verification token
        
        Args:
            token: Email verification token
            db: Database session
            
        Returns:
            UserResponse: Updated user data
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        # Find the verification token
        result = await db.execute(
            select(EmailVerificationToken)
            .where(EmailVerificationToken.token == token)
        )
        db_token = result.scalar_one_or_none()
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        # Check if token is expired
        if datetime.utcnow() > db_token.expires_at:
            # Clean up expired token
            await db.delete(db_token)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired"
            )
        
        # Get the user
        result = await db.execute(
            select(User).where(User.id == db_token.user_id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user verification status
        db_user.is_verified = True
        db_user.updated_at = datetime.utcnow()
        
        # Delete the verification token (one-time use)
        await db.delete(db_token)
        
        try:
            await db.commit()
            return UserResponse.model_validate(db_user)
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify email"
            )
    
    async def authenticate_user(self, email: str, password: str, db: AsyncSession) -> Optional[User]:
        """
        Authenticate user with email and password
        
        Args:
            email: User email
            password: User password
            db: Database session
            
        Returns:
            User object if authentication successful, None otherwise
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def create_user_tokens(self, user: User) -> TokenResponse:
        """
        Create access and refresh tokens for user
        
        Args:
            user: User object
            
        Returns:
            TokenResponse with access and refresh tokens
        """
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        refresh_token = self.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60  # Convert to seconds
        )
    
    async def get_current_user(self, token: str, db: AsyncSession) -> User:
        """
        Get current user from JWT token
        
        Args:
            token: JWT access token
            db: Database session
            
        Returns:
            User object
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        try:
            payload = self.verify_token(token)
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    async def request_password_reset(self, email: str, db: AsyncSession) -> bool:
        """
        Create password reset token and send reset email
        
        Args:
            email: User email address
            db: Database session
            
        Returns:
            bool: True if reset email was sent (or user doesn't exist)
            
        Note:
            Always returns True to prevent email enumeration attacks
        """
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal that user doesn't exist - return True anyway
            return True
        
        # Check if user is active and verified
        if not user.is_active or not user.is_verified:
            # Don't send reset email for inactive/unverified users
            return True
        
        try:
            # Delete any existing password reset tokens for this user
            existing_tokens = await db.execute(
                select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
            )
            for token in existing_tokens.scalars():
                await db.delete(token)
            
            # Create new password reset token
            reset_token = self.generate_password_reset_token()
            token_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour to reset
            
            db_token = PasswordResetToken(
                user_id=user.id,
                token=reset_token,
                expires_at=token_expires
            )
            
            db.add(db_token)
            await db.commit()
            
            # Import email service here to avoid circular imports
            from app.services.email_service import email_service
            
            # Send password reset email
            email_sent = email_service.send_password_reset_email(
                email=user.email,
                first_name=user.first_name,
                reset_token=reset_token
            )
            
            if not email_sent:
                # Log warning but don't fail the request
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to send password reset email to {user.email}")
            
            return True
            
        except Exception as e:
            await db.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create password reset token for {email}: {e}")
            # Still return True to prevent information disclosure
            return True
    
    async def reset_password(self, reset_data: PasswordResetConfirm, db: AsyncSession) -> bool:
        """
        Reset user password using reset token
        
        Args:
            reset_data: Password reset confirmation data
            db: Database session
            
        Returns:
            bool: True if password was reset successfully
            
        Raises:
            HTTPException: If token is invalid, expired, or reset fails
        """
        # Find the password reset token
        result = await db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token == reset_data.token)
        )
        db_token = result.scalar_one_or_none()
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Check if token is expired
        if datetime.utcnow() > db_token.expires_at:
            # Clean up expired token
            await db.delete(db_token)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Get the user
        result = await db.execute(
            select(User).where(User.id == db_token.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        try:
            # Update user password
            user.password_hash = self.hash_password(reset_data.new_password)
            user.updated_at = datetime.utcnow()
            
            # Delete the reset token (one-time use)
            await db.delete(db_token)
            
            # Delete any other existing reset tokens for this user
            other_tokens = await db.execute(
                select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
            )
            for token in other_tokens.scalars():
                await db.delete(token)
            
            await db.commit()
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Password reset successfully for user: {user.email}")
            
            return True
            
        except Exception as e:
            await db.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to reset password for user {user.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )


# Create a global instance
auth_service = AuthService()