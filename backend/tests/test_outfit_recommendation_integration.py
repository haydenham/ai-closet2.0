"""
Integration tests for outfit recommendation API with feedback loop
"""
import pytest
import json
from typing import List
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.clothing_item import ClothingItem
from app.models.outfit_recommendation import OutfitRecommendation, RecommendationFeedback
from app.services.gemini_service import OutfitRecommendation as GeminiOutfitRecommendation, OutfitItem
from app.core.dependencies import get_current_user
from app.core.database import get_sync_session


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_clothing_items(db_session: Session, test_user: User):
    """Create test clothing items for the user"""
    items = [
        ClothingItem(
            user_id=test_user.id,
            filename="blue_shirt.jpg",
            original_filename="blue_shirt.jpg",
            category="top",
            color="blue",
            tags=["cotton", "casual", "button-down"],
            image_url="https://example.com/blue_shirt.jpg"
        ),
        ClothingItem(
            user_id=test_user.id,
            filename="black_jeans.jpg",
            original_filename="black_jeans.jpg",
            category="bottom",
            color="black",
            tags=["denim", "casual", "slim-fit"],
            image_url="https://example.com/black_jeans.jpg"
        ),
        ClothingItem(
            user_id=test_user.id,
            filename="white_sneakers.jpg",
            original_filename="white_sneakers.jpg",
            category="shoes",
            color="white",
            tags=["sneakers", "casual", "comfortable"],
            image_url="https://example.com/white_sneakers.jpg"
        )
    ]
    
    for item in items:
        db_session.add(item)
    
    db_session.commit()
    
    for item in items:
        db_session.refresh(item)
    
    return items


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_current_user(test_user: User):
    """Mock current user dependency"""
    def _get_current_user():
        return test_user
    return _get_current_user


@pytest.fixture
def mock_db_session(db_session: Session):
    """Mock database session dependency"""
    def _get_db():
        return db_session
    return _get_db


class TestOutfitRecommendationIntegration:
    """Integration tests for outfit recommendation API with feedback loop"""
    
    @patch('app.services.gemini_service.gemini_service.generate_outfit_recommendation')
    @patch('app.services.gemini_service.gemini_service.validate_inputs')
    def test_complete_recommendation_workflow(
        self,
        mock_validate,
        mock_generate,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_clothing_items: List[ClothingItem],
        mock_current_user,
        mock_db_session
    ):
        """Test complete workflow: generate recommendation -> store -> retrieve -> feedback"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            # Mock AI service responses
            mock_validate.return_value = True
            mock_ai_recommendation = GeminiOutfitRecommendation(
                top=OutfitItem(type="shirt", features=["blue", "cotton", "casual"]),
                bottom=OutfitItem(type="jeans", features=["black", "denim", "casual"]),
                shoes=OutfitItem(type="sneakers", features=["white", "casual", "comfortable"])
            )
            mock_generate.return_value = mock_ai_recommendation
            
            # Step 1: Generate and match outfit recommendation
            request_data = {
                "gender": "men",
                "style": "casual",
                "weather": "mild",
                "occasion": "weekend",
                "user_request": "I need a casual outfit for weekend activities"
            }
            
            response = client.post("/outfit-recommendations/generate-and-match", json=request_data)
            assert response.status_code == 200
            
            recommendation_data = response.json()
            assert recommendation_data["success"] is True
            assert "recommendation_id" in recommendation_data
            assert "matched_outfit" in recommendation_data
            assert "matching_scores" in recommendation_data
            
            recommendation_id = recommendation_data["recommendation_id"]
            
            # Verify recommendation was stored in database
            import uuid
            recommendation_uuid = uuid.UUID(recommendation_id)
            db_recommendation = db_session.query(OutfitRecommendation).filter(
                OutfitRecommendation.id == recommendation_uuid
            ).first()
            assert db_recommendation is not None
            assert db_recommendation.user_id == test_user.id
            assert db_recommendation.prompt == request_data["user_request"]
            assert db_recommendation.occasion == request_data["occasion"]
            assert db_recommendation.weather == request_data["weather"]
            
            # Step 2: Retrieve recommendation history
            history_response = client.get("/outfit-recommendations/history")
            assert history_response.status_code == 200
            
            history_data = history_response.json()
            assert len(history_data) == 1
            assert history_data[0]["id"] == recommendation_id
            
            # Step 3: Get specific recommendation
            detail_response = client.get(f"/outfit-recommendations/{recommendation_id}")
            assert detail_response.status_code == 200
            
            detail_data = detail_response.json()
            assert detail_data["id"] == recommendation_id
            assert detail_data["prompt"] == request_data["user_request"]
            
            # Step 4: Submit feedback
            feedback_data = {
                "rating": 4,
                "feedback_type": "general",
                "comments": "Great recommendation! Loved the casual style.",
                "style_accuracy": 5,
                "item_matching": 4,
                "occasion_appropriateness": 5,
                "feedback_tags": ["stylish", "comfortable"]
            }
            
            feedback_response = client.post(
                f"/outfit-recommendations/{recommendation_id}/feedback",
                json=feedback_data
            )
            assert feedback_response.status_code == 200
            
            feedback_result = feedback_response.json()
            assert feedback_result["rating"] == 4
            assert feedback_result["comments"] == feedback_data["comments"]
            assert feedback_result["recommendation_id"] == recommendation_id
            
            # Verify feedback was stored
            db_feedback = db_session.query(RecommendationFeedback).filter(
                RecommendationFeedback.recommendation_id == recommendation_uuid
            ).first()
            assert db_feedback is not None
            assert db_feedback.rating == 4
            assert db_feedback.user_id == test_user.id
            
            # Verify recommendation was updated with feedback
            db_session.refresh(db_recommendation)
            assert db_recommendation.feedback_score == 4
            assert db_recommendation.feedback_comments == feedback_data["comments"]
            
            # Step 5: Toggle favorite status
            favorite_response = client.put(
                f"/outfit-recommendations/{recommendation_id}/favorite?is_favorite=true"
            )
            assert favorite_response.status_code == 200
            
            favorite_result = favorite_response.json()
            assert favorite_result["success"] is True
            assert favorite_result["is_favorite"] is True
            
            # Verify favorite status was updated
            db_session.refresh(db_recommendation)
            assert db_recommendation.is_favorite is True
            
            # Step 6: Get analytics
            analytics_response = client.get("/outfit-recommendations/analytics/stats")
            assert analytics_response.status_code == 200
            
            analytics_data = analytics_response.json()
            assert analytics_data["total_recommendations"] == 1
            assert analytics_data["favorite_count"] == 1
            assert analytics_data["average_rating"] == 4.0
            assert "weekend" in analytics_data["recommendations_by_occasion"]
            assert len(analytics_data["recent_recommendations"]) == 1
            
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
    
    def test_recommendation_history_filtering(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        mock_current_user,
        mock_db_session
    ):
        """Test recommendation history with filtering options"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            # Create test recommendations with different attributes
            recommendations = [
                OutfitRecommendation(
                    user_id=test_user.id,
                    prompt="Casual weekend outfit",
                    ai_response="{'top': 'shirt', 'bottom': 'jeans'}",
                    ai_model_used="gemini-pro",
                    occasion="weekend",
                    weather="mild",
                    is_favorite=True
                ),
                OutfitRecommendation(
                    user_id=test_user.id,
                    prompt="Business meeting outfit",
                    ai_response="{'top': 'blazer', 'bottom': 'trousers'}",
                    ai_model_used="gemini-pro",
                    occasion="business",
                    weather="cold",
                    is_favorite=False
                ),
                OutfitRecommendation(
                    user_id=test_user.id,
                    prompt="Summer party outfit",
                    ai_response="{'top': 'dress', 'shoes': 'heels'}",
                    ai_model_used="gemini-pro",
                    occasion="party",
                    weather="warm",
                    is_favorite=True
                )
            ]
            
            for rec in recommendations:
                db_session.add(rec)
            db_session.commit()
            
            # Test filtering by occasion
            response = client.get("/outfit-recommendations/history?occasion=business")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["occasion"] == "business"
            
            # Test filtering by weather
            response = client.get("/outfit-recommendations/history?weather=warm")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["weather"] == "warm"
            
            # Test filtering by favorite status
            response = client.get("/outfit-recommendations/history?is_favorite=true")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            for item in data:
                assert item["is_favorite"] is True
            
            # Test pagination
            response = client.get("/outfit-recommendations/history?limit=2&offset=0")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            
            response = client.get("/outfit-recommendations/history?limit=2&offset=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            
        finally:
            app.dependency_overrides.clear()
    
    def test_feedback_validation_and_error_handling(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        mock_current_user,
        mock_db_session
    ):
        """Test feedback validation and error handling"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            # Create a test recommendation
            recommendation = OutfitRecommendation(
                user_id=test_user.id,
                prompt="Test outfit",
                ai_response="{'top': 'shirt'}",
                ai_model_used="gemini-pro"
            )
            db_session.add(recommendation)
            db_session.commit()
            db_session.refresh(recommendation)
            
            # Test invalid rating (too low)
            invalid_feedback = {
                "rating": 0,
                "feedback_type": "general",
                "comments": "Test feedback"
            }
            
            response = client.post(
                f"/outfit-recommendations/{recommendation.id}/feedback",
                json=invalid_feedback
            )
            assert response.status_code == 422  # Validation error
            
            # Test invalid rating (too high)
            invalid_feedback["rating"] = 6
            response = client.post(
                f"/outfit-recommendations/{recommendation.id}/feedback",
                json=invalid_feedback
            )
            assert response.status_code == 422  # Validation error
            
            # Test invalid feedback type
            invalid_feedback = {
                "rating": 4,
                "feedback_type": "invalid_type",
                "comments": "Test feedback"
            }
            
            response = client.post(
                f"/outfit-recommendations/{recommendation.id}/feedback",
                json=invalid_feedback
            )
            assert response.status_code == 422  # Validation error
            
            # Test feedback for non-existent recommendation (invalid UUID format)
            valid_feedback = {
                "rating": 4,
                "feedback_type": "general",
                "comments": "Test feedback"
            }
            
            response = client.post(
                "/outfit-recommendations/non-existent-id/feedback",
                json=valid_feedback
            )
            assert response.status_code == 400  # Bad Request for invalid UUID format
            
            # Test feedback for valid UUID but non-existent recommendation
            import uuid
            fake_uuid = str(uuid.uuid4())
            response = client.post(
                f"/outfit-recommendations/{fake_uuid}/feedback",
                json=valid_feedback
            )
            assert response.status_code == 404  # Not found
            
            # Test valid feedback
            response = client.post(
                f"/outfit-recommendations/{recommendation.id}/feedback",
                json=valid_feedback
            )
            assert response.status_code == 200
            
            feedback_data = response.json()
            assert feedback_data["rating"] == 4
            assert feedback_data["feedback_type"] == "general"
            assert feedback_data["comments"] == "Test feedback"
            
        finally:
            app.dependency_overrides.clear()
    
    @patch('app.services.gemini_service.gemini_service.generate_outfit_recommendation')
    @patch('app.services.gemini_service.gemini_service.validate_inputs')
    def test_recommendation_analytics_and_performance_tracking(
        self,
        mock_validate,
        mock_generate,
        client: TestClient,
        db_session: Session,
        test_user: User,
        mock_current_user,
        mock_db_session
    ):
        """Test recommendation analytics and performance tracking"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            # Create multiple recommendations with different attributes and feedback
            recommendations_data = [
                {
                    "occasion": "work",
                    "weather": "cold",
                    "season": "winter",
                    "feedback_score": 5
                },
                {
                    "occasion": "party",
                    "weather": "warm",
                    "season": "summer",
                    "feedback_score": 4
                },
                {
                    "occasion": "work",
                    "weather": "mild",
                    "season": "spring",
                    "feedback_score": 3
                },
                {
                    "occasion": "casual",
                    "weather": "warm",
                    "season": "summer",
                    "feedback_score": None,
                    "is_favorite": True
                }
            ]
            
            for i, rec_data in enumerate(recommendations_data):
                recommendation = OutfitRecommendation(
                    user_id=test_user.id,
                    prompt=f"Test outfit {i+1}",
                    ai_response=f"{{'top': 'item{i+1}'}}",
                    ai_model_used="gemini-pro",
                    occasion=rec_data["occasion"],
                    weather=rec_data["weather"],
                    season=rec_data["season"],
                    feedback_score=rec_data.get("feedback_score"),
                    is_favorite=rec_data.get("is_favorite", False)
                )
                db_session.add(recommendation)
            
            db_session.commit()
            
            # Get analytics
            response = client.get("/outfit-recommendations/analytics/stats")
            assert response.status_code == 200
            
            analytics = response.json()
            
            # Verify basic counts
            assert analytics["total_recommendations"] == 4
            assert analytics["favorite_count"] == 1
            assert analytics["archived_count"] == 0
            
            # Verify average rating (only counting recommendations with feedback)
            expected_avg = (5 + 4 + 3) / 3  # 4.0
            assert analytics["average_rating"] == round(expected_avg, 2)
            
            # Verify groupings
            assert analytics["recommendations_by_occasion"]["work"] == 2
            assert analytics["recommendations_by_occasion"]["party"] == 1
            assert analytics["recommendations_by_occasion"]["casual"] == 1
            
            assert analytics["recommendations_by_season"]["winter"] == 1
            assert analytics["recommendations_by_season"]["summer"] == 2
            assert analytics["recommendations_by_season"]["spring"] == 1
            
            assert analytics["most_used_models"]["gemini-pro"] == 4
            
            # Verify recent recommendations
            assert len(analytics["recent_recommendations"]) == 4
            
        finally:
            app.dependency_overrides.clear()
    
    def test_recommendation_improvement_based_on_feedback(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        mock_current_user,
        mock_db_session
    ):
        """Test that feedback is properly stored for recommendation improvement"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            # Create a recommendation
            recommendation = OutfitRecommendation(
                user_id=test_user.id,
                prompt="Business casual outfit",
                ai_response="{'top': 'blazer', 'bottom': 'chinos'}",
                ai_model_used="gemini-pro",
                occasion="work",
                weather="mild"
            )
            db_session.add(recommendation)
            db_session.commit()
            db_session.refresh(recommendation)
            
            # Submit detailed feedback
            feedback_data = {
                "rating": 3,
                "feedback_type": "style_mismatch",
                "comments": "The blazer was too formal for business casual. Prefer more relaxed options.",
                "style_accuracy": 2,
                "item_matching": 4,
                "occasion_appropriateness": 3,
                "feedback_tags": ["too_formal", "prefer_casual", "good_fit"]
            }
            
            response = client.post(
                f"/outfit-recommendations/{recommendation.id}/feedback",
                json=feedback_data
            )
            assert response.status_code == 200
            
            # Verify detailed feedback was stored
            db_feedback = db_session.query(RecommendationFeedback).filter(
                RecommendationFeedback.recommendation_id == recommendation.id
            ).first()
            
            assert db_feedback is not None
            assert db_feedback.rating == 3
            assert db_feedback.feedback_type == "style_mismatch"
            assert db_feedback.style_accuracy == 2
            assert db_feedback.item_matching == 4
            assert db_feedback.occasion_appropriateness == 3
            assert "too_formal" in db_feedback.feedback_tags
            assert "prefer_casual" in db_feedback.feedback_tags
            assert "good_fit" in db_feedback.feedback_tags
            
            # Verify recommendation was updated
            db_session.refresh(recommendation)
            assert recommendation.feedback_score == 3
            assert "too formal" in recommendation.feedback_comments.lower()
            
            # Test that we can query feedback for analysis
            all_feedback = db_session.query(RecommendationFeedback).filter(
                RecommendationFeedback.user_id == test_user.id
            ).all()
            
            assert len(all_feedback) == 1
            assert all_feedback[0].feedback_type == "style_mismatch"
            
            # This feedback data would be used by the system to:
            # 1. Adjust future recommendations for this user
            # 2. Improve the matching algorithm
            # 3. Train better style preferences
            # 4. Identify common issues with specific item combinations
            
        finally:
            app.dependency_overrides.clear()