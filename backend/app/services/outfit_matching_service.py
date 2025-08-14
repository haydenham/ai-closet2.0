"""
Feature-based outfit matching service for AI-generated recommendations
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import math

from sqlalchemy.orm import Session
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.services.gemini_service import OutfitRecommendation as GeminiOutfitRecommendation, OutfitItem
# Create a mock GCPVisionService for testing
class MockGCPVisionService:
    def __init__(self):
        pass
    
    def analyze_clothing_image(self, image_data):
        return {
            'extracted_features': [],
            'confidence_scores': {},
            'suggested_category': 'unknown'
        }

try:
    from app.services.gcp_vision_service import GCPVisionService as RealGCPVisionService
    HAS_GCP_VISION = True
except (ImportError, AttributeError):
    HAS_GCP_VISION = False
    RealGCPVisionService = None

logger = logging.getLogger(__name__)


@dataclass
class FeatureMatch:
    """Data class for feature matching results"""
    clothing_item: ClothingItem
    match_score: float
    matched_features: List[str]
    missing_features: List[str]
    confidence_score: float
    weather_compatibility: float
    color_coordination: float
    style_consistency: float


@dataclass
class OutfitMatchResult:
    """Data class for complete outfit matching results"""
    top: Optional[FeatureMatch] = None
    bottom: Optional[FeatureMatch] = None
    shoes: Optional[FeatureMatch] = None
    accessories: List[FeatureMatch] = None
    outerwear: Optional[FeatureMatch] = None
    overall_score: float = 0.0
    color_harmony_score: float = 0.0
    style_consistency_score: float = 0.0
    weather_appropriateness: float = 0.0
    missing_categories: List[str] = None


class OutfitMatchingService:
    """Service for matching AI-generated outfit recommendations with user's closet items"""
    
    def __init__(self):
        if HAS_GCP_VISION and RealGCPVisionService:
            try:
                self.vision_service = RealGCPVisionService()
            except Exception:
                # Fall back to mock if real service fails to initialize
                self.vision_service = MockGCPVisionService()
        else:
            # Use mock service for testing or when GCP Vision is not available
            self.vision_service = MockGCPVisionService()
        
        # Color harmony mappings
        self.color_harmony_rules = {
            'complementary': {
                'red': ['green', 'teal'],
                'blue': ['orange', 'yellow'],
                'purple': ['yellow', 'lime'],
                'green': ['red', 'pink'],
                'orange': ['blue', 'navy'],
                'yellow': ['purple', 'violet']
            },
            'analogous': {
                'red': ['orange', 'pink', 'burgundy'],
                'blue': ['purple', 'teal', 'navy'],
                'green': ['yellow', 'teal', 'lime'],
                'orange': ['red', 'yellow', 'coral'],
                'purple': ['blue', 'pink', 'violet'],
                'yellow': ['orange', 'lime', 'gold']
            },
            'neutral': ['white', 'black', 'gray', 'beige', 'brown', 'tan', 'cream']
        }
        
        # Weather-appropriate features
        self.weather_features = {
            'warm': {
                'materials': ['cotton', 'linen', 'silk', 'chiffon', 'jersey'],
                'styles': ['sleeveless', 'short-sleeve', 'tank', 'shorts', 'sandals', 'light'],
                'avoid': ['wool', 'fleece', 'heavy', 'thick', 'boots', 'coat']
            },
            'cold': {
                'materials': ['wool', 'fleece', 'cashmere', 'leather', 'denim'],
                'styles': ['long-sleeve', 'sweater', 'jacket', 'boots', 'pants', 'thick'],
                'avoid': ['sleeveless', 'shorts', 'sandals', 'thin', 'light']
            }
        }
        
        # Style consistency mappings
        self.style_compatibility = {
            'casual': ['relaxed', 'comfortable', 'everyday', 'denim', 'sneakers', 'cotton'],
            'formal': ['elegant', 'sophisticated', 'dress', 'suit', 'heels', 'silk'],
            'business': ['professional', 'structured', 'blazer', 'trousers', 'leather'],
            'trendy': ['fashionable', 'modern', 'stylish', 'contemporary', 'designer'],
            'classic': ['timeless', 'traditional', 'conservative', 'neutral', 'basic'],
            'bohemian': ['flowy', 'artistic', 'ethnic', 'layered', 'natural'],
            'sporty': ['athletic', 'active', 'performance', 'sneakers', 'stretchy'],
            'edgy': ['bold', 'unconventional', 'leather', 'dark', 'statement']
        }
    
    def match_outfit_to_closet(
        self,
        db: Session,
        user: User,
        ai_recommendation: GeminiOutfitRecommendation,
        weather: str = "mild",
        style_preference: Optional[str] = None
    ) -> OutfitMatchResult:
        """
        Match AI-generated outfit recommendation to user's closet items
        
        Args:
            db: Database session
            user: User object
            ai_recommendation: AI-generated outfit recommendation
            weather: Weather condition (warm/cold/mild)
            style_preference: User's style preference
            
        Returns:
            OutfitMatchResult with matched items and scores
        """
        logger.info(f"Matching outfit for user {user.id} with weather: {weather}")
        
        # Get user's closet items
        closet_items = db.query(ClothingItem).filter(
            ClothingItem.user_id == user.id
        ).all()
        
        if not closet_items:
            logger.warning(f"No closet items found for user {user.id}")
            return OutfitMatchResult()
        
        # Group items by category
        items_by_category = self._group_items_by_category(closet_items)
        
        # Match each outfit component
        result = OutfitMatchResult()
        result.accessories = []
        
        # Match top
        if ai_recommendation.top:
            result.top = self._find_best_match(
                items_by_category.get('top', []),
                ai_recommendation.top,
                weather,
                style_preference
            )
        
        # Match bottom
        if ai_recommendation.bottom:
            result.bottom = self._find_best_match(
                items_by_category.get('bottom', []),
                ai_recommendation.bottom,
                weather,
                style_preference
            )
        
        # Match shoes
        if ai_recommendation.shoes:
            result.shoes = self._find_best_match(
                items_by_category.get('shoes', []),
                ai_recommendation.shoes,
                weather,
                style_preference
            )
        
        # Match outerwear
        if ai_recommendation.outerwear:
            result.outerwear = self._find_best_match(
                items_by_category.get('layering', []) + items_by_category.get('outerwear', []),
                ai_recommendation.outerwear,
                weather,
                style_preference
            )
        
        # Match accessories
        if ai_recommendation.accessories:
            for accessory in ai_recommendation.accessories:
                match = self._find_best_match(
                    items_by_category.get('accessory', []),
                    accessory,
                    weather,
                    style_preference
                )
                if match:
                    result.accessories.append(match)
        
        # Calculate overall scores
        result = self._calculate_overall_scores(result, weather, style_preference)
        
        # Track missing categories for future shopping feature
        missing_categories = []
        if ai_recommendation.top and not result.top:
            missing_categories.append('top')
        if ai_recommendation.bottom and not result.bottom:
            missing_categories.append('bottom')
        if ai_recommendation.shoes and not result.shoes:
            missing_categories.append('shoes')
        if ai_recommendation.outerwear and not result.outerwear:
            missing_categories.append('outerwear')
        if ai_recommendation.accessories and len(result.accessories or []) < len(ai_recommendation.accessories):
            missing_categories.append('accessories')
        
        result.missing_categories = missing_categories
        
        logger.info(f"Outfit matching completed with overall score: {result.overall_score:.3f}")
        if missing_categories:
            logger.info(f"Missing categories for future shopping feature: {missing_categories}")
        
        return result
    
    def _group_items_by_category(self, items: List[ClothingItem]) -> Dict[str, List[ClothingItem]]:
        """Group clothing items by category"""
        grouped = defaultdict(list)
        
        for item in items:
            category = item.category.lower()
            grouped[category].append(item)
        
        return dict(grouped)
    
    def _find_best_match(
        self,
        candidate_items: List[ClothingItem],
        target_item: OutfitItem,
        weather: str,
        style_preference: Optional[str]
    ) -> Optional[FeatureMatch]:
        """
        Find the best matching item from candidates for a target outfit item
        
        Args:
            candidate_items: List of clothing items to choose from
            target_item: AI-requested outfit item with features
            weather: Weather condition
            style_preference: User's style preference
            
        Returns:
            Best matching FeatureMatch or None if no suitable match
        """
        if not candidate_items:
            return None
        
        best_match = None
        best_score = 0.0
        
        for item in candidate_items:
            match = self._calculate_feature_match(
                item, target_item, weather, style_preference
            )
            
            if match.match_score > best_score:
                best_score = match.match_score
                best_match = match
        
        # Only return matches above minimum threshold
        if best_match and best_match.match_score >= 0.3:
            return best_match
        
        return None
    
    def _calculate_feature_match(
        self,
        clothing_item: ClothingItem,
        target_item: OutfitItem,
        weather: str,
        style_preference: Optional[str]
    ) -> FeatureMatch:
        """
        Calculate feature matching score between a clothing item and target features
        
        Args:
            clothing_item: User's clothing item
            target_item: AI-requested item with features
            weather: Weather condition
            style_preference: User's style preference
            
        Returns:
            FeatureMatch with detailed scoring
        """
        # Get item features from tags and extracted features
        item_features = set()
        
        # Add tags as features
        if clothing_item.tags:
            item_features.update(tag.lower() for tag in clothing_item.tags)
        
        # Add color as feature
        if clothing_item.color:
            item_features.add(clothing_item.color.lower())
        
        # Add category as feature
        item_features.add(clothing_item.category.lower())
        
        # Convert target features to lowercase set
        target_features = set(feature.lower() for feature in target_item.features)
        
        # Calculate feature overlap
        matched_features = list(item_features.intersection(target_features))
        missing_features = list(target_features - item_features)
        
        # Base feature match score
        if target_features:
            feature_score = len(matched_features) / len(target_features)
        else:
            feature_score = 0.5  # Neutral score if no specific features requested
        
        # Weather compatibility score
        weather_score = self._calculate_weather_compatibility(item_features, weather)
        
        # Color coordination score (placeholder - will be calculated in context)
        color_score = 0.8  # Default neutral score
        
        # Style consistency score
        style_score = self._calculate_style_consistency(item_features, style_preference)
        
        # Calculate overall match score with weights
        weights = {
            'features': 0.4,
            'weather': 0.2,
            'color': 0.2,
            'style': 0.2
        }
        
        overall_score = (
            feature_score * weights['features'] +
            weather_score * weights['weather'] +
            color_score * weights['color'] +
            style_score * weights['style']
        )
        
        # Confidence score based on number of matched features
        confidence_score = min(1.0, len(matched_features) / max(1, len(target_features) * 0.7))
        
        return FeatureMatch(
            clothing_item=clothing_item,
            match_score=overall_score,
            matched_features=matched_features,
            missing_features=missing_features,
            confidence_score=confidence_score,
            weather_compatibility=weather_score,
            color_coordination=color_score,
            style_consistency=style_score
        )
    
    def _calculate_weather_compatibility(self, item_features: set, weather: str) -> float:
        """Calculate weather compatibility score for an item"""
        if weather not in self.weather_features:
            return 0.8  # Neutral score for unknown weather
        
        weather_rules = self.weather_features[weather]
        
        # Check for appropriate materials and styles
        appropriate_count = 0
        inappropriate_count = 0
        
        for feature in item_features:
            if feature in weather_rules['materials'] or feature in weather_rules['styles']:
                appropriate_count += 1
            elif feature in weather_rules['avoid']:
                inappropriate_count += 1
        
        # Calculate score
        if appropriate_count + inappropriate_count == 0:
            return 0.7  # Neutral score if no weather-specific features
        
        score = appropriate_count / (appropriate_count + inappropriate_count)
        
        # Penalize inappropriate features more heavily
        if inappropriate_count > 0:
            score *= (1 - inappropriate_count * 0.2)
        
        return max(0.0, min(1.0, score))
    
    def _calculate_style_consistency(self, item_features: set, style_preference: Optional[str]) -> float:
        """Calculate style consistency score"""
        if not style_preference or style_preference not in self.style_compatibility:
            return 0.8  # Neutral score if no style preference
        
        style_features = set(self.style_compatibility[style_preference])
        
        # Check for style-consistent features
        consistent_features = item_features.intersection(style_features)
        
        if not style_features:
            return 0.8
        
        # Base score from feature overlap
        base_score = len(consistent_features) / len(style_features)
        
        # Bonus for having any consistent features
        if consistent_features:
            base_score = max(base_score, 0.6)
        
        return min(1.0, base_score)
    
    def _calculate_overall_scores(
        self,
        result: OutfitMatchResult,
        weather: str,
        style_preference: Optional[str]
    ) -> OutfitMatchResult:
        """Calculate overall outfit scores"""
        matches = []
        
        # Collect all matches
        if result.top:
            matches.append(result.top)
        if result.bottom:
            matches.append(result.bottom)
        if result.shoes:
            matches.append(result.shoes)
        if result.outerwear:
            matches.append(result.outerwear)
        if result.accessories:
            matches.extend(result.accessories)
        
        if not matches:
            return result
        
        # Calculate overall match score
        result.overall_score = sum(match.match_score for match in matches) / len(matches)
        
        # Calculate color harmony score
        result.color_harmony_score = self._calculate_color_harmony(matches)
        
        # Calculate style consistency across outfit
        result.style_consistency_score = self._calculate_outfit_style_consistency(matches, style_preference)
        
        # Calculate weather appropriateness
        result.weather_appropriateness = sum(match.weather_compatibility for match in matches) / len(matches)
        
        # Adjust overall score based on harmony and consistency
        harmony_weight = 0.2
        consistency_weight = 0.15
        weather_weight = 0.15
        
        result.overall_score = (
            result.overall_score * 0.5 +
            result.color_harmony_score * harmony_weight +
            result.style_consistency_score * consistency_weight +
            result.weather_appropriateness * weather_weight
        )
        
        return result
    
    def _calculate_color_harmony(self, matches: List[FeatureMatch]) -> float:
        """Calculate color harmony score for the outfit"""
        colors = []
        
        # Extract colors from matches
        for match in matches:
            if match.clothing_item.color:
                colors.append(match.clothing_item.color.lower())
        
        if len(colors) < 2:
            return 0.8  # Neutral score for single color or no colors
        
        harmony_score = 0.0
        color_pairs = 0
        
        # Check all color pairs for harmony
        for i in range(len(colors)):
            for j in range(i + 1, len(colors)):
                color1, color2 = colors[i], colors[j]
                pair_score = self._calculate_color_pair_harmony(color1, color2)
                harmony_score += pair_score
                color_pairs += 1
        
        if color_pairs == 0:
            return 0.8
        
        return harmony_score / color_pairs
    
    def _calculate_color_pair_harmony(self, color1: str, color2: str) -> float:
        """Calculate harmony score between two colors"""
        # Same color - perfect harmony
        if color1 == color2:
            return 1.0
        
        # Neutral colors go with everything
        if color1 in self.color_harmony_rules['neutral'] or color2 in self.color_harmony_rules['neutral']:
            return 0.9
        
        # Check complementary colors
        for base_color, complements in self.color_harmony_rules['complementary'].items():
            if (color1 == base_color and color2 in complements) or \
               (color2 == base_color and color1 in complements):
                return 0.85
        
        # Check analogous colors
        for base_color, analogous in self.color_harmony_rules['analogous'].items():
            if (color1 == base_color and color2 in analogous) or \
               (color2 == base_color and color1 in analogous):
                return 0.8
        
        # Default score for unknown color combinations
        return 0.6
    
    def _calculate_outfit_style_consistency(
        self,
        matches: List[FeatureMatch],
        style_preference: Optional[str]
    ) -> float:
        """Calculate style consistency across the entire outfit"""
        if not style_preference:
            return 0.8
        
        style_scores = [match.style_consistency for match in matches]
        
        if not style_scores:
            return 0.8
        
        # Average style consistency with penalty for high variance
        avg_score = sum(style_scores) / len(style_scores)
        
        # Calculate variance penalty
        if len(style_scores) > 1:
            variance = sum((score - avg_score) ** 2 for score in style_scores) / len(style_scores)
            variance_penalty = min(0.2, variance)
            avg_score -= variance_penalty
        
        return max(0.0, min(1.0, avg_score))
    
    def get_match_explanation(self, match: FeatureMatch) -> Dict[str, Any]:
        """Get detailed explanation of why an item was matched"""
        return {
            'item_id': str(match.clothing_item.id),
            'item_category': match.clothing_item.category,
            'match_score': round(match.match_score, 3),
            'confidence': round(match.confidence_score, 3),
            'matched_features': match.matched_features,
            'missing_features': match.missing_features,
            'weather_compatibility': round(match.weather_compatibility, 3),
            'color_coordination': round(match.color_coordination, 3),
            'style_consistency': round(match.style_consistency, 3),
            'explanation': self._generate_match_explanation(match)
        }
    
    def _generate_match_explanation(self, match: FeatureMatch) -> str:
        """Generate human-readable explanation for the match"""
        explanations = []
        
        if match.matched_features:
            explanations.append(f"Matches {len(match.matched_features)} requested features: {', '.join(match.matched_features[:3])}")
        
        if match.weather_compatibility > 0.8:
            explanations.append("Excellent weather compatibility")
        elif match.weather_compatibility < 0.5:
            explanations.append("Limited weather compatibility")
        
        if match.style_consistency > 0.8:
            explanations.append("Strong style consistency")
        
        if match.missing_features:
            explanations.append(f"Missing features: {', '.join(match.missing_features[:2])}")
        
        return "; ".join(explanations) if explanations else "Basic compatibility match"


# Global service instance - initialize when needed
outfit_matching_service = None

def get_outfit_matching_service():
    """Get or create the global outfit matching service instance"""
    global outfit_matching_service
    if outfit_matching_service is None:
        outfit_matching_service = OutfitMatchingService()
    return outfit_matching_service