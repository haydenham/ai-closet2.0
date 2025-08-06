"""
Tests for Feature Learning Service
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime, timedelta
import numpy as np

from app.services.feature_learning_service import FeatureLearningService
from app.models.quiz_system import (
    QuizClothingItem, FeatureLearningData, FeatureCorrelation,
    StyleAssignmentFeedback, QuizResponse, StyleCategory
)
from app.models.user import User


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def feature_learning_service(mock_db):
    """Feature learning service with mocked dependencies"""
    with patch('app.services.feature_learning_service.GCPVisionService'):
        service = FeatureLearningService(mock_db)
        return service


@pytest.fixture
def sample_clothing_item():
    """Sample clothing item for testing"""
    item = Mock(spec=QuizClothingItem)
    item.id = "test-item-id"
    item.name = "Test Shirt"
    item.image_url = "https://example.com/image.jpg"
    item.features = ["casual", "cotton"]
    item.auto_extracted_features = []
    item.feature_confidence_scores = {}
    item.satisfaction_score = None
    item.selection_count = 0
    
    # Mock methods
    item.has_feature = Mock(return_value=False)
    item.add_feature = Mock()
    item.remove_feature = Mock()
    item.update_satisfaction_score = Mock()
    
    return item


@pytest.fixture
def sample_quiz_response():
    """Sample quiz response for testing"""
    response = Mock(spec=QuizResponse)
    response.id = "test-response-id"
    response.user_id = "test-user-id"
    response.assigned_category = "casual"
    response.user_satisfaction_rating = 4
    response.selected_items = []
    return response


class TestFeatureLearningService:
    """Test cases for FeatureLearningService"""
    
    @pytest.mark.asyncio
    async def test_extract_features_from_image_success(self, feature_learning_service, mock_db, sample_clothing_item):
        """Test successful feature extraction from image"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_clothing_item
        
        # Mock vision service response
        vision_response = {
            'extracted_features': ['blue', 'cotton', 'casual'],
            'confidence_scores': {'blue': 0.9, 'cotton': 0.8, 'casual': 0.7},
            'suggested_category': 'top',
            'dominant_colors': [{'color_name': 'blue', 'score': 0.9}]
        }
        feature_learning_service.vision_service.analyze_clothing_image = Mock(return_value=vision_response)
        
        # Execute
        result = await feature_learning_service.extract_features_from_image("test-item-id", b"fake_image_data")
        
        # Verify
        assert result['success'] is True
        assert result['item_id'] == "test-item-id"
        assert result['extracted_features'] == ['blue', 'cotton', 'casual']
        assert result['confidence_scores'] == {'blue': 0.9, 'cotton': 0.8, 'casual': 0.7}
        
        # Verify database operations
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_extract_features_item_not_found(self, feature_learning_service, mock_db):
        """Test feature extraction when item is not found"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = await feature_learning_service.extract_features_from_image("nonexistent-id", b"fake_image_data")
        
        # Verify
        assert result['success'] is False
        assert 'error' in result
        assert "not found" in result['error']
    
    @pytest.mark.asyncio
    async def test_extract_features_vision_api_error(self, feature_learning_service, mock_db, sample_clothing_item):
        """Test feature extraction when Vision API returns error"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_clothing_item
        
        # Mock vision service error
        vision_response = {
            'error': 'Vision API error',
            'extracted_features': [],
            'confidence_scores': {},
            'suggested_category': 'unknown'
        }
        feature_learning_service.vision_service.analyze_clothing_image = Mock(return_value=vision_response)
        
        # Execute
        result = await feature_learning_service.extract_features_from_image("test-item-id", b"fake_image_data")
        
        # Verify
        assert 'error' in result
        assert result['error'] == 'Vision API error'
    
    @pytest.mark.asyncio
    async def test_batch_extract_features(self, feature_learning_service, mock_db, sample_clothing_item):
        """Test batch feature extraction"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_clothing_item
        
        # Mock download image data
        feature_learning_service._download_image_data = AsyncMock(return_value=b"fake_image_data")
        
        # Mock vision service
        vision_response = {
            'extracted_features': ['blue', 'cotton'],
            'confidence_scores': {'blue': 0.9, 'cotton': 0.8},
            'suggested_category': 'top',
            'success': True
        }
        feature_learning_service.extract_features_from_image = AsyncMock(return_value=vision_response)
        
        # Execute
        results = await feature_learning_service.batch_extract_features(["item1", "item2"])
        
        # Verify
        assert len(results) == 2
        assert all(result.get('success') for result in results)
    
    def test_track_user_satisfaction_success(self, feature_learning_service, mock_db, sample_quiz_response):
        """Test successful user satisfaction tracking"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quiz_response
        
        satisfaction_data = {
            'overall_rating': 4,
            'accuracy_rating': 4,
            'feedback_type': 'mostly_right',
            'detailed_feedback': 'Good recommendations',
            'feature_feedback': {},
            'item_ratings': {}
        }
        
        # Execute
        result = feature_learning_service.track_user_satisfaction(
            "test-user-id", "test-response-id", satisfaction_data
        )
        
        # Verify
        assert result is True
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
    
    def test_track_user_satisfaction_quiz_not_found(self, feature_learning_service, mock_db):
        """Test satisfaction tracking when quiz response not found"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        satisfaction_data = {'overall_rating': 4}
        
        # Execute
        result = feature_learning_service.track_user_satisfaction(
            "test-user-id", "nonexistent-id", satisfaction_data
        )
        
        # Verify
        assert result is False
    
    def test_discover_feature_patterns_success(self, feature_learning_service, mock_db):
        """Test successful feature pattern discovery"""
        # Setup - create mock items with features
        mock_items = []
        for i in range(10):
            item = Mock(spec=QuizClothingItem)
            item.features = ['casual', 'cotton'] if i < 5 else ['formal', 'silk']
            item.auto_extracted_features = ['blue'] if i % 2 == 0 else ['black']
            mock_items.append(item)
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_items
        
        # Execute
        patterns = feature_learning_service.discover_feature_patterns(min_support=0.3)
        
        # Verify
        assert isinstance(patterns, list)
        # Should discover patterns based on the mock data
    
    def test_discover_feature_patterns_insufficient_data(self, feature_learning_service, mock_db):
        """Test pattern discovery with insufficient data"""
        # Setup - return too few items
        mock_db.query.return_value.filter.return_value.all.return_value = [Mock(), Mock()]
        
        # Execute
        patterns = feature_learning_service.discover_feature_patterns()
        
        # Verify
        assert patterns == []
    
    def test_validate_features_success(self, feature_learning_service, mock_db):
        """Test successful feature validation"""
        # Setup
        mock_learning_data = Mock(spec=FeatureLearningData)
        mock_learning_data.validation_count = 0
        mock_learning_data.rejection_count = 0
        mock_learning_data.validation_ratio = 1.0
        
        mock_item = Mock(spec=QuizClothingItem)
        mock_item.has_feature.return_value = False
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_learning_data, mock_item]
        
        validation_data = [{
            'feature_name': 'casual',
            'item_id': 'test-item-id',
            'is_valid': True,
            'confidence': 0.9
        }]
        
        # Execute
        result = feature_learning_service.validate_features(validation_data)
        
        # Verify
        assert result['validated'] == 1
        assert result['rejected'] == 0
        assert mock_learning_data.validation_count == 1
        mock_db.commit.assert_called()
    
    def test_validate_features_rejection(self, feature_learning_service, mock_db):
        """Test feature validation with rejection"""
        # Setup
        mock_learning_data = Mock(spec=FeatureLearningData)
        mock_learning_data.validation_count = 0
        mock_learning_data.rejection_count = 0
        mock_learning_data.validation_ratio = 0.0
        
        mock_item = Mock(spec=QuizClothingItem)
        mock_item.has_feature.return_value = True
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_learning_data, mock_item]
        
        validation_data = [{
            'feature_name': 'casual',
            'item_id': 'test-item-id',
            'is_valid': False,
            'confidence': 0.9
        }]
        
        # Execute
        result = feature_learning_service.validate_features(validation_data)
        
        # Verify
        assert result['validated'] == 0
        assert result['rejected'] == 1
        assert mock_learning_data.rejection_count == 1
    
    def test_mine_feature_correlations_success(self, feature_learning_service, mock_db):
        """Test successful feature correlation mining"""
        # Setup - create mock items with overlapping features
        mock_items = []
        for i in range(10):
            item = Mock(spec=QuizClothingItem)
            if i < 5:
                item.features = ['casual', 'cotton']
                item.auto_extracted_features = ['blue']
            else:
                item.features = ['formal', 'silk']
                item.auto_extracted_features = ['black']
            mock_items.append(item)
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing correlations
        
        # Execute
        correlations = feature_learning_service.mine_feature_correlations()
        
        # Verify
        assert isinstance(correlations, list)
        mock_db.add.assert_called()  # Should add new correlations
        mock_db.commit.assert_called()
    
    def test_mine_feature_correlations_no_items(self, feature_learning_service, mock_db):
        """Test correlation mining with no items"""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Execute
        correlations = feature_learning_service.mine_feature_correlations()
        
        # Verify
        assert correlations == []
    
    def test_analyze_behavioral_patterns_success(self, feature_learning_service, mock_db):
        """Test successful behavioral pattern analysis"""
        # Setup
        mock_responses = []
        for i in range(5):
            response = Mock(spec=QuizResponse)
            response.assigned_category = 'casual'
            response.user_satisfaction_rating = 4
            response.selected_items = []
            mock_responses.append(response)
        
        mock_db.query.return_value.all.return_value = mock_responses
        
        # Execute
        result = feature_learning_service.analyze_behavioral_patterns()
        
        # Verify
        assert result['total_responses'] == 5
        assert 'style_accuracy' in result
        assert 'feature_preferences' in result
        assert 'recommendations' in result
    
    def test_analyze_behavioral_patterns_no_data(self, feature_learning_service, mock_db):
        """Test behavioral analysis with no data"""
        # Setup
        mock_db.query.return_value.all.return_value = []
        
        # Execute
        result = feature_learning_service.analyze_behavioral_patterns()
        
        # Verify
        assert 'error' in result
        assert 'No quiz responses found' in result['error']
    
    @pytest.mark.asyncio
    async def test_run_daily_improvement_cycle_success(self, feature_learning_service, mock_db):
        """Test successful daily improvement cycle"""
        # Setup - mock all the sub-methods
        feature_learning_service.batch_extract_features = AsyncMock(return_value=[])
        feature_learning_service.discover_feature_patterns = Mock(return_value=[])
        feature_learning_service.mine_feature_correlations = Mock(return_value=[])
        feature_learning_service.analyze_behavioral_patterns = Mock(return_value={'total_responses': 0})
        feature_learning_service._process_pending_validations = Mock(return_value={'processed_feedback': 0})
        feature_learning_service._cleanup_old_learning_data = Mock(return_value={'removed_entries': 0})
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        # Execute
        result = await feature_learning_service.run_daily_improvement_cycle()
        
        # Verify
        assert 'timestamp' in result
        assert 'feature_extraction' in result
        assert 'pattern_discovery' in result
        assert 'correlation_mining' in result
        assert 'behavioral_analysis' in result
        assert 'validation_updates' in result
        assert isinstance(result['errors'], list)
    
    @pytest.mark.asyncio
    async def test_run_daily_improvement_cycle_with_errors(self, feature_learning_service, mock_db):
        """Test daily improvement cycle with errors"""
        # Setup - make one method raise an exception
        feature_learning_service.batch_extract_features = AsyncMock(side_effect=Exception("Test error"))
        feature_learning_service.discover_feature_patterns = Mock(return_value=[])
        feature_learning_service.mine_feature_correlations = Mock(return_value=[])
        feature_learning_service.analyze_behavioral_patterns = Mock(return_value={'total_responses': 0})
        feature_learning_service._process_pending_validations = Mock(return_value={'processed_feedback': 0})
        feature_learning_service._cleanup_old_learning_data = Mock(return_value={'removed_entries': 0})
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        # Execute
        result = await feature_learning_service.run_daily_improvement_cycle()
        
        # Verify
        assert len(result['errors']) > 0
        assert any('Test error' in error for error in result['errors'])
    
    def test_get_learning_metrics_success(self, feature_learning_service, mock_db):
        """Test successful learning metrics retrieval"""
        # Setup - mock database queries
        mock_db.query.return_value.count.return_value = 100
        mock_db.query.return_value.filter.return_value.count.return_value = 80
        mock_db.query.return_value.group_by.return_value.all.return_value = [
            ('manual', 50), ('cv_auto', 30)
        ]
        
        # Execute
        result = feature_learning_service.get_learning_metrics()
        
        # Verify
        assert 'feature_extraction' in result
        assert 'feature_learning' in result
        assert 'correlations' in result
        assert 'user_satisfaction' in result
        assert 'feature_sources' in result
        
        assert result['feature_extraction']['total_items'] == 100
        assert result['feature_sources']['manual'] == 50
        assert result['feature_sources']['cv_auto'] == 30
    
    def test_get_learning_metrics_database_error(self, feature_learning_service, mock_db):
        """Test learning metrics with database error"""
        # Setup
        mock_db.query.side_effect = Exception("Database error")
        
        # Execute
        result = feature_learning_service.get_learning_metrics()
        
        # Verify
        assert 'error' in result
        assert 'Database error' in result['error']
    
    @pytest.mark.asyncio
    async def test_download_image_data_success(self, feature_learning_service):
        """Test successful image download"""
        # Setup
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"image_data")
        
        mock_session = Mock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            # Execute
            result = await feature_learning_service._download_image_data("https://example.com/image.jpg")
            
            # Verify
            assert result == b"image_data"
    
    @pytest.mark.asyncio
    async def test_download_image_data_failure(self, feature_learning_service):
        """Test image download failure"""
        # Setup
        mock_response = Mock()
        mock_response.status = 404
        
        mock_session = Mock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            # Execute
            result = await feature_learning_service._download_image_data("https://example.com/nonexistent.jpg")
            
            # Verify
            assert result is None
    
    def test_validate_features_from_feedback(self, feature_learning_service, mock_db):
        """Test feature validation from user feedback"""
        # Setup
        mock_feedback = Mock(spec=StyleAssignmentFeedback)
        mock_feedback.feature_feedback = {
            'item1': {'casual': True, 'formal': False}
        }
        
        mock_quiz_response = Mock(spec=QuizResponse)
        mock_item = Mock(spec=QuizClothingItem)
        mock_item.id = 'item1'
        mock_quiz_response.selected_items = [mock_item]
        mock_feedback.quiz_response = mock_quiz_response
        
        mock_learning_data = Mock(spec=FeatureLearningData)
        mock_learning_data.validation_count = 0
        mock_learning_data.rejection_count = 0
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_learning_data
        
        # Execute
        feature_learning_service._validate_features_from_feedback(mock_feedback)
        
        # Verify
        assert mock_learning_data.validation_count == 1  # 'casual': True
        assert mock_learning_data.rejection_count == 1   # 'formal': False
        mock_db.commit.assert_called()
    
    def test_store_feature_pattern(self, feature_learning_service, mock_db):
        """Test storing discovered feature pattern"""
        # Setup
        pattern = {
            'features': ['casual', 'cotton', 'blue'],
            'confidence': 0.8,
            'item_count': 10
        }
        
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing correlation
        
        # Execute
        feature_learning_service._store_feature_pattern(pattern)
        
        # Verify
        # Should create correlations for all feature pairs
        expected_pairs = 3  # (casual,cotton), (casual,blue), (cotton,blue)
        assert mock_db.add.call_count == expected_pairs
        mock_db.commit.assert_called()
    
    def test_process_pending_validations(self, feature_learning_service, mock_db):
        """Test processing pending validations"""
        # Setup
        mock_feedback = Mock(spec=StyleAssignmentFeedback)
        mock_feedback.created_at = datetime.utcnow()
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_feedback]
        
        feature_learning_service._validate_features_from_feedback = Mock()
        
        # Execute
        result = feature_learning_service._process_pending_validations()
        
        # Verify
        assert result['processed_feedback'] == 1
        assert result['status'] == 'success'
        feature_learning_service._validate_features_from_feedback.assert_called_once_with(mock_feedback)
    
    def test_cleanup_old_learning_data(self, feature_learning_service, mock_db):
        """Test cleanup of old learning data"""
        # Setup
        old_data = [Mock(spec=FeatureLearningData) for _ in range(3)]
        mock_db.query.return_value.filter.return_value.all.return_value = old_data
        
        # Execute
        result = feature_learning_service._cleanup_old_learning_data()
        
        # Verify
        assert result['removed_entries'] == 3
        assert result['status'] == 'success'
        assert mock_db.delete.call_count == 3
        mock_db.commit.assert_called()


@pytest.mark.integration
class TestFeatureLearningIntegration:
    """Integration tests for feature learning service"""
    
    @pytest.mark.asyncio
    async def test_full_learning_cycle_integration(self, feature_learning_service, mock_db):
        """Test complete learning cycle integration"""
        # This would be a more comprehensive test that exercises
        # multiple components together in a realistic scenario
        pass
    
    def test_feature_correlation_accuracy(self, feature_learning_service, mock_db):
        """Test accuracy of feature correlation calculations"""
        # This would test the mathematical accuracy of correlation calculations
        # with known input data and expected outputs
        pass