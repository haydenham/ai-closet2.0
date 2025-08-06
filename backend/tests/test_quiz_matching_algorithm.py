"""
Tests for the feature-based style matching algorithm and quiz completion system
"""
import pytest
import uuid
from decimal import Decimal
from typing import Dict, List
from unittest.mock import Mock

from app.models.quiz_system import QuizClothingItem, StyleCategory, QuizResponse
from app.services.quiz_service import StyleCategoryService, QuizResponseService, StyleFeedbackService
from app.schemas.quiz_system import QuizResponseCreate


class TestStyleMatchingAlgorithm:
    """Test the core style matching algorithm"""
    
    def test_weighted_scoring_prioritizes_complete_outfit(self, db_session):
        """Test that complete outfit selections have higher weight in scoring"""
        # Create test style category
        category = StyleCategory(
            id=uuid.uuid4(),
            name="Minimalist",
            gender="male",
            features=["minimal", "clean", "neutral", "simple"]
        )
        db_session.add(category)
        
        # Create test items
        complete_outfit_item = QuizClothingItem(
            id=uuid.uuid4(),
            name="Minimal Complete Outfit",
            image_url="test.jpg",
            gender="male",
            category="complete_outfit",
            features=["minimal", "clean", "neutral", "simple"]  # Perfect match
        )
        
        top_item = QuizClothingItem(
            id=uuid.uuid4(),
            name="Loud Graphic Tee",
            image_url="test.jpg",
            gender="male",
            category="top",
            features=["graphic", "bold", "colorful"]  # No match
        )
        
        db_session.add_all([complete_outfit_item, top_item])
        db_session.commit()
        
        selected_items = {
            'complete_outfit': complete_outfit_item,
            'top': top_item,
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None
        }
        
        scores = StyleCategoryService.calculate_weighted_style_scores(
            db_session, selected_items, "male"
        )
        
        # Should score high due to complete outfit match despite top mismatch
        assert scores["Minimalist"] > 60  # Complete outfit weight should dominate
    
    def test_confidence_scoring_with_clear_winner(self, db_session):
        """Test confidence scoring when there's a clear style winner"""
        # Create two distinct categories
        minimalist = StyleCategory(
            id=uuid.uuid4(),
            name="Minimalist",
            gender="male",
            features=["minimal", "clean", "neutral"]
        )
        
        streetwear = StyleCategory(
            id=uuid.uuid4(),
            name="Streetwear",
            gender="male",
            features=["graphic", "oversized", "bold"]
        )
        
        db_session.add_all([minimalist, streetwear])
        
        # Create items that strongly match minimalist
        items = {}
        for category in ['top', 'bottom', 'complete_outfit']:
            item = QuizClothingItem(
                id=uuid.uuid4(),
                name=f"Minimal {category}",
                image_url="test.jpg",
                gender="male",
                category=category,
                features=["minimal", "clean", "neutral"]
            )
            items[category] = item
            db_session.add(item)
        
        # Fill remaining categories with None
        for category in ['shoes', 'layering', 'accessory']:
            items[category] = None
        
        db_session.commit()
        
        scores = StyleCategoryService.calculate_weighted_style_scores(
            db_session, items, "male"
        )
        
        confidence = StyleCategoryService.calculate_confidence_score(scores, items)
        
        # Should have high confidence due to clear winner
        assert confidence > 70
        assert scores["Minimalist"] > scores["Streetwear"]
    
    def test_confidence_scoring_with_close_match(self, db_session):
        """Test confidence scoring when multiple styles are close"""
        # Create categories with overlapping features
        classic = StyleCategory(
            id=uuid.uuid4(),
            name="Classic",
            gender="male",
            features=["tailored", "formal", "neutral", "clean"]
        )
        
        minimalist = StyleCategory(
            id=uuid.uuid4(),
            name="Minimalist",
            gender="male",
            features=["minimal", "clean", "neutral", "simple"]
        )
        
        db_session.add_all([classic, minimalist])
        
        # Create items with overlapping features
        item = QuizClothingItem(
            id=uuid.uuid4(),
            name="Clean Neutral Shirt",
            image_url="test.jpg",
            gender="male",
            category="complete_outfit",
            features=["clean", "neutral"]  # Matches both categories
        )
        
        db_session.add(item)
        db_session.commit()
        
        selected_items = {
            'complete_outfit': item,
            'top': None,
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None
        }
        
        scores = StyleCategoryService.calculate_weighted_style_scores(
            db_session, selected_items, "male"
        )
        
        confidence = StyleCategoryService.calculate_confidence_score(scores, selected_items)
        
        # Should have lower confidence due to close scores
        assert confidence < 50
    
    def test_hybrid_style_detection(self, db_session):
        """Test detection of hybrid style preferences"""
        # Create multiple categories
        categories = [
            StyleCategory(
                id=uuid.uuid4(),
                name="Minimalist",
                gender="female",
                features=["minimal", "clean", "neutral"]
            ),
            StyleCategory(
                id=uuid.uuid4(),
                name="Classic",
                gender="female",
                features=["elegant", "timeless", "clean"]
            ),
            StyleCategory(
                id=uuid.uuid4(),
                name="Streetwear",
                gender="female",
                features=["oversized", "graphic", "bold"]
            )
        ]
        
        for cat in categories:
            db_session.add(cat)
        
        # Create items that match multiple categories
        item1 = QuizClothingItem(
            id=uuid.uuid4(),
            name="Clean Elegant Top",
            image_url="test.jpg",
            gender="female",
            category="top",
            features=["clean", "elegant", "minimal"]
        )
        
        item2 = QuizClothingItem(
            id=uuid.uuid4(),
            name="Timeless Neutral Outfit",
            image_url="test.jpg",
            gender="female",
            category="complete_outfit",
            features=["timeless", "neutral", "clean"]
        )
        
        db_session.add_all([item1, item2])
        db_session.commit()
        
        selected_items = {
            'top': item1,
            'complete_outfit': item2,
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None
        }
        
        scores = StyleCategoryService.calculate_weighted_style_scores(
            db_session, selected_items, "female"
        )
        
        hybrid_styles = StyleCategoryService.detect_hybrid_styles(scores, threshold=15.0)
        
        # Should detect multiple close styles
        assert len(hybrid_styles) >= 2
        assert "Minimalist" in hybrid_styles or "Classic" in hybrid_styles
    
    def test_enhanced_style_assignment_complete_flow(self, db_session):
        """Test the complete enhanced style assignment flow"""
        # Create test data
        category = StyleCategory(
            id=uuid.uuid4(),
            name="Athleisure",
            gender="female",
            features=["athletic", "comfortable", "casual"]
        )
        db_session.add(category)
        
        items = {}
        for cat in ['top', 'bottom', 'shoes', 'complete_outfit']:
            item = QuizClothingItem(
                id=uuid.uuid4(),
                name=f"Athletic {cat}",
                image_url="test.jpg",
                gender="female",
                category=cat,
                features=["athletic", "comfortable"]
            )
            items[cat] = item
            db_session.add(item)
        
        # Add non-matching items
        for cat in ['layering', 'accessory']:
            items[cat] = None
        
        db_session.commit()
        
        assignment = StyleCategoryService.get_enhanced_style_assignment(
            db_session, items, "female"
        )
        
        assert assignment['primary_style'] == "Athleisure"
        assert assignment['confidence'] > 0
        assert assignment['primary_category'] is not None
        assert isinstance(assignment['scores'], dict)
        assert isinstance(assignment['hybrid_styles'], list)
        assert isinstance(assignment['is_hybrid'], bool)


class TestQuizCompletionSystem:
    """Test the complete quiz processing system"""
    
    def test_process_complete_quiz_with_all_items(self, db_session, test_user):
        """Test processing a complete quiz with all item categories"""
        # Create test category
        category = StyleCategory(
            id=uuid.uuid4(),
            name="Streetwear",
            gender="male",
            features=["graphic", "oversized", "casual"]
        )
        db_session.add(category)
        
        # Create test items for all categories
        item_ids = {}
        items = {}
        
        for cat in ['top', 'bottom', 'shoes', 'layering', 'accessory', 'complete_outfit']:
            item = QuizClothingItem(
                id=uuid.uuid4(),
                name=f"Streetwear {cat}",
                image_url="test.jpg",
                gender="male",
                category=cat,
                features=["graphic", "oversized", "casual"]
            )
            items[cat] = item
            item_ids[cat] = item.id
            db_session.add(item)
        
        db_session.commit()
        
        # Process quiz
        response = QuizResponseService.process_complete_quiz(
            db=db_session,
            user_id=test_user.id,
            gender="male",
            selected_items=item_ids
        )
        
        assert response.assigned_category == "Streetwear"
        assert response.confidence_score is not None
        assert response.confidence_score > 0
        assert len(response.selected_item_ids) == 6
        assert response.calculated_scores is not None
    
    def test_process_quiz_with_partial_items(self, db_session, test_user):
        """Test processing quiz with only some item categories filled"""
        # Create test category
        category = StyleCategory(
            id=uuid.uuid4(),
            name="Minimalist",
            gender="female",
            features=["minimal", "clean", "neutral"]
        )
        db_session.add(category)
        
        # Create items for only some categories
        item_ids = {}
        
        for cat in ['top', 'complete_outfit']:
            item = QuizClothingItem(
                id=uuid.uuid4(),
                name=f"Minimal {cat}",
                image_url="test.jpg",
                gender="female",
                category=cat,
                features=["minimal", "clean", "neutral"]
            )
            item_ids[cat] = item.id
            db_session.add(item)
        
        # Add dummy items for required categories
        for cat in ['bottom', 'shoes', 'layering', 'accessory']:
            dummy_item = QuizClothingItem(
                id=uuid.uuid4(),
                name=f"Dummy {cat}",
                image_url="test.jpg",
                gender="female",
                category=cat,
                features=["random"]
            )
            item_ids[cat] = dummy_item.id
            db_session.add(dummy_item)
        
        db_session.commit()
        
        response = QuizResponseService.process_complete_quiz(
            db=db_session,
            user_id=test_user.id,
            gender="female",
            selected_items=item_ids
        )
        
        assert response.assigned_category == "Minimalist"
        assert response.confidence_score is not None
    
    def test_quiz_with_custom_weights(self, db_session, test_user):
        """Test quiz processing with custom category weights"""
        # Create test category
        category = StyleCategory(
            id=uuid.uuid4(),
            name="Classic",
            gender="male",
            features=["tailored", "formal", "classic"]
        )
        db_session.add(category)
        
        # Create items
        item_ids = {}
        for cat in ['top', 'bottom', 'shoes', 'layering', 'accessory', 'complete_outfit']:
            item = QuizClothingItem(
                id=uuid.uuid4(),
                name=f"Classic {cat}",
                image_url="test.jpg",
                gender="male",
                category=cat,
                features=["tailored", "formal"] if cat != 'complete_outfit' else ["classic"]
            )
            item_ids[cat] = item.id
            db_session.add(item)
        
        db_session.commit()
        
        # Custom weights that prioritize individual items over complete outfit
        custom_weights = {
            'top': 0.3,
            'bottom': 0.3,
            'shoes': 0.2,
            'layering': 0.1,
            'accessory': 0.05,
            'complete_outfit': 0.05
        }
        
        response = QuizResponseService.process_complete_quiz(
            db=db_session,
            user_id=test_user.id,
            gender="male",
            selected_items=item_ids,
            weights=custom_weights
        )
        
        assert response.assigned_category == "Classic"
        # Should still work with custom weights


class TestUserFeedbackSystem:
    """Test the user feedback system for algorithm improvement"""
    
    def test_create_style_feedback(self, db_session, test_user):
        """Test creating style assignment feedback"""
        # Create a quiz response first
        response = QuizResponse(
            id=uuid.uuid4(),
            user_id=test_user.id,
            selected_item_ids=["item1", "item2"],
            calculated_scores={"Minimalist": 80.0, "Classic": 60.0},
            assigned_category="Minimalist",
            confidence_score=Decimal('75.50')
        )
        db_session.add(response)
        db_session.commit()
        
        # Create feedback
        feedback = StyleFeedbackService.create_style_feedback(
            db=db_session,
            quiz_response_id=response.id,
            user_id=test_user.id,
            accuracy_rating=4,
            feedback_type="mostly_right",
            preferred_style="Classic",
            feedback_text="Close but I prefer more formal styles",
            feature_feedback={"formal": "missing", "casual": "too_much"}
        )
        
        assert feedback.accuracy_rating == 4
        assert feedback.feedback_type == "mostly_right"
        assert feedback.preferred_style == "Classic"
        assert feedback.feature_feedback["formal"] == "missing"
    
    def test_feedback_metrics_calculation(self, db_session, test_user):
        """Test calculation of algorithm improvement metrics"""
        from app.models.quiz_system import StyleAssignmentFeedback
        
        # Create multiple feedback entries
        response = QuizResponse(
            id=uuid.uuid4(),
            user_id=test_user.id,
            selected_item_ids=["item1"],
            calculated_scores={"Style1": 70.0},
            assigned_category="Style1"
        )
        db_session.add(response)
        
        feedback_data = [
            (5, "perfect"),
            (4, "mostly_right"),
            (2, "too_broad"),
            (1, "completely_wrong"),
            (3, "too_narrow")
        ]
        
        for rating, feedback_type in feedback_data:
            feedback = StyleAssignmentFeedback(
                id=uuid.uuid4(),
                quiz_response_id=response.id,
                user_id=test_user.id,
                accuracy_rating=rating,
                feedback_type=feedback_type
            )
            db_session.add(feedback)
        
        db_session.commit()
        
        metrics = StyleFeedbackService.get_feedback_metrics(db_session, days=30)
        
        assert metrics['total_feedback_count'] == 5
        assert metrics['average_accuracy_rating'] == 3.0  # (5+4+2+1+3)/5
        assert 'too_broad' in metrics['feedback_distribution']
        assert len(metrics['most_common_issues']) > 0
        assert len(metrics['improvement_suggestions']) > 0
    
    def test_feature_accuracy_analysis(self, db_session, test_user):
        """Test analysis of specific feature accuracy"""
        from app.models.quiz_system import StyleAssignmentFeedback, QuizResponseItem
        
        # Create test data structure
        category = StyleCategory(
            id=uuid.uuid4(),
            name="TestStyle",
            gender="male",
            features=["test_feature"]
        )
        
        item = QuizClothingItem(
            id=uuid.uuid4(),
            name="Test Item",
            image_url="test.jpg",
            gender="male",
            category="top",
            features=["test_feature", "other_feature"]
        )
        
        response = QuizResponse(
            id=uuid.uuid4(),
            user_id=test_user.id,
            selected_item_ids=[str(item.id)],
            calculated_scores={"TestStyle": 80.0},
            assigned_category="TestStyle"
        )
        
        response_item = QuizResponseItem(
            id=uuid.uuid4(),
            quiz_response_id=response.id,
            clothing_item_id=item.id,
            question_category="top"
        )
        
        feedback = StyleAssignmentFeedback(
            id=uuid.uuid4(),
            quiz_response_id=response.id,
            user_id=test_user.id,
            accuracy_rating=4,
            feedback_type="mostly_right"
        )
        
        db_session.add_all([category, item, response, response_item, feedback])
        db_session.commit()
        
        analysis = StyleFeedbackService.analyze_feature_accuracy(
            db_session, "test_feature", days=30
        )
        
        assert analysis['feature_name'] == "test_feature"
        assert analysis['sample_size'] == 1
        assert analysis['average_accuracy'] == 4.0


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_features_handling(self, db_session):
        """Test handling of items with no features"""
        category = StyleCategory(
            id=uuid.uuid4(),
            name="TestStyle",
            gender="male",
            features=["some_feature"]
        )
        db_session.add(category)
        
        item_with_no_features = QuizClothingItem(
            id=uuid.uuid4(),
            name="Empty Item",
            image_url="test.jpg",
            gender="male",
            category="top",
            features=[]
        )
        db_session.add(item_with_no_features)
        db_session.commit()
        
        selected_items = {
            'top': item_with_no_features,
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None,
            'complete_outfit': None
        }
        
        scores = StyleCategoryService.calculate_weighted_style_scores(
            db_session, selected_items, "male"
        )
        
        # Should handle gracefully without errors
        assert isinstance(scores, dict)
        assert scores["TestStyle"] == 0.0
    
    def test_no_matching_categories(self, db_session):
        """Test behavior when no style categories exist"""
        # Don't create any categories
        
        item = QuizClothingItem(
            id=uuid.uuid4(),
            name="Test Item",
            image_url="test.jpg",
            gender="male",
            category="top",
            features=["some_feature"]
        )
        db_session.add(item)
        db_session.commit()
        
        selected_items = {
            'top': item,
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None,
            'complete_outfit': None
        }
        
        assignment = StyleCategoryService.get_enhanced_style_assignment(
            db_session, selected_items, "male"
        )
        
        assert assignment['primary_style'] is None
        assert assignment['confidence'] == 0.0
        assert assignment['scores'] == {}
        assert assignment['hybrid_styles'] == []
        assert assignment['is_hybrid'] is False
    
    def test_all_none_items(self, db_session):
        """Test handling when all selected items are None"""
        category = StyleCategory(
            id=uuid.uuid4(),
            name="TestStyle",
            gender="female",
            features=["test_feature"]
        )
        db_session.add(category)
        db_session.commit()
        
        selected_items = {
            'top': None,
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None,
            'complete_outfit': None
        }
        
        scores = StyleCategoryService.calculate_weighted_style_scores(
            db_session, selected_items, "female"
        )
        
        confidence = StyleCategoryService.calculate_confidence_score(scores, selected_items)
        
        assert scores["TestStyle"] == 0.0
        assert confidence == 0.0
    
    def test_invalid_gender_handling(self, db_session):
        """Test handling of invalid gender values"""
        # This should be handled at the API validation level,
        # but test service robustness
        
        item = QuizClothingItem(
            id=uuid.uuid4(),
            name="Test Item",
            image_url="test.jpg",
            gender="male",
            category="top",
            features=["test_feature"]
        )
        db_session.add(item)
        db_session.commit()
        
        selected_items = {
            'top': item,
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None,
            'complete_outfit': None
        }
        
        # Should return empty results for invalid gender
        scores = StyleCategoryService.calculate_weighted_style_scores(
            db_session, selected_items, "invalid_gender"
        )
        
        assert scores == {}


# Fixtures for testing
@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    from app.models.user import User
    
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def db_session():
    """Mock database session for testing"""
    # This would typically be a real test database session
    # For now, return a mock that can be used in tests
    from unittest.mock import Mock
    
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.query = Mock()
    
    # Mock query methods
    def mock_filter(*args):
        mock_query = Mock()
        mock_query.filter = mock_filter
        mock_query.all = Mock(return_value=[])
        mock_query.first = Mock(return_value=None)
        return mock_query
    
    session.query.return_value.filter = mock_filter
    
    return session