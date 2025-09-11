"""
Feature-based outfit matching service for AI-generated recommendations

🚀 NEW 4-METRIC WEIGHTED SCORING SYSTEM IMPLEMENTED:

1. SEMANTIC FEATURE MAPPING (35%) - Maps AI vocabulary to real clothing descriptors
   - Addresses core vocabulary mismatch between AI terms and user tags
   - Uses semantic dictionary to translate terms like "smart-casual" → ["business", "professional", "dressy"]
   
2. STYLE CONTEXT CONSISTENCY (25%) - Natural activity context matching  
   - Combines occasion + description into natural format like "wine bar tasting then a walk"
   - Matches training data format used for AI model
   - Evaluates alignment with overall AI style direction
   
3. CATEGORY APPROPRIATENESS (20%) - Ensures correct item type for outfit role
   - Handles category mapping issues (tops/top, bottoms/bottom)
   - Special handling for versatile items (blazers can be outerwear or tops)
   
4. COLOR HARMONY (20%) - Flexible color coordination with AI recommendations
   - Uses AI color palette from recommendations 
   - Neutral colors work with everything, earth tones work together
   - Color family matching for harmonious combinations

This replaces the previous flat scoring system that was causing poor matches.
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
        logger.info(f"🤖 AI Recommendation:")
        if ai_recommendation.top:
            logger.info(f"   Top: {ai_recommendation.top.type} - {ai_recommendation.top.features}")
        if ai_recommendation.bottom:
            logger.info(f"   Bottom: {ai_recommendation.bottom.type} - {ai_recommendation.bottom.features}")
        if ai_recommendation.shoes:
            logger.info(f"   Shoes: {ai_recommendation.shoes.type} - {ai_recommendation.shoes.features}")
        if ai_recommendation.outerwear:
            logger.info(f"   Outerwear: {ai_recommendation.outerwear.type} - {ai_recommendation.outerwear.features}")
        if ai_recommendation.accessories:
            for i, acc in enumerate(ai_recommendation.accessories):
                logger.info(f"   Accessory {i+1}: {acc.type} - {acc.features}")
        
        # Get user's closet items
        closet_items = db.query(ClothingItem).filter(
            ClothingItem.user_id == user.id
        ).all()
        
        if not closet_items:
            logger.warning(f"No closet items found for user {user.id}")
            return OutfitMatchResult()
        
        # Group items by category
        items_by_category = self._group_items_by_category(closet_items)
        logger.info(f"📂 Items grouped by category: {list(items_by_category.keys())}")
        for category, items in items_by_category.items():
            logger.info(f"   {category}: {len(items)} items")
        
        # Match each outfit component
        result = OutfitMatchResult()
        result.accessories = []
        
        # Match top (handle database category naming mismatch)
        if ai_recommendation.top:
            # Extract style context from full AI response
            style_context = self._extract_style_context(
                ai_recommendation.__dict__, 
                getattr(ai_recommendation, 'occasion', None),
                getattr(ai_recommendation, 'description', None)
            )
            
            top_candidates = (items_by_category.get('top', []) + 
                            items_by_category.get('tops', []))
            result.top = self._find_best_match(
                top_candidates,
                ai_recommendation.top,
                weather,
                style_preference,
                style_context
            )

        # Match bottom (handle database category naming mismatch)
        if ai_recommendation.bottom:
            # Use same style context for consistency
            if 'style_context' not in locals():
                style_context = self._extract_style_context(
                    ai_recommendation.__dict__, 
                    getattr(ai_recommendation, 'occasion', None),
                    getattr(ai_recommendation, 'description', None)
                )
            
            bottom_candidates = (items_by_category.get('bottom', []) + 
                               items_by_category.get('bottoms', []))
            result.bottom = self._find_best_match(
                bottom_candidates,
                ai_recommendation.bottom,
                weather,
                style_preference,
                style_context
            )

        # Match shoes
        if ai_recommendation.shoes:
            # Use same style context for consistency
            if 'style_context' not in locals():
                style_context = self._extract_style_context(
                    ai_recommendation.__dict__, 
                    getattr(ai_recommendation, 'occasion', None),
                    getattr(ai_recommendation, 'description', None)
                )
            
            result.shoes = self._find_best_match(
                items_by_category.get('shoes', []),
                ai_recommendation.shoes,
                weather,
                style_preference,
                style_context
            )

        # Match outerwear (handle multiple category options)
        if ai_recommendation.outerwear:
            # Use same style context for consistency
            if 'style_context' not in locals():
                style_context = self._extract_style_context(
                    ai_recommendation.__dict__, 
                    getattr(ai_recommendation, 'occasion', None),
                    getattr(ai_recommendation, 'description', None)
                )
            
            outerwear_candidates = (items_by_category.get('layering', []) + 
                                  items_by_category.get('outerwear', []) +
                                  items_by_category.get('formal', []))  # Include formal wear as potential outerwear
            result.outerwear = self._find_best_match(
                outerwear_candidates,
                ai_recommendation.outerwear,
                weather,
                style_preference,
                style_context
            )

        # Match accessories (handle multiple category options)
        if ai_recommendation.accessories:
            # Use same style context for consistency
            if 'style_context' not in locals():
                style_context = self._extract_style_context(
                    ai_recommendation.__dict__, 
                    getattr(ai_recommendation, 'occasion', None),
                    getattr(ai_recommendation, 'description', None)
                )
            
            for accessory in ai_recommendation.accessories:
                # Try multiple categories for accessories
                accessory_candidates = (items_by_category.get('accessory', []) + 
                                      items_by_category.get('accessories', []) +
                                      items_by_category.get('formal', []))  # Include formal items as potential accessories
                match = self._find_best_match(
                    accessory_candidates,
                    accessory,
                    weather,
                    style_preference,
                    style_context
                )
                if match:
                    result.accessories.append(match)        # Calculate overall scores
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
        style_preference: Optional[str],
        style_context: Optional[Dict[str, Any]] = None
    ) -> Optional[FeatureMatch]:
        """
        Find the best matching item from candidates for a target outfit item
        
        Args:
            candidate_items: List of clothing items to choose from
            target_item: AI-requested outfit item with features
            weather: Weather condition
            style_preference: User's style preference
            style_context: Enhanced style context from AI recommendation + occasion
            
        Returns:
            Best matching FeatureMatch or None if no suitable match
        """
        logger.info(f"🔍 Finding best match for {target_item.type}")
        logger.info(f"   Target features: {target_item.features}")
        logger.info(f"   Available candidates: {len(candidate_items)}")
        if style_context:
            logger.info(f"   Style context: {style_context.get('style_keywords', [])} | Activity: {style_context.get('activity_context', 'N/A')}")
        
        if not candidate_items:
            logger.warning(f"   ❌ No candidates available for {target_item.type}")
            return None
        
        best_match = None
        best_score = 0.0
        
        for item in candidate_items:
            match = self._calculate_feature_match(
                item, target_item, weather, style_preference, style_context
            )
            
            logger.info(f"   📊 Item {str(item.id)[:8]}... ({item.color} {item.category})")
            logger.info(f"      Tags: {item.tags}")
            logger.info(f"      🎯 TOTAL SCORE: {match.match_score:.3f}")
            logger.info(f"      🧠 Semantic Features (35%): {match.style_consistency:.3f}")
            logger.info(f"      🎨 Style Context (25%): {match.weather_compatibility:.3f}")
            logger.info(f"      📂 Category Match (20%): N/A")  # Will need to extract this from calculation
            logger.info(f"      🌈 Color Harmony (20%): {match.color_coordination:.3f}")
            logger.info(f"      ✅ Matched features: {match.matched_features}")
            logger.info(f"      ❌ Missing features: {match.missing_features}")
            
            if match.match_score > best_score:
                best_score = match.match_score
                best_match = match
        
        # Only return matches above minimum threshold
        threshold = 0.3
        if best_match and best_match.match_score >= threshold:
            logger.info(f"   ✅ BEST MATCH: {str(best_match.clothing_item.id)[:8]}... (score: {best_match.match_score:.3f})")
            return best_match
        else:
            logger.warning(f"   ❌ NO MATCH above threshold {threshold}. Best was {best_score:.3f}")
            return None
    
    def _calculate_feature_match(
        self,
        clothing_item: ClothingItem,
        target_item: OutfitItem,
        weather: str,
        style_preference: Optional[str],
        style_context: Optional[Dict[str, Any]] = None
    ) -> FeatureMatch:
        """
        NEW 4-METRIC WEIGHTED SCORING SYSTEM
        
        Calculate comprehensive feature matching using:
        1. Semantic Feature Mapping (35%) - AI features vs item tags with semantic mapping
        2. Style Context Consistency (25%) - Activity context and AI style elements  
        3. Category Appropriateness (20%) - Right item type for the category
        4. Color Harmony (20%) - Color coordination with AI recommendations
        
        Args:
            clothing_item: User's clothing item
            target_item: AI-requested item with features
            weather: Weather condition
            style_preference: User's style preference
            style_context: Enhanced style context from AI recommendation + occasion
            
        Returns:
            FeatureMatch with detailed scoring
        """
        # Get item features from tags, extracted features, and user descriptions
        item_features = set()
        
        # Add tags as features
        if clothing_item.tags:
            item_features.update(tag.lower() for tag in clothing_item.tags)
        
        # Add color as feature
        if clothing_item.color:
            item_features.add(clothing_item.color.lower())
        
        # Add category as feature
        item_features.add(clothing_item.category.lower())
        
        # DISABLED: Extract features from user description (Fashion-CLIP handles feature extraction now)
        # if clothing_item.description:
        #     description_features = self._extract_features_from_description(clothing_item.description)
        #     item_features.update(description_features)
        
        # Get target features from AI recommendation
        target_features = set(feature.lower() for feature in target_item.features)
        
        # ===== METRIC 1: SEMANTIC FEATURE MAPPING (35%) =====
        semantic_score = self._calculate_semantic_feature_match(item_features, target_features, style_context)
        
        # ===== METRIC 2: STYLE CONTEXT CONSISTENCY (25%) =====
        style_context_score = self._calculate_style_context_consistency(item_features, style_context) if style_context else 0.6
        
        # ===== METRIC 3: CATEGORY APPROPRIATENESS (20%) =====
        category_score = self._calculate_category_appropriateness(clothing_item, target_item)
        
        # ===== METRIC 4: COLOR HARMONY (20%) =====
        color_score = self._calculate_ai_color_harmony(clothing_item, target_item, style_context)
        
        # ===== WEIGHTED COMBINATION =====
        weights = {
            'semantic': 0.35,      # Primary: semantic feature matching with AI vocabulary
            'style_context': 0.25, # Style consistency from AI + natural activity context
            'category': 0.20,      # Category appropriateness for outfit role
            'color': 0.20         # Color harmony with AI color palette
        }
        
        overall_score = (
            semantic_score * weights['semantic'] +
            style_context_score * weights['style_context'] +
            category_score * weights['category'] +
            color_score * weights['color']
        )
        
        # Calculate matched/missing features for debugging
        matched_features = list(item_features.intersection(target_features))
        missing_features = list(target_features - item_features)
        
        # Confidence score based on semantic matching strength
        confidence_score = min(1.0, semantic_score * 1.2)
        
        return FeatureMatch(
            clothing_item=clothing_item,
            match_score=overall_score,
            matched_features=matched_features,
            missing_features=missing_features,
            confidence_score=confidence_score,
            weather_compatibility=style_context_score,  # Repurposed for style context
            color_coordination=color_score,
            style_consistency=semantic_score  # Repurposed for semantic matching
        )
    
    def _extract_features_from_description(self, description: str) -> set:
        """
        Extract relevant features from user-provided item descriptions
        
        Args:
            description: User's description of the clothing item
            
        Returns:
            Set of extracted features
        """
        if not description:
            return set()
        
        description_lower = description.lower()
        features = set()
        
        # Style and occasion keywords
        style_keywords = {
            'casual': 'casual', 'formal': 'formal', 'business': 'business', 
            'professional': 'professional', 'dressy': 'dressy', 'elegant': 'elegant',
            'sporty': 'sporty', 'athletic': 'athletic', 'trendy': 'trendy',
            'classic': 'classic', 'vintage': 'vintage', 'modern': 'modern',
            'bohemian': 'bohemian', 'boho': 'bohemian', 'edgy': 'edgy',
            'cute': 'cute', 'sexy': 'sexy', 'comfortable': 'comfortable',
            'cozy': 'cozy', 'chic': 'chic', 'sophisticated': 'sophisticated'
        }
        
        # Material and texture keywords
        material_keywords = {
            'cotton': 'cotton', 'silk': 'silk', 'wool': 'wool', 'cashmere': 'cashmere',
            'linen': 'linen', 'denim': 'denim', 'leather': 'leather', 'suede': 'suede',
            'polyester': 'polyester', 'nylon': 'nylon', 'spandex': 'stretchy',
            'fleece': 'fleece', 'velvet': 'velvet', 'satin': 'satin',
            'soft': 'soft', 'smooth': 'smooth', 'rough': 'textured',
            'stretchy': 'stretchy', 'thick': 'thick', 'thin': 'thin',
            'lightweight': 'light', 'heavy': 'heavy'
        }
        
        # Pattern keywords
        pattern_keywords = {
            'striped': 'striped', 'stripes': 'striped', 'polka dot': 'polka_dot',
            'floral': 'floral', 'plaid': 'plaid', 'checkered': 'checkered',
            'solid': 'solid', 'plain': 'solid', 'patterned': 'patterned',
            'printed': 'printed', 'geometric': 'geometric'
        }
        
        # Fit keywords
        fit_keywords = {
            'tight': 'fitted', 'fitted': 'fitted', 'loose': 'loose', 'baggy': 'loose',
            'oversized': 'oversized', 'slim': 'slim', 'regular': 'regular',
            'relaxed': 'relaxed', 'tailored': 'tailored'
        }
        
        # Occasion keywords
        occasion_keywords = {
            'work': 'work', 'office': 'work', 'meeting': 'formal',
            'party': 'party', 'date': 'date', 'wedding': 'wedding',
            'travel': 'travel', 'vacation': 'vacation', 'beach': 'beach',
            'gym': 'athletic', 'workout': 'athletic', 'running': 'athletic',
            'everyday': 'everyday', 'weekend': 'casual'
        }
        
        # Weather keywords
        weather_keywords = {
            'summer': 'summer', 'winter': 'winter', 'spring': 'spring', 'fall': 'fall',
            'hot': 'hot', 'warm': 'warm', 'cool': 'cool', 'cold': 'cold',
            'sunny': 'sunny', 'rainy': 'rainy', 'windy': 'windy'
        }
        
        # Extract features from all keyword categories
        all_keywords = {
            **style_keywords, **material_keywords, **pattern_keywords,
            **fit_keywords, **occasion_keywords, **weather_keywords
        }
        
        for keyword, feature in all_keywords.items():
            if keyword in description_lower:
                features.add(feature)
        
        # Extract color mentions (basic color detection)
        color_keywords = [
            'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink',
            'black', 'white', 'gray', 'grey', 'brown', 'beige', 'navy',
            'maroon', 'burgundy', 'teal', 'lime', 'coral', 'lavender'
        ]
        
        for color in color_keywords:
            if color in description_lower:
                features.add(color)
        
        return features
    
    def _extract_style_context(self, ai_response: Dict, occasion: str = None, description: str = None) -> Dict[str, Any]:
        """
        Extract style context primarily from AI recommendation output,
        with natural activity context combining occasion and description.
        
        Based on training data patterns like "wine bar tasting then a walk" or "thrifting downtown then boba".
        """
        try:
            style_context = {
                'ai_features': set(),
                'ai_colors': set(), 
                'ai_types': set(),
                'activity_context': "",
                'style_keywords': set()
            }
            
            # Extract features, colors, and types from AI recommendation
            for category, item_data in ai_response.items():
                if isinstance(item_data, dict):
                    # Extract item type
                    if 'type' in item_data:
                        style_context['ai_types'].add(item_data['type'])
                    
                    # Extract primary and alternative colors
                    if 'color' in item_data:
                        style_context['ai_colors'].add(item_data['color'])
                    if 'color_alternatives' in item_data:
                        style_context['ai_colors'].update(item_data['color_alternatives'])
                    
                    # Extract features (this is the rich context from AI)
                    if 'features' in item_data and isinstance(item_data['features'], list):
                        style_context['ai_features'].update(item_data['features'])
            
            # Create natural activity description combining occasion and description
            # This matches training format like "birthday dinner at a buzzy ramen spot"
            activity_parts = []
            if occasion and occasion.strip():
                activity_parts.append(occasion.strip())
            if description and description.strip():
                activity_parts.append(description.strip())
            
            style_context['activity_context'] = " ".join(activity_parts) if activity_parts else ""
            
            # Extract meaningful keywords from the combined activity text
            if style_context['activity_context']:
                activity_words = style_context['activity_context'].lower().split()
                # Filter out common words and keep meaningful style/activity keywords
                meaningful_words = [word for word in activity_words 
                                  if len(word) > 3 and word not in {'with', 'then', 'for', 'and', 'the', 'at', 'to', 'in', 'on'}]
                style_context['style_keywords'].update(meaningful_words)
            
            logger.info(f"Style context extracted - AI features: {len(style_context['ai_features'])}, "
                       f"AI colors: {len(style_context['ai_colors'])}, AI types: {len(style_context['ai_types'])}, "
                       f"Activity: '{style_context['activity_context'][:80]}{'...' if len(style_context['activity_context']) > 80 else ''}', "
                       f"Keywords: {style_context['style_keywords']}")
            
            return style_context
            
        except Exception as e:
            logger.error(f"Error extracting style context: {str(e)}")
            return {
                'ai_features': set(),
                'ai_colors': set(),
                'ai_types': set(), 
                'activity_context': "",
                'style_keywords': set()
            }
    
    def _calculate_semantic_feature_match(self, item_features: set, target_features: set, style_context: Optional[Dict[str, Any]] = None) -> float:
        """
        METRIC 1: Semantic Feature Mapping (35%)
        
        Maps AI vocabulary to real clothing descriptors using semantic relationships.
        Addresses the core issue of vocabulary mismatch between AI and user tags.
        """
        if not target_features:
            return 0.6  # Neutral score if no target features
        
        # Semantic mapping dictionary - maps AI terms to common clothing descriptors
        semantic_mappings = {
            # Style mappings
            'smart-casual': ['business', 'professional', 'dressy', 'polished', 'clean'],
            'evening-ready': ['formal', 'dressy', 'elegant', 'sophisticated', 'fancy'],
            'polished finish': ['formal', 'dressy', 'business', 'professional', 'clean'],
            'refined construction': ['quality', 'well-made', 'structured', 'tailored'],
            'architectural silhouette': ['structured', 'tailored', 'geometric', 'modern'],
            'artisanal finish': ['handmade', 'unique', 'textured', 'bohemian', 'crafted'],
            
            # Texture/material mappings
            'brushed fleece': ['soft', 'warm', 'cozy', 'comfortable', 'fleece'],
            'thermal knit': ['warm', 'winter', 'thick', 'insulated', 'cozy'],
            'moisture-wicking': ['athletic', 'sporty', 'performance', 'activewear'],
            'breathable fabric': ['summer', 'light', 'airy', 'comfortable', 'cotton'],
            'quick-dry': ['athletic', 'sporty', 'performance', 'travel'],
            'water-resistant': ['outdoor', 'practical', 'weather', 'jacket'],
            
            # Fit/silhouette mappings
            'relaxed fit': ['loose', 'comfortable', 'casual', 'oversized'],
            'tailored fit': ['fitted', 'structured', 'professional', 'sharp'],
            'wide leg': ['flowy', 'loose', 'palazzo', 'relaxed'],
            'cropped length': ['short', 'ankle', 'cropped', 'modern'],
            'longline hem': ['long', 'tunic', 'extended', 'covering'],
            
            # Color/aesthetic mappings  
            'vintage vibe': ['retro', 'classic', 'timeless', 'old-school'],
            'modern aesthetic': ['contemporary', 'current', 'trendy', 'fresh'],
            'minimalist': ['simple', 'clean', 'basic', 'unadorned'],
            'bohemian': ['boho', 'free-spirited', 'artistic', 'flowing'],
            
            # Weather mappings
            'windproof': ['jacket', 'outdoor', 'protective', 'weather'],
            'insulated fill': ['warm', 'winter', 'puffy', 'insulated', 'down'],
            'upf-rated': ['sun protection', 'summer', 'outdoor', 'uv'],
            
            # Hardware/details mappings
            'minimal hardware': ['simple', 'clean', 'understated', 'basic'],
            'contrast stitching': ['detailed', 'accented', 'highlighted', 'decorative'],
            'utility pockets': ['functional', 'practical', 'cargo', 'multi-pocket'],
            'zip pocket': ['secure', 'functional', 'detailed', 'practical']
        }
        
        # Calculate direct matches
        direct_matches = item_features.intersection(target_features)
        direct_score = len(direct_matches) / len(target_features) if target_features else 0
        
        # Calculate semantic matches
        semantic_matches = 0
        for target_feature in target_features:
            if target_feature in semantic_mappings:
                mapped_terms = set(semantic_mappings[target_feature])
                if mapped_terms.intersection(item_features):
                    semantic_matches += 1
        
        semantic_score = semantic_matches / len(target_features) if target_features else 0
        
        # Combine direct and semantic matching (weighted toward semantic for AI vocabulary)
        combined_score = (direct_score * 0.3) + (semantic_score * 0.7)
        
        return min(1.0, combined_score)
    
    def _calculate_style_context_consistency(self, item_features: set, style_context: Optional[Dict[str, Any]]) -> float:
        """
        METRIC 2: Style Context Consistency (25%)
        
        Evaluates how well the item fits the natural activity context from AI + occasion.
        Uses the combined activity text like "wine bar tasting then a walk".
        """
        if not style_context:
            return 0.6  # Neutral score if no context
        
        context_score = 0.0
        context_factors = 0
        
        # Activity context matching
        activity_keywords = style_context.get('style_keywords', set())
        if activity_keywords:
            activity_matches = len(item_features.intersection(activity_keywords))
            activity_score = min(1.0, activity_matches / max(1, len(activity_keywords) * 0.3))
            context_score += activity_score * 0.4
            context_factors += 0.4
        
        # AI features consistency (how well item aligns with overall AI style direction)
        ai_features = style_context.get('ai_features', set())
        if ai_features:
            # Look for style-level alignment rather than exact feature matching
            style_alignment = self._calculate_style_alignment(item_features, ai_features)
            context_score += style_alignment * 0.3
            context_factors += 0.3
        
        # AI color palette consistency  
        ai_colors = style_context.get('ai_colors', set())
        if ai_colors:
            color_alignment = self._calculate_color_alignment(item_features, ai_colors)
            context_score += color_alignment * 0.3
            context_factors += 0.3
        
        # Normalize by actual factors used
        if context_factors > 0:
            return context_score / context_factors
        else:
            return 0.6  # Neutral if no context available
    
    def _calculate_category_appropriateness(self, clothing_item: ClothingItem, target_item: OutfitItem) -> float:
        """
        METRIC 3: Category Appropriateness (20%)
        
        Ensures the item type is appropriate for the requested outfit role.
        """
        # Category matching rules
        category_mappings = {
            'top': ['top', 'tops', 'shirt', 'blouse', 'sweater', 'tank', 'tee'],
            'bottom': ['bottom', 'bottoms', 'pants', 'jeans', 'shorts', 'skirt'],
            'shoes': ['shoes', 'footwear', 'sneakers', 'boots', 'sandals'],
            'outerwear': ['jacket', 'coat', 'blazer', 'cardigan', 'hoodie', 'sweater'],
            'accessory': ['accessory', 'accessories', 'bag', 'hat', 'jewelry', 'belt', 'scarf']
        }
        
        # Get the target category based on clothing item category
        item_category = clothing_item.category.lower()
        
        # Check direct category match first
        for target_cat, acceptable_cats in category_mappings.items():
            if item_category in acceptable_cats:
                return 1.0  # Perfect category match
        
        # Type-based matching for edge cases
        target_type = target_item.type.lower()
        
        # Special handling for versatile items
        if any(word in target_type for word in ['cardigan', 'blazer', 'jacket']):
            if item_category in ['outerwear', 'layering', 'formal', 'tops']:
                return 0.9
        
        if any(word in target_type for word in ['dress', 'jumpsuit']):
            if item_category in ['dresses', 'formal', 'tops']:
                return 0.9
        
        # Partial match fallback
        return 0.4  # Some utility but not ideal category
    
    def _calculate_ai_color_harmony(self, clothing_item: ClothingItem, target_item: OutfitItem, style_context: Optional[Dict[str, Any]]) -> float:
        """
        METRIC 4: Color Harmony (20%)
        
        Evaluates color coordination with AI recommendations using flexible matching.
        """
        if not clothing_item.color:
            return 0.5  # Neutral if no color info
        
        item_color = clothing_item.color.lower()
        
        # Get AI color palette from style context
        ai_colors = set()
        if style_context:
            ai_colors = style_context.get('ai_colors', set())
        
        # Add target item colors
        if hasattr(target_item, 'color') and target_item.color:
            ai_colors.add(target_item.color.lower())
        if hasattr(target_item, 'color_alternatives') and target_item.color_alternatives:
            ai_colors.update(alt.lower() for alt in target_item.color_alternatives)
        
        if not ai_colors:
            return 0.6  # Neutral if no AI colors available
        
        # Direct color match
        if item_color in ai_colors:
            return 1.0
        
        # Flexible color harmony rules
        harmony_score = self._calculate_flexible_color_harmony(item_color, ai_colors)
        
        return harmony_score
    
    def _calculate_style_alignment(self, item_features: set, ai_features: set) -> float:
        """Helper method for style alignment calculation"""
        if not ai_features:
            return 0.5
        
        # Look for complementary style themes rather than exact matches
        style_themes = {
            'formal': ['business', 'professional', 'dressy', 'elegant', 'polished'],
            'casual': ['relaxed', 'comfortable', 'everyday', 'easy'],
            'athletic': ['sporty', 'performance', 'activewear', 'gym'],
            'bohemian': ['boho', 'artistic', 'free-spirited', 'flowing'],
            'vintage': ['retro', 'classic', 'timeless', 'old-school']
        }
        
        # Find dominant themes in AI features
        ai_themes = set()
        for feature in ai_features:
            for theme, keywords in style_themes.items():
                if any(keyword in feature for keyword in keywords):
                    ai_themes.add(theme)
        
        # Find themes in item features
        item_themes = set()
        for feature in item_features:
            for theme, keywords in style_themes.items():
                if feature in keywords:
                    item_themes.add(theme)
        
        # Calculate theme alignment
        if ai_themes and item_themes:
            alignment = len(ai_themes.intersection(item_themes)) / len(ai_themes.union(item_themes))
            return alignment
        
        return 0.5  # Neutral if no clear themes
    
    def _calculate_color_alignment(self, item_features: set, ai_colors: set) -> float:
        """Helper method for color alignment calculation"""
        # Extract colors from item features
        item_colors = set()
        for feature in item_features:
            if feature in ai_colors:
                item_colors.add(feature)
        
        if ai_colors and item_colors:
            return len(item_colors) / len(ai_colors)
        
        return 0.5  # Neutral if no color overlap
    
    def _calculate_flexible_color_harmony(self, item_color: str, ai_colors: set) -> float:
        """Helper method for flexible color harmony"""
        # Color harmony rules (simplified for now)
        neutral_colors = {'black', 'white', 'gray', 'grey', 'beige', 'navy', 'cream'}
        earth_tones = {'brown', 'tan', 'khaki', 'olive', 'camel', 'rust'}
        
        # Neutrals work with everything
        if item_color in neutral_colors:
            return 0.8
        
        # Earth tones work well together
        if item_color in earth_tones and any(color in earth_tones for color in ai_colors):
            return 0.7
        
        # Similar color families (this could be expanded with color theory)
        blues = {'blue', 'navy', 'teal', 'turquoise', 'sky'}
        reds = {'red', 'burgundy', 'wine', 'crimson', 'coral'}
        greens = {'green', 'olive', 'forest', 'sage', 'mint'}
        
        color_families = [blues, reds, greens, earth_tones, neutral_colors]
        
        for family in color_families:
            if item_color in family and any(color in family for color in ai_colors):
                return 0.6
        
        return 0.3  # Low harmony but not completely incompatible
    
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
        
        # DISABLED: Check if description contributed to the match (now using Fashion-CLIP)
        # if match.clothing_item.description:
        #     description_features = self._extract_features_from_description(match.clothing_item.description)
        #     matched_description_features = set(match.matched_features).intersection(description_features)
        #     if matched_description_features:
        #         explanations.append(f"Description provided helpful details for matching")
        
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