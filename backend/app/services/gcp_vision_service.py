"""
Google Cloud Vision API service for automatic feature extraction from clothing images
"""
from typing import List, Dict, Optional, Tuple

try:
    from google.cloud import vision
    HAS_GCP_VISION = True
except ImportError:
    HAS_GCP_VISION = False
    vision = None

import io

from app.core.config import settings


class GCPVisionService:
    """Service for analyzing clothing images using Google Cloud Vision API"""
    
    def __init__(self):
        if not HAS_GCP_VISION:
            raise ImportError("Google Cloud Vision API is not available")
        self.client = vision.ImageAnnotatorClient()
        
        # Feature mapping for clothing analysis
        self.color_mappings = {
            'red': ['red', 'crimson', 'scarlet', 'burgundy', 'maroon'],
            'blue': ['blue', 'navy', 'azure', 'cobalt', 'indigo'],
            'green': ['green', 'olive', 'emerald', 'forest', 'lime'],
            'yellow': ['yellow', 'gold', 'amber', 'lemon', 'mustard'],
            'orange': ['orange', 'coral', 'peach', 'tangerine'],
            'purple': ['purple', 'violet', 'lavender', 'plum', 'magenta'],
            'pink': ['pink', 'rose', 'fuchsia', 'salmon'],
            'brown': ['brown', 'tan', 'beige', 'khaki', 'chocolate'],
            'black': ['black', 'charcoal', 'ebony'],
            'white': ['white', 'ivory', 'cream', 'pearl'],
            'gray': ['gray', 'grey', 'silver', 'slate']
        }
        
        self.pattern_keywords = {
            'striped': ['stripe', 'striped', 'stripes'],
            'polka-dot': ['polka', 'dot', 'dotted', 'spots'],
            'floral': ['floral', 'flower', 'flowers', 'botanical'],
            'geometric': ['geometric', 'triangle', 'square', 'diamond'],
            'plaid': ['plaid', 'checkered', 'tartan', 'gingham'],
            'solid': ['solid', 'plain', 'uniform']
        }
        
        self.texture_keywords = {
            'smooth': ['smooth', 'silk', 'satin', 'glossy'],
            'rough': ['rough', 'textured', 'coarse'],
            'knit': ['knit', 'knitted', 'sweater', 'jersey'],
            'woven': ['woven', 'cotton', 'linen', 'canvas'],
            'leather': ['leather', 'suede', 'hide'],
            'denim': ['denim', 'jeans', 'chambray']
        }
    
    def analyze_clothing_image(self, image_data: bytes) -> Dict[str, any]:
        """
        Analyze a clothing image and extract features
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dict containing extracted features and confidence scores
        """
        try:
            # Create Vision API image object
            image = vision.Image(content=image_data)
            
            # Perform multiple types of analysis
            results = {}
            
            # 1. Label Detection (general object/clothing detection)
            labels_response = self.client.label_detection(image=image)
            results['labels'] = self._process_labels(labels_response.label_annotations)
            
            # 2. Object Localization (specific clothing items)
            objects_response = self.client.object_localization(image=image)
            results['objects'] = self._process_objects(objects_response.localized_object_annotations)
            
            # 3. Image Properties (dominant colors)
            properties_response = self.client.image_properties(image=image)
            results['colors'] = self._process_colors(properties_response.image_properties_annotation)
            
            # 4. Text Detection (brand names, labels)
            text_response = self.client.text_detection(image=image)
            results['text'] = self._process_text(text_response.text_annotations)
            
            # 5. Extract clothing features
            features = self._extract_clothing_features(results)
            
            return {
                'raw_analysis': results,
                'extracted_features': features['features'],
                'confidence_scores': features['confidence_scores'],
                'suggested_category': features['suggested_category'],
                'dominant_colors': results['colors']['dominant'],
                'detected_text': results['text']
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'extracted_features': [],
                'confidence_scores': {},
                'suggested_category': 'unknown'
            }
    
    def _process_labels(self, label_annotations) -> Dict[str, any]:
        """Process label detection results"""
        labels = []
        for label in label_annotations:
            labels.append({
                'description': label.description.lower(),
                'score': label.score,
                'topicality': label.topicality
            })
        
        return {
            'all_labels': labels,
            'high_confidence': [l for l in labels if l['score'] > 0.7],
            'clothing_related': [l for l in labels if self._is_clothing_related(l['description'])]
        }
    
    def _process_objects(self, object_annotations) -> Dict[str, any]:
        """Process object localization results"""
        objects = []
        for obj in object_annotations:
            objects.append({
                'name': obj.name.lower(),
                'score': obj.score,
                'bounding_box': {
                    'vertices': [(vertex.x, vertex.y) for vertex in obj.bounding_poly.normalized_vertices]
                }
            })
        
        return {
            'all_objects': objects,
            'clothing_objects': [o for o in objects if self._is_clothing_related(o['name'])]
        }
    
    def _process_colors(self, image_properties) -> Dict[str, any]:
        """Process dominant color analysis"""
        colors = []
        
        if image_properties.dominant_colors:
            for color_info in image_properties.dominant_colors.colors:
                rgb = color_info.color
                color_name = self._rgb_to_color_name(rgb.red, rgb.green, rgb.blue)
                
                colors.append({
                    'rgb': (rgb.red, rgb.green, rgb.blue),
                    'color_name': color_name,
                    'score': color_info.score,
                    'pixel_fraction': color_info.pixel_fraction
                })
        
        return {
            'all_colors': colors,
            'dominant': colors[:3] if colors else [],  # Top 3 colors
            'primary_color': colors[0]['color_name'] if colors else 'unknown'
        }
    
    def _process_text(self, text_annotations) -> List[str]:
        """Process text detection results"""
        detected_text = []
        
        for text in text_annotations:
            if len(text.description) > 1:  # Filter out single characters
                detected_text.append(text.description.strip())
        
        return detected_text[:5]  # Return top 5 text detections
    
    def _extract_clothing_features(self, analysis_results) -> Dict[str, any]:
        """Extract clothing-specific features from analysis results"""
        features = []
        confidence_scores = {}
        suggested_category = 'unknown'
        
        # Extract features from labels
        for label in analysis_results['labels']['clothing_related']:
            feature = label['description']
            features.append(feature)
            confidence_scores[feature] = label['score']
        
        # Extract color features
        for color_info in analysis_results['colors']['dominant']:
            color_feature = color_info['color_name']
            if color_feature != 'unknown':
                features.append(color_feature)
                confidence_scores[color_feature] = color_info['score']
        
        # Extract pattern features from labels
        for label in analysis_results['labels']['all_labels']:
            for pattern, keywords in self.pattern_keywords.items():
                if any(keyword in label['description'] for keyword in keywords):
                    features.append(pattern)
                    confidence_scores[pattern] = label['score']
        
        # Extract texture features from labels
        for label in analysis_results['labels']['all_labels']:
            for texture, keywords in self.texture_keywords.items():
                if any(keyword in label['description'] for keyword in keywords):
                    features.append(texture)
                    confidence_scores[texture] = label['score']
        
        # Suggest category based on detected objects and labels
        suggested_category = self._suggest_category(analysis_results)
        
        # Remove duplicates while preserving order
        features = list(dict.fromkeys(features))
        
        return {
            'features': features,
            'confidence_scores': confidence_scores,
            'suggested_category': suggested_category
        }
    
    def _is_clothing_related(self, description: str) -> bool:
        """Check if a description is clothing-related"""
        clothing_keywords = [
            'clothing', 'shirt', 'pants', 'dress', 'skirt', 'jacket', 'coat',
            'sweater', 'hoodie', 'jeans', 'shorts', 'blouse', 'top', 'bottom',
            'shoes', 'sneakers', 'boots', 'sandals', 'heels', 'flats',
            'hat', 'cap', 'scarf', 'belt', 'bag', 'purse', 'accessory',
            'sleeve', 'collar', 'button', 'zipper', 'pocket', 'fabric',
            'cotton', 'silk', 'wool', 'leather', 'denim', 'polyester'
        ]
        
        return any(keyword in description.lower() for keyword in clothing_keywords)
    
    def _rgb_to_color_name(self, r: int, g: int, b: int) -> str:
        """Convert RGB values to color name"""
        # Simple color name mapping based on RGB values
        if r > 200 and g > 200 and b > 200:
            return 'white'
        elif r < 50 and g < 50 and b < 50:
            return 'black'
        elif r < 100 and g < 100 and b < 100:
            return 'gray'
        elif r > g and r > b:
            if g > 100:
                return 'orange' if g > b else 'red'
            else:
                return 'red'
        elif g > r and g > b:
            return 'green'
        elif b > r and b > g:
            if r > 100:
                return 'purple'
            else:
                return 'blue'
        elif r > 150 and g > 150 and b < 100:
            return 'yellow'
        elif r > 150 and g < 100 and b > 150:
            return 'purple'
        elif r < 100 and g > 150 and b > 150:
            return 'cyan'
        else:
            return 'unknown'
    
    def _suggest_category(self, analysis_results) -> str:
        """Suggest clothing category based on analysis"""
        # Category mapping based on detected objects and labels
        category_keywords = {
            'top': ['shirt', 'blouse', 'sweater', 'hoodie', 'jacket', 'coat', 'top', 'tshirt', 't-shirt'],
            'bottom': ['pants', 'jeans', 'shorts', 'skirt', 'trousers', 'leggings', 'bottom'],
            'shoes': ['shoes', 'sneakers', 'boots', 'sandals', 'heels', 'flats', 'footwear'],
            'accessory': ['hat', 'cap', 'scarf', 'belt', 'bag', 'purse', 'jewelry', 'watch'],
            'layering': ['jacket', 'coat', 'cardigan', 'blazer', 'vest', 'outerwear']
        }
        
        # Check objects first
        for obj in analysis_results['objects']['all_objects']:
            for category, keywords in category_keywords.items():
                if any(keyword in obj['name'] for keyword in keywords):
                    return category
        
        # Check labels
        for label in analysis_results['labels']['all_labels']:
            for category, keywords in category_keywords.items():
                if any(keyword in label['description'] for keyword in keywords):
                    return category
        
        return 'unknown'
    
    def batch_analyze_images(self, image_data_list: List[bytes]) -> List[Dict[str, any]]:
        """
        Analyze multiple images in batch for better efficiency
        """
        results = []
        
        for image_data in image_data_list:
            result = self.analyze_clothing_image(image_data)
            results.append(result)
        
        return results
    
    def get_feature_suggestions(self, image_url: str) -> Dict[str, any]:
        """
        Get feature suggestions for an image URL (for existing images)
        """
        try:
            # Download image from URL
            import requests
            response = requests.get(image_url)
            image_data = response.content
            
            return self.analyze_clothing_image(image_data)
            
        except Exception as e:
            return {
                'error': f"Failed to analyze image from URL: {str(e)}",
                'extracted_features': [],
                'confidence_scores': {},
                'suggested_category': 'unknown'
            }