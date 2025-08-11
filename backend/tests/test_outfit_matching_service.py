"""
Tests for outfit matching service
"""
import pytest
from unittest.mock import Mock, patch
from typing import List

from app.services.outfit_matching_service import (
    OutfitMatchingService,
    FeatureMatch,
    OutfitMatchResult
)
from app.services.gemini_service import OutfitRecommendation as GeminiOutfitRecommendation, OutfitItem
from app.models.clothing_item import ClothingItem
from app.models.user import User


class TestOutfitMatchingService:
    """Test cases for OutfitMatchingService"""
    
    @pytest.fixture
    def service(self):
        """Create outfit matching service instance"""
        return OutfitMatchingService()
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user"""
        user = Mock(spec=User)
        user.id = "user-123"
        return user
    
    @pytest.fixture
    def sample_clothing_items(self):
        """Create sample clothing items for testing"""
        items = []
        
        # Red cotton t-shirt
        item1 = Mock(spec=ClothingItem)
        item1.id = "item-1"
        item1.category = "top"
        item1.color = "red"
        item1.tags = ["cotton", "casual", "short-sleeve"]
        items.append(item1)
        
        # Blue jeans
        item2 = Mock(spec=ClothingItem)
        item2.id = "item-2"
        item2.category = "bottom"
        item2.color = "blue"
        item2.tags = ["denim", "casual", "pants"]
        items.append(item2)
        
        # White sneakers
        item3 = Mock(spec=ClothingItem)
        item3.id = "item-3"
        item3.category = "shoes"
        item3.color = "white"
        item3.tags = ["sneakers", "casual", "comfortable"]
        items.append(item3)
        
        # Black leather jacket
        item4 = Mock(spec=ClothingItem)
        item4.id = "item-4"
        item4.category = "layering"
        item4.color = "black"
        item4.tags = ["leather", "jacket", "edgy"]
        items.append(item4)
        
        # Brown belt (accessory)
        item5 = Mock(spec=ClothingItem)
        item5.id = "item-5"
        item5.category = "accessory"
        item5.color = "brown"
        item5.tags = ["belt", "leather", "casual"]
        items.append(item5)
        
        return items
    
    @pytest.fixture
    def sample_ai_recommendation(self):
        """Create sample AI recommendation"""
        return GeminiOutfitRecommendation(
            top=OutfitItem(type="t-shirt", features=["red", "cotton", "casual"]),
            bottom=OutfitItem(type="jeans", features=["blue", "denim", "casual"]),
            shoes=OutfitItem(type="sneakers", features=["white", "comfortable", "casual"]),
            accessories=[OutfitItem(type="belt", features=["brown", "leather"])],
            outerwear=OutfitItem(type="jacket", features=["black", "leather", "edgy"])
        )
    
    def test_group_items_by_category(self, service, sample_clothing_items):
        """Test grouping items by category"""
        grouped = service._group_items_by_category(sample_clothing_items)
        
        assert "top" in grouped
        assert "bottom" in grouped
        assert "shoes" in grouped
        assert "layering" in grouped
        assert "accessory" in grouped
        
        assert len(grouped["top"]) == 1
        assert len(grouped["bottom"]) == 1
        assert len(grouped["shoes"]) == 1
        assert len(grouped["layering"]) == 1
        assert len(grouped["accessory"]) == 1
    
    def test_calculate_feature_match_perfect_match(self, service, sample_clothing_items):
        """Test feature matching with perfect match"""
        item = sample_clothing_items[0]  # Red cotton t-shirt
        target = OutfitItem(type="t-shirt", features=["red", "cotton", "casual"])
        
        match = service._calculate_feature_match(item, target, "warm", "casual")
        
        assert match.clothing_item == item
        assert match.match_score > 0.8  # Should be high score
        assert len(match.matched_features) == 3  # All features match
        assert len(match.missing_features) == 0
        assert match.confidence_score > 0.8
    
    def test_calculate_feature_match_partial_match(self, service, sample_clothing_items):
        """Test feature matching with partial match"""
        item = sample_clothing_items[0]  # Red cotton t-shirt
        target = OutfitItem(type="shirt", features=["red", "silk", "formal"])
        
        match = service._calculate_feature_match(item, target, "warm", "casual")
        
        assert match.clothing_item == item
        assert 0.3 < match.match_score < 0.8  # Moderate score
        assert "red" in match.matched_features
        assert "silk" in match.missing_features
        assert "formal" in match.missing_features
    
    def test_calculate_feature_match_no_match(self, service, sample_clothing_items):
        """Test feature matching with no match"""
        item = sample_clothing_items[0]  # Red cotton t-shirt
        target = OutfitItem(type="dress", features=["green", "silk", "formal"])
        
        match = service._calculate_feature_match(item, target, "warm", "formal")
        
        assert match.clothing_item == item
        assert match.match_score < 0.5  # Low score
        assert len(match.matched_features) == 0
        assert len(match.missing_features) == 3
    
    def test_weather_compatibility_warm_weather(self, service):
        """Test weather compatibility for warm weather"""
        # Appropriate for warm weather
        warm_features = {"cotton", "short-sleeve", "light"}
        score = service._calculate_weather_compatibility(warm_features, "warm")
        assert score > 0.8
        
        # Inappropriate for warm weather
        cold_features = {"wool", "thick", "boots"}
        score = service._calculate_weather_compatibility(cold_features, "warm")
        assert score < 0.5
    
    def test_weather_compatibility_cold_weather(self, service):
        """Test weather compatibility for cold weather"""
        # Appropriate for cold weather
        cold_features = {"wool", "long-sleeve", "thick"}
        score = service._calculate_weather_compatibility(cold_features, "cold")
        assert score > 0.8
        
        # Inappropriate for cold weather
        warm_features = {"sleeveless", "shorts", "sandals"}
        score = service._calculate_weather_compatibility(warm_features, "cold")
        assert score < 0.5
    
    def test_style_consistency_matching_style(self, service):
        """Test style consistency with matching style"""
        casual_features = {"relaxed", "comfortable", "denim", "sneakers"}
        score = service._calculate_style_consistency(casual_features, "casual")
        assert score > 0.7
        
        formal_features = {"elegant", "dress", "heels", "silk"}
        score = service._calculate_style_consistency(formal_features, "formal")
        assert score > 0.7
    
    def test_style_consistency_mismatched_style(self, service):
        """Test style consistency with mismatched style"""
        casual_features = {"relaxed", "comfortable", "denim"}
        score = service._calculate_style_consistency(casual_features, "formal")
        assert score < 0.8  # Should be lower but not terrible
        
        formal_features = {"elegant", "dress", "heels"}
        score = service._calculate_style_consistency(formal_features, "casual")
        assert score < 0.8
    
    def test_find_best_match_with_candidates(self, service, sample_clothing_items):
        """Test finding best match from candidates"""
        candidates = [sample_clothing_items[0], sample_clothing_items[1]]  # t-shirt and jeans
        target = OutfitItem(type="top", features=["red", "cotton", "casual"])
        
        match = service._find_best_match(candidates, target, "warm", "casual")
        
        assert match is not None
        assert match.clothing_item == sample_clothing_items[0]  # Should pick t-shirt
        assert match.match_score >= 0.3
    
    def test_find_best_match_no_candidates(self, service):
        """Test finding best match with no candidates"""
        target = OutfitItem(type="top", features=["red", "cotton"])
        
        match = service._find_best_match([], target, "warm", "casual")
        
        assert match is None
    
    def test_find_best_match_below_threshold(self, service, sample_clothing_items):
        """Test finding best match below threshold"""
        candidates = [sample_clothing_items[0]]  # Red t-shirt
        target = OutfitItem(type="dress", features=["green", "silk", "formal"])  # Very different
        
        match = service._find_best_match(candidates, target, "warm", "formal")
        
        # Should return None if score is below threshold
        assert match is None or match.match_score >= 0.3
    
    def test_color_harmony_same_colors(self, service):
        """Test color harmony with same colors"""
        score = service._calculate_color_pair_harmony("red", "red")
        assert score == 1.0
    
    def test_color_harmony_neutral_colors(self, service):
        """Test color harmony with neutral colors"""
        score = service._calculate_color_pair_harmony("black", "red")
        assert score == 0.9
        
        score = service._calculate_color_pair_harmony("white", "blue")
        assert score == 0.9
    
    def test_color_harmony_complementary_colors(self, service):
        """Test color harmony with complementary colors"""
        score = service._calculate_color_pair_harmony("red", "green")
        assert score == 0.85
        
        score = service._calculate_color_pair_harmony("blue", "orange")
        assert score == 0.85
    
    def test_color_harmony_analogous_colors(self, service):
        """Test color harmony with analogous colors"""
        score = service._calculate_color_pair_harmony("red", "orange")
        assert score == 0.8
        
        score = service._calculate_color_pair_harmony("blue", "purple")
        assert score == 0.8
    
    def test_color_harmony_unknown_combination(self, service):
        """Test color harmony with unknown color combination"""
        score = service._calculate_color_pair_harmony("red", "yellow")
        assert score == 0.6  # Default score
    
    @patch('app.services.outfit_matching_service.ClothingItem')
    def test_match_outfit_to_closet_complete_match(self, mock_clothing_item, service, mock_user, sample_clothing_items, sample_ai_recommendation):
        """Test complete outfit matching"""
        # Mock database query
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = sample_clothing_items
        
        result = service.match_outfit_to_closet(
            db=mock_db,
            user=mock_user,
            ai_recommendation=sample_ai_recommendation,
            weather="warm",
            style_preference="casual"
        )
        
        assert isinstance(result, OutfitMatchResult)
        assert result.top is not None
        assert result.bottom is not None
        assert result.shoes is not None
        assert result.outerwear is not None
        assert len(result.accessories) > 0
        assert result.overall_score > 0
    
    @patch('app.services.outfit_matching_service.ClothingItem')
    def test_match_outfit_to_closet_empty_closet(self, mock_clothing_item, service, mock_user, sample_ai_recommendation):
        """Test outfit matching with empty closet"""
        # Mock database query returning empty list
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = service.match_outfit_to_closet(
            db=mock_db,
            user=mock_user,
            ai_recommendation=sample_ai_recommendation,
            weather="warm",
            style_preference="casual"
        )
        
        assert isinstance(result, OutfitMatchResult)
        assert result.top is None
        assert result.bottom is None
        assert result.shoes is None
        assert result.overall_score == 0.0
    
    def test_calculate_overall_scores_complete_outfit(self, service):
        """Test overall score calculation with complete outfit"""
        # Create mock matches
        mock_item1 = Mock(spec=ClothingItem)
        mock_item1.color = "red"
        mock_item2 = Mock(spec=ClothingItem)
        mock_item2.color = "blue"
        
        match1 = FeatureMatch(
            clothing_item=mock_item1,
            match_score=0.8,
            matched_features=["red", "cotton"],
            missing_features=[],
            confidence_score=0.9,
            weather_compatibility=0.8,
            color_coordination=0.7,
            style_consistency=0.8
        )
        
        match2 = FeatureMatch(
            clothing_item=mock_item2,
            match_score=0.7,
            matched_features=["blue", "denim"],
            missing_features=[],
            confidence_score=0.8,
            weather_compatibility=0.9,
            color_coordination=0.8,
            style_consistency=0.7
        )
        
        result = OutfitMatchResult(top=match1, bottom=match2)
        result = service._calculate_overall_scores(result, "warm", "casual")
        
        assert result.overall_score > 0
        assert result.color_harmony_score > 0
        assert result.style_consistency_score > 0
        assert result.weather_appropriateness > 0
    
    def test_get_match_explanation(self, service, sample_clothing_items):
        """Test match explanation generation"""
        item = sample_clothing_items[0]  # Red cotton t-shirt
        match = FeatureMatch(
            clothing_item=item,
            match_score=0.85,
            matched_features=["red", "cotton", "casual"],
            missing_features=["silk"],
            confidence_score=0.9,
            weather_compatibility=0.8,
            color_coordination=0.7,
            style_consistency=0.8
        )
        
        explanation = service.get_match_explanation(match)
        
        assert "item_id" in explanation
        assert "match_score" in explanation
        assert "matched_features" in explanation
        assert "missing_features" in explanation
        assert "explanation" in explanation
        assert explanation["match_score"] == 0.85
        assert len(explanation["matched_features"]) == 3
        assert len(explanation["missing_features"]) == 1


class TestFeatureMatchingEdgeCases:
    """Test edge cases for feature matching"""
    
    @pytest.fixture
    def service(self):
        return OutfitMatchingService()
    
    def test_empty_features_target(self, service):
        """Test matching with empty target features"""
        item = Mock(spec=ClothingItem)
        item.id = "item-1"
        item.category = "top"
        item.color = "red"
        item.tags = ["cotton"]
        
        target = OutfitItem(type="shirt", features=[])
        
        match = service._calculate_feature_match(item, target, "warm", "casual")
        
        assert match.match_score > 0  # Should have neutral score
        assert len(match.matched_features) == 0
        assert len(match.missing_features) == 0
    
    def test_empty_features_item(self, service):
        """Test matching with item having no features"""
        item = Mock(spec=ClothingItem)
        item.id = "item-1"
        item.category = "top"
        item.color = None
        item.tags = None
        
        target = OutfitItem(type="shirt", features=["red", "cotton"])
        
        match = service._calculate_feature_match(item, target, "warm", "casual")
        
        assert match.match_score >= 0
        assert len(match.matched_features) == 1  # Only category matches
        assert len(match.missing_features) == 2
    
    def test_unknown_weather_condition(self, service):
        """Test weather compatibility with unknown condition"""
        features = {"cotton", "casual"}
        score = service._calculate_weather_compatibility(features, "unknown")
        assert score == 0.8  # Should return neutral score
    
    def test_unknown_style_preference(self, service):
        """Test style consistency with unknown preference"""
        features = {"casual", "comfortable"}
        score = service._calculate_style_consistency(features, "unknown_style")
        assert score == 0.8  # Should return neutral score
    
    def test_no_style_preference(self, service):
        """Test style consistency with no preference"""
        features = {"casual", "comfortable"}
        score = service._calculate_style_consistency(features, None)
        assert score == 0.8  # Should return neutral score


class TestWeatherAwareMatching:
    """Test weather-aware matching functionality"""
    
    @pytest.fixture
    def service(self):
        return OutfitMatchingService()
    
    def test_warm_weather_matching(self, service):
        """Test matching for warm weather conditions"""
        # Create items appropriate for warm weather
        warm_item = Mock(spec=ClothingItem)
        warm_item.id = "warm-item"
        warm_item.category = "top"
        warm_item.color = "white"
        warm_item.tags = ["cotton", "short-sleeve", "light"]
        
        cold_item = Mock(spec=ClothingItem)
        cold_item.id = "cold-item"
        cold_item.category = "top"
        cold_item.color = "black"
        cold_item.tags = ["wool", "long-sleeve", "thick"]
        
        target = OutfitItem(type="shirt", features=["light", "comfortable"])
        
        warm_match = service._calculate_feature_match(warm_item, target, "warm", "casual")
        cold_match = service._calculate_feature_match(cold_item, target, "warm", "casual")
        
        # Warm weather item should score higher for warm weather
        assert warm_match.weather_compatibility > cold_match.weather_compatibility
        assert warm_match.match_score > cold_match.match_score
    
    def test_cold_weather_matching(self, service):
        """Test matching for cold weather conditions"""
        # Create items appropriate for cold weather
        warm_item = Mock(spec=ClothingItem)
        warm_item.id = "warm-item"
        warm_item.category = "top"
        warm_item.color = "white"
        warm_item.tags = ["cotton", "sleeveless", "light"]
        
        cold_item = Mock(spec=ClothingItem)
        cold_item.id = "cold-item"
        cold_item.category = "top"
        cold_item.color = "black"
        cold_item.tags = ["wool", "long-sleeve", "thick"]
        
        target = OutfitItem(type="sweater", features=["warm", "comfortable"])
        
        warm_match = service._calculate_feature_match(warm_item, target, "cold", "casual")
        cold_match = service._calculate_feature_match(cold_item, target, "cold", "casual")
        
        # Cold weather item should score higher for cold weather
        assert cold_match.weather_compatibility > warm_match.weather_compatibility
        assert cold_match.match_score > warm_match.match_score


class TestColorCoordination:
    """Test color coordination functionality"""
    
    @pytest.fixture
    def service(self):
        return OutfitMatchingService()
    
    def test_monochromatic_outfit(self, service):
        """Test color harmony for monochromatic outfit"""
        # Create matches with same color
        items = []
        for i in range(3):
            item = Mock(spec=ClothingItem)
            item.color = "blue"
            items.append(FeatureMatch(
                clothing_item=item,
                match_score=0.8,
                matched_features=[],
                missing_features=[],
                confidence_score=0.8,
                weather_compatibility=0.8,
                color_coordination=0.8,
                style_consistency=0.8
            ))
        
        score = service._calculate_color_harmony(items)
        assert score == 1.0  # Perfect harmony for same colors
    
    def test_neutral_color_outfit(self, service):
        """Test color harmony with neutral colors"""
        # Create matches with neutral colors
        colors = ["black", "white", "gray"]
        items = []
        for color in colors:
            item = Mock(spec=ClothingItem)
            item.color = color
            items.append(FeatureMatch(
                clothing_item=item,
                match_score=0.8,
                matched_features=[],
                missing_features=[],
                confidence_score=0.8,
                weather_compatibility=0.8,
                color_coordination=0.8,
                style_consistency=0.8
            ))
        
        score = service._calculate_color_harmony(items)
        assert score >= 0.9  # High harmony for neutrals
    
    def test_complementary_color_outfit(self, service):
        """Test color harmony with complementary colors"""
        # Create matches with complementary colors
        colors = ["red", "green"]
        items = []
        for color in colors:
            item = Mock(spec=ClothingItem)
            item.color = color
            items.append(FeatureMatch(
                clothing_item=item,
                match_score=0.8,
                matched_features=[],
                missing_features=[],
                confidence_score=0.8,
                weather_compatibility=0.8,
                color_coordination=0.8,
                style_consistency=0.8
            ))
        
        score = service._calculate_color_harmony(items)
        assert score >= 0.85  # Good harmony for complementary colors


if __name__ == "__main__":
    pytest.main([__file__])