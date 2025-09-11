"""
Focused GCP Vision service for color and brand detection.
This service extracts only what GCP Vision does well: colors and text/brand recognition.
"""
import logging
from typing import List, Dict, Optional, Any
import base64
import re

try:
    from google.cloud import vision
    HAS_GCP_VISION = True
except ImportError:
    HAS_GCP_VISION = False
    vision = None

from app.core.config import settings

logger = logging.getLogger(__name__)

class GCPColorBrandService:
    """
    Focused GCP Vision service for color and brand detection only.
    
    This service is designed to complement Fashion-CLIP by providing:
    - Accurate color detection and analysis
    - Brand name recognition from text/logos
    - Color dominance and palette information
    """
    
    def __init__(self):
        if not HAS_GCP_VISION:
            raise ImportError("Google Cloud Vision API is not available")
        
        self.client = vision.ImageAnnotatorClient()
        
        # Known fashion brands for validation
        self.fashion_brands = {
            'nike', 'adidas', 'puma', 'under armour', 'reebok', 'converse', 'vans',
            'levi\'s', 'levis', 'gap', 'zara', 'h&m', 'uniqlo', 'calvin klein',
            'tommy hilfiger', 'polo ralph lauren', 'lacoste', 'champion', 'supreme',
            'gucci', 'prada', 'versace', 'armani', 'dolce & gabbana', 'burberry',
            'coach', 'michael kors', 'kate spade', 'marc jacobs', 'tory burch',
            'forever 21', 'old navy', 'american eagle', 'hollister', 'abercrombie',
            'patagonia', 'north face', 'columbia', 'timberland', 'dr. martens'
        }
        
        # Standard color names for consistency
        self.standard_colors = {
            'black', 'white', 'gray', 'grey', 'red', 'blue', 'green', 'yellow',
            'orange', 'purple', 'pink', 'brown', 'beige', 'tan', 'navy', 'khaki',
            'cream', 'ivory', 'silver', 'gold', 'maroon', 'teal', 'turquoise',
            'coral', 'salmon', 'mint', 'lime', 'olive', 'burgundy', 'magenta'
        }
        
        logger.info("GCP Color & Brand service initialized")
    
    async def analyze_colors_and_brands(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze image for colors and brand information.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary containing color and brand analysis
        """
        try:
            # Create Vision API image object
            image = vision.Image(content=image_data)
            
            # Run both analyses in parallel
            color_analysis = self._analyze_colors(image)
            brand_analysis = self._detect_brands(image)
            
            return {
                'success': True,
                'colors': color_analysis,
                'brands': brand_analysis,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"GCP color/brand analysis failed: {str(e)}")
            return {
                'success': False,
                'colors': {},
                'brands': {},
                'error': str(e)
            }
    
    def _analyze_colors(self, image: vision.Image) -> Dict[str, Any]:
        """Extract color information from the image."""
        try:
            # Get image properties for color analysis
            response = self.client.image_properties(image=image)
            colors = response.image_properties_annotation.dominant_colors.colors
            
            # Process dominant colors
            dominant_colors = []
            color_percentages = {}
            
            for color in colors[:10]:  # Top 10 colors
                # Convert RGB to color name
                rgb = (
                    int(color.color.red),
                    int(color.color.green), 
                    int(color.color.blue)
                )
                
                color_name = self._rgb_to_color_name(rgb)
                percentage = color.percentage_area * 100
                
                dominant_colors.append({
                    'color': color_name,
                    'rgb': rgb,
                    'percentage': round(percentage, 2)
                })
                
                # Aggregate similar colors
                if color_name in color_percentages:
                    color_percentages[color_name] += percentage
                else:
                    color_percentages[color_name] = percentage
            
            # Get primary color (highest percentage)
            primary_color = max(color_percentages.items(), key=lambda x: x[1])[0] if color_percentages else 'unknown'
            
            return {
                'primary_color': primary_color,
                'dominant_colors': dominant_colors,
                'color_percentages': {k: round(v, 2) for k, v in color_percentages.items()},
                'total_colors': len(set(c['color'] for c in dominant_colors))
            }
            
        except Exception as e:
            logger.error(f"Color analysis failed: {str(e)}")
            return {
                'primary_color': 'unknown',
                'dominant_colors': [],
                'color_percentages': {},
                'total_colors': 0
            }
    
    def _detect_brands(self, image: vision.Image) -> Dict[str, Any]:
        """Detect brand names from text in the image."""
        try:
            # Get text detection
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            
            if not texts:
                return {
                    'detected_brands': [],
                    'all_text': [],
                    'confidence_scores': {}
                }
            
            # Extract all text
            all_text = []
            detected_brands = []
            confidence_scores = {}
            
            for text in texts[1:]:  # Skip the first one (full text)
                text_content = text.description.lower().strip()
                all_text.append(text_content)
                
                # Check if text matches known brands
                for brand in self.fashion_brands:
                    if self._text_matches_brand(text_content, brand):
                        confidence = self._calculate_text_confidence(text)
                        detected_brands.append({
                            'brand': brand,
                            'matched_text': text_content,
                            'confidence': confidence
                        })
                        confidence_scores[brand] = confidence
            
            # Remove duplicates and sort by confidence
            unique_brands = {}
            for brand_info in detected_brands:
                brand = brand_info['brand']
                if brand not in unique_brands or brand_info['confidence'] > unique_brands[brand]['confidence']:
                    unique_brands[brand] = brand_info
            
            final_brands = sorted(unique_brands.values(), key=lambda x: x['confidence'], reverse=True)
            
            return {
                'detected_brands': final_brands,
                'all_text': list(set(all_text)),  # Remove duplicates
                'confidence_scores': confidence_scores
            }
            
        except Exception as e:
            logger.error(f"Brand detection failed: {str(e)}")
            return {
                'detected_brands': [],
                'all_text': [],
                'confidence_scores': {}
            }
    
    def _rgb_to_color_name(self, rgb: tuple) -> str:
        """Convert RGB values to standard color name."""
        r, g, b = rgb
        
        # Simple color classification based on RGB values
        # This is a basic implementation - could be enhanced with more sophisticated color matching
        
        # Calculate color properties
        total = r + g + b
        if total < 50:  # Very dark
            return 'black'
        elif total > 650:  # Very light
            return 'white'
        elif abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30:  # Grayscale
            if total < 300:
                return 'gray'
            else:
                return 'light gray'
        
        # Color detection
        max_val = max(r, g, b)
        if max_val == r and r > g + 50 and r > b + 50:
            if g > 100:  # Has some green
                return 'orange' if g > b else 'pink'
            elif b > 100:  # Has some blue
                return 'purple'
            else:
                return 'red'
        elif max_val == g and g > r + 50 and g > b + 50:
            if r > 100:  # Has some red
                return 'yellow' if r > b else 'lime'
            else:
                return 'green'
        elif max_val == b and b > r + 50 and b > g + 50:
            if r > 100:  # Has some red
                return 'purple'
            elif g > 100:  # Has some green
                return 'teal'
            else:
                return 'blue'
        
        # Mixed colors
        if r > 150 and g > 150 and b < 100:
            return 'yellow'
        elif r > 150 and b > 150 and g < 100:
            return 'magenta'
        elif g > 150 and b > 150 and r < 100:
            return 'cyan'
        elif r > 100 and g > 50 and b < 50:
            return 'orange' if g < 100 else 'yellow'
        elif r > 50 and g > 100 and b < 50:
            return 'lime'
        elif r < 50 and g > 100 and b > 50:
            return 'teal'
        elif r < 100 and g < 100 and b > 150:
            return 'navy' if total < 400 else 'blue'
        elif r > 100 and g < 100 and b < 100:
            return 'maroon' if total < 300 else 'red'
        elif r > 100 and g > 70 and b > 70 and total < 400:
            return 'brown'
        
        # Default fallback
        return 'unknown'
    
    def _text_matches_brand(self, text: str, brand: str) -> bool:
        """Check if detected text matches a known brand."""
        # Exact match
        if text == brand.lower():
            return True
        
        # Partial match for multi-word brands
        if ' ' in brand:
            brand_words = brand.lower().split()
            if any(word in text for word in brand_words if len(word) > 2):
                return True
        
        # Handle common variations
        brand_variations = {
            'levis': ['levi\'s', 'levi', 'levis'],
            'h&m': ['h&m', 'hm', 'h and m'],
            'tommy hilfiger': ['tommy', 'hilfiger'],
            'calvin klein': ['calvin', 'klein', 'ck'],
            'polo ralph lauren': ['polo', 'ralph lauren', 'ralph', 'lauren'],
            'under armour': ['under armour', 'underarmour', 'ua'],
            'north face': ['north face', 'northface', 'tnf'],
            'dr. martens': ['dr martens', 'doc martens', 'martens']
        }
        
        for main_brand, variations in brand_variations.items():
            if brand.lower() == main_brand:
                return any(var in text for var in variations)
        
        return False
    
    def _calculate_text_confidence(self, text_annotation) -> float:
        """Calculate confidence score for detected text."""
        # This is a simplified confidence calculation
        # In a real implementation, you might use the bounding box size,
        # text clarity, or other factors
        base_confidence = 0.8
        
        # Longer text generally more reliable
        length_bonus = min(len(text_annotation.description) * 0.05, 0.2)
        
        return min(base_confidence + length_bonus, 1.0)


# Global service instance
gcp_color_brand_service = None

def get_gcp_color_brand_service() -> Optional[GCPColorBrandService]:
    """Get the global GCP Color & Brand service instance."""
    global gcp_color_brand_service
    
    if gcp_color_brand_service is None:
        try:
            gcp_color_brand_service = GCPColorBrandService()
            logger.info("GCP Color & Brand service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GCP Color & Brand service: {str(e)}")
            gcp_color_brand_service = None
    
    return gcp_color_brand_service
