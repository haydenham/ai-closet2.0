"""
Integration tests for outfit recommendation improvements and analytics
"""
import pytest
import json
from typing import List
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

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
def test_recommendations_with_feedback(db_session: Session, test_user: User):
    """Create test recommendations with various feedback scores"""
    recommendations = []
    
    # Create recommendations with different ratings and feedback over time
    base_date = datetime.utcnow() - timedelta(days=30)
    
    recommendation_data = [
        {"prompt": "Casual weekend outfit", "occasion": "weekend", "weather": "mild", "rating": 5, "days_ago": 25},
        {"prompt": "Business meeting outfit", "occasion": "business", "weather": "cold", "rating": 3, "days_ago": 20},
        {"prompt": "Date night outfit", "occasion": "date", "weather": "warm", "rating": 4, "days_ago": 15},
        {"prompt": "Gym workout outfit", "occasion": "gym", "weather": "mild", "rating": 5, "days_ago": 10},
        {"prompt": "Formal dinner outfit", "occasion": "formal", "weather": "cold", "rating": 2, "days_ago": 5},
        {"prompt": "Casual Friday outfit", "occasion": "work", "weather": "mild", "rating": 4, "days_ago": 3},
        {"prompt": "Weekend brunch outfit", "occasion": "casual", "weather": "warm", "rating": 5, "days_ago": 1}
    ]
    
    for i, data in enumerate(recommendation_data):
        recommendation = OutfitRecommendation(
            user_id=test_user.id,
            prompt=data["prompt"],
            ai_response=f"{{'top': 'item{i}', 'bottom': 'item{i}'}}",
            ai_model_used="gemini-pro",
            occasion=data["occasion"],
            weather=data["weather"],
            feedback_score=data["rating"],
            feedback_comments=f"Test feedback for recommendation {i}",
            created_at=base_date + timedelta(days=data["days_ago"])
        )
        db_session.add(recommendation)
        recommendations.append(recommendation)
    
    db_session.commit()
    
    # Create detailed feedback for some recommendations
    for i, rec in enumerate(recommendations[:5]):  # Add detailed feedback for first 5
        db_session.refresh(rec)
        feedback = RecommendationFeedback(
            recommendation_id=rec.id,
            user_id=test_user.id,
            rating=recommendation_data[i]["rating"],
            feedback_type="general" if recommendation_data[i]["rating"] >= 4 else "style_mismatch",
            comments=f"Detailed feedback for recommendation {i}",
            style_accuracy=recommendation_data[i]["rating"],
            item_matching=recommendation_data[i]["rating"],
            occasion_appropriateness=recommendation_data[i]["rating"],
            feedback_tags=["stylish", "comfortable"] if recommendation_data[i]["rating"] >= 4 else ["needs_improvement"]
        )
        db_session.add(feedback)
    
    db_session.commit()
    return recommendations


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


class TestOutfitRecommendationImprovements:
    """Integration tests for outfit recommendation improvements and analytics"""
    
    @patch('app.services.gemini_service.gemini_service.generate_outfit_recommendation')
    @patch('app.services.gemini_service.gemini_service.validate_inputs')
    def test_missing_categories_tracking_for_no_matches(
        self,
        mock_validate,
        mock_generate,
        client: TestClient,
        db_session: Session,
        test_user: User,
        mock_current_user,
        mock_db_session
    ):
        """Test missing categories tracking when no closet matches are found"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            # Mock AI service responses
            mock_validate.return_value = True
            mock_ai_recommendation = GeminiOutfitRecommendation(
                top=OutfitItem(type="blazer", features=["navy", "wool", "formal"]),
                bottom=OutfitItem(type="dress_pants", features=["charcoal", "wool", "formal"]),
                shoes=OutfitItem(type="oxford_shoes", features=["black", "leather", "formal"])
            )
            mock_generate.return_value = mock_ai_recommendation
            
            # User has no formal clothing items, so should track missing categories
            request_data = {
                "gender": "men",
                "style": "formal",
                "weather": "cold",
                "occasion": "business",
                "user_request": "I need a formal business outfit for an important meeting"
            }
            
            response = client.post("/outfit-recommendations/generate-and-match", json=request_data)
            assert response.status_code == 200
            
            recommendation_data = response.json()
            assert recommendation_data["success"] is True
            
            # Should have missing categories tracked for future shopping feature
            assert "missing_categories" in recommendation_data
            assert len(recommendation_data["missing_categories"]) > 0
            
            # Should track the categories that couldn't be matched
            missing_categories = recommendation_data["missing_categories"]
            assert "top" in missing_categories  # No formal blazer
            assert "bottom" in missing_categories  # No formal pants
            assert "shoes" in missing_categories  # No formal shoes
            
        finally:
            app.dependency_overrides.clear()
    
    def test_improvement_metrics_analysis(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_recommendations_with_feedback: List[OutfitRecommendation],
        mock_current_user,
        mock_db_session
    ):
        """Test improvement metrics analysis endpoint"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            # Test monthly metrics
            response = client.get("/outfit-recommendations/improvement/metrics?period=month")
            assert response.status_code == 200
            
            metrics_data = response.json()
            assert metrics_data["success"] is True
            assert "metrics" in metrics_data
            
            metrics = metrics_data["metrics"]
            assert metrics["user_id"] == str(test_user.id)
            assert metrics["time_period"] == "month"
            assert metrics["total_recommendations"] > 0
            assert "average_rating" in metrics
            assert "rating_trend" in metrics
            assert "feedback_categories" in metrics
            assert "common_issues" in metrics
            assert "improvement_suggestions" in metrics
            assert "satisfaction_score" in metrics
            
            # Test weekly metrics
            response = client.get("/outfit-recommendations/improvement/metrics?period=week")
            assert response.status_code == 200
            
            weekly_data = response.json()
            assert weekly_data["success"] is True
            weekly_metrics = weekly_data["metrics"]
            assert weekly_metrics["time_period"] == "week"
            
        finally:
            app.dependency_overrides.clear()
    
    def test_recommendation_patterns_analysis(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_recommendations_with_feedback: List[OutfitRecommendation],
        mock_current_user,
        mock_db_session
    ):
        """Test recommendation patterns analysis endpoint"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            response = client.get("/outfit-recommendations/improvement/patterns?limit=5")
            assert response.status_code == 200
            
            patterns_data = response.json()
            assert patterns_data["success"] is True
            assert "patterns" in patterns_data
            
            patterns = patterns_data["patterns"]
            assert isinstance(patterns, list)
            
            if patterns:  # If we have patterns
                pattern = patterns[0]
                assert "type" in pattern
                assert "description" in pattern
                assert "frequency" in pattern
                assert "success_rate" in pattern
                assert "user_satisfaction" in pattern
                
                # Patterns should be sorted by success rate
                for i in range(1, len(patterns)):
                    assert patterns[i-1]["success_rate"] >= patterns[i]["success_rate"]
            
        finally:
            app.dependency_overrides.clear()
    
    def test_comprehensive_improvement_recommendations(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_recommendations_with_feedback: List[OutfitRecommendation],
        test_clothing_items: List[ClothingItem],
        mock_current_user,
        mock_db_session
    ):
        """Test comprehensive improvement recommendations endpoint"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            response = client.get("/outfit-recommendations/improvement/recommendations")
            assert response.status_code == 200
            
            improvement_data = response.json()
            assert improvement_data["success"] is True
            assert "improvement_data" in improvement_data
            
            data = improvement_data["improvement_data"]
            assert "user_id" in data
            assert "analysis_date" in data
            assert "metrics" in data
            assert "patterns" in data
            assert "closet_gaps" in data
            assert "personalized_tips" in data
            assert "next_steps" in data
            
            # Check metrics structure
            metrics = data["metrics"]
            assert "week" in metrics
            assert "month" in metrics
            
            # Check closet gaps analysis
            closet_gaps = data["closet_gaps"]
            assert isinstance(closet_gaps, list)
            
            if closet_gaps:
                gap = closet_gaps[0]
                assert "category" in gap
                assert "current_count" in gap
                assert "recommended_minimum" in gap
                assert "gap_size" in gap
                assert "priority" in gap
            
            # Check personalized tips
            tips = data["personalized_tips"]
            assert isinstance(tips, list)
            assert len(tips) > 0
            
            # Check next steps
            next_steps = data["next_steps"]
            assert isinstance(next_steps, list)
            assert len(next_steps) > 0
            
        finally:
            app.dependency_overrides.clear()
    
    def test_recommendation_performance_tracking(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_recommendations_with_feedback: List[OutfitRecommendation],
        mock_current_user,
        mock_db_session
    ):
        """Test recommendation performance tracking endpoint"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            # Get a test recommendation
            recommendation = test_recommendations_with_feedback[0]
            
            # Track performance with feedback
            feedback_data = {
                "rating": 4,
                "feedback_type": "general",
                "comments": "Great recommendation for performance tracking test",
                "style_accuracy": 4,
                "item_matching": 5,
                "occasion_appropriateness": 4,
                "feedback_tags": ["stylish", "comfortable", "well_matched"]
            }
            
            response = client.post(
                f"/outfit-recommendations/{recommendation.id}/track-performance",
                json=feedback_data
            )
            assert response.status_code == 200
            
            tracking_data = response.json()
            assert tracking_data["success"] is True
            assert "performance_data" in tracking_data
            
            performance = tracking_data["performance_data"]
            assert "recommendation_id" in performance
            assert "user_id" in performance
            assert "rating" in performance
            assert "feedback_type" in performance
            assert "improvement_areas" in performance
            assert "success_indicators" in performance
            assert "tracked_at" in performance
            
            # Check success indicators for high rating
            success_indicators = performance["success_indicators"]
            assert "high_satisfaction" in success_indicators
            assert "good_closet_match" in success_indicators
            
        finally:
            app.dependency_overrides.clear()
    
    def test_improvement_metrics_insufficient_data(
        self,
        client: TestClient,
        db_session: Session,
        mock_current_user,
        mock_db_session
    ):
        """Test improvement metrics with insufficient data"""
        
        # Create user with no recommendations
        user = User(
            email="newuser@example.com",
            password_hash="hashed_password",
            first_name="New",
            last_name="User",
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        def _get_new_user():
            return user
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = _get_new_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            response = client.get("/outfit-recommendations/improvement/metrics?period=month")
            assert response.status_code == 200
            
            metrics_data = response.json()
            assert metrics_data["success"] is True
            
            metrics = metrics_data["metrics"]
            assert metrics["total_recommendations"] == 0
            assert metrics["average_rating"] == 0.0
            assert "Insufficient data for analysis" in metrics["common_issues"]
            assert "Generate more recommendations to enable analysis" in metrics["improvement_suggestions"]
            
        finally:
            app.dependency_overrides.clear()
    
    def test_error_handling_invalid_recommendation_id(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        mock_current_user,
        mock_db_session
    ):
        """Test error handling for invalid recommendation IDs"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            # Test invalid UUID format
            feedback_data = {
                "rating": 4,
                "feedback_type": "general",
                "comments": "Test feedback"
            }
            
            response = client.post(
                "/outfit-recommendations/invalid-id/track-performance",
                json=feedback_data
            )
            assert response.status_code == 400
            assert "Invalid recommendation ID format" in response.json()["detail"]
            
            # Test valid UUID but non-existent recommendation
            import uuid
            fake_uuid = str(uuid.uuid4())
            response = client.post(
                f"/outfit-recommendations/{fake_uuid}/track-performance",
                json=feedback_data
            )
            assert response.status_code == 404
            assert "Recommendation not found" in response.json()["detail"]
            
        finally:
            app.dependency_overrides.clear()
    
    def test_missing_categories_tracking_accuracy(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        mock_current_user,
        mock_db_session
    ):
        """Test the accuracy of missing categories tracking"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            # Test the outfit matching service directly
            from app.services.outfit_matching_service import get_outfit_matching_service
            from app.services.gemini_service import OutfitRecommendation as GeminiOutfitRecommendation, OutfitItem
            
            matching_service = get_outfit_matching_service()
            
            # Create AI recommendation for formal wear (user has no formal items)
            ai_recommendation = GeminiOutfitRecommendation(
                top=OutfitItem(type="dress_shirt", features=["white", "cotton", "formal"]),
                bottom=OutfitItem(type="suit_pants", features=["navy", "wool", "formal"]),
                shoes=OutfitItem(type="dress_shoes", features=["black", "leather", "formal"]),
                outerwear=OutfitItem(type="blazer", features=["navy", "wool", "formal"])
            )
            
            # Match to empty closet (should track missing categories)
            match_result = matching_service.match_outfit_to_closet(
                db=db_session,
                user=test_user,
                ai_recommendation=ai_recommendation,
                weather="mild",
                style_preference="formal"
            )
            
            # Should have missing categories tracked
            assert match_result.missing_categories is not None
            assert len(match_result.missing_categories) > 0
            
            # Should track all the categories that couldn't be matched
            missing_categories = match_result.missing_categories
            expected_missing = ["top", "bottom", "shoes", "outerwear"]
            
            for category in expected_missing:
                assert category in missing_categories, f"Expected {category} to be in missing categories"
            
        finally:
            app.dependency_overrides.clear()
    
    def test_recommendation_analytics_comprehensive_workflow(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_recommendations_with_feedback: List[OutfitRecommendation],
        mock_current_user,
        mock_db_session
    ):
        """Test comprehensive analytics workflow"""
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_current_user
        app.dependency_overrides[get_sync_session] = mock_db_session
        
        try:
            # Step 1: Get current analytics
            analytics_response = client.get("/outfit-recommendations/analytics/stats")
            assert analytics_response.status_code == 200
            
            initial_analytics = analytics_response.json()
            initial_total = initial_analytics["total_recommendations"]
            
            # Step 2: Get improvement metrics
            metrics_response = client.get("/outfit-recommendations/improvement/metrics")
            assert metrics_response.status_code == 200
            
            metrics_data = metrics_response.json()
            assert metrics_data["success"] is True
            
            # Step 3: Get patterns
            patterns_response = client.get("/outfit-recommendations/improvement/patterns")
            assert patterns_response.status_code == 200
            
            patterns_data = patterns_response.json()
            assert patterns_data["success"] is True
            
            # Step 4: Get comprehensive recommendations
            recommendations_response = client.get("/outfit-recommendations/improvement/recommendations")
            assert recommendations_response.status_code == 200
            
            recommendations_data = recommendations_response.json()
            assert recommendations_data["success"] is True
            
            # Verify data consistency across endpoints
            improvement_data = recommendations_data["improvement_data"]
            month_metrics = improvement_data["metrics"]["month"]
            
            # Total recommendations should be consistent
            assert month_metrics["total_recommendations"] <= initial_total
            
            # Should have actionable insights
            assert len(improvement_data["personalized_tips"]) > 0
            assert len(improvement_data["next_steps"]) > 0
            
            # If we have patterns, they should be meaningful
            if improvement_data["patterns"]:
                for pattern in improvement_data["patterns"]:
                    assert pattern["frequency"] > 0
                    assert 0 <= pattern["success_rate"] <= 1
                    assert pattern["satisfaction"] > 0
            
        finally:
            app.dependency_overrides.clear()