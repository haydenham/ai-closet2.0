"""
Authentication API endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.schemas.user import (
    UserResponse, 
    TokenResponse,
    EmailVerification
)
from app.schemas.security import (
    SecureUserCreate,
    SecureUserLogin,
    SecurePasswordReset,
    SecurePasswordResetConfirm
)
from app.services.auth_service import auth_service
from app.services.email_service import email_service
from app.core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: SecureUserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Register a new user account
    
    Creates a new user account with email verification required.
    Sends a verification email to the provided email address.
    
    Args:
        user_data: User registration data including email, password, and names
        db: Database session dependency
        
    Returns:
        UserResponse: Created user data (without password)
        
    Raises:
        HTTPException 400: If email already exists or validation fails
        HTTPException 500: If user creation fails
    """
    try:
        # Register user and get verification token
        user_response, verification_token = await auth_service.register_user(user_data, db)
        
        # Send verification email
        email_sent = email_service.send_verification_email(
            email=user_data.email,
            first_name=user_data.first_name,
            verification_token=verification_token
        )
        
        if not email_sent:
            logger.warning(f"Failed to send verification email to {user_data.email}")
            # Don't fail registration if email sending fails
        
        logger.info(f"User registered successfully: {user_data.email}")
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/verify-email", response_model=UserResponse)
async def verify_email(
    verification_data: EmailVerification,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Verify user email address
    
    Verifies the user's email address using the verification token
    sent during registration.
    
    Args:
        verification_data: Email verification data containing the token
        db: Database session dependency
        
    Returns:
        UserResponse: Updated user data with verified status
        
    Raises:
        HTTPException 400: If token is invalid or expired
        HTTPException 404: If user not found
        HTTPException 500: If verification fails
    """
    try:
        user_response = await auth_service.verify_email(verification_data.token, db)
        logger.info(f"Email verified successfully for user: {user_response.email}")
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during email verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: SecureUserLogin,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Authenticate user and return access tokens
    
    Authenticates user credentials and returns JWT access and refresh tokens.
    User must have verified their email address to login.
    
    Args:
        login_data: User login credentials (email and password)
        db: Database session dependency
        
    Returns:
        TokenResponse: JWT access and refresh tokens
        
    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 403: If email is not verified
        HTTPException 500: If authentication fails
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
            db=db
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Check if email is verified
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email address not verified. Please check your email and verify your account."
            )
        
        # Create tokens
        tokens = await auth_service.create_user_tokens(user)
        
        logger.info(f"User logged in successfully: {user.email}")
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during user login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate user"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: dict,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Refresh access token using refresh token
    
    Creates a new access token using a valid refresh token.
    
    Args:
        refresh_data: Dictionary containing refresh_token
        db: Database session dependency
        
    Returns:
        TokenResponse: New JWT access and refresh tokens
        
    Raises:
        HTTPException 401: If refresh token is invalid
        HTTPException 404: If user not found
        HTTPException 500: If token refresh fails
    """
    try:
        refresh_token = refresh_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )
        
        # Verify refresh token
        payload = auth_service.verify_token(refresh_token)
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Get user
        user = await auth_service.get_current_user(refresh_token, db)
        
        # Create new tokens
        tokens = await auth_service.create_user_tokens(user)
        
        logger.info(f"Token refreshed successfully for user: {user.email}")
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user),
):
    """
    Get current authenticated user information
    
    Returns the current user's profile information based on the
    provided JWT access token.
    
    Args:
        current_user: Current authenticated user dependency
        
    Returns:
        UserResponse: Current user's profile data
        
    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout_user():
    """
    Logout user (client-side token removal)
    
    Since JWT tokens are stateless, logout is handled client-side
    by removing the tokens from storage. This endpoint exists for
    consistency and potential future server-side token blacklisting.
    
    Returns:
        dict: Success message
    """
    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
async def forgot_password(
    reset_request: SecurePasswordReset,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Request password reset
    
    Sends a password reset email to the user if the email exists.
    Always returns success to prevent email enumeration attacks.
    
    Args:
        reset_request: Password reset request data containing email
        db: Database session dependency
        
    Returns:
        dict: Success message
        
    Note:
        This endpoint always returns success, regardless of whether
        the email exists, to prevent email enumeration attacks.
    """
    try:
        await auth_service.request_password_reset(reset_request.email, db)
        
        logger.info(f"Password reset requested for email: {reset_request.email}")
        return {
            "message": "If the email address exists in our system, you will receive a password reset link shortly."
        }
        
    except Exception as e:
        logger.error(f"Unexpected error during password reset request: {e}")
        # Still return success message to prevent information disclosure
        return {
            "message": "If the email address exists in our system, you will receive a password reset link shortly."
        }


@router.post("/reset-password")
async def reset_password(
    reset_data: SecurePasswordResetConfirm,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Reset password using reset token
    
    Resets the user's password using a valid reset token received via email.
    The token is single-use and expires after 1 hour.
    
    Args:
        reset_data: Password reset confirmation data containing token and new password
        db: Database session dependency
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException 400: If token is invalid or expired
        HTTPException 403: If account is deactivated
        HTTPException 404: If user not found
        HTTPException 500: If password reset fails
    """
    try:
        success = await auth_service.reset_password(reset_data, db)
        
        if success:
            logger.info("Password reset completed successfully")
            return {"message": "Password has been reset successfully. You can now log in with your new password."}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during password reset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )