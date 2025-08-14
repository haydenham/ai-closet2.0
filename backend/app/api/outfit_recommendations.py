"""
API endpoints for outfit recommendations using Gemini AI.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.database import get_sync_session
from app.models.user import User
from app.models.outfit_recommendation import OutfitRecommendation as OutfitRecommendationModel, RecommendationFeedback
from app.services.gemini_service import gemini_service, OutfitRecommendation
from app.services.outfit_matching_service import get_outfit_matching_service
from app.schemas.outfit_recommendation import (
    OutfitRecommendationCreate, OutfitRecommendationResponse, 
    RecommendationFeedbackResponse,
    OutfitRecommendationSearch, RecommendationStats
)
from app.schemas.security import SecureOutfitRequest, SecureRecommendationFeedback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/outfit-recommendations", tags=["outfit-recommendations"])


# Use SecureOutfitRequest from security schemas instead


class OutfitResponseSchema(BaseModel):
    """Schema for outfit recommendation responses."""
    success: bool
    recommendation: Dict[str, Any]
    request_details: Dict[str, str]
    message: str


@router.post("/generate", response_model=OutfitResponseSchema)
async def generate_outfit_recommendation(
    request: SecureOutfitRequest,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Generate outfit recommendation using Gemini AI.
    
    This endpoint takes user preferences and generates a personalized outfit
    recommendation using the Gemini AI model with structured JSON output.
    """
    try:
        logger.info(f"Generating outfit recommendation for user {current_user.id}")
        
        # Validate inputs
        gemini_service.validate_inputs(
            gender=request.gender,
            style=request.style,
            weather=request.weather,
            occasion=request.occasion
        )
        
        # Generate recommendation using Gemini service
        recommendation = await gemini_service.generate_outfit_recommendation(
            gender=request.gender,
            style=request.style,
            weather=request.weather,
            occasion=request.occasion,
            user_request=request.user_request
        )
        
        # Convert to dictionary for response
        recommendation_dict = recommendation.model_dump(exclude_none=True)
        
        logger.info(f"Successfully generated outfit recommendation for user {current_user.id}")
        
        return OutfitResponseSchema(
            success=True,
            recommendation=recommendation_dict,
            request_details={
                "gender": request.gender,
                "style": request.style,
                "weather": request.weather,
                "occasion": request.occasion,
                "user_request": request.user_request
            },
            message="Outfit recommendation generated successfully"
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Error generating outfit recommendation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate outfit recommendation: {str(e)}"
        )


@router.get("/validate-inputs")
async def validate_recommendation_inputs(
    gender: str,
    style: str,
    weather: str,
    occasion: str,
    current_user: User = Depends(get_current_user)
):
    """
    Validate input parameters for outfit recommendations.
    
    This endpoint can be used by the frontend to validate user inputs
    before submitting a recommendation request.
    """
    try:
        is_valid = gemini_service.validate_inputs(
            gender=gender,
            style=style,
            weather=weather,
            occasion=occasion
        )
        
        return {
            "success": True,
            "valid": is_valid,
            "message": "Input validation successful"
        }
        
    except ValueError as e:
        return {
            "success": False,
            "valid": False,
            "message": str(e)
        }


@router.get("/supported-options")
async def get_supported_options(
    current_user: User = Depends(get_current_user)
):
    """
    Get supported options for outfit recommendation parameters.
    
    Returns the valid values for gender, weather, and example styles/occasions.
    """
    return {
        "success": True,
        "options": {
            "genders": ["men", "women", "unisex"],
            "weather": ["warm", "cold", "mild"],
            "example_styles": [
                "classic", "casual", "trendy", "formal", "bohemian",
                "minimalist", "vintage", "sporty", "elegant", "edgy"
            ],
            "example_occasions": [
                "work", "business", "casual", "party", "date", "wedding",
                "interview", "weekend", "vacation", "gym", "formal_event"
            ]
        },
        "message": "Supported options retrieved successfully"
    }


@router.post("/generate-and-match", response_model=Dict[str, Any])
async def generate_and_match_outfit(
    request: SecureOutfitRequest,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Generate outfit recommendation using Gemini AI and match to user's closet.
    
    This endpoint combines AI-generated outfit suggestions with matching
    to the user's actual clothing items for personalized recommendations.
    """
    try:
        logger.info(f"Generating and matching outfit for user {current_user.id}")
        
        # Validate inputs
        gemini_service.validate_inputs(
            gender=request.gender,
            style=request.style,
            weather=request.weather,
            occasion=request.occasion
        )
        
        # Generate AI recommendation
        ai_recommendation = await gemini_service.generate_outfit_recommendation(
            gender=request.gender,
            style=request.style,
            weather=request.weather,
            occasion=request.occasion,
            user_request=request.user_request
        )
        
        # Match to user's closet
        matching_service = get_outfit_matching_service()
        match_result = matching_service.match_outfit_to_closet(
            db=db,
            user=current_user,
            ai_recommendation=ai_recommendation,
            weather=request.weather,
            style_preference=request.style
        )
        
        # Store recommendation in database
        db_recommendation = OutfitRecommendationModel(
            user_id=current_user.id,
            prompt=request.user_request,
            ai_response=str(ai_recommendation.model_dump()),
            outfit_components=ai_recommendation.model_dump(exclude_none=True),
            ai_model_used="gemini-pro",
            occasion=request.occasion,
            weather=request.weather,
            similarity_scores={
                "overall_score": match_result.overall_score,
                "color_harmony": match_result.color_harmony_score,
                "style_consistency": match_result.style_consistency_score,
                "weather_appropriateness": match_result.weather_appropriateness
            }
        )
        
        # Add matched clothing items to recommendation
        if match_result.top:
            db_recommendation.add_clothing_item(match_result.top.clothing_item)
        if match_result.bottom:
            db_recommendation.add_clothing_item(match_result.bottom.clothing_item)
        if match_result.shoes:
            db_recommendation.add_clothing_item(match_result.shoes.clothing_item)
        if match_result.outerwear:
            db_recommendation.add_clothing_item(match_result.outerwear.clothing_item)
        if match_result.accessories:
            for acc in match_result.accessories:
                db_recommendation.add_clothing_item(acc.clothing_item)
        
        db.add(db_recommendation)
        db.commit()
        db.refresh(db_recommendation)
        
        # Build response with both AI recommendation and matched items
        response = {
            "success": True,
            "recommendation_id": str(db_recommendation.id),
            "ai_recommendation": ai_recommendation.model_dump(exclude_none=True),
            "matched_outfit": {
                "top": matching_service.get_match_explanation(match_result.top) if match_result.top else None,
                "bottom": matching_service.get_match_explanation(match_result.bottom) if match_result.bottom else None,
                "shoes": matching_service.get_match_explanation(match_result.shoes) if match_result.shoes else None,
                "outerwear": matching_service.get_match_explanation(match_result.outerwear) if match_result.outerwear else None,
                "accessories": [matching_service.get_match_explanation(acc) for acc in match_result.accessories] if match_result.accessories else []
            },
            "matching_scores": {
                "overall_score": round(match_result.overall_score, 3),
                "color_harmony": round(match_result.color_harmony_score, 3),
                "style_consistency": round(match_result.style_consistency_score, 3),
                "weather_appropriateness": round(match_result.weather_appropriateness, 3)
            },
            "missing_categories": match_result.missing_categories or [],
            "request_details": {
                "gender": request.gender,
                "style": request.style,
                "weather": request.weather,
                "occasion": request.occasion,
                "user_request": request.user_request
            },
            "message": "Outfit generated and matched successfully"
        }
        
        logger.info(f"Successfully generated and matched outfit for user {current_user.id} with score {match_result.overall_score:.3f}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Error generating and matching outfit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate and match outfit: {str(e)}"
        )


@router.get("/history", response_model=List[OutfitRecommendationResponse])
async def get_recommendation_history(
    limit: int = 20,
    offset: int = 0,
    occasion: Optional[str] = None,
    weather: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's outfit recommendation history with optional filtering.
    
    This endpoint returns a paginated list of the user's past recommendations
    with optional filters for occasion, weather, and favorite status.
    """
    try:
        logger.info(f"Fetching recommendation history for user {current_user.id}")
        
        # Build query
        query = db.query(OutfitRecommendationModel).filter(
            OutfitRecommendationModel.user_id == current_user.id,
            OutfitRecommendationModel.is_archived == False
        )
        
        # Apply filters
        if occasion:
            query = query.filter(OutfitRecommendationModel.occasion == occasion)
        if weather:
            query = query.filter(OutfitRecommendationModel.weather == weather)
        if is_favorite is not None:
            query = query.filter(OutfitRecommendationModel.is_favorite == is_favorite)
        
        # Order by creation date (newest first) and apply pagination
        recommendations = query.order_by(
            OutfitRecommendationModel.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        logger.info(f"Found {len(recommendations)} recommendations for user {current_user.id}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error fetching recommendation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recommendation history: {str(e)}"
        )


@router.get("/{recommendation_id}", response_model=OutfitRecommendationResponse)
async def get_recommendation(
    recommendation_id: str,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific outfit recommendation by ID.
    
    This endpoint returns detailed information about a specific recommendation
    including matched items and feedback.
    """
    try:
        import uuid
        try:
            recommendation_uuid = uuid.UUID(recommendation_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid recommendation ID format"
            )
        
        recommendation = db.query(OutfitRecommendationModel).filter(
            OutfitRecommendationModel.id == recommendation_uuid,
            OutfitRecommendationModel.user_id == current_user.id
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )
        
        return recommendation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recommendation {recommendation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recommendation: {str(e)}"
        )


@router.post("/{recommendation_id}/feedback", response_model=RecommendationFeedbackResponse)
async def submit_recommendation_feedback(
    recommendation_id: str,
    feedback: SecureRecommendationFeedback,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Submit feedback for a specific outfit recommendation.
    
    This endpoint allows users to provide detailed feedback on recommendations
    to improve future suggestions.
    """
    try:
        import uuid
        try:
            recommendation_uuid = uuid.UUID(recommendation_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid recommendation ID format"
            )
        
        # Verify recommendation exists and belongs to user
        recommendation = db.query(OutfitRecommendationModel).filter(
            OutfitRecommendationModel.id == recommendation_uuid,
            OutfitRecommendationModel.user_id == current_user.id
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )
        
        # Create feedback entry
        db_feedback = RecommendationFeedback(
            recommendation_id=recommendation.id,
            user_id=current_user.id,
            rating=feedback.rating,
            feedback_type=feedback.feedback_type,
            comments=feedback.comments,
            style_accuracy=feedback.style_accuracy,
            item_matching=feedback.item_matching,
            occasion_appropriateness=feedback.occasion_appropriateness,
            feedback_tags=feedback.feedback_tags
        )
        
        # Update recommendation with basic feedback
        recommendation.set_feedback(feedback.rating, feedback.comments)
        
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        
        logger.info(f"Feedback submitted for recommendation {recommendation_id} by user {current_user.id}")
        return db_feedback
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback for recommendation {recommendation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.put("/{recommendation_id}/favorite")
async def toggle_recommendation_favorite(
    recommendation_id: str,
    is_favorite: bool,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle favorite status for a recommendation.
    
    This endpoint allows users to mark/unmark recommendations as favorites
    for easy access later.
    """
    try:
        import uuid
        try:
            recommendation_uuid = uuid.UUID(recommendation_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid recommendation ID format"
            )
        
        recommendation = db.query(OutfitRecommendationModel).filter(
            OutfitRecommendationModel.id == recommendation_uuid,
            OutfitRecommendationModel.user_id == current_user.id
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )
        
        recommendation.is_favorite = is_favorite
        db.commit()
        
        action = "favorited" if is_favorite else "unfavorited"
        logger.info(f"Recommendation {recommendation_id} {action} by user {current_user.id}")
        
        return {
            "success": True,
            "message": f"Recommendation {action} successfully",
            "is_favorite": is_favorite
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite for recommendation {recommendation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update favorite status: {str(e)}"
        )


@router.get("/analytics/stats", response_model=RecommendationStats)
async def get_recommendation_analytics(
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get recommendation analytics and statistics for the user.
    
    This endpoint provides insights into the user's recommendation history,
    preferences, and feedback patterns.
    """
    try:
        # Get all user recommendations
        recommendations = db.query(OutfitRecommendationModel).filter(
            OutfitRecommendationModel.user_id == current_user.id
        ).all()
        
        # Calculate basic stats
        total_recommendations = len(recommendations)
        favorite_count = sum(1 for r in recommendations if r.is_favorite)
        archived_count = sum(1 for r in recommendations if r.is_archived)
        
        # Calculate average rating
        ratings = [r.feedback_score for r in recommendations if r.feedback_score is not None]
        average_rating = sum(ratings) / len(ratings) if ratings else None
        
        # Group by occasion and season
        recommendations_by_occasion = {}
        recommendations_by_season = {}
        most_used_models = {}
        
        for rec in recommendations:
            if rec.occasion:
                recommendations_by_occasion[rec.occasion] = recommendations_by_occasion.get(rec.occasion, 0) + 1
            if rec.season:
                recommendations_by_season[rec.season] = recommendations_by_season.get(rec.season, 0) + 1
            if rec.ai_model_used:
                most_used_models[rec.ai_model_used] = most_used_models.get(rec.ai_model_used, 0) + 1
        
        # Get recent recommendations (last 5)
        recent_recommendations = db.query(OutfitRecommendationModel).filter(
            OutfitRecommendationModel.user_id == current_user.id
        ).order_by(OutfitRecommendationModel.created_at.desc()).limit(5).all()
        
        stats = RecommendationStats(
            total_recommendations=total_recommendations,
            favorite_count=favorite_count,
            archived_count=archived_count,
            average_rating=round(average_rating, 2) if average_rating else None,
            recommendations_by_occasion=recommendations_by_occasion,
            recommendations_by_season=recommendations_by_season,
            most_used_models=most_used_models,
            recent_recommendations=recent_recommendations
        )
        
        logger.info(f"Analytics generated for user {current_user.id}: {total_recommendations} total recommendations")
        return stats
        
    except Exception as e:
        logger.error(f"Error generating recommendation analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the outfit recommendation service.
    
    This endpoint can be used to verify that the Gemini service is properly
    configured and accessible.
    """
    try:
        # Check if the service is properly initialized
        if not hasattr(gemini_service, 'model'):
            raise Exception("Gemini service not properly initialized")
        
        # Check configuration
        from app.core.config import settings
        if not settings.GCP_PROJECT_ID or not settings.GEMINI_ENDPOINT_ID:
            raise Exception("Gemini configuration incomplete")
        
        return {
            "success": True,
            "status": "healthy",
            "message": "Outfit recommendation service is operational",
            "configuration": {
                "project_id": settings.GCP_PROJECT_ID,
                "location": settings.GCP_LOCATION,
                "endpoint_configured": bool(settings.GEMINI_ENDPOINT_ID)
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


@router.get("/improvement/metrics")
async def get_improvement_metrics(
    period: str = "month",
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get improvement metrics for the current user.
    
    This endpoint provides detailed analysis of recommendation performance
    and improvement trends over time.
    """
    try:
        from app.services.recommendation_improvement_service import get_improvement_service
        
        improvement_service = get_improvement_service()
        metrics = improvement_service.analyze_user_improvement_metrics(db, current_user, period)
        
        return {
            "success": True,
            "metrics": {
                "user_id": metrics.user_id,
                "time_period": metrics.time_period,
                "total_recommendations": metrics.total_recommendations,
                "average_rating": metrics.average_rating,
                "rating_trend": metrics.rating_trend,
                "feedback_categories": metrics.feedback_categories,
                "common_issues": metrics.common_issues,
                "improvement_suggestions": metrics.improvement_suggestions,
                "satisfaction_score": metrics.satisfaction_score
            },
            "message": f"Improvement metrics for {period} period retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting improvement metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get improvement metrics: {str(e)}"
        )


@router.get("/improvement/patterns")
async def get_recommendation_patterns(
    limit: int = 10,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get recommendation patterns and insights for the current user.
    
    This endpoint analyzes patterns in the user's recommendation history
    to identify preferences and successful combinations.
    """
    try:
        from app.services.recommendation_improvement_service import get_improvement_service
        
        improvement_service = get_improvement_service()
        patterns = improvement_service.analyze_recommendation_patterns(db, current_user, limit)
        
        return {
            "success": True,
            "patterns": [
                {
                    "type": pattern.pattern_type,
                    "description": pattern.description,
                    "frequency": pattern.frequency,
                    "success_rate": round(pattern.success_rate, 3),
                    "user_satisfaction": round(pattern.user_satisfaction, 2)
                }
                for pattern in patterns
            ],
            "message": "Recommendation patterns retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendation patterns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendation patterns: {str(e)}"
        )


@router.get("/improvement/recommendations")
async def get_improvement_recommendations(
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive improvement recommendations for the current user.
    
    This endpoint provides personalized suggestions for improving
    recommendation quality and user satisfaction.
    """
    try:
        from app.services.recommendation_improvement_service import get_improvement_service
        
        improvement_service = get_improvement_service()
        recommendations = improvement_service.get_improvement_recommendations(db, current_user)
        
        return {
            "success": True,
            "improvement_data": recommendations,
            "message": "Improvement recommendations retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting improvement recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get improvement recommendations: {str(e)}"
        )


@router.post("/{recommendation_id}/track-performance")
async def track_recommendation_performance(
    recommendation_id: str,
    feedback: SecureRecommendationFeedback,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Track performance metrics for a specific recommendation.
    
    This endpoint records detailed performance data for recommendation
    improvement analysis and algorithm enhancement.
    """
    try:
        from app.services.recommendation_improvement_service import get_improvement_service
        
        # Verify recommendation belongs to user
        import uuid
        try:
            recommendation_uuid = uuid.UUID(recommendation_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid recommendation ID format"
            )
        
        recommendation = db.query(OutfitRecommendationModel).filter(
            OutfitRecommendationModel.id == recommendation_uuid,
            OutfitRecommendationModel.user_id == current_user.id
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )
        
        # Track performance
        improvement_service = get_improvement_service()
        performance_data = improvement_service.track_recommendation_performance(
            db, recommendation_id, feedback.dict()
        )
        
        return {
            "success": True,
            "performance_data": performance_data,
            "message": "Recommendation performance tracked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking recommendation performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track performance: {str(e)}"
        )