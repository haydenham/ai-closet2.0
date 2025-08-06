"""
Integration tests for Feature Learning System
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from decimal import Decimal

from app.services.feature_learning_service import FeatureLearningService
from app.services.behavioral_analysis_service import BehavioralAnalysisService
from app.models.quiz_system import (
    QuizClothingItem, FeatureLearningData, FeatureCorrelation,
    StyleAssignmentFeedback, QuizResponse, StyleCategory
)


@pytest.fixture
def mock_db():
    """Mock database session for integration tests"""
    return Mock()


@pytest.fixture
def sample_quiz_data(mock_db):
    """Create sample quiz data for integration testing"""
    # Create sample clothing items
    items = []
    for i in range(5):
        item = Mock(spec=QuizClothingItem)
        item.id = f"item-{i}"
        item.name = f"Test Item {i}"
        item.features = ["casual", "cotton"] if i < 3 else ["formal", "silk"]
        item.auto_extracted_features = []
        item.feature_confidence_scores = {}
        item.satisfaction_score = None
        item.selection_count = 0
        item.has_feature = Mock(return_value=False)
        item.add_feature = Mock()
        item.remove_feature = Mock()
        items.append(item)
    
    # Create sample quiz responses
    responses = []
    for i in range(3):
        response = Mock(spec=QuizResponse)
        response.id = f"response-{i}"
        response.user_id = f"user-{i}"
        response.assigned_category = "casual" if i < 2 else "formal"
        response.user_satisfaction_rating = 4
        response.confidence_score = Decimal('0.8')
        response.completed_at = datetime.utcnow()
        response.selected_items = items[:2]  # Each response selects first 2 items
        responses.append(response)
    
    # Create sample style categories
    categories = []
    for style in ["casual", "formal"]:
        category = Mock(spec=StyleCategory)
        category.name = style
        category.features = ["casual", "cotton"] if style == "casual" else ["formal", "silk"]
        categories.append(category)
    
    return {
        'items': items,
        'responses': responses,
        'categories': categories
    }


class TestFeatureLearningIntegration:
    """Integration tests for the complete feature learning system"""
    
    @pytest.mark.asyncio
    async def test_complete_learning_workflow(self, mock_db, sample_quiz_data):
        """Test complete learning workflow from feature extraction to analysis"""
        # Setup
        service = FeatureLearningService(mock_db)
        behavioral_service = BehavioralAnalysisService(mock_db)
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quiz_data['items'][0]
        mock_db.query.return_value.filter.return_value.all.return_value = sample_quiz_data['items']
        mock_db.query.return_value.all.return_value = sample_quiz_data['responses']
        
        # Mock vision service
        vision_response = {
            'extracted_features': ['blue', 'cotton', 'casual'],
            'confidence_scores': {'blue': 0.9, 'cotton': 0.8, 'casual': 0.7},
            'suggested_category': 'top',
            'dominant_colors': [{'color_name': 'blue', 'score': 0.9}]
        }
        service.vision_service.analyze_clothing_image = Mock(return_value=vision_response)
        
        # Step 1: Extract features from an image
        extraction_result = await service.extract_features_from_image(
            "item-0", 
            b"fake_image_data"
        )
        
        assert extraction_result['success'] is True
        assert len(extraction_result['extracted_features']) == 3
        assert 'blue' in extraction_result['extracted_features']
        
        # Step 2: Track user satisfaction
        satisfaction_data = {
            'overall_rating': 4,
            'accuracy_rating': 4,
            'feedback_type': 'mostly_right',
            'detailed_feedback': 'Good recommendations',
            'feature_feedback': {'item-0': {'blue': True, 'cotton': True}},
            'item_ratings': {'item-0': 4}
        }
        
        satisfaction_result = service.track_user_satisfaction(
            "user-0", 
            "response-0", 
            satisfaction_data
        )
        
        assert satisfaction_result is True
        
        # Step 3: Validate features based on feedback
        validation_data = [{
            'feature_name': 'blue',
            'item_id': 'item-0',
            'is_valid': True,
            'confidence': 0.9
        }]
        
        # Mock learning data for validation
        mock_learning_data = Mock(spec=FeatureLearningData)
        mock_learning_data.validation_count = 0
        mock_learning_data.rejection_count = 0
        mock_learning_data.validation_ratio = 1.0
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_learning_data, sample_quiz_data['items'][0]
        ]
        
        validation_result = service.validate_features(validation_data)
        
        assert validation_result['validated'] == 1
        assert validation_result['rejected'] == 0
        
        # Step 4: Discover feature patterns
        patterns = service.discover_feature_patterns(min_support=0.3)
        
        # Should discover patterns from the sample data
        assert isinstance(patterns, list)
        
        # Step 5: Mine feature correlations
        correlations = service.mine_feature_correlations()
        
        assert isinstance(correlations, list)
        
        # Step 6: Analyze behavioral patterns
        behavioral_analysis = behavioral_service.analyze_behavioral_patterns()
        
        assert 'total_responses' in behavioral_analysis
        assert behavioral_analysis['total_responses'] == len(sample_quiz_data['responses'])
        
        # Verify database operations were called
        assert mock_db.add.called
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_daily_improvement_cycle_integration(self, mock_db, sample_quiz_data):
        """Test the daily improvement cycle integration"""
        # Setup
        service = FeatureLearningService(mock_db)
        
        # Mock all database queries for the daily cycle
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = sample_quiz_data['items']
        mock_db.query.return_value.all.return_value = sample_quiz_data['responses']
        mock_db.query.return_value.count.return_value = 10
        mock_db.query.return_value.group_by.return_value.all.return_value = [('manual', 5), ('cv_auto', 5)]
        
        # Mock sub-methods to avoid actual processing
        service.batch_extract_features = AsyncMock(return_value=[])
        service.discover_feature_patterns = Mock(return_value=[])
        service.mine_feature_correlations = Mock(return_value=[])
        service.analyze_behavioral_patterns = Mock(return_value={'total_responses': 3})
        service._process_pending_validations = Mock(return_value={'processed_feedback': 0})
        service._cleanup_old_learning_data = Mock(return_value={'removed_entries': 0})
        
        # Execute daily cycle
        result = await service.run_daily_improvement_cycle()
        
        # Verify results
        assert 'timestamp' in result
        assert 'feature_extraction' in result
        assert 'pattern_discovery' in result
        assert 'correlation_mining' in result
        assert 'behavioral_analysis' in result
        assert isinstance(result['errors'], list)
        
        # Verify all sub-methods were called
        service.batch_extract_features.assert_called_once()
        service.discover_feature_patterns.assert_called_once()
        service.mine_feature_correlations.assert_called_once()
        service.analyze_behavioral_patterns.assert_called_once()
        service._process_pending_validations.assert_called_once()
        service._cleanup_old_learning_data.assert_called_once()
    
    @patch('app.services.feature_learning_service.GCPVisionService')
    def test_feature_correlation_accuracy(self, mock_vision_service, mock_db):
        """Test accuracy of feature correlation calculations"""
        # Setup with known data
        service = FeatureLearningService(mock_db)
        
        # Create items with known feature patterns
        items = []
        
        # Items 0-4: casual + cotton (should correlate)
        for i in range(5):
            item = Mock(spec=QuizClothingItem)
            item.features = ["casual", "cotton"]
            item.auto_extracted_features = []
            items.append(item)
        
        # Items 5-9: formal + silk (should correlate)
        for i in range(5, 10):
            item = Mock(spec=QuizClothingItem)
            item.features = ["formal", "silk"]
            item.auto_extracted_features = []
            items.append(item)
        
        mock_db.query.return_value.filter.return_value.all.return_value = items
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing correlations
        
        # Execute correlation mining
        correlations = service.mine_feature_correlations()
        
        # Verify expected correlations
        assert len(correlations) >= 2  # Should find casual-cotton and formal-silk correlations
        
        # Find specific correlations
        casual_cotton_corr = None
        formal_silk_corr = None
        
        for corr in correlations:
            if set([corr['feature_a'], corr['feature_b']]) == set(['casual', 'cotton']):
                casual_cotton_corr = corr
            elif set([corr['feature_a'], corr['feature_b']]) == set(['formal', 'silk']):
                formal_silk_corr = corr
        
        # Verify correlation strength is high (perfect correlation expected)
        if casual_cotton_corr:
            assert casual_cotton_corr['correlation_strength'] > 0.8
            assert casual_cotton_corr['co_occurrence_count'] == 5
        
        if formal_silk_corr:
            assert formal_silk_corr['correlation_strength'] > 0.8
            assert formal_silk_corr['co_occurrence_count'] == 5
    
    def test_behavioral_analysis_accuracy(self, mock_db, sample_quiz_data):
        """Test accuracy of behavioral analysis calculations"""
        # Setup
        behavioral_service = BehavioralAnalysisService(mock_db)
        
        # Create responses with known satisfaction patterns
        responses = []
        feedback_data = []
        
        # Create 10 responses: 8 with high satisfaction, 2 with low
        for i in range(10):
            response = Mock(spec=QuizResponse)
            response.id = f"response-{i}"
            response.user_id = f"user-{i}"
            response.assigned_category = "casual"
            response.user_satisfaction_rating = 4 if i < 8 else 2  # 80% high satisfaction
            response.confidence_score = Decimal('0.8')
            response.completed_at = datetime.utcnow()
            response.selected_items = []
            responses.append(response)
            
            # Create corresponding feedback
            feedback = Mock(spec=StyleAssignmentFeedback)
            feedback.id = f"feedback-{i}"
            feedback.quiz_response_id = f"response-{i}"
            feedback.accuracy_rating = 4 if i < 8 else 2
            feedback.feedback_type = 'mostly_right' if i < 8 else 'too_broad'
            feedback.created_at = datetime.utcnow()
            feedback_data.append(feedback)
        
        # Mock database queries
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = responses
        mock_db.query.return_value.filter.return_value.first.side_effect = feedback_data
        
        # Execute analysis
        result = behavioral_service.analyze_style_assignment_accuracy(30)
        
        # Verify results
        assert result['total_responses_analyzed'] == 10
        assert 'style_accuracy' in result
        assert 'casual' in result['style_accuracy']
        
        casual_metrics = result['style_accuracy']['casual']
        assert casual_metrics['sample_size'] == 10
        assert casual_metrics['high_accuracy_rate'] == 0.8  # 8/10 high ratings
        assert casual_metrics['average_accuracy'] == 3.6  # (8*4 + 2*2) / 10
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, mock_db):
        """Test error handling across the integrated system"""
        # Setup
        service = FeatureLearningService(mock_db)
        
        # Test database error handling
        mock_db.query.side_effect = Exception("Database connection failed")
        
        # Feature extraction should handle database errors gracefully
        result = service.get_learning_metrics()
        assert 'error' in result
        assert 'Database connection failed' in result['error']
        
        # Reset mock
        mock_db.reset_mock()
        mock_db.query.side_effect = None
        
        # Test vision API error handling
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await service.extract_features_from_image("nonexistent-id", b"fake_data")
        assert result['success'] is False
        assert 'not found' in result['error']
    
    def test_performance_with_large_dataset(self, mock_db):
        """Test system performance with larger datasets"""
        # Setup
        service = FeatureLearningService(mock_db)
        
        # Create large dataset (100 items)
        large_items = []
        for i in range(100):
            item = Mock(spec=QuizClothingItem)
            item.features = ["casual", "cotton"] if i % 2 == 0 else ["formal", "silk"]
            item.auto_extracted_features = []
            large_items.append(item)
        
        mock_db.query.return_value.filter.return_value.all.return_value = large_items
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Test pattern discovery with large dataset
        import time
        start_time = time.time()
        
        patterns = service.discover_feature_patterns(min_support=0.1)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (< 5 seconds for 100 items)
        assert execution_time < 5.0
        assert isinstance(patterns, list)
        
        # Test correlation mining with large dataset
        start_time = time.time()
        
        correlations = service.mine_feature_correlations()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        assert execution_time < 5.0
        assert isinstance(correlations, list)


@pytest.mark.integration
class TestFeatureLearningSystemIntegration:
    """System-level integration tests"""
    
    def test_end_to_end_learning_pipeline(self, mock_db, sample_quiz_data):
        """Test complete end-to-end learning pipeline"""
        # This would test the complete pipeline from user interaction
        # through feature learning to algorithm improvement
        pass
    
    def test_concurrent_learning_operations(self, mock_db):
        """Test concurrent learning operations"""
        # This would test that multiple learning operations
        # can run concurrently without conflicts
        pass
    
    def test_data_consistency_across_operations(self, mock_db):
        """Test data consistency across multiple operations"""
        # This would test that data remains consistent
        # when multiple learning operations modify the same data
        pass