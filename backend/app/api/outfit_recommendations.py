"""
API endpoints for outfit recommendations using Gemini AI.
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_sync_session, get_current_user
from app.models.user import User
from app.services.gemini_service import gemini_service, OutfitRecommendation
from app.services.outfit_matching_service import get_outfit_matching_service
from app.schemas.outfit_recommendation import OutfitRecommendationCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/outfit-recommendations", tags=["outfit-recommendations"])


class OutfitRequestSchema(BaseModel):
    """Schema for outfit recommendation requests."""
    gender: str = Field(..., description="User's gender (men/women/unisex)")
    style: str = Field(..., description="Style preference (classic, casual, trendy, formal, etc.)")
    weather: str = Field(..., description="Weather condition (warm/cold/mild)")
    occasion: str = Field(..., description="Occasion type (work, party, casual, date, business, etc.)")
    user_request: str = Field(..., description="User's specific request or prompt", min_length=1, max_length=500)


class OutfitResponseSchema(BaseModel):
    """Schema for outfit recommendation responses."""
    success: bool
    recommendation: Dict[str, Any]
    request_details: Dict[str, str]
    message: str


@router.post("/generate", response_model=OutfitResponseSchema)
async def generate_outfit_recommendation(
    request: OutfitRequestSchema,
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
    request: OutfitRequestSchema,
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
        
        # Build response with both AI recommendation and matched items
        response = {
            "success": True,
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