"""
Quiz system API endpoints
"""
import uuid
import logging
import traceback
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_sync_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.quiz_system import QuizClothingItem as QuizClothingItemModel
from app.services.quiz_service import (
    QuizClothingItemService,
    StyleCategoryService,
    QuizResponseService,
    FeatureLearningService
)
from app.schemas.quiz_system import (
    QuizClothingItem as QuizClothingItemSchema,
    QuizClothingItemCreate,
    QuizClothingItemUpdate,
    StyleCategory,
    StyleCategoryCreate,
    StyleCategoryUpdate,
    QuizResponse,
    QuizResponseCreate,
    QuizResponseFeedback,
    QuizResponseWithItems,
    EnhancedQuizResponse,
    QuizQuestionsResponse,
    QuizClothingItemsResponse,
    StyleScores,
    QuizAnalytics,
    FeatureLearningData,
    FeatureLearningDataCreate,
    FeatureValidation,
    FeatureCorrelation,
    FeatureInsights,
    StyleAssignmentFeedback,
    StyleAssignmentFeedbackCreate,
    AlgorithmImprovementMetrics
)

router = APIRouter(prefix="/quiz", tags=["quiz"])
logger = logging.getLogger(__name__)


# Quiz Taking Endpoints
@router.get("/clothing-items/{gender}/{category}", response_model=List[QuizClothingItemSchema])
async def get_clothing_items_by_category(
    gender: str,
    category: str,
    db: Session = Depends(get_sync_session)
):
    """Get clothing items for quiz by gender and category"""
    if gender not in ["male", "female"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gender must be 'male' or 'female'"
        )
    
    items = QuizClothingItemService.get_clothing_items_by_category(
        db, gender, category
    )
    return items


@router.get("/questions/{gender}", response_model=QuizQuestionsResponse)
async def get_quiz_questions(
    gender: str,
    db: Session = Depends(get_sync_session)
):
    """Get all quiz questions for a specific gender"""
    if gender not in ["male", "female"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gender must be 'male' or 'female'"
        )
    
    categories = ["top", "bottom", "shoes", "layering", "accessory", "complete_outfit"]
    questions = {}
    
    for category in categories:
        items = QuizClothingItemService.get_clothing_items_by_category(
            db, gender, category
        )
        questions[category] = QuizClothingItemsResponse(
            category=category,
            items=items
        )
    
    return QuizQuestionsResponse(gender=gender, questions=questions)


@router.post("/submit", response_model=EnhancedQuizResponse)
async def submit_quiz(
    quiz_data: QuizResponseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Submit quiz responses and get enhanced style assignment with confidence scoring"""
    try:
        logger.info(f"Processing quiz submission for user {current_user.id}")
        logger.debug(f"Quiz data: {quiz_data}")
        
        response = QuizResponseService.process_complete_quiz(
            db=db,
            user_id=current_user.id,
            gender=quiz_data.gender,
            selected_items=quiz_data.selected_items,
            weights=quiz_data.weights
        )
        
        logger.info(f"Quiz processed successfully, response ID: {response.id}")
        
        # Load related data for enhanced response
        item_ids = [uuid.UUID(item_id) for item_id in response.selected_item_ids]
        selected_items = db.query(QuizClothingItemModel).filter(
            QuizClothingItemModel.id.in_(item_ids)
        ).all()
        
        # Extract hybrid style information from calculated_scores
        is_hybrid = response.calculated_scores.get('_is_hybrid', False)
        hybrid_styles = response.calculated_scores.get('_hybrid_styles', [])
        primary_score = response.calculated_scores.get('_primary_score', 0.0)
        
        # Clean up the scores (remove internal fields)
        clean_scores = {k: v for k, v in response.calculated_scores.items() if not k.startswith('_')}
        response.calculated_scores = clean_scores
        
        # Generate user-friendly style message
        style_message = f"Your preferred style is {response.assigned_category}"
        confidence_percentage = int(float(response.confidence_score) * 100)
        style_message += f" (based on your quiz responses with {confidence_percentage}% confidence)"
        
        # Create enhanced response
        enhanced_response = EnhancedQuizResponse(
            **response.__dict__,
            selected_items=selected_items,
            assigned_category_obj=response.assigned_category_obj,
            is_hybrid=is_hybrid,
            hybrid_styles=hybrid_styles,
            primary_score=primary_score,
            style_message=style_message
        )
        
        logger.info(f"Enhanced response created successfully")
        return enhanced_response
    except Exception as e:
        logger.error(f"Error processing quiz submission for user {current_user.id}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing quiz: {str(e)}"
        )


@router.post("/feedback/{response_id}")
async def submit_quiz_feedback(
    response_id: uuid.UUID,
    feedback: QuizResponseFeedback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Submit user feedback for quiz results"""
    # Verify the response belongs to the current user
    response = db.query(QuizResponse).filter(
        QuizResponse.id == response_id,
        QuizResponse.user_id == current_user.id
    ).first()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz response not found"
        )
    
    updated_response = QuizResponseService.update_user_feedback(
        db, response_id, feedback.satisfaction_rating, feedback.feedback_text
    )
    
    return {"message": "Feedback submitted successfully"}


@router.post("/style-feedback/{response_id}", response_model=StyleAssignmentFeedback)
async def submit_style_assignment_feedback(
    response_id: uuid.UUID,
    feedback: StyleAssignmentFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Submit detailed feedback on style assignment accuracy"""
    from app.services.quiz_service import StyleFeedbackService
    
    # Verify the response belongs to the current user
    response = db.query(QuizResponse).filter(
        QuizResponse.id == response_id,
        QuizResponse.user_id == current_user.id
    ).first()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz response not found"
        )
    
    style_feedback = StyleFeedbackService.create_style_feedback(
        db=db,
        quiz_response_id=response_id,
        user_id=current_user.id,
        accuracy_rating=feedback.accuracy_rating,
        feedback_type=feedback.feedback_type,
        preferred_style=feedback.preferred_style,
        feedback_text=feedback.feedback_text,
        feature_feedback=feedback.feature_feedback
    )
    
    return style_feedback


@router.get("/categories", response_model=List[StyleCategory])
async def get_style_categories(
    gender: Optional[str] = Query(None, pattern="^(men|women)$"),
    db: Session = Depends(get_sync_session)
):
    """Get available style categories"""
    if gender:
        categories = StyleCategoryService.get_categories_by_gender(db, gender)
    else:
        # Get all categories
        men_categories = StyleCategoryService.get_categories_by_gender(db, "men")
        women_categories = StyleCategoryService.get_categories_by_gender(db, "women")
        categories = men_categories + women_categories
    
    return categories


@router.get("/responses", response_model=List[QuizResponse])
async def get_user_quiz_responses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Get user's quiz response history"""
    responses = QuizResponseService.get_user_quiz_responses(db, current_user.id)
    return responses


@router.get("/responses/latest", response_model=Optional[QuizResponseWithItems])
async def get_latest_quiz_response(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Get user's latest quiz response with full details"""
    response = QuizResponseService.get_latest_user_response(db, current_user.id)
    if not response:
        return None
    
    # Load related data
    item_ids = [uuid.UUID(item_id) for item_id in response.selected_item_ids]
    selected_items = db.query(QuizClothingItemModel).filter(
        QuizClothingItemModel.id.in_(item_ids)
    ).all()
    
    response_dict = response.__dict__.copy()
    response_dict['selected_items'] = selected_items
    response_dict['assigned_category_obj'] = response.assigned_category_obj
    
    return QuizResponseWithItems(**response_dict)


# Admin Endpoints
@router.post("/admin/clothing-items", response_model=QuizClothingItemSchema)
async def create_clothing_item(
    item_data: QuizClothingItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Create a new quiz clothing item (Admin only)"""
    # TODO: Add admin permission check
    item = QuizClothingItemService.create_clothing_item(
        db=db,
        name=item_data.name,
        image_url=item_data.image_url,
        gender=item_data.gender,
        category=item_data.category,
        features=item_data.features
    )
    return item


@router.put("/admin/clothing-items/{item_id}", response_model=QuizClothingItemSchema)
async def update_clothing_item(
    item_id: uuid.UUID,
    item_data: QuizClothingItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Update a quiz clothing item (Admin only)"""
    # TODO: Add admin permission check
    item = QuizClothingItemService.update_clothing_item(
        db, item_id, **item_data.dict(exclude_unset=True)
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found"
        )
    
    return item


@router.delete("/admin/clothing-items/{item_id}")
async def delete_clothing_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Delete a quiz clothing item (Admin only)"""
    # TODO: Add admin permission check
    success = QuizClothingItemService.delete_clothing_item(db, item_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found"
        )
    
    return {"message": "Clothing item deleted successfully"}


@router.post("/admin/categories", response_model=StyleCategory)
async def create_style_category(
    category_data: StyleCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Create a new style category (Admin only)"""
    # TODO: Add admin permission check
    category = StyleCategoryService.create_style_category(
        db=db,
        name=category_data.name,
        gender=category_data.gender,
        features=category_data.features,
        ai_theme_prompt=category_data.ai_theme_prompt,
        description=category_data.description
    )
    return category


@router.put("/admin/categories/{category_id}", response_model=StyleCategory)
async def update_style_category(
    category_id: uuid.UUID,
    category_data: StyleCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Update a style category (Admin only)"""
    # TODO: Add admin permission check
    category = StyleCategoryService.get_category_by_id(db, category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Style category not found"
        )
    
    # Update fields
    update_data = category_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    return category


@router.get("/admin/analytics", response_model=QuizAnalytics)
async def get_quiz_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Get quiz analytics (Admin only)"""
    # TODO: Add admin permission check
    # TODO: Implement analytics calculation
    return QuizAnalytics(
        total_responses=0,
        category_distribution={},
        average_confidence=0.0,
        satisfaction_ratings={},
        most_selected_items=[],
        feature_popularity={}
    )


# Feature Learning Endpoints
@router.post("/features/suggest", response_model=FeatureLearningData)
async def suggest_feature(
    feature_data: FeatureLearningDataCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Suggest a new feature for a clothing item"""
    learning_data = FeatureLearningService.add_feature_suggestion(
        db=db,
        feature_name=feature_data.feature_name,
        item_id=feature_data.item_id,
        source=feature_data.source,
        confidence_score=feature_data.confidence_score
    )
    return learning_data


@router.post("/features/validate/{learning_data_id}")
async def validate_feature(
    learning_data_id: uuid.UUID,
    validation: FeatureValidation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Validate or reject a feature suggestion"""
    # TODO: Add admin permission check for validation
    learning_data = FeatureLearningService.validate_feature(
        db, learning_data_id, validation.is_valid
    )
    
    if not learning_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature learning data not found"
        )
    
    return {"message": "Feature validation recorded"}


@router.get("/features/correlations/{feature}", response_model=List[FeatureCorrelation])
async def get_feature_correlations(
    feature: str,
    min_strength: float = Query(0.5, ge=0.0, le=1.0),
    db: Session = Depends(get_sync_session)
):
    """Get feature correlations for a specific feature"""
    correlations = FeatureLearningService.get_feature_correlations(
        db, feature, min_strength
    )
    return correlations


@router.get("/features/pending", response_model=List[FeatureLearningData])
async def get_pending_feature_validations(
    source: Optional[str] = Query(None, pattern="^(manual|cv_auto|user_suggested|algorithm_discovered)$"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Get pending feature validations (Admin only)"""
    # TODO: Add admin permission check
    pending = FeatureLearningService.get_pending_validations(db, source, limit)
    return pending


@router.get("/features/insights", response_model=FeatureInsights)
async def get_feature_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Get feature learning insights (Admin only)"""
    # TODO: Add admin permission check
    # TODO: Implement insights calculation
    return FeatureInsights(
        pending_validations=0,
        validated_features=0,
        rejected_features=0,
        top_correlations=[],
        accuracy_by_source={},
        recent_discoveries=[]
    )


@router.get("/admin/algorithm-metrics", response_model=AlgorithmImprovementMetrics)
async def get_algorithm_improvement_metrics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Get algorithm improvement metrics based on user feedback (Admin only)"""
    from app.services.quiz_service import StyleFeedbackService
    
    # TODO: Add admin permission check
    metrics = StyleFeedbackService.get_feedback_metrics(db, days)
    
    return AlgorithmImprovementMetrics(**metrics)


@router.get("/admin/feature-accuracy/{feature_name}")
async def get_feature_accuracy_analysis(
    feature_name: str,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_session)
):
    """Get accuracy analysis for a specific feature (Admin only)"""
    from app.services.quiz_service import StyleFeedbackService
    
    # TODO: Add admin permission check
    analysis = StyleFeedbackService.analyze_feature_accuracy(db, feature_name, days)
    
    return analysis