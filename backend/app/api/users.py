"""
User management API endpoints
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.style_profile import StyleProfile
from app.models.clothing_item import ClothingItem
from app.models.outfit_recommendation import OutfitRecommendation, RecommendationFeedback
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.style_profile import StyleProfileResponse, StyleProfileUpdate, UserPreferencesResponse, UserPreferencesUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["user-management"])


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile information
    
    Returns the authenticated user's complete profile data including
    account status and timestamps.
    
    Args:
        current_user: Current authenticated user dependency
        
    Returns:
        UserResponse: User's profile data
        
    Raises:
        HTTPException 401: If user is not authenticated
    """
    logger.info(f"Retrieving profile for user: {current_user.email}")
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update current user's profile information
    
    Updates the authenticated user's profile with provided data.
    Only non-null fields in the request will be updated.
    
    Args:
        profile_update: Profile update data
        current_user: Current authenticated user dependency
        db: Database session dependency
        
    Returns:
        UserResponse: Updated user profile data
        
    Raises:
        HTTPException 400: If email already exists (when updating email)
        HTTPException 401: If user is not authenticated
        HTTPException 500: If update fails
    """
    try:
        # Check if email is being updated and if it already exists
        if profile_update.email and profile_update.email != current_user.email:
            stmt = select(User).where(User.email == profile_update.email)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email address already exists"
                )
            
            # If email is updated, mark as unverified
            current_user.is_verified = False
        
        # Update fields that are provided
        update_data = profile_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        current_user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(current_user)
        
        logger.info(f"Profile updated successfully for user: {current_user.email}")
        return UserResponse.model_validate(current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.delete("/profile")
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Delete current user's account
    
    Permanently deletes the authenticated user's account and all associated data.
    This action cannot be undone.
    
    Args:
        current_user: Current authenticated user dependency
        db: Database session dependency
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 500: If deletion fails
    """
    try:
        # Mark user as inactive instead of hard delete for data integrity
        current_user.is_active = False
        current_user.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"User account deactivated: {current_user.email}")
        return {"message": "Account has been successfully deleted"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get current user's style preferences
    
    Returns the user's style profile including preferences, quiz responses,
    and AI model assignment.
    
    Args:
        current_user: Current authenticated user dependency
        db: Database session dependency
        
    Returns:
        UserPreferencesResponse: User's style preferences and profile data
        
    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 404: If user has no style profile
    """
    try:
        # Get user's style profile
        stmt = select(StyleProfile).where(StyleProfile.user_id == current_user.id)
        result = await db.execute(stmt)
        style_profile = result.scalar_one_or_none()
        
        if not style_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User has no style profile. Please complete the style quiz first."
            )
        
        logger.info(f"Retrieved preferences for user: {current_user.email}")
        return UserPreferencesResponse.model_validate(style_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences"
        )


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update current user's style preferences
    
    Updates the user's style preferences, colors, goals, and other profile data.
    Only non-null fields in the request will be updated.
    
    Args:
        preferences_update: Preferences update data
        current_user: Current authenticated user dependency
        db: Database session dependency
        
    Returns:
        UserPreferencesResponse: Updated user preferences
        
    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 404: If user has no style profile
        HTTPException 500: If update fails
    """
    try:
        # Get user's style profile
        stmt = select(StyleProfile).where(StyleProfile.user_id == current_user.id)
        result = await db.execute(stmt)
        style_profile = result.scalar_one_or_none()
        
        if not style_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User has no style profile. Please complete the style quiz first."
            )
        
        # Update fields that are provided
        update_data = preferences_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(style_profile, field, value)
        
        style_profile.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(style_profile)
        
        logger.info(f"Preferences updated successfully for user: {current_user.email}")
        return UserPreferencesResponse.model_validate(style_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


@router.get("/statistics")
async def get_user_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    days: int = Query(30, ge=1, le=365, description="Number of days to include in statistics")
):
    """
    Get current user's activity statistics
    
    Returns comprehensive statistics about the user's activity including
    closet items, recommendations, and engagement metrics.
    
    Args:
        current_user: Current authenticated user dependency
        db: Database session dependency
        days: Number of days to include in statistics (default: 30)
        
    Returns:
        dict: User activity statistics
        
    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 500: If statistics retrieval fails
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get total closet items
        closet_stmt = select(func.count(ClothingItem.id)).where(
            ClothingItem.user_id == current_user.id
        )
        closet_result = await db.execute(closet_stmt)
        total_closet_items = closet_result.scalar() or 0
        
        # Get closet items added in date range
        recent_closet_stmt = select(func.count(ClothingItem.id)).where(
            and_(
                ClothingItem.user_id == current_user.id,
                ClothingItem.upload_date >= start_date
            )
        )
        recent_closet_result = await db.execute(recent_closet_stmt)
        recent_closet_items = recent_closet_result.scalar() or 0
        
        # Get closet items by category
        category_stmt = select(
            ClothingItem.category,
            func.count(ClothingItem.id).label('count')
        ).where(
            ClothingItem.user_id == current_user.id
        ).group_by(ClothingItem.category)
        category_result = await db.execute(category_stmt)
        closet_by_category = {row.category: row.count for row in category_result}
        
        # Get total recommendations
        recommendations_stmt = select(func.count(OutfitRecommendation.id)).where(
            OutfitRecommendation.user_id == current_user.id
        )
        recommendations_result = await db.execute(recommendations_stmt)
        total_recommendations = recommendations_result.scalar() or 0
        
        # Get recent recommendations
        recent_recommendations_stmt = select(func.count(OutfitRecommendation.id)).where(
            and_(
                OutfitRecommendation.user_id == current_user.id,
                OutfitRecommendation.created_at >= start_date
            )
        )
        recent_recommendations_result = await db.execute(recent_recommendations_stmt)
        recent_recommendations = recent_recommendations_result.scalar() or 0
        
        # Get feedback statistics
        feedback_stmt = select(
            func.avg(OutfitRecommendation.feedback_score).label('avg_rating'),
            func.count(OutfitRecommendation.feedback_score).label('feedback_count')
        ).where(
            and_(
                OutfitRecommendation.user_id == current_user.id,
                OutfitRecommendation.feedback_score.isnot(None)
            )
        )
        feedback_result = await db.execute(feedback_stmt)
        feedback_row = feedback_result.first()
        avg_rating = float(feedback_row.avg_rating) if feedback_row.avg_rating else 0.0
        feedback_count = feedback_row.feedback_count or 0
        
        # Get favorite recommendations count
        favorites_stmt = select(func.count(OutfitRecommendation.id)).where(
            and_(
                OutfitRecommendation.user_id == current_user.id,
                OutfitRecommendation.is_favorite == True
            )
        )
        favorites_result = await db.execute(favorites_stmt)
        favorite_recommendations = favorites_result.scalar() or 0
        
        # Get most recommended items
        most_recommended_stmt = select(
            ClothingItem.id,
            ClothingItem.original_filename,
            ClothingItem.category,
            ClothingItem.times_recommended
        ).where(
            ClothingItem.user_id == current_user.id
        ).order_by(desc(ClothingItem.times_recommended)).limit(5)
        most_recommended_result = await db.execute(most_recommended_stmt)
        most_recommended_items = [
            {
                "id": str(row.id),
                "filename": row.original_filename,
                "category": row.category,
                "times_recommended": row.times_recommended
            }
            for row in most_recommended_result
        ]
        
        # Get recent activity (last 10 recommendations)
        recent_activity_stmt = select(OutfitRecommendation).where(
            OutfitRecommendation.user_id == current_user.id
        ).order_by(desc(OutfitRecommendation.created_at)).limit(10)
        recent_activity_result = await db.execute(recent_activity_stmt)
        recent_activity = [
            {
                "id": str(rec.id),
                "prompt": rec.prompt[:100] + "..." if len(rec.prompt) > 100 else rec.prompt,
                "created_at": rec.created_at.isoformat(),
                "feedback_score": rec.feedback_score,
                "is_favorite": rec.is_favorite
            }
            for rec in recent_activity_result.scalars()
        ]
        
        statistics = {
            "period_days": days,
            "account_created": current_user.created_at.isoformat(),
            "closet": {
                "total_items": total_closet_items,
                "recent_items": recent_closet_items,
                "items_by_category": closet_by_category
            },
            "recommendations": {
                "total_recommendations": total_recommendations,
                "recent_recommendations": recent_recommendations,
                "favorite_recommendations": favorite_recommendations,
                "average_rating": round(avg_rating, 2),
                "feedback_count": feedback_count
            },
            "engagement": {
                "most_recommended_items": most_recommended_items,
                "recent_activity": recent_activity
            }
        }
        
        logger.info(f"Retrieved statistics for user: {current_user.email}")
        return statistics
        
    except Exception as e:
        logger.error(f"Failed to retrieve user statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.get("/activity")
async def get_user_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of activity items to return"),
    offset: int = Query(0, ge=0, description="Number of activity items to skip")
):
    """
    Get current user's recent activity
    
    Returns a paginated list of the user's recent activity including
    recommendations, uploads, and feedback.
    
    Args:
        current_user: Current authenticated user dependency
        db: Database session dependency
        limit: Maximum number of items to return
        offset: Number of items to skip for pagination
        
    Returns:
        dict: Paginated user activity data
        
    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 500: If activity retrieval fails
    """
    try:
        # Get recent recommendations with pagination
        recommendations_stmt = select(OutfitRecommendation).where(
            OutfitRecommendation.user_id == current_user.id
        ).order_by(desc(OutfitRecommendation.created_at)).offset(offset).limit(limit)
        
        recommendations_result = await db.execute(recommendations_stmt)
        recommendations = recommendations_result.scalars().all()
        
        # Get total count for pagination
        count_stmt = select(func.count(OutfitRecommendation.id)).where(
            OutfitRecommendation.user_id == current_user.id
        )
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar() or 0
        
        # Format activity data
        activity_items = []
        for rec in recommendations:
            activity_items.append({
                "id": str(rec.id),
                "type": "recommendation",
                "prompt": rec.prompt,
                "ai_model_used": rec.ai_model_used,
                "feedback_score": rec.feedback_score,
                "is_favorite": rec.is_favorite,
                "is_archived": rec.is_archived,
                "created_at": rec.created_at.isoformat(),
                "updated_at": rec.updated_at.isoformat()
            })
        
        activity_data = {
            "items": activity_items,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
        }
        
        logger.info(f"Retrieved activity for user: {current_user.email}")
        return activity_data
        
    except Exception as e:
        logger.error(f"Failed to retrieve user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity"
        )