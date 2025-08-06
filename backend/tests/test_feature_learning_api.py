"""
Tests for Feature Learning API endpoints
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

from app.api.feature_learning import router
from app.models.user import User


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    user = Mock(spec=User)
    user.id = "test-user-id"
    user.email = "test@example.com"
    return user


@pytest.fixture
def client():
    """Test client for API endpoints"""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestFeatureLearningAPI:
    """Test cases for Feature Learning API endpoints"""
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_extract_features_success(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test successful feature extraction endpoint"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.batch_extract_features = AsyncMock(return_value=[
            {'success': True, 'item_id': 'item1'},
            {'success': True, 'item_id': 'item2'}
        ])
        mock_service_class.return_value = mock_service
        
        # Mock database query for unprocessed items
        mock_db.query.return_value.filter.return_value.all.return_value = [
            Mock(id='item1'), Mock(id='item2')
        ]
        
        request_data = {
            "item_ids": ["item1", "item2"],
            "force_reprocess": False
        }
        
        # Execute
        response = client.post("/feature-learning/extract-features", json=request_data)
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["processed_items"] == 2
        assert data["successful_extractions"] == 2
        assert data["failed_extractions"] == 0
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_extract_features_large_batch_background(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test feature extraction with large batch processed in background"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock database query for many unprocessed items
        mock_items = [Mock(id=f'item{i}') for i in range(15)]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_items
        
        request_data = {
            "item_ids": [f"item{i}" for i in range(15)],
            "force_reprocess": False
        }
        
        # Execute
        response = client.post("/feature-learning/extract-features", json=request_data)
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["processed_items"] == 15
        assert "Processing started in background" in str(data["results"])
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_extract_features_no_items_to_process(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test feature extraction when no items need processing"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock database query returning no unprocessed items
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        request_data = {
            "item_ids": ["item1", "item2"],
            "force_reprocess": False
        }
        
        # Execute
        response = client.post("/feature-learning/extract-features", json=request_data)
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["processed_items"] == 0
        assert data["successful_extractions"] == 0
        assert data["failed_extractions"] == 0
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_extract_features_service_error(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test feature extraction with service error"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.batch_extract_features = AsyncMock(side_effect=Exception("Service error"))
        mock_service_class.return_value = mock_service
        
        mock_db.query.return_value.filter.return_value.all.return_value = [Mock(id='item1')]
        
        request_data = {
            "item_ids": ["item1"],
            "force_reprocess": False
        }
        
        # Execute
        response = client.post("/feature-learning/extract-features", json=request_data)
        
        # Verify
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Service error" in response.json()["detail"]
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_track_satisfaction_success(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test successful satisfaction tracking"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.track_user_satisfaction.return_value = True
        mock_service_class.return_value = mock_service
        
        request_data = {
            "quiz_response_id": "test-response-id",
            "overall_rating": 4,
            "accuracy_rating": 4,
            "feedback_type": "mostly_right",
            "detailed_feedback": "Good recommendations"
        }
        
        # Execute
        response = client.post("/feature-learning/track-satisfaction", json=request_data)
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "tracked successfully" in data["message"]
        
        # Verify service was called with correct parameters
        mock_service.track_user_satisfaction.assert_called_once()
        call_args = mock_service.track_user_satisfaction.call_args
        assert call_args[0][0] == str(mock_current_user.id)
        assert call_args[0][1] == "test-response-id"
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_track_satisfaction_failure(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test satisfaction tracking failure"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.track_user_satisfaction.return_value = False
        mock_service_class.return_value = mock_service
        
        request_data = {
            "quiz_response_id": "test-response-id",
            "overall_rating": 4,
            "accuracy_rating": 4,
            "feedback_type": "mostly_right"
        }
        
        # Execute
        response = client.post("/feature-learning/track-satisfaction", json=request_data)
        
        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Failed to track satisfaction" in response.json()["detail"]
    
    def test_track_satisfaction_invalid_rating(self, client):
        """Test satisfaction tracking with invalid rating"""
        request_data = {
            "quiz_response_id": "test-response-id",
            "overall_rating": 6,  # Invalid - should be 1-5
            "accuracy_rating": 4,
            "feedback_type": "mostly_right"
        }
        
        # Execute
        response = client.post("/feature-learning/track-satisfaction", json=request_data)
        
        # Verify
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_discover_patterns_immediate(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test immediate pattern discovery"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_patterns = [
            {'features': ['casual', 'cotton'], 'confidence': 0.8},
            {'features': ['formal', 'silk'], 'confidence': 0.9}
        ]
        mock_service.discover_feature_patterns.return_value = mock_patterns
        mock_service_class.return_value = mock_service
        
        request_data = {
            "min_support": 0.2,
            "force_refresh": False
        }
        
        # Execute
        response = client.post("/feature-learning/discover-patterns", json=request_data)
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["patterns_discovered"] == 2
        assert len(data["patterns"]) == 2
        assert data["min_support"] == 0.2
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_discover_patterns_background(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test background pattern discovery"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        request_data = {
            "min_support": 0.1,
            "force_refresh": True
        }
        
        # Execute
        response = client.post("/feature-learning/discover-patterns", json=request_data)
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "started in background" in data["message"]
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_validate_features_success(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test successful feature validation"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.validate_features.return_value = {
            'validated': 2,
            'rejected': 1,
            'updated_features': []
        }
        mock_service_class.return_value = mock_service
        
        request_data = {
            "validations": [
                {
                    "feature_name": "casual",
                    "item_id": "item1",
                    "is_valid": True,
                    "confidence": 0.9
                },
                {
                    "feature_name": "formal",
                    "item_id": "item2",
                    "is_valid": False,
                    "confidence": 0.7
                }
            ]
        }
        
        # Execute
        response = client.post("/feature-learning/validate-features", json=request_data)
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["validation_results"]["validated"] == 2
        assert data["validation_results"]["rejected"] == 1
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_validate_features_service_error(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test feature validation with service error"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.validate_features.return_value = {'error': 'Validation failed'}
        mock_service_class.return_value = mock_service
        
        request_data = {
            "validations": [
                {
                    "feature_name": "casual",
                    "item_id": "item1",
                    "is_valid": True
                }
            ]
        }
        
        # Execute
        response = client.post("/feature-learning/validate-features", json=request_data)
        
        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Validation failed" in response.json()["detail"]
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    def test_get_correlations_success(self, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test successful correlation retrieval"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        # Mock correlation objects
        mock_correlation = Mock()
        mock_correlation.feature_a = 'casual'
        mock_correlation.feature_b = 'cotton'
        mock_correlation.correlation_strength = 0.8
        mock_correlation.co_occurrence_count = 10
        mock_correlation.co_occurrence_rate = 0.5
        mock_correlation.updated_at = Mock()
        mock_correlation.updated_at.isoformat.return_value = '2023-01-01T00:00:00'
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_correlation]
        
        # Execute
        response = client.get("/feature-learning/correlations?min_strength=0.3&limit=10")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["correlations"]) == 1
        assert data["correlations"][0]["feature_a"] == "casual"
        assert data["correlations"][0]["feature_b"] == "cotton"
        assert data["min_strength_filter"] == 0.3
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_mine_correlations_success(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test successful correlation mining"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.post("/feature-learning/mine-correlations")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "started in background" in data["message"]
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.BehavioralAnalysisService')
    def test_get_behavioral_analysis_style_accuracy(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test behavioral analysis for style accuracy"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.analyze_style_assignment_accuracy.return_value = {
            'total_responses_analyzed': 50,
            'style_accuracy': {'casual': {'high_accuracy_rate': 0.8}}
        }
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.get("/feature-learning/behavioral-analysis?analysis_type=style_accuracy&time_period_days=30")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["analysis_type"] == "style_accuracy"
        assert data["results"]["total_responses_analyzed"] == 50
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.BehavioralAnalysisService')
    def test_get_behavioral_analysis_invalid_type(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test behavioral analysis with invalid analysis type"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        # Execute
        response = client.get("/feature-learning/behavioral-analysis?analysis_type=invalid_type")
        
        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unknown analysis type" in response.json()["detail"]
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.BehavioralAnalysisService')
    def test_get_improvement_recommendations_success(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test successful improvement recommendations retrieval"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_recommendations = [
            {
                'priority': 'high',
                'category': 'style_improvement',
                'recommendation': 'Improve casual style accuracy'
            }
        ]
        mock_service.generate_improvement_recommendations.return_value = mock_recommendations
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.get("/feature-learning/improvement-recommendations")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["recommendations"]) == 1
        assert data["total_recommendations"] == 1
        assert data["recommendations"][0]["priority"] == "high"
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_get_learning_metrics_success(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test successful learning metrics retrieval"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_metrics = {
            'feature_extraction': {'total_items': 100, 'items_with_auto_features': 80, 'extraction_coverage': 0.8},
            'feature_learning': {'total_learning_entries': 200, 'validated_features': 150, 'validation_rate': 0.75},
            'correlations': {'total_correlations': 50, 'strong_correlations': 20, 'strong_correlation_rate': 0.4},
            'user_satisfaction': {'total_responses': 300, 'satisfied_responses': 240, 'satisfaction_rate': 0.8},
            'feature_sources': {'manual': 100, 'cv_auto': 80, 'user_suggested': 20}
        }
        mock_service.get_learning_metrics.return_value = mock_metrics
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.get("/feature-learning/metrics")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["feature_extraction"]["total_items"] == 100
        assert data["user_satisfaction"]["satisfaction_rate"] == 0.8
        assert data["feature_sources"]["manual"] == 100
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    @patch('app.api.feature_learning.FeatureLearningService')
    def test_run_daily_improvement_cycle_success(self, mock_service_class, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test successful daily improvement cycle trigger"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.post("/feature-learning/daily-improvement-cycle")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "started in background" in data["message"]
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    def test_get_item_learning_data_success(self, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test successful item learning data retrieval"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        # Mock clothing item
        mock_item = Mock()
        mock_item.id = "test-item-id"
        mock_item.name = "Test Shirt"
        mock_item.features = ["casual", "cotton"]
        mock_item.auto_extracted_features = ["blue"]
        mock_item.feature_confidence_scores = {"blue": 0.9}
        mock_item.satisfaction_score = 4.2
        mock_item.selection_count = 5
        
        # Mock learning data
        mock_learning_data = Mock()
        mock_learning_data.feature_name = "casual"
        mock_learning_data.source = "manual"
        mock_learning_data.confidence_score = 0.8
        mock_learning_data.validation_count = 3
        mock_learning_data.rejection_count = 1
        mock_learning_data.validation_ratio = 0.75
        mock_learning_data.created_at = Mock()
        mock_learning_data.created_at.isoformat.return_value = '2023-01-01T00:00:00'
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_item
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_learning_data]
        
        # Execute
        response = client.get("/feature-learning/learning-data/test-item-id")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["item_id"] == "test-item-id"
        assert data["item_name"] == "Test Shirt"
        assert data["manual_features"] == ["casual", "cotton"]
        assert data["auto_extracted_features"] == ["blue"]
        assert len(data["learning_data"]) == 1
        assert data["learning_data"][0]["feature_name"] == "casual"
    
    @patch('app.api.feature_learning.get_db')
    @patch('app.api.feature_learning.get_current_user')
    def test_get_item_learning_data_not_found(self, mock_get_user, mock_get_db, client, mock_current_user, mock_db):
        """Test item learning data retrieval for non-existent item"""
        # Setup
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_current_user
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        response = client.get("/feature-learning/learning-data/nonexistent-id")
        
        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]


@pytest.mark.integration
class TestFeatureLearningAPIIntegration:
    """Integration tests for Feature Learning API"""
    
    def test_complete_learning_workflow(self, client):
        """Test complete learning workflow from extraction to analysis"""
        # This would test the full workflow:
        # 1. Extract features from images
        # 2. Track user satisfaction
        # 3. Validate features
        # 4. Discover patterns
        # 5. Mine correlations
        # 6. Generate recommendations
        pass
    
    def test_api_error_handling(self, client):
        """Test API error handling across all endpoints"""
        # This would test various error scenarios:
        # - Invalid input data
        # - Database errors
        # - Service failures
        # - Authentication issues
        pass