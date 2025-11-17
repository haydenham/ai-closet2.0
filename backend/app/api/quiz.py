"""
Quiz system API endpoints - Simplified v2.0
"""
import uuid
import logging
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_sync_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.quiz import (
    QuizItemService,
    CategoryService,
    ScoringService,
    ResponseService
)
from app.schemas.quiz import (
    QuizQuestionsResponse,
    QuizSubmission,
    QuizResultResponse,
    QuizResponse as QuizResponseSchema,
    StyleCategory,
    QuizItem as QuizItemSchema,
    QuizItemCreate,
    QuizItemUpdate,
    StyleCategoryCreate
)

router = APIRouter(prefix="/quiz", tags=["quiz"])
logger = logging.getLogger(__name__)


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@router.get("/questions/{gender}", response_model=QuizQuestionsResponse)
async def get_quiz_questions(
    gender: str,
    db: Session = Depends(get_sync_session)
):
    """
    Get all quiz questions for a specific gender
    
    Returns 5 question types, each with 10 images representing different styles:
    - pants
    - shirt
    - shorts
    - overlayer
    - shoes
    """
    if gender not in ["female", "male"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gender must be 'female' or 'male'"
        )
    
    # Define question text for each type
    question_texts = {
        "pants": "Select the pants you would most want to wear",
        "shirt": "Select the top you would most want to wear",
        "shorts": "Select the shorts you would most want to wear",
        "overlayer": "Select the jacket or layering piece you would most want to wear",
        "shoes": "Select the shoes you would most want to wear"
    }
    
    try:
        questions_data = QuizItemService.get_quiz_questions(db, gender)
        
        # Format with question text
        from app.schemas.quiz import QuizQuestionType
        questions = {}
        for question_type, items in questions_data.items():
            if not items:
                logger.warning(f"No items found for {gender} {question_type}")
            
            questions[question_type] = QuizQuestionType(
                question_text=question_texts.get(question_type, f"Select your preferred {question_type}"),
                items=items
            )
        
        return QuizQuestionsResponse(
            gender=gender,
            questions=questions
        )
    
    except Exception as e:
        logger.error(f"Error fetching quiz questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quiz questions"
        )


@router.post("/submit", response_model=QuizResultResponse)
async def submit_quiz(
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """
    Submit quiz responses and get style assignment
    
    Algorithm:
    - Each of 5 questions gives 1 point to the selected style category
    - Primary style = category with most points
    - Secondary style = category with 2nd most points (random if tie)
    - Edge case: If all 5 same category, only primary style returned
    """
    try:
        # Submit quiz and calculate results
        quiz_response = ResponseService.submit_quiz(
            db=db,
            user_id=current_user.id,
            gender=submission.gender,
            selections=submission.selections
        )
        
        # Return results
        return QuizResultResponse(
            id=quiz_response.id,
            primary_style=quiz_response.primary_style,
            secondary_style=quiz_response.secondary_style,
            style_message=quiz_response.style_message,
            scores=quiz_response.scores,
            completed_at=quiz_response.completed_at
        )
    
    except ValueError as e:
        logger.warning(f"Invalid quiz submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit quiz"
        )


@router.get("/results/latest", response_model=Optional[QuizResultResponse])
async def get_latest_result(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Get user's most recent quiz result"""
    try:
        response = ResponseService.get_user_latest_response(db, current_user.id)
        
        if not response:
            return None
        
        return QuizResultResponse(
            id=response.id,
            primary_style=response.primary_style,
            secondary_style=response.secondary_style,
            style_message=response.style_message,
            scores=response.scores,
            completed_at=response.completed_at
        )
    
    except Exception as e:
        logger.error(f"Error fetching latest result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quiz result"
        )


@router.get("/history", response_model=list[QuizResponseSchema])
async def get_quiz_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Get user's quiz history"""
    try:
        responses = ResponseService.get_user_quiz_history(
            db,
            current_user.id,
            limit=limit
        )
        return responses
    
    except Exception as e:
        logger.error(f"Error fetching quiz history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quiz history"
        )


# ============================================================================
# ADMIN ENDPOINTS (for managing quiz items)
# ============================================================================

@router.get("/admin/categories", response_model=list[StyleCategory])
async def get_style_categories(
    gender: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Get all style categories (admin only)"""
    # TODO: Add admin permission check
    try:
        categories = CategoryService.get_all_categories(db, gender=gender)
        return categories
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories"
        )


@router.post("/admin/categories", response_model=StyleCategory)
async def create_style_category(
    category_data: StyleCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Create a new style category (admin only)"""
    # TODO: Add admin permission check
    try:
        category = CategoryService.create_category(
            db=db,
            name=category_data.name,
            gender=category_data.gender,
            description=category_data.description,
            ai_theme_prompt=category_data.ai_theme_prompt
        )
        return category
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category"
        )


@router.get("/admin/items", response_model=list[QuizItemSchema])
async def get_all_quiz_items(
    gender: Optional[str] = None,
    question_type: Optional[str] = None,
    style_category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Get all quiz items with optional filters (admin only)"""
    # TODO: Add admin permission check
    try:
        items = QuizItemService.get_all_items(
            db,
            gender=gender,
            question_type=question_type,
            style_category=style_category
        )
        return items
    except Exception as e:
        logger.error(f"Error fetching items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch items"
        )


@router.post("/admin/items", response_model=QuizItemSchema)
async def create_quiz_item(
    item_data: QuizItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Create a new quiz item (admin only)"""
    # TODO: Add admin permission check
    try:
        item = QuizItemService.create_item(
            db=db,
            name=item_data.name,
            image_url=item_data.image_url,
            question_type=item_data.question_type,
            style_category=item_data.style_category,
            gender=item_data.gender,
            display_order=item_data.display_order
        )
        return item
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create item"
        )


@router.put("/admin/items/{item_id}", response_model=QuizItemSchema)
async def update_quiz_item(
    item_id: uuid.UUID,
    item_data: QuizItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Update a quiz item (admin only)"""
    # TODO: Add admin permission check
    try:
        item = QuizItemService.update_item(
            db,
            item_id,
            **item_data.model_dump(exclude_unset=True)
        )
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz item not found"
            )
        
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update item"
        )


@router.delete("/admin/items/{item_id}")
async def delete_quiz_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Delete a quiz item (admin only)"""
    # TODO: Add admin permission check
    try:
        success = QuizItemService.delete_item(db, item_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz item not found"
            )
        
        return {"message": "Quiz item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete item"
        )
