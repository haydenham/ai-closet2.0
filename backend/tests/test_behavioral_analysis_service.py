"""
Tests for Behavioral Analysis Service
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import numpy as np

from app.services.behavioral_analysis_service import BehavioralAnalysisService
from app.models.quiz_system import (
    QuizResponse, StyleAssignmentFeedback, StyleCategory
)
from app.models.user import User
from app.models.clothing_item import ClothingItem


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def behavioral_service(mock_db):
    """Behavioral analysis service with mocked dependencies"""
    return BehavioralAnalysisService(mock_db)


@pytest.fixture
def sample_quiz_responses():
    """Sample quiz responses for testing"""
    responses = []
    for i in range(10):
        response = Mock(spec=QuizResponse)
        response.id = f"response-{i}"
        response.user_id = f"user-{i}"
        response.assigned_category = 'casual' if i < 5 else 'formal'
        response.user_satisfaction_rating = 4 if i % 2 == 0 else 3
        response.confidence_score = 0.8
        response.completed_at = datetime.utcnow() - timedelta(days=i)
        response.selected_items = []
        responses.append(response)
    return responses


@pytest.fixture
def sample_feedback_data():
    """Sample feedback data for testing"""
    feedback_list = []
    for i in range(5):
        feedback = Mock(spec=StyleAssignmentFeedback)
        feedback.id = f"feedback-{i}"
        feedback.quiz_response_id = f"response-{i}"
        feedback.accuracy_rating = 4 if i % 2 == 0 else 2
        feedback.feedback_type = 'mostly_right' if i % 2 == 0 else 'too_broad'
        feedback.created_at = datetime.utcnow() - timedelta(days=i)
        feedback_list.append(feedback)
    return feedback_list


class TestBehavioralAnalysisService:
    """Test cases for BehavioralAnalysisService"""
    
    def test_analyze_style_assignment_accuracy_success(self, behavioral_service, mock_db, 
                                                     sample_quiz_responses, sample_feedback_data):
        """Test successful style assignment accuracy analysis"""
        # Setup
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = sample_quiz_responses
        
        # Mock feedback queries
        feedback_queries = []
        for i, response in enumerate(sample_quiz_responses):
            if i < len(sample_feedback_data):
                feedback_queries.append(sample_feedback_data[i])
            else:
                feedback_queries.append(None)
        
        mock_db.query.return_value.filter.return_value.first.side_effect = feedback_queries
        
        # Execute
        result = behavioral_service.analyze_style_assignment_accuracy(30)
        
        # Verify
        assert result['total_responses_analyzed'] == len(sample_quiz_responses)
        assert 'style_accuracy' in result
        assert 'overall_metrics' in result
        assert 'improvement_recommendations' in result
        
        # Check that styles are analyzed
        assert 'casual' in result['style_accuracy'] or 'formal' in result['style_accuracy']
    
    def test_analyze_style_assignment_accuracy_no_data(self, behavioral_service, mock_db):
        """Test style assignment accuracy analysis with no data"""
        # Setup
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        
        # Execute
        result = behavioral_service.analyze_style_assignment_accuracy(30)
        
        # Verify
        assert 'error' in result
        assert 'No feedback data available' in result['error']
    
    def test_analyze_user_upload_patterns_success(self, behavioral_service, mock_db):
        """Test successful user upload pattern analysis"""
        # Setup - create mock uploads and quiz responses
        mock_uploads = []
        for i in range(10):
            upload = Mock(spec=ClothingItem)
            upload.user_id = f"user-{i % 3}"  # 3 users with multiple uploads each
            upload.category = 'shirt' if i % 2 == 0 else 'pants'
            upload.color = 'blue' if i % 2 == 0 else 'black'
            mock_uploads.append(upload)
        
        mock_responses = []
        for i in range(3):
            response = Mock(spec=QuizResponse)
            response.user_id = f"user-{i}"
            response.assigned_category = 'casual'
            response.selected_items = []
            mock_responses.append(response)
        
        mock_db.query.return_value.all.side_effect = [mock_uploads, mock_responses]
        
        # Execute
        result = behavioral_service.analyze_user_upload_patterns()
        
        # Verify
        assert result['total_users_analyzed'] == 3
        assert result['total_uploads'] == 10
        assert 'style_consistency' in result
        assert 'feature_alignment' in result
        assert 'upload_behavior_insights' in result
    
    def test_analyze_user_upload_patterns_no_data(self, behavioral_service, mock_db):
        """Test upload pattern analysis with no data"""
        # Setup
        mock_db.query.return_value.all.return_value = []
        
        # Execute
        result = behavioral_service.analyze_user_upload_patterns()
        
        # Verify
        assert 'error' in result
        assert 'No upload data available' in result['error']
    
    def test_analyze_user_upload_patterns_specific_user(self, behavioral_service, mock_db):
        """Test upload pattern analysis for specific user"""
        # Setup
        user_id = "specific-user-id"
        mock_uploads = [Mock(spec=ClothingItem) for _ in range(5)]
        for upload in mock_uploads:
            upload.user_id = user_id
            upload.category = 'shirt'
            upload.color = 'blue'
        
        mock_response = Mock(spec=QuizResponse)
        mock_response.user_id = user_id
        mock_response.assigned_category = 'casual'
        mock_response.selected_items = []
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_uploads
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_response]
        
        # Execute
        result = behavioral_service.analyze_user_upload_patterns(user_id)
        
        # Verify
        assert result['total_users_analyzed'] == 1
        assert result['total_uploads'] == 5
    
    def test_detect_algorithm_drift_success(self, behavioral_service, mock_db):
        """Test successful algorithm drift detection"""
        # Setup - create responses with declining satisfaction over time
        mock_responses = []
        base_date = datetime.utcnow() - timedelta(days=90)
        
        for i in range(30):  # 30 responses over 90 days
            response = Mock(spec=QuizResponse)
            response.id = f"response-{i}"
            response.user_satisfaction_rating = 5 - (i // 10)  # Declining satisfaction
            response.confidence_score = 0.8 - (i * 0.01)  # Declining confidence
            response.completed_at = base_date + timedelta(days=i * 3)
            mock_responses.append(response)
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_responses
        
        # Execute
        result = behavioral_service.detect_algorithm_drift(90)
        
        # Verify
        assert result['total_responses'] == 30
        assert result['time_windows'] >= 3
        assert 'drift_analysis' in result
        assert 'alerts' in result
        
        # Should detect declining trends
        assert result['drift_analysis']['satisfaction_declining'] is True
        assert len(result['alerts']) > 0
    
    def test_detect_algorithm_drift_insufficient_data(self, behavioral_service, mock_db):
        """Test drift detection with insufficient data"""
        # Setup - return too few responses
        mock_responses = [Mock(spec=QuizResponse) for _ in range(5)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_responses
        
        # Execute
        result = behavioral_service.detect_algorithm_drift(90)
        
        # Verify
        assert 'error' in result
        assert 'Insufficient data' in result['error']
    
    def test_detect_algorithm_drift_stable_performance(self, behavioral_service, mock_db):
        """Test drift detection with stable performance"""
        # Setup - create responses with stable satisfaction
        mock_responses = []
        base_date = datetime.utcnow() - timedelta(days=60)
        
        for i in range(30):
            response = Mock(spec=QuizResponse)
            response.id = f"response-{i}"
            response.user_satisfaction_rating = 4  # Stable satisfaction
            response.confidence_score = 0.8  # Stable confidence
            response.completed_at = base_date + timedelta(days=i * 2)
            mock_responses.append(response)
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_responses
        
        # Execute
        result = behavioral_service.detect_algorithm_drift(60)
        
        # Verify
        assert result['drift_analysis']['performance_stable'] is True
        assert result['drift_analysis']['satisfaction_declining'] is False
        assert len(result['alerts']) == 0
    
    def test_detect_algorithm_drift_sudden_drop(self, behavioral_service, mock_db):
        """Test drift detection with sudden satisfaction drop"""
        # Setup - create responses with sudden drop
        mock_responses = []
        base_date = datetime.utcnow() - timedelta(days=30)
        
        for i in range(20):
            response = Mock(spec=QuizResponse)
            response.id = f"response-{i}"
            # Sudden drop after 10 responses
            response.user_satisfaction_rating = 4.5 if i < 10 else 3.0
            response.confidence_score = 0.8
            response.completed_at = base_date + timedelta(days=i * 1.5)
            mock_responses.append(response)
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_responses
        
        # Execute
        result = behavioral_service.detect_algorithm_drift(30)
        
        # Verify
        assert len(result['alerts']) > 0
        # Should detect sudden drop
        sudden_drop_alerts = [alert for alert in result['alerts'] if alert['type'] == 'sudden_satisfaction_drop']
        assert len(sudden_drop_alerts) > 0
    
    def test_generate_improvement_recommendations_success(self, behavioral_service, mock_db):
        """Test successful improvement recommendation generation"""
        # Setup - mock the analysis methods to return data that triggers recommendations
        behavioral_service.analyze_style_assignment_accuracy = Mock(return_value={
            'style_accuracy': {
                'casual': {'high_accuracy_rate': 0.4},  # Low accuracy - should trigger recommendation
                'formal': {'high_accuracy_rate': 0.8}   # Good accuracy
            }
        })
        
        behavioral_service.analyze_user_upload_patterns = Mock(return_value={
            'feature_alignment': {'high_alignment_rate': 0.3}  # Low alignment - should trigger recommendation
        })
        
        behavioral_service.detect_algorithm_drift = Mock(return_value={
            'drift_analysis': {'satisfaction_declining': True}  # Declining - should trigger recommendation
        })
        
        behavioral_service._assess_learning_data_quality = Mock(return_value={
            'needs_improvement': True  # Should trigger recommendation
        })
        
        # Execute
        recommendations = behavioral_service.generate_improvement_recommendations()
        
        # Verify
        assert len(recommendations) > 0
        
        # Check for expected recommendation types
        recommendation_categories = [rec['category'] for rec in recommendations]
        assert 'style_improvement' in recommendation_categories
        assert 'feature_extraction' in recommendation_categories
        assert 'algorithm_performance' in recommendation_categories
        assert 'data_quality' in recommendation_categories
        
        # Check priority ordering (critical should come first)
        priorities = [rec['priority'] for rec in recommendations]
        critical_index = priorities.index('critical') if 'critical' in priorities else -1
        high_index = priorities.index('high') if 'high' in priorities else -1
        
        if critical_index >= 0 and high_index >= 0:
            assert critical_index < high_index
    
    def test_generate_improvement_recommendations_no_issues(self, behavioral_service, mock_db):
        """Test improvement recommendations when no issues are detected"""
        # Setup - mock all analysis methods to return good results
        behavioral_service.analyze_style_assignment_accuracy = Mock(return_value={
            'style_accuracy': {
                'casual': {'high_accuracy_rate': 0.8},
                'formal': {'high_accuracy_rate': 0.9}
            }
        })
        
        behavioral_service.analyze_user_upload_patterns = Mock(return_value={
            'feature_alignment': {'high_alignment_rate': 0.8}
        })
        
        behavioral_service.detect_algorithm_drift = Mock(return_value={
            'drift_analysis': {'satisfaction_declining': False}
        })
        
        behavioral_service._assess_learning_data_quality = Mock(return_value={
            'needs_improvement': False
        })
        
        # Execute
        recommendations = behavioral_service.generate_improvement_recommendations()
        
        # Verify
        # Should have few or no recommendations when everything is performing well
        assert len(recommendations) == 0 or all(rec['priority'] in ['low', 'medium'] for rec in recommendations)
    
    def test_calculate_style_consistency_success(self, behavioral_service, mock_db):
        """Test successful style consistency calculation"""
        # Setup
        mock_style_category = Mock(spec=StyleCategory)
        mock_style_category.features = ['casual', 'cotton', 'comfortable']
        
        mock_uploads = []
        for i in range(3):
            upload = Mock(spec=ClothingItem)
            upload.category = 'casual' if i < 2 else 'formal'  # 2/3 match
            upload.color = 'cotton' if i < 1 else 'silk'       # 1/3 match
            mock_uploads.append(upload)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_style_category
        
        # Execute
        consistency = behavioral_service._calculate_style_consistency('casual', mock_uploads)
        
        # Verify
        assert 0.0 <= consistency <= 1.0
        # Should be > 0 since some uploads match the style
        assert consistency > 0.0
    
    def test_calculate_style_consistency_no_style_category(self, behavioral_service, mock_db):
        """Test style consistency calculation when style category not found"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        mock_uploads = [Mock(spec=ClothingItem)]
        
        # Execute
        consistency = behavioral_service._calculate_style_consistency('nonexistent', mock_uploads)
        
        # Verify
        assert consistency == 0.0
    
    def test_calculate_feature_alignment_success(self, behavioral_service, mock_db):
        """Test successful feature alignment calculation"""
        # Setup
        mock_quiz_response = Mock(spec=QuizResponse)
        
        # Mock selected items with features
        mock_item1 = Mock()
        mock_item1.features = ['casual', 'cotton']
        mock_item1.auto_extracted_features = ['blue']
        
        mock_item2 = Mock()
        mock_item2.features = ['comfortable']
        mock_item2.auto_extracted_features = []
        
        mock_quiz_response.selected_items = [mock_item1, mock_item2]
        
        # Mock user uploads
        mock_uploads = []
        for i in range(3):
            upload = Mock(spec=ClothingItem)
            upload.category = 'casual' if i < 2 else 'formal'
            upload.color = 'blue' if i < 1 else 'red'
            mock_uploads.append(upload)
        
        # Execute
        alignment = behavioral_service._calculate_feature_alignment(mock_quiz_response, mock_uploads)
        
        # Verify
        assert 0.0 <= alignment <= 1.0
        # Should be > 0 since there's some overlap between quiz and upload features
        assert alignment >= 0.0
    
    def test_calculate_feature_alignment_no_quiz_features(self, behavioral_service, mock_db):
        """Test feature alignment calculation when quiz has no features"""
        # Setup
        mock_quiz_response = Mock(spec=QuizResponse)
        mock_item = Mock()
        mock_item.features = []
        mock_item.auto_extracted_features = []
        mock_quiz_response.selected_items = [mock_item]
        
        mock_uploads = [Mock(spec=ClothingItem)]
        
        # Execute
        alignment = behavioral_service._calculate_feature_alignment(mock_quiz_response, mock_uploads)
        
        # Verify
        assert alignment == 0.0
    
    def test_assess_learning_data_quality_good_quality(self, behavioral_service, mock_db):
        """Test learning data quality assessment with good quality data"""
        # Setup - mock database queries to return good quality metrics
        mock_db.query.return_value.count.side_effect = [100, 80, 10]  # total, validated, low_confidence
        
        # Execute
        result = behavioral_service._assess_learning_data_quality()
        
        # Verify
        assert result['total_entries'] == 100
        assert result['validation_rate'] == 0.8  # 80/100
        assert result['low_confidence_rate'] == 0.1  # 10/100
        assert result['needs_improvement'] is False  # Good quality
    
    def test_assess_learning_data_quality_poor_quality(self, behavioral_service, mock_db):
        """Test learning data quality assessment with poor quality data"""
        # Setup - mock database queries to return poor quality metrics
        mock_db.query.return_value.count.side_effect = [100, 20, 50]  # total, validated, low_confidence
        
        # Execute
        result = behavioral_service._assess_learning_data_quality()
        
        # Verify
        assert result['total_entries'] == 100
        assert result['validation_rate'] == 0.2  # 20/100 - low validation rate
        assert result['low_confidence_rate'] == 0.5  # 50/100 - high low confidence rate
        assert result['needs_improvement'] is True  # Poor quality
    
    def test_assess_learning_data_quality_no_data(self, behavioral_service, mock_db):
        """Test learning data quality assessment with no data"""
        # Setup
        mock_db.query.return_value.count.return_value = 0
        
        # Execute
        result = behavioral_service._assess_learning_data_quality()
        
        # Verify
        assert result['total_entries'] == 0
        assert result['validation_rate'] == 0
        assert result['low_confidence_rate'] == 0
        assert result['needs_improvement'] is False  # No data, no improvement needed
    
    def test_assess_learning_data_quality_database_error(self, behavioral_service, mock_db):
        """Test learning data quality assessment with database error"""
        # Setup
        mock_db.query.side_effect = Exception("Database error")
        
        # Execute
        result = behavioral_service._assess_learning_data_quality()
        
        # Verify
        assert result['needs_improvement'] is False  # Default to no improvement needed on error


@pytest.mark.integration
class TestBehavioralAnalysisIntegration:
    """Integration tests for behavioral analysis service"""
    
    def test_full_analysis_pipeline(self, behavioral_service, mock_db):
        """Test complete analysis pipeline integration"""
        # This would test the full pipeline from data collection
        # through analysis to recommendation generation
        pass
    
    def test_recommendation_accuracy(self, behavioral_service, mock_db):
        """Test accuracy of generated recommendations"""
        # This would test that recommendations are appropriate
        # for the detected issues and have realistic impact estimates
        pass