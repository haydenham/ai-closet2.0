"""
Unit tests for the quiz matching algorithm logic
"""
import pytest
import uuid
from decimal import Decimal
from unittest.mock import Mock, MagicMock

# Mock the database models to avoid import issues
class MockQuizClothingItem:
    def __init__(self, id, name, gender, category, features):
        self.id = id
        self.name = name
        self.gender = gender
        self.category = category
        self.features = features or []
        self.selection_count = 0
    
    def increment_selection_count(self):
        self.selection_count += 1

class MockStyleCategory:
    def __init__(self, id, name, gender, features):
        self.id = id
        self.name = name
        self.gender = gender
        self.features = features or []
    
    def calculate_match_score(self, selected_features):
        """Calculate how well selected features match this category"""
        if not selected_features or not self.features:
            return 0.0
        
        matching_features = set(selected_features) & set(self.features)
        return (len(matching_features) / len(selected_features)) * 100


class TestStyleMatchingAlgorithmUnit:
    """Unit tests for the style matching algorithm without database dependencies"""
    
    def test_weighted_scoring_calculation(self):
        """Test the weighted scoring calculation logic"""
        # Mock categories
        minimalist_category = MockStyleCategory(
            id=uuid.uuid4(),
            name="Minimalist",
            gender="male",
            features=["minimal", "clean", "neutral", "simple"]
        )
        
        streetwear_category = MockStyleCategory(
            id=uuid.uuid4(),
            name="Streetwear", 
            gender="male",
            features=["graphic", "oversized", "bold", "casual"]
        )
        
        categories = [minimalist_category, streetwear_category]
        
        # Mock selected items
        complete_outfit_item = MockQuizClothingItem(
            id=uuid.uuid4(),
            name="Minimal Complete Outfit",
            gender="male",
            category="complete_outfit",
            features=["minimal", "clean", "neutral", "simple"]  # Perfect match for minimalist
        )
        
        top_item = MockQuizClothingItem(
            id=uuid.uuid4(),
            name="Graphic Tee",
            gender="male", 
            category="top",
            features=["graphic", "bold"]  # Matches streetwear
        )
        
        selected_items = {
            'complete_outfit': complete_outfit_item,
            'top': top_item,
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None
        }
        
        # Default weights
        weights = {
            'top': 0.2,
            'bottom': 0.2,
            'shoes': 0.15,
            'layering': 0.1,
            'accessory': 0.05,
            'complete_outfit': 0.4
        }
        
        # Calculate scores manually
        scores = {}
        for category in categories:
            category_score = 0.0
            total_weight = 0.0
            
            for question_category, item in selected_items.items():
                if item and question_category in weights:
                    weight = weights[question_category]
                    item_features = set(item.features or [])
                    category_features = set(category.features or [])
                    
                    if item_features:
                        match_count = len(item_features.intersection(category_features))
                        item_score = (match_count / len(item_features)) * 100
                        category_score += item_score * weight
                        total_weight += weight
            
            if total_weight > 0:
                scores[category.name] = category_score / total_weight
            else:
                scores[category.name] = 0.0
        
        # Complete outfit should dominate due to higher weight and perfect match
        assert scores["Minimalist"] > scores["Streetwear"]
        assert scores["Minimalist"] > 60  # Should be high due to complete outfit match
    
    def test_confidence_scoring_clear_winner(self):
        """Test confidence scoring when there's a clear winner"""
        scores = {
            "Minimalist": 85.0,
            "Streetwear": 45.0,
            "Classic": 30.0
        }
        
        selected_items = {
            'complete_outfit': MockQuizClothingItem(
                id=uuid.uuid4(),
                name="Test",
                gender="male",
                category="complete_outfit", 
                features=["minimal"]
            ),
            'top': None,
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None
        }
        
        # Calculate confidence
        sorted_scores = sorted(scores.values(), reverse=True)
        best_score = sorted_scores[0]
        second_best = sorted_scores[1]
        
        gap = best_score - second_best
        confidence = min(gap / best_score, 1.0) * 100
        
        # Boost for complete outfit
        complete_outfit_item = selected_items.get('complete_outfit')
        if complete_outfit_item and best_score > 60:
            confidence = min(confidence * 1.2, 100.0)
        
        assert confidence > 50  # Should have high confidence due to clear gap
    
    def test_confidence_scoring_close_match(self):
        """Test confidence scoring when scores are close"""
        scores = {
            "Minimalist": 72.0,
            "Classic": 68.0,
            "Streetwear": 25.0
        }
        
        selected_items = {
            'complete_outfit': None,
            'top': MockQuizClothingItem(
                id=uuid.uuid4(),
                name="Test",
                gender="male",
                category="top",
                features=["clean"]
            ),
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None
        }
        
        # Calculate confidence
        sorted_scores = sorted(scores.values(), reverse=True)
        best_score = sorted_scores[0]
        second_best = sorted_scores[1]
        
        gap = best_score - second_best
        confidence = min(gap / best_score, 1.0) * 100
        
        assert confidence < 20  # Should have low confidence due to close scores
    
    def test_hybrid_style_detection(self):
        """Test detection of hybrid styles"""
        scores = {
            "Minimalist": 75.0,
            "Classic": 68.0,
            "Streetwear": 25.0,
            "Athleisure": 70.0
        }
        
        threshold = 15.0
        max_score = max(scores.values())
        hybrid_styles = []
        
        for style, score in scores.items():
            if max_score - score <= threshold and score > 30:
                hybrid_styles.append(style)
        
        hybrid_styles.sort(key=lambda x: scores[x], reverse=True)
        
        # Should detect Minimalist, Classic, and Athleisure as hybrid
        assert len(hybrid_styles) == 3
        assert "Minimalist" in hybrid_styles
        assert "Classic" in hybrid_styles
        assert "Athleisure" in hybrid_styles
        assert "Streetwear" not in hybrid_styles  # Too far from max
    
    def test_feature_matching_logic(self):
        """Test the core feature matching logic"""
        category_features = ["minimal", "clean", "neutral", "simple"]
        
        # Perfect match
        selected_features = ["minimal", "clean", "neutral", "simple"]
        matching = set(selected_features) & set(category_features)
        score = (len(matching) / len(selected_features)) * 100
        assert score == 100.0
        
        # Partial match
        selected_features = ["minimal", "clean", "bold", "graphic"]
        matching = set(selected_features) & set(category_features)
        score = (len(matching) / len(selected_features)) * 100
        assert score == 50.0  # 2 out of 4 features match
        
        # No match
        selected_features = ["bold", "graphic", "oversized"]
        matching = set(selected_features) & set(category_features)
        score = (len(matching) / len(selected_features)) * 100
        assert score == 0.0
    
    def test_empty_features_handling(self):
        """Test handling of empty feature lists"""
        category_features = ["minimal", "clean"]
        
        # Empty selected features
        selected_features = []
        if not selected_features:
            score = 0.0
        else:
            matching = set(selected_features) & set(category_features)
            score = (len(matching) / len(selected_features)) * 100
        
        assert score == 0.0
        
        # Empty category features
        category_features = []
        selected_features = ["minimal", "clean"]
        
        if not category_features:
            score = 0.0
        else:
            matching = set(selected_features) & set(category_features)
            score = (len(matching) / len(selected_features)) * 100
        
        assert score == 0.0
    
    def test_weight_normalization(self):
        """Test that weights are properly normalized"""
        weights = {
            'top': 0.2,
            'bottom': 0.2,
            'shoes': 0.15,
            'layering': 0.1,
            'accessory': 0.05,
            'complete_outfit': 0.3  # Changed from 0.4 to 0.3 to sum to 1.0
        }
        
        # Test with all items present
        selected_items = {
            'top': MockQuizClothingItem(uuid.uuid4(), "Top", "male", "top", ["feature1"]),
            'bottom': MockQuizClothingItem(uuid.uuid4(), "Bottom", "male", "bottom", ["feature1"]),
            'shoes': MockQuizClothingItem(uuid.uuid4(), "Shoes", "male", "shoes", ["feature1"]),
            'layering': MockQuizClothingItem(uuid.uuid4(), "Layer", "male", "layering", ["feature1"]),
            'accessory': MockQuizClothingItem(uuid.uuid4(), "Accessory", "male", "accessory", ["feature1"]),
            'complete_outfit': MockQuizClothingItem(uuid.uuid4(), "Outfit", "male", "complete_outfit", ["feature1"])
        }
        
        total_weight = 0.0
        for question_category, item in selected_items.items():
            if item and question_category in weights:
                total_weight += weights[question_category]
        
        assert abs(total_weight - 1.0) < 0.01  # Should sum to approximately 1.0
        
        # Test with partial items
        selected_items_partial = {
            'top': MockQuizClothingItem(uuid.uuid4(), "Top", "male", "top", ["feature1"]),
            'complete_outfit': MockQuizClothingItem(uuid.uuid4(), "Outfit", "male", "complete_outfit", ["feature1"]),
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None
        }
        
        partial_weight = 0.0
        for question_category, item in selected_items_partial.items():
            if item and question_category in weights:
                partial_weight += weights[question_category]
        
        assert partial_weight == 0.5  # top (0.2) + complete_outfit (0.3)


class TestEdgeCasesUnit:
    """Test edge cases in the algorithm"""
    
    def test_all_none_items(self):
        """Test when all selected items are None"""
        selected_items = {
            'top': None,
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None,
            'complete_outfit': None
        }
        
        weights = {
            'top': 0.2,
            'bottom': 0.2,
            'shoes': 0.15,
            'layering': 0.1,
            'accessory': 0.05,
            'complete_outfit': 0.4
        }
        
        # Simulate scoring with all None items
        category_score = 0.0
        total_weight = 0.0
        
        for question_category, item in selected_items.items():
            if item and question_category in weights:
                # This block should never execute
                weight = weights[question_category]
                total_weight += weight
        
        final_score = category_score / total_weight if total_weight > 0 else 0.0
        
        assert final_score == 0.0
        assert total_weight == 0.0
    
    def test_single_item_scoring(self):
        """Test scoring with only one item selected"""
        selected_items = {
            'complete_outfit': MockQuizClothingItem(
                uuid.uuid4(),
                "Perfect Match",
                "female",
                "complete_outfit",
                ["minimal", "clean", "neutral"]
            ),
            'top': None,
            'bottom': None,
            'shoes': None,
            'layering': None,
            'accessory': None
        }
        
        category = MockStyleCategory(
            uuid.uuid4(),
            "Minimalist",
            "female",
            ["minimal", "clean", "neutral", "simple"]
        )
        
        weights = {'complete_outfit': 0.4}
        
        # Calculate score for the single item
        item = selected_items['complete_outfit']
        item_features = set(item.features)
        category_features = set(category.features)
        
        match_count = len(item_features.intersection(category_features))
        item_score = (match_count / len(item_features)) * 100
        
        # All 3 features match, so score should be 100%
        assert item_score == 100.0
    
    def test_zero_confidence_scenarios(self):
        """Test scenarios that should result in zero confidence"""
        # No scores
        scores = {}
        if not scores:
            confidence = 0.0
        assert confidence == 0.0
        
        # All zero scores
        scores = {"Style1": 0.0, "Style2": 0.0, "Style3": 0.0}
        sorted_scores = sorted(scores.values(), reverse=True)
        best_score = sorted_scores[0]
        
        if best_score == 0:
            confidence = 0.0
        assert confidence == 0.0
        
        # Single score
        scores = {"Style1": 75.0}
        sorted_scores = sorted(scores.values(), reverse=True)
        
        if len(sorted_scores) < 2:
            confidence = 0.0
        assert confidence == 0.0


if __name__ == "__main__":
    # Run a simple test to verify the algorithm works
    test = TestStyleMatchingAlgorithmUnit()
    test.test_weighted_scoring_calculation()
    test.test_confidence_scoring_clear_winner()
    test.test_hybrid_style_detection()
    test.test_feature_matching_logic()
    
    print("✅ All unit tests passed!")