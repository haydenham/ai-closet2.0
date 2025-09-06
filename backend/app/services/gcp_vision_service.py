"""
Google Cloud Vision API service for automatic feature extraction from clothing images
"""
from typing import List, Dict, Optional, Tuple
import colorsys
import io
import base64

try:
    from google.cloud import vision
    HAS_GCP_VISION = True
except ImportError:
    HAS_GCP_VISION = False
    vision = None

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    import numpy as np
    from scipy.ndimage import gaussian_filter, label
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from app.core.config import settings


class GCPVisionService:
    """Service for analyzing clothing images using Google Cloud Vision API"""
    
    def __init__(self):
        if not HAS_GCP_VISION:
            raise ImportError("Google Cloud Vision API is not available")
        if not HAS_PIL:
            raise ImportError("PIL/Pillow is required for image normalization")
        self.client = vision.ImageAnnotatorClient()
        
        # Feature mapping for clothing analysis
        # Enhanced color mapping for fashion classification
        self.color_mappings = {
            'red': ['red', 'crimson', 'scarlet', 'burgundy', 'maroon', 'cherry', 'ruby'],
            'pink': ['pink', 'rose', 'fuchsia', 'salmon', 'coral', 'blush', 'magenta'],
            'orange': ['orange', 'peach', 'tangerine', 'rust', 'burnt-orange', 'apricot'],
            'yellow': ['yellow', 'gold', 'amber', 'lemon', 'mustard', 'canary', 'cream'],
            'green': ['green', 'olive', 'emerald', 'forest-green', 'lime', 'sage', 'mint'],
            'blue': ['blue', 'navy', 'azure', 'cobalt', 'indigo', 'slate-blue', 'powder-blue'],
            'purple': ['purple', 'violet', 'lavender', 'plum', 'magenta', 'eggplant', 'amethyst'],
            'brown': ['brown', 'tan', 'beige', 'khaki', 'chocolate', 'coffee', 'camel', 'taupe'],
            'black': ['black', 'charcoal', 'ebony', 'onyx', 'jet-black'],
            'white': ['white', 'ivory', 'cream', 'pearl', 'off-white', 'eggshell'],
            'gray': ['gray', 'grey', 'silver', 'slate', 'light-gray', 'dark-gray', 'charcoal']
        }
        
        # Enhanced pattern detection with comprehensive keywords and style analysis
        self.pattern_keywords = {
            'striped': ['stripe', 'striped', 'stripes', 'horizontal stripe', 'vertical stripe', 'pinstripe'],
            'polka-dot': ['polka', 'dot', 'dotted', 'spots', 'spotted', 'circles', 'polka dot'],
            'floral': ['floral', 'flower', 'flowers', 'botanical', 'roses', 'petals', 'bloom', 'garden'],
            'geometric': ['geometric', 'triangle', 'square', 'diamond', 'hexagon', 'pattern', 'angular'],
            'plaid': ['plaid', 'checkered', 'tartan', 'gingham', 'checked', 'checker', 'scottish'],
            'solid': ['solid', 'plain', 'uniform', 'single color', 'monochrome'],
            'abstract': ['abstract', 'artistic', 'modern', 'contemporary', 'graphic'],
            'paisley': ['paisley', 'teardrop', 'ornate', 'traditional'],
            'animal-print': ['leopard', 'zebra', 'snake', 'animal print', 'wild', 'safari'],
            'houndstooth': ['houndstooth', 'dogtooth', 'check'],
            'chevron': ['chevron', 'zigzag', 'herringbone', 'v-shape'],
            'tie-dye': ['tie dye', 'tie-dye', 'psychedelic', 'swirl', 'gradient']
        }
        
        # Enhanced texture detection with fabric and surface analysis
        self.texture_keywords = {
            'smooth': ['smooth', 'silk', 'satin', 'glossy', 'sleek', 'polished', 'shiny'],
            'rough': ['rough', 'textured', 'coarse', 'bumpy', 'grainy', 'rustic'],
            'knit': ['knit', 'knitted', 'sweater', 'jersey', 'ribbed', 'cable knit', 'chunky knit'],
            'woven': ['woven', 'cotton', 'linen', 'canvas', 'twill', 'oxford', 'chambray'],
            'leather': ['leather', 'suede', 'hide', 'faux leather', 'vegan leather', 'patent leather'],
            'denim': ['denim', 'jeans', 'chambray', 'jean', 'distressed', 'raw denim'],
            'velvet': ['velvet', 'velour', 'plush', 'soft', 'luxurious'],
            'corduroy': ['corduroy', 'cord', 'ribbed fabric', 'wales'],
            'lace': ['lace', 'delicate', 'sheer', 'transparent', 'feminine'],
            'mesh': ['mesh', 'net', 'perforated', 'breathable', 'sports mesh'],
            'sequined': ['sequin', 'sequined', 'sparkly', 'glittery', 'embellished'],
            'embroidered': ['embroidered', 'embroidery', 'stitched', 'detailed'],
            'quilted': ['quilted', 'padded', 'puffy', 'diamond quilted'],
            'fleece': ['fleece', 'fuzzy', 'warm', 'polar fleece'],
            'wool': ['wool', 'woolen', 'merino', 'cashmere', 'alpaca']
        }
        
        # Style and occasion mapping for outfit recommendations
        self.style_keywords = {
            'casual': ['casual', 'relaxed', 'everyday', 'comfortable', 'laid-back'],
            'formal': ['formal', 'dress', 'elegant', 'sophisticated', 'professional'],
            'business': ['business', 'office', 'work', 'professional', 'corporate'],
            'sporty': ['sport', 'athletic', 'gym', 'workout', 'active', 'performance'],
            'bohemian': ['boho', 'bohemian', 'free-spirited', 'artistic', 'flowing'],
            'vintage': ['vintage', 'retro', 'classic', 'timeless', 'antique'],
            'edgy': ['edgy', 'punk', 'rock', 'rebellious', 'alternative'],
            'romantic': ['romantic', 'feminine', 'delicate', 'soft', 'pretty'],
            'minimalist': ['minimal', 'simple', 'clean', 'modern', 'sleek'],
            'streetwear': ['street', 'urban', 'hip hop', 'trendy', 'cool']
        }
        
        # Garment specific features for better classification
        self.garment_features = {
            'necklines': ['crew neck', 'v-neck', 'scoop neck', 'off-shoulder', 'halter', 'turtleneck'],
            'sleeves': ['long sleeve', 'short sleeve', 'sleeveless', 'cap sleeve', 'bell sleeve'],
            'fits': ['slim fit', 'loose fit', 'regular fit', 'oversized', 'fitted', 'relaxed'],
            'lengths': ['mini', 'midi', 'maxi', 'knee-length', 'ankle-length', 'cropped'],
            'closures': ['button-up', 'zipper', 'pullover', 'wrap', 'tie'],
            'details': ['pockets', 'hood', 'collar', 'cuffs', 'belt', 'pleats', 'ruffles']
        }
    
    def normalize_image(self, image_data: bytes, enhance_clothing_focus: bool = True) -> bytes:
        """
        Normalize image before analysis to improve feature extraction accuracy
        
        Args:
            image_data: Raw image bytes
            enhance_clothing_focus: Whether to apply clothing-specific enhancements
            
        Returns:
            Normalized image bytes
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply normalization pipeline
            normalized_image = self._apply_normalization_pipeline(image, enhance_clothing_focus)
            
            # Convert back to bytes
            output_buffer = io.BytesIO()
            normalized_image.save(output_buffer, format='JPEG', quality=95)
            return output_buffer.getvalue()
            
        except Exception as e:
            # If normalization fails, return original image
            return image_data
    
    def _apply_normalization_pipeline(self, image: Image.Image, enhance_clothing_focus: bool) -> Image.Image:
        """Apply comprehensive normalization pipeline"""
        
        # 1. Resize for consistent processing (maintain aspect ratio)
        normalized_image = self._resize_image(image)
        
        # 2. Color normalization
        normalized_image = self._normalize_colors(normalized_image)
        
        # 3. Contrast and brightness enhancement
        normalized_image = self._enhance_contrast_brightness(normalized_image)
        
        # 4. Background suppression (if clothing focus enabled)
        if enhance_clothing_focus:
            normalized_image = self._suppress_background(normalized_image)
        
        # 5. Noise reduction
        normalized_image = self._reduce_noise(normalized_image)
        
        return normalized_image
    
    def _resize_image(self, image: Image.Image, max_dimension: int = 1024) -> Image.Image:
        """Resize image maintaining aspect ratio"""
        width, height = image.size
        
        # Only resize if image is larger than max_dimension
        if max(width, height) > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int((height * max_dimension) / width)
            else:
                new_height = max_dimension
                new_width = int((width * max_dimension) / height)
            
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
    
    def _normalize_colors(self, image: Image.Image) -> Image.Image:
        """Normalize color distribution and white balance"""
        # Convert to numpy array for processing
        img_array = np.array(image)
        
        # Auto white balance using gray world assumption
        img_array = self._auto_white_balance(img_array)
        
        # Normalize color channels
        img_array = self._normalize_color_channels(img_array)
        
        # Convert back to PIL Image
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        return Image.fromarray(img_array)
    
    def _auto_white_balance(self, img_array: np.ndarray) -> np.ndarray:
        """Apply automatic white balance correction"""
        # Calculate mean values for each channel
        mean_r = np.mean(img_array[:, :, 0])
        mean_g = np.mean(img_array[:, :, 1])
        mean_b = np.mean(img_array[:, :, 2])
        
        # Calculate gray reference (average of all channels)
        gray_ref = (mean_r + mean_g + mean_b) / 3
        
        # Calculate scaling factors
        scale_r = gray_ref / mean_r if mean_r > 0 else 1.0
        scale_g = gray_ref / mean_g if mean_g > 0 else 1.0
        scale_b = gray_ref / mean_b if mean_b > 0 else 1.0
        
        # Apply scaling with limits to prevent over-correction
        scale_r = np.clip(scale_r, 0.7, 1.5)
        scale_g = np.clip(scale_g, 0.7, 1.5)
        scale_b = np.clip(scale_b, 0.7, 1.5)
        
        # Apply corrections
        img_array[:, :, 0] = img_array[:, :, 0] * scale_r
        img_array[:, :, 1] = img_array[:, :, 1] * scale_g
        img_array[:, :, 2] = img_array[:, :, 2] * scale_b
        
        return img_array
    
    def _normalize_color_channels(self, img_array: np.ndarray) -> np.ndarray:
        """Normalize individual color channels"""
        for channel in range(3):
            channel_data = img_array[:, :, channel]
            
            # Calculate percentiles for robust normalization
            p2, p98 = np.percentile(channel_data, (2, 98))
            
            # Normalize to full range while preserving relative values
            if p98 > p2:
                normalized_channel = ((channel_data - p2) / (p98 - p2)) * 255
                img_array[:, :, channel] = np.clip(normalized_channel, 0, 255)
        
        return img_array
    
    def _enhance_contrast_brightness(self, image: Image.Image) -> Image.Image:
        """Enhance contrast and brightness for better feature detection"""
        # Auto-adjust contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)  # Slight contrast boost
        
        # Auto-adjust brightness based on image statistics
        img_array = np.array(image)
        mean_brightness = np.mean(img_array)
        
        # Target brightness around 128 (middle gray)
        if mean_brightness < 100:  # Too dark
            brightness_factor = 1.2
        elif mean_brightness > 180:  # Too bright
            brightness_factor = 0.9
        else:
            brightness_factor = 1.0
        
        if brightness_factor != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness_factor)
        
        return image
    
    def _suppress_background(self, image: Image.Image) -> Image.Image:
        """Suppress background colors to focus on clothing items"""
        # Convert to numpy array
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Use multiple strategies to identify background
        background_mask = self._create_comprehensive_background_mask(img_array)
        
        # Apply background suppression
        img_array = self._apply_background_suppression(img_array, background_mask)
        
        return Image.fromarray(img_array.astype(np.uint8))
    
    def _create_comprehensive_background_mask(self, img_array: np.ndarray) -> np.ndarray:
        """Create comprehensive background mask using multiple methods"""
        height, width = img_array.shape[:2]
        
        # Method 1: Edge-based background detection
        edge_mask = self._edge_based_background_mask(img_array)
        
        # Method 2: Center-focused mask (assume clothing is in center)
        center_mask = self._center_focused_mask(height, width)
        
        # Method 3: Color uniformity mask (large uniform areas likely background)
        uniformity_mask = self._color_uniformity_mask(img_array)
        
        # Combine masks with weights
        combined_mask = (edge_mask * 0.4 + center_mask * 0.3 + uniformity_mask * 0.3) > 0.5
        
        return combined_mask
    
    def _edge_based_background_mask(self, img_array: np.ndarray) -> np.ndarray:
        """Identify background based on edge pixels"""
        height, width = img_array.shape[:2]
        
        # Sample edge pixels
        edge_pixels = []
        
        # Sample more comprehensively from edges
        border_width = min(50, width // 10)  # Adaptive border width
        
        # Top and bottom edges
        edge_pixels.extend(img_array[:border_width, :].reshape(-1, 3))
        edge_pixels.extend(img_array[-border_width:, :].reshape(-1, 3))
        
        # Left and right edges  
        edge_pixels.extend(img_array[:, :border_width].reshape(-1, 3))
        edge_pixels.extend(img_array[:, -border_width:].reshape(-1, 3))
        
        if len(edge_pixels) == 0:
            return np.zeros((height, width), dtype=bool)
        
        edge_pixels = np.array(edge_pixels)
        
        # Find multiple background colors using clustering-like approach
        background_colors = self._find_background_colors(edge_pixels)
        
        # Create mask for all background colors
        background_mask = np.zeros((height, width), dtype=bool)
        
        for bg_color in background_colors:
            color_mask = self._create_background_mask(img_array, bg_color, threshold=40)
            background_mask = background_mask | color_mask
        
        return background_mask.astype(float)
    
    def _find_background_colors(self, edge_pixels: np.ndarray, max_colors: int = 3) -> List[np.ndarray]:
        """Find dominant background colors from edge pixels"""
        # Simple clustering approach
        unique_colors, counts = np.unique(edge_pixels, axis=0, return_counts=True)
        
        # Get top colors by frequency
        sorted_indices = np.argsort(counts)[::-1]
        top_colors = unique_colors[sorted_indices[:max_colors]]
        
        return [color for color in top_colors]
    
    def _center_focused_mask(self, height: int, width: int) -> np.ndarray:
        """Create mask that prioritizes center region (where clothing typically is)"""
        # Create distance from center
        center_y, center_x = height // 2, width // 2
        
        y_coords, x_coords = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
        
        # Calculate distance from center
        distance_from_center = np.sqrt((y_coords - center_y)**2 + (x_coords - center_x)**2)
        
        # Normalize distance
        max_distance = np.sqrt(center_y**2 + center_x**2)
        normalized_distance = distance_from_center / max_distance
        
        # Create mask where edges (far from center) are considered background
        # Higher values = more likely to be background
        center_mask = normalized_distance
        
        return center_mask
    
    def _color_uniformity_mask(self, img_array: np.ndarray) -> np.ndarray:
        """Identify uniform color regions (likely background)"""
        height, width = img_array.shape[:2]
        
        # Calculate local color variance
        kernel_size = min(20, min(height, width) // 10)
        uniformity_mask = np.zeros((height, width), dtype=float)
        
        for i in range(0, height, kernel_size):
            for j in range(0, width, kernel_size):
                # Get local patch
                end_i = min(i + kernel_size, height)
                end_j = min(j + kernel_size, width)
                patch = img_array[i:end_i, j:end_j]
                
                # Calculate color variance in patch
                patch_variance = np.var(patch.reshape(-1, 3), axis=0).mean()
                
                # Low variance = uniform color = likely background
                uniformity_score = 1.0 / (1.0 + patch_variance / 100.0)  # Higher = more uniform
                
                uniformity_mask[i:end_i, j:end_j] = uniformity_score
        
        return uniformity_mask
    
    def _apply_background_suppression(self, img_array: np.ndarray, background_mask: np.ndarray) -> np.ndarray:
        """Apply sophisticated background suppression"""
        height, width = img_array.shape[:2]
        result_array = img_array.copy().astype(float)
        
        # Convert to HSV for better color manipulation
        for i in range(height):
            for j in range(width):
                if background_mask[i, j] > 0.5:  # This pixel is likely background
                    r, g, b = result_array[i, j] / 255.0
                    h, s, v = colorsys.rgb_to_hsv(r, g, b)
                    
                    # Reduce saturation and adjust value for background pixels
                    suppression_factor = background_mask[i, j]
                    s *= (1.0 - suppression_factor * 0.7)  # Reduce saturation more
                    v = v * 0.9 + 0.1  # Slightly brighten to make less prominent
                    
                    # Convert back to RGB
                    r, g, b = colorsys.hsv_to_rgb(h, s, v)
                    result_array[i, j] = [r * 255, g * 255, b * 255]
        
        return result_array
    
    def _estimate_background_color(self, edge_pixels: np.ndarray) -> Optional[np.ndarray]:
        """Estimate background color from edge pixels"""
        if len(edge_pixels) == 0:
            return None
        
        # Use median color as background estimate (robust to outliers)
        background_color = np.median(edge_pixels, axis=0)
        return background_color
    
    def _create_background_mask(self, img_array: np.ndarray, background_color: np.ndarray, threshold: float = 30) -> np.ndarray:
        """Create mask identifying background pixels"""
        # Calculate color distance from background
        color_diff = np.sqrt(np.sum((img_array - background_color) ** 2, axis=2))
        
        # Create mask where pixels are similar to background
        background_mask = color_diff < threshold
        
        return background_mask
    
    def _desaturate_background(self, img_array: np.ndarray, background_mask: np.ndarray) -> np.ndarray:
        """Reduce saturation of background pixels"""
        # Convert to HSV for saturation adjustment
        height, width = img_array.shape[:2]
        hsv_array = np.zeros_like(img_array, dtype=np.float32)
        
        for i in range(height):
            for j in range(width):
                r, g, b = img_array[i, j] / 255.0
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                
                # Reduce saturation for background pixels
                if background_mask[i, j]:
                    s *= 0.3  # Significantly reduce saturation
                
                # Convert back to RGB
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                hsv_array[i, j] = [r * 255, g * 255, b * 255]
        
        return hsv_array
    
    def _reduce_noise(self, image: Image.Image) -> Image.Image:
        """Apply noise reduction while preserving important details"""
        # Apply gentle bilateral-like filtering using PIL
        # Use a slight blur followed by sharpening to reduce noise while preserving edges
        
        # Slight gaussian blur to reduce noise
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Sharpen to restore edge definition
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)
        
        return image
    
    def analyze_clothing_image(self, image_data: bytes, normalize_image: bool = True) -> Dict[str, any]:
        """
        Analyze a clothing image and extract comprehensive features including advanced pattern and texture detection
        
        Args:
            image_data: Raw image bytes
            normalize_image: Whether to apply image normalization preprocessing
            
        Returns:
            Dict containing extracted features and confidence scores
        """
        try:
            # Apply image normalization if enabled
            processed_image_data = image_data
            if normalize_image:
                processed_image_data = self.normalize_image(image_data, enhance_clothing_focus=True)
            
            # Create Vision API image object
            image = vision.Image(content=processed_image_data)
            
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
            
            # 5. Advanced Pattern Detection using image analysis
            results['patterns'] = self._analyze_patterns(processed_image_data)
            
            # 6. Advanced Texture Analysis
            results['textures'] = self._analyze_textures(processed_image_data, results['labels'])
            
            # 7. Style and Garment Feature Detection
            results['style_features'] = self._analyze_style_features(results['labels'], results['objects'])
            
            # 8. Extract comprehensive clothing features
            features = self._extract_comprehensive_features(results)
            
            return {
                'raw_analysis': results,
                'extracted_features': features['features'],
                'confidence_scores': features['confidence_scores'],
                'suggested_category': features['suggested_category'],
                'dominant_colors': results['colors']['dominant'],
                'detected_text': results['text'],
                'pattern_analysis': results['patterns'],
                'texture_analysis': results['textures'],
                'style_analysis': results['style_features']
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
        """Process dominant color analysis with enhanced accuracy"""
        colors = []
        
        if image_properties.dominant_colors:
            for color_info in image_properties.dominant_colors.colors:
                rgb = color_info.color
                color_name = self._rgb_to_color_name(rgb.red, rgb.green, rgb.blue)
                
                # Calculate color confidence based on pixel coverage and saturation
                confidence = self._calculate_color_confidence(
                    rgb.red, rgb.green, rgb.blue, 
                    color_info.pixel_fraction, 
                    color_info.score
                )
                
                colors.append({
                    'rgb': (rgb.red, rgb.green, rgb.blue),
                    'color_name': color_name,
                    'score': color_info.score,
                    'pixel_fraction': color_info.pixel_fraction,
                    'confidence': confidence
                })
        
        # Sort by confidence and pixel coverage
        colors.sort(key=lambda x: (x['confidence'], x['pixel_fraction']), reverse=True)
        
        # Filter out low-confidence colors
        high_confidence_colors = [c for c in colors if c['confidence'] > 0.6]
        
        return {
            'all_colors': colors,
            'dominant': high_confidence_colors[:3] if high_confidence_colors else colors[:3],
            'primary_color': high_confidence_colors[0]['color_name'] if high_confidence_colors else (colors[0]['color_name'] if colors else 'unknown'),
            'color_diversity': len(set(c['color_name'] for c in high_confidence_colors[:5]))
        }
    
    def _calculate_color_confidence(self, r: int, g: int, b: int, pixel_fraction: float, score: float) -> float:
        """Calculate confidence score for color detection"""
        # Normalize RGB
        r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
        
        # Calculate saturation (higher saturation = more confident color identification)
        max_val = max(r_norm, g_norm, b_norm)
        min_val = min(r_norm, g_norm, b_norm)
        saturation = (max_val - min_val) / max_val if max_val > 0 else 0
        
        # Calculate brightness
        brightness = (r_norm + g_norm + b_norm) / 3
        
        # Base confidence from Vision API score
        confidence = score
        
        # Boost confidence for well-saturated colors (easier to identify)
        if saturation > 0.3:
            confidence *= 1.2
        elif saturation < 0.1:  # Very low saturation (grayscale)
            confidence *= 0.8
        
        # Boost confidence for colors with significant pixel coverage
        if pixel_fraction > 0.3:
            confidence *= 1.1
        elif pixel_fraction < 0.05:
            confidence *= 0.7
        
        # Reduce confidence for very dark or very bright colors (harder to distinguish)
        if brightness < 0.1 or brightness > 0.95:
            confidence *= 0.9
        
        return min(confidence, 1.0)  # Cap at 1.0
        
        return {
            'all_colors': colors,
            'dominant': colors[:3] if colors else [],  # Top 3 colors
            'primary_color': colors[0]['color_name'] if colors else 'unknown'
        }
    
    def _analyze_patterns(self, image_data: bytes) -> Dict[str, any]:
        """
        Advanced pattern detection using image analysis techniques
        """
        try:
            # Convert to PIL Image for analysis
            image = Image.open(io.BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Resize for consistent analysis
            analysis_size = (256, 256)
            analysis_image = image.resize(analysis_size)
            analysis_array = np.array(analysis_image)
            
            patterns_detected = {}
            
            # 1. Detect stripes using frequency analysis
            stripe_confidence = self._detect_stripes(analysis_array)
            if stripe_confidence > 0.3:
                patterns_detected['striped'] = stripe_confidence
            
            # 2. Detect polka dots using circular pattern detection
            polka_confidence = self._detect_polka_dots(analysis_array)
            if polka_confidence > 0.3:
                patterns_detected['polka-dot'] = polka_confidence
            
            # 3. Detect geometric patterns using edge analysis
            geometric_confidence = self._detect_geometric_patterns(analysis_array)
            if geometric_confidence > 0.3:
                patterns_detected['geometric'] = geometric_confidence
            
            # 4. Detect plaid/checkered patterns
            plaid_confidence = self._detect_plaid_patterns(analysis_array)
            if plaid_confidence > 0.3:
                patterns_detected['plaid'] = plaid_confidence
            
            # 5. Detect solid/uniform patterns
            solid_confidence = self._detect_solid_pattern(analysis_array)
            if solid_confidence > 0.7:  # Higher threshold for solid
                patterns_detected['solid'] = solid_confidence
            
            # 6. Detect floral patterns (using texture complexity)
            floral_confidence = self._detect_floral_pattern(analysis_array)
            if floral_confidence > 0.4:
                patterns_detected['floral'] = floral_confidence
            
            return {
                'detected_patterns': patterns_detected,
                'primary_pattern': max(patterns_detected.items(), key=lambda x: x[1])[0] if patterns_detected else 'unknown',
                'pattern_complexity': self._calculate_pattern_complexity(analysis_array),
                'total_patterns': len(patterns_detected)
            }
            
        except Exception as e:
            return {
                'detected_patterns': {},
                'primary_pattern': 'unknown',
                'pattern_complexity': 0.0,
                'total_patterns': 0,
                'error': str(e)
            }
    
    def _detect_stripes(self, img_array: np.ndarray) -> float:
        """Detect stripe patterns using frequency analysis"""
        try:
            # Convert to grayscale for pattern analysis
            gray = np.mean(img_array, axis=2)
            
            # Analyze both horizontal and vertical frequencies
            h_fft = np.fft.fft(np.mean(gray, axis=0))  # Horizontal analysis
            v_fft = np.fft.fft(np.mean(gray, axis=1))  # Vertical analysis
            
            # Find dominant frequencies
            h_freq_strength = np.max(np.abs(h_fft[1:len(h_fft)//4]))  # Ignore DC component
            v_freq_strength = np.max(np.abs(v_fft[1:len(v_fft)//4]))
            
            # Normalize by image dimensions
            h_normalized = h_freq_strength / (gray.shape[1] * 255)
            v_normalized = v_freq_strength / (gray.shape[0] * 255)
            
            # Return higher of horizontal or vertical stripe strength
            stripe_strength = max(h_normalized, v_normalized)
            
            # Convert to confidence score (0-1)
            confidence = min(stripe_strength * 10, 1.0)  # Scale factor based on testing
            
            return confidence
            
        except Exception:
            return 0.0
    
    def _detect_polka_dots(self, img_array: np.ndarray) -> float:
        """Detect polka dot patterns using circular detection"""
        try:
            # Convert to grayscale
            gray = np.mean(img_array, axis=2).astype(np.uint8)
            
            # Apply edge detection
            from scipy.ndimage import gaussian_filter
            
            # Smooth the image first
            smoothed = gaussian_filter(gray, sigma=1.0)
            
            # Simple edge detection using gradient
            grad_x = np.abs(np.gradient(smoothed, axis=1))
            grad_y = np.abs(np.gradient(smoothed, axis=0))
            edges = grad_x + grad_y
            
            # Look for circular patterns by analyzing local variance in small windows
            window_size = 8
            circle_evidence = 0
            total_windows = 0
            
            for i in range(0, gray.shape[0] - window_size, window_size // 2):
                for j in range(0, gray.shape[1] - window_size, window_size // 2):
                    window = gray[i:i+window_size, j:j+window_size]
                    
                    # Calculate center vs edge contrast
                    center = window[window_size//4:3*window_size//4, window_size//4:3*window_size//4]
                    center_mean = np.mean(center)
                    
                    # Check if this could be a dot (high contrast between center and edges)
                    edge_ring = np.concatenate([
                        window[0, :], window[-1, :], window[:, 0], window[:, -1]
                    ])
                    edge_mean = np.mean(edge_ring)
                    
                    contrast = abs(center_mean - edge_mean)
                    if contrast > 30:  # Significant contrast threshold
                        circle_evidence += 1
                    
                    total_windows += 1
            
            if total_windows == 0:
                return 0.0
            
            # Calculate confidence based on proportion of circular evidence
            confidence = circle_evidence / total_windows
            
            # Boost confidence if we found many potential dots
            if circle_evidence > 5:
                confidence *= 1.2
            
            return min(confidence, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_geometric_patterns(self, img_array: np.ndarray) -> float:
        """Detect geometric patterns using edge analysis"""
        try:
            # Convert to grayscale
            gray = np.mean(img_array, axis=2).astype(np.uint8)
            
            # Calculate gradients
            grad_x = np.abs(np.gradient(gray.astype(float), axis=1))
            grad_y = np.abs(np.gradient(gray.astype(float), axis=0))
            
            # Find strong edges
            edge_threshold = np.percentile(grad_x + grad_y, 85)  # Top 15% of gradients
            strong_edges = (grad_x + grad_y) > edge_threshold
            
            # Analyze edge orientation and straightness
            edge_pixels = np.sum(strong_edges)
            total_pixels = gray.shape[0] * gray.shape[1]
            
            if edge_pixels == 0:
                return 0.0
            
            # Look for straight lines (geometric patterns tend to have straight edges)
            # Count horizontal and vertical edge alignments
            h_alignment = np.sum(grad_y > grad_x) / edge_pixels  # More vertical edges
            v_alignment = np.sum(grad_x > grad_y) / edge_pixels  # More horizontal edges
            
            # Geometric patterns have strong directional alignment
            geometric_strength = max(h_alignment, v_alignment)
            
            # Also consider edge density (geometric patterns tend to have regular edge spacing)
            edge_density = edge_pixels / total_pixels
            
            # Combine factors
            confidence = geometric_strength * edge_density * 5  # Scale factor
            
            return min(confidence, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_plaid_patterns(self, img_array: np.ndarray) -> float:
        """Detect plaid/checkered patterns using grid analysis"""
        try:
            # Convert to grayscale
            gray = np.mean(img_array, axis=2)
            
            # Analyze both horizontal and vertical repetition
            h_profile = np.mean(gray, axis=0)  # Average across rows
            v_profile = np.mean(gray, axis=1)  # Average across columns
            
            # Look for regular oscillations (checkered pattern)
            h_fft = np.fft.fft(h_profile)
            v_fft = np.fft.fft(v_profile)
            
            # Find if there are strong regular frequencies
            h_peaks = np.abs(h_fft[1:len(h_fft)//3])  # Look at first third of frequencies
            v_peaks = np.abs(v_fft[1:len(v_fft)//3])
            
            # Check for multiple regular peaks (characteristic of plaid)
            h_regular = np.sum(h_peaks > np.mean(h_peaks) * 2)
            v_regular = np.sum(v_peaks > np.mean(v_peaks) * 2)
            
            # Plaid patterns should have regularity in both directions
            regularity_score = min(h_regular, v_regular) / max(len(h_peaks), len(v_peaks)) * 10
            
            # Also check for grid-like crossings
            crossings = self._detect_grid_crossings(gray)
            
            confidence = (regularity_score + crossings) / 2
            
            return min(confidence, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_grid_crossings(self, gray: np.ndarray) -> float:
        """Detect grid-like crossing patterns"""
        try:
            # Look for intersection points in a grid
            grad_x = np.gradient(gray, axis=1)
            grad_y = np.gradient(gray, axis=0)
            
            # Find points where gradients change direction (potential intersections)
            x_zero_crossings = np.diff(np.sign(grad_x), axis=1) != 0
            y_zero_crossings = np.diff(np.sign(grad_y), axis=0) != 0
            
            # Count intersection-like points
            if x_zero_crossings.shape != y_zero_crossings.shape:
                return 0.0
            
            intersections = np.logical_and(x_zero_crossings, y_zero_crossings)
            intersection_density = np.sum(intersections) / (gray.shape[0] * gray.shape[1])
            
            # Scale to confidence
            return min(intersection_density * 20, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_solid_pattern(self, img_array: np.ndarray) -> float:
        """Detect solid/uniform color patterns"""
        try:
            # Calculate color variance across the image
            color_variance = np.var(img_array, axis=(0, 1))  # Variance for each channel
            total_variance = np.mean(color_variance)
            
            # Also calculate spatial variance (texture smoothness)
            gray = np.mean(img_array, axis=2)
            spatial_variance = np.var(gray)
            
            # Low variance indicates solid pattern
            # Normalize variances (typical range 0-255^2)
            color_uniformity = 1.0 / (1.0 + total_variance / 1000.0)
            spatial_uniformity = 1.0 / (1.0 + spatial_variance / 1000.0)
            
            # Combine both measures
            confidence = (color_uniformity + spatial_uniformity) / 2
            
            return confidence
            
        except Exception:
            return 0.0
    
    def _detect_floral_pattern(self, img_array: np.ndarray) -> float:
        """Detect floral patterns using texture complexity analysis"""
        try:
            # Convert to grayscale
            gray = np.mean(img_array, axis=2)
            
            # Calculate local texture complexity
            complexity_map = self._calculate_local_complexity(gray)
            
            # Floral patterns typically have:
            # 1. Medium to high complexity (organic shapes)
            # 2. Irregular but distributed patterns
            # 3. Curved edges rather than straight lines
            
            avg_complexity = np.mean(complexity_map)
            complexity_variance = np.var(complexity_map)
            
            # Look for curved edges using gradient direction variance
            grad_x = np.gradient(gray, axis=1)
            grad_y = np.gradient(gray, axis=0)
            
            # Calculate edge direction
            edge_directions = np.arctan2(grad_y, grad_x)
            direction_variance = np.var(edge_directions[~np.isnan(edge_directions)])
            
            # Floral patterns have high direction variance (curved lines)
            curve_score = min(direction_variance / (np.pi / 4), 1.0)
            
            # Combine complexity and curve measures
            floral_score = (avg_complexity * 0.4 + complexity_variance * 0.3 + curve_score * 0.3)
            
            # Scale to reasonable confidence range
            confidence = min(floral_score / 100, 1.0)
            
            return confidence
            
        except Exception:
            return 0.0
    
    def _calculate_local_complexity(self, gray: np.ndarray, window_size: int = 8) -> np.ndarray:
        """Calculate local texture complexity using sliding window"""
        try:
            complexity_map = np.zeros_like(gray)
            
            for i in range(0, gray.shape[0] - window_size, window_size // 2):
                for j in range(0, gray.shape[1] - window_size, window_size // 2):
                    window = gray[i:i+window_size, j:j+window_size]
                    
                    # Calculate local variance and gradient magnitude
                    local_var = np.var(window)
                    grad_x = np.abs(np.gradient(window, axis=1))
                    grad_y = np.abs(np.gradient(window, axis=0))
                    grad_magnitude = np.mean(grad_x + grad_y)
                    
                    # Combine variance and gradient for complexity score
                    complexity = local_var + grad_magnitude
                    complexity_map[i:i+window_size, j:j+window_size] = complexity
            
            return complexity_map
            
        except Exception:
            return np.zeros_like(gray)
    
    def _calculate_pattern_complexity(self, img_array: np.ndarray) -> float:
        """Calculate overall pattern complexity of the image"""
        try:
            # Convert to grayscale
            gray = np.mean(img_array, axis=2)
            
            # Calculate various complexity measures
            
            # 1. Color variance
            color_var = np.var(img_array, axis=(0, 1))
            avg_color_var = np.mean(color_var)
            
            # 2. Spatial frequency content
            fft_2d = np.fft.fft2(gray)
            freq_magnitude = np.abs(fft_2d)
            high_freq_energy = np.sum(freq_magnitude[gray.shape[0]//4:, gray.shape[1]//4:])
            total_energy = np.sum(freq_magnitude)
            freq_complexity = high_freq_energy / total_energy if total_energy > 0 else 0
            
            # 3. Edge density
            grad_x = np.abs(np.gradient(gray, axis=1))
            grad_y = np.abs(np.gradient(gray, axis=0))
            edge_density = np.mean(grad_x + grad_y)
            
            # Combine measures and normalize
            complexity = (avg_color_var / 1000 + freq_complexity + edge_density / 100) / 3
            
            return min(complexity, 1.0)
            
        except Exception:
            return 0.0
    
    def _process_text(self, text_annotations) -> List[str]:
        """Process text detection results"""
        detected_text = []
        
        for text in text_annotations:
            if len(text.description) > 1:  # Filter out single characters
                detected_text.append(text.description.strip())
        
        return detected_text[:5]  # Return top 5 text detections
    
    def _analyze_textures(self, image_data: bytes, labels_data: Dict) -> Dict[str, any]:
        """
        Advanced texture analysis using multiple techniques
        """
        try:
            # Convert to PIL Image for analysis
            image = Image.open(io.BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize for consistent analysis
            analysis_image = image.resize((256, 256))
            img_array = np.array(analysis_image)
            gray = np.mean(img_array, axis=2).astype(np.uint8)
            
            textures_detected = {}
            
            # 1. Surface roughness analysis
            roughness_score = self._analyze_surface_roughness(gray)
            if roughness_score > 0.6:
                textures_detected['rough'] = roughness_score
            elif roughness_score < 0.3:
                textures_detected['smooth'] = 1.0 - roughness_score
            
            # 2. Fabric texture detection
            fabric_scores = self._detect_fabric_textures(img_array, gray)
            for fabric, score in fabric_scores.items():
                if score > 0.4:
                    textures_detected[fabric] = score
            
            # 3. Material shine/gloss detection
            shine_score = self._detect_material_shine(img_array)
            if shine_score > 0.5:
                if 'smooth' not in textures_detected:
                    textures_detected['smooth'] = shine_score
                # Enhance existing smooth score
                elif textures_detected['smooth'] < shine_score:
                    textures_detected['smooth'] = shine_score
            
            # 4. Pattern-based texture (knit, woven, etc.)
            pattern_textures = self._detect_pattern_textures(gray)
            for texture, score in pattern_textures.items():
                if score > 0.4:
                    textures_detected[texture] = score
            
            # 5. Keyword-based texture enhancement from labels
            keyword_textures = self._extract_texture_from_labels(labels_data)
            for texture, score in keyword_textures.items():
                if texture in textures_detected:
                    # Boost confidence if both analysis and keywords agree
                    textures_detected[texture] = min(textures_detected[texture] + score * 0.3, 1.0)
                elif score > 0.7:  # High confidence from keywords alone
                    textures_detected[texture] = score
            
            return {
                'detected_textures': textures_detected,
                'primary_texture': max(textures_detected.items(), key=lambda x: x[1])[0] if textures_detected else 'unknown',
                'surface_roughness': roughness_score,
                'material_shine': shine_score,
                'total_textures': len(textures_detected)
            }
            
        except Exception as e:
            return {
                'detected_textures': {},
                'primary_texture': 'unknown',
                'surface_roughness': 0.0,
                'material_shine': 0.0,
                'total_textures': 0,
                'error': str(e)
            }
    
    def _analyze_surface_roughness(self, gray: np.ndarray) -> float:
        """Analyze surface roughness using texture analysis"""
        try:
            # Calculate local binary patterns for texture analysis
            lbp_score = self._calculate_local_binary_pattern_variance(gray)
            
            # Calculate gradient variance (rough surfaces have higher gradient variance)
            grad_x = np.gradient(gray.astype(float), axis=1)
            grad_y = np.gradient(gray.astype(float), axis=0)
            grad_variance = np.var(grad_x) + np.var(grad_y)
            
            # Calculate local variance in small windows
            window_size = 8
            local_variances = []
            
            for i in range(0, gray.shape[0] - window_size, window_size):
                for j in range(0, gray.shape[1] - window_size, window_size):
                    window = gray[i:i+window_size, j:j+window_size]
                    local_variances.append(np.var(window))
            
            avg_local_variance = np.mean(local_variances) if local_variances else 0
            variance_of_variances = np.var(local_variances) if local_variances else 0
            
            # Combine measures (normalize to 0-1 range)
            roughness = (lbp_score * 0.4 + 
                        min(grad_variance / 10000, 1.0) * 0.3 + 
                        min(avg_local_variance / 1000, 1.0) * 0.3)
            
            return min(roughness, 1.0)
            
        except Exception:
            return 0.5  # Default middle value
    
    def _calculate_local_binary_pattern_variance(self, gray: np.ndarray) -> float:
        """Calculate LBP variance for texture analysis"""
        try:
            # Simplified LBP calculation
            lbp_map = np.zeros_like(gray, dtype=np.uint8)
            
            for i in range(1, gray.shape[0] - 1):
                for j in range(1, gray.shape[1] - 1):
                    center = gray[i, j]
                    
                    # Check 8 neighbors
                    neighbors = [
                        gray[i-1, j-1], gray[i-1, j], gray[i-1, j+1],
                        gray[i, j+1], gray[i+1, j+1], gray[i+1, j],
                        gray[i+1, j-1], gray[i, j-1]
                    ]
                    
                    # Create binary pattern
                    binary_pattern = 0
                    for k, neighbor in enumerate(neighbors):
                        if neighbor >= center:
                            binary_pattern |= (1 << k)
                    
                    lbp_map[i, j] = binary_pattern
            
            # Calculate variance of LBP values (higher variance = more texture)
            lbp_variance = np.var(lbp_map)
            
            # Normalize (typical range 0-16000 for 8-bit images)
            return min(lbp_variance / 16000, 1.0)
            
        except Exception:
            return 0.5
    
    def _detect_fabric_textures(self, img_array: np.ndarray, gray: np.ndarray) -> Dict[str, float]:
        """Detect specific fabric textures"""
        fabric_scores = {}
        
        try:
            # Denim detection - look for specific blue tones and texture
            denim_score = self._detect_denim_texture(img_array)
            if denim_score > 0.3:
                fabric_scores['denim'] = denim_score
            
            # Leather detection - look for grain patterns and color
            leather_score = self._detect_leather_texture(img_array, gray)
            if leather_score > 0.3:
                fabric_scores['leather'] = leather_score
            
            # Knit detection - look for regular loop patterns
            knit_score = self._detect_knit_texture(gray)
            if knit_score > 0.3:
                fabric_scores['knit'] = knit_score
            
            # Woven detection - look for crosshatch patterns
            woven_score = self._detect_woven_texture(gray)
            if woven_score > 0.3:
                fabric_scores['woven'] = woven_score
            
            # Velvet/plush detection - look for uniform soft texture
            velvet_score = self._detect_velvet_texture(gray)
            if velvet_score > 0.3:
                fabric_scores['velvet'] = velvet_score
            
            return fabric_scores
            
        except Exception:
            return {}
    
    def _detect_denim_texture(self, img_array: np.ndarray) -> float:
        """Detect denim fabric characteristics"""
        try:
            # Check for blue color dominance
            blue_channel = img_array[:, :, 2]  # Blue channel
            other_channels = (img_array[:, :, 0] + img_array[:, :, 1]) / 2  # R+G average
            
            blue_dominance = np.mean(blue_channel > other_channels)
            
            # Check for denim-like texture (regular weave pattern)
            gray = np.mean(img_array, axis=2)
            
            # Look for regular crosshatch pattern typical of denim
            crosshatch_score = self._detect_crosshatch_pattern(gray)
            
            # Check color range (denim typically in blue spectrum)
            hsv_values = []
            for i in range(0, img_array.shape[0], 4):  # Sample every 4th pixel
                for j in range(0, img_array.shape[1], 4):
                    r, g, b = img_array[i, j] / 255.0
                    h, s, v = colorsys.rgb_to_hsv(r, g, b)
                    hsv_values.append((h, s, v))
            
            # Denim typically has hue in blue range (0.5-0.7) with moderate saturation
            blue_hue_count = sum(1 for h, s, v in hsv_values 
                               if 0.5 <= h <= 0.7 and s > 0.2)
            blue_hue_ratio = blue_hue_count / len(hsv_values) if hsv_values else 0
            
            # Combine factors
            denim_confidence = (blue_dominance * 0.3 + crosshatch_score * 0.4 + blue_hue_ratio * 0.3)
            
            return min(denim_confidence, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_leather_texture(self, img_array: np.ndarray, gray: np.ndarray) -> float:
        """Detect leather texture characteristics"""
        try:
            # Leather has characteristic grain patterns and color ranges
            grain_score = self._detect_grain_pattern(gray)
            
            # Check for leather-like colors (browns, blacks, tans)
            color_score = self._check_leather_colors(img_array)
            
            # Check for moderate shininess (leather has some reflectivity)
            shine_score = self._detect_material_shine(img_array)
            moderate_shine = 1.0 - abs(shine_score - 0.5) * 2  # Peak at 0.5 shine
            
            # Combine factors
            leather_confidence = (grain_score * 0.5 + color_score * 0.3 + moderate_shine * 0.2)
            
            return min(leather_confidence, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_knit_texture(self, gray: np.ndarray) -> float:
        """Detect knitted fabric texture"""
        try:
            # Knits have regular loop patterns - look for small-scale regularity
            regularity_score = self._detect_small_scale_regularity(gray, scale=4)
            
            # Knits also have some "give" which creates slight blurring - check for soft edges
            edge_softness = self._calculate_edge_softness(gray)
            
            # Combine factors
            knit_confidence = (regularity_score * 0.6 + edge_softness * 0.4)
            
            return min(knit_confidence, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_woven_texture(self, gray: np.ndarray) -> float:
        """Detect woven fabric texture"""
        try:
            # Woven fabrics have crosshatch patterns
            crosshatch_score = self._detect_crosshatch_pattern(gray)
            
            # They also have regular over-under patterns
            regularity_score = self._detect_small_scale_regularity(gray, scale=6)
            
            # Woven fabrics typically have sharper edges than knits
            edge_sharpness = 1.0 - self._calculate_edge_softness(gray)
            
            # Combine factors
            woven_confidence = (crosshatch_score * 0.5 + regularity_score * 0.3 + edge_sharpness * 0.2)
            
            return min(woven_confidence, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_velvet_texture(self, gray: np.ndarray) -> float:
        """Detect velvet/plush texture"""
        try:
            # Velvet has very uniform, soft texture with minimal variation
            uniformity_score = 1.0 - (np.var(gray) / 10000)  # High uniformity
            
            # Soft edges
            edge_softness = self._calculate_edge_softness(gray)
            
            # Low high-frequency content (smooth texture)
            fft_2d = np.fft.fft2(gray)
            high_freq_energy = np.sum(np.abs(fft_2d[gray.shape[0]//3:, gray.shape[1]//3:]))
            total_energy = np.sum(np.abs(fft_2d))
            low_freq_ratio = 1.0 - (high_freq_energy / total_energy) if total_energy > 0 else 0
            
            # Combine factors
            velvet_confidence = (uniformity_score * 0.4 + edge_softness * 0.3 + low_freq_ratio * 0.3)
            
            return min(max(velvet_confidence, 0.0), 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_material_shine(self, img_array: np.ndarray) -> float:
        """Detect material shininess/glossiness"""
        try:
            # Look for bright spots and reflections
            brightness = np.mean(img_array, axis=2)
            
            # Find very bright areas
            bright_threshold = np.percentile(brightness, 95)
            bright_areas = brightness > bright_threshold
            bright_ratio = np.sum(bright_areas) / brightness.size
            
            # Look for high local variance in brightness (indicates reflections)
            local_variance = self._calculate_local_variance(brightness, window_size=8)
            high_variance_areas = local_variance > np.percentile(local_variance, 90)
            variance_ratio = np.sum(high_variance_areas) / local_variance.size
            
            # Combine factors
            shine_score = (bright_ratio * 0.6 + variance_ratio * 0.4)
            
            return min(shine_score * 5, 1.0)  # Scale factor
            
        except Exception:
            return 0.0
    
    def _detect_pattern_textures(self, gray: np.ndarray) -> Dict[str, float]:
        """Detect textures based on repeating patterns"""
        pattern_textures = {}
        
        try:
            # Quilted pattern detection
            quilted_score = self._detect_quilted_pattern(gray)
            if quilted_score > 0.3:
                pattern_textures['quilted'] = quilted_score
            
            # Mesh pattern detection
            mesh_score = self._detect_mesh_pattern(gray)
            if mesh_score > 0.3:
                pattern_textures['mesh'] = mesh_score
            
            # Corduroy detection (vertical lines)
            corduroy_score = self._detect_corduroy_pattern(gray)
            if corduroy_score > 0.3:
                pattern_textures['corduroy'] = corduroy_score
            
            return pattern_textures
            
        except Exception:
            return {}
    
    def _detect_crosshatch_pattern(self, gray: np.ndarray) -> float:
        """Detect crosshatch/grid patterns"""
        try:
            # Calculate gradients
            grad_x = np.abs(np.gradient(gray.astype(float), axis=1))
            grad_y = np.abs(np.gradient(gray.astype(float), axis=0))
            
            # Look for regular intersections
            grid_strength = np.mean(grad_x * grad_y)  # High where both gradients are strong
            
            # Normalize
            return min(grid_strength / 1000, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_grain_pattern(self, gray: np.ndarray) -> float:
        """Detect leather-like grain patterns"""
        try:
            # Look for small-scale irregular patterns
            local_complexity = self._calculate_local_complexity(gray, window_size=6)
            
            # Grain patterns have moderate complexity (not too smooth, not too busy)
            optimal_complexity = 50  # Adjust based on testing
            complexity_score = 1.0 - abs(np.mean(local_complexity) - optimal_complexity) / optimal_complexity
            
            return max(min(complexity_score, 1.0), 0.0)
            
        except Exception:
            return 0.0
    
    def _check_leather_colors(self, img_array: np.ndarray) -> float:
        """Check if colors are typical for leather"""
        try:
            # Sample colors and check for leather-typical hues
            leather_colors = 0
            total_samples = 0
            
            for i in range(0, img_array.shape[0], 8):
                for j in range(0, img_array.shape[1], 8):
                    r, g, b = img_array[i, j] / 255.0
                    h, s, v = colorsys.rgb_to_hsv(r, g, b)
                    
                    # Brown/tan range OR black/gray range
                    is_leather_color = ((0.08 <= h <= 0.15 and s > 0.2) or  # Brown range
                                      (s < 0.2 and v < 0.8))  # Black/gray range
                    
                    if is_leather_color:
                        leather_colors += 1
                    total_samples += 1
            
            return leather_colors / total_samples if total_samples > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _extract_texture_from_labels(self, labels_data: Dict) -> Dict[str, float]:
        """Extract texture information from GCP Vision labels"""
        texture_scores = {}
        
        try:
            all_labels = labels_data.get('all_labels', [])
            
            for label in all_labels:
                description = label['description'].lower()
                confidence = label['score']
                
                # Match against texture keywords
                for texture, keywords in self.texture_keywords.items():
                    if any(keyword in description for keyword in keywords):
                        # Boost confidence for high-scoring labels
                        enhanced_confidence = confidence
                        if confidence > 0.8:
                            enhanced_confidence *= 1.2
                        
                        texture_scores[texture] = min(enhanced_confidence, 1.0)
            
            return texture_scores
            
        except Exception:
            return {}
    
    def _calculate_local_variance(self, brightness: np.ndarray, window_size: int = 8) -> np.ndarray:
        """Calculate local variance for shine detection"""
        try:
            variance_map = np.zeros_like(brightness)
            
            for i in range(0, brightness.shape[0] - window_size, window_size // 2):
                for j in range(0, brightness.shape[1] - window_size, window_size // 2):
                    window = brightness[i:i+window_size, j:j+window_size]
                    local_var = np.var(window)
                    variance_map[i:i+window_size, j:j+window_size] = local_var
            
            return variance_map
            
        except Exception:
            return np.zeros_like(brightness)
    
    def _detect_small_scale_regularity(self, gray: np.ndarray, scale: int = 4) -> float:
        """Detect small-scale regular patterns for knit/woven detection"""
        try:
            # Look for regular patterns at small scales
            regularity_scores = []
            
            for i in range(0, gray.shape[0] - scale*4, scale*2):
                for j in range(0, gray.shape[1] - scale*4, scale*2):
                    # Extract small patches
                    patch1 = gray[i:i+scale*2, j:j+scale*2]
                    patch2 = gray[i+scale:i+scale*3, j:j+scale*2]
                    patch3 = gray[i:i+scale*2, j+scale:j+scale*3]
                    
                    # Calculate similarity between adjacent patches
                    if patch1.shape == patch2.shape:
                        similarity1 = 1.0 / (1.0 + np.mean(np.abs(patch1 - patch2)))
                    else:
                        similarity1 = 0
                    
                    if patch1.shape == patch3.shape:
                        similarity2 = 1.0 / (1.0 + np.mean(np.abs(patch1 - patch3)))
                    else:
                        similarity2 = 0
                    
                    regularity_scores.append((similarity1 + similarity2) / 2)
            
            return np.mean(regularity_scores) if regularity_scores else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_edge_softness(self, gray: np.ndarray) -> float:
        """Calculate edge softness for texture analysis"""
        try:
            # Calculate gradients
            grad_x = np.gradient(gray.astype(float), axis=1)
            grad_y = np.gradient(gray.astype(float), axis=0)
            grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Find edges
            edge_threshold = np.percentile(grad_magnitude, 85)
            edges = grad_magnitude > edge_threshold
            
            if np.sum(edges) == 0:
                return 0.5  # Default middle value
            
            # Calculate edge sharpness (high gradient = sharp, low gradient = soft)
            edge_gradients = grad_magnitude[edges]
            avg_edge_strength = np.mean(edge_gradients)
            
            # Convert to softness (inverse of sharpness)
            # Normalize by typical gradient range
            softness = 1.0 / (1.0 + avg_edge_strength / 50.0)
            
            return min(max(softness, 0.0), 1.0)
            
        except Exception:
            return 0.5
    
    def _detect_quilted_pattern(self, gray: np.ndarray) -> float:
        """Detect quilted patterns (diamond/square stitching)"""
        try:
            # Look for diamond or square grid patterns
            # Calculate both horizontal and vertical gradients
            grad_x = np.abs(np.gradient(gray.astype(float), axis=1))
            grad_y = np.abs(np.gradient(gray.astype(float), axis=0))
            
            # Look for regular grid intersections
            grid_strength = self._detect_grid_crossings(gray)
            
            # Also look for diagonal patterns typical of quilting
            diagonal_strength = self._detect_diagonal_patterns(gray)
            
            # Combine factors
            quilted_confidence = (grid_strength * 0.6 + diagonal_strength * 0.4)
            
            return min(quilted_confidence, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_diagonal_patterns(self, gray: np.ndarray) -> float:
        """Detect diagonal patterns for quilted detection"""
        try:
            # Create diagonal kernels
            kernel_size = min(8, min(gray.shape) // 8)
            
            # Simple diagonal detection by comparing diagonal neighbors
            diagonal_evidence = 0
            total_checks = 0
            
            for i in range(kernel_size, gray.shape[0] - kernel_size, kernel_size):
                for j in range(kernel_size, gray.shape[1] - kernel_size, kernel_size):
                    # Check diagonal patterns
                    center = gray[i, j]
                    
                    # Diagonal neighbors
                    diag1 = (gray[i-kernel_size//2, j-kernel_size//2] + gray[i+kernel_size//2, j+kernel_size//2]) / 2
                    diag2 = (gray[i-kernel_size//2, j+kernel_size//2] + gray[i+kernel_size//2, j-kernel_size//2]) / 2
                    
                    # If diagonals are similar, it suggests a diagonal pattern
                    diagonal_similarity = 1.0 / (1.0 + abs(diag1 - diag2))
                    if diagonal_similarity > 0.8:
                        diagonal_evidence += 1
                    
                    total_checks += 1
            
            return diagonal_evidence / total_checks if total_checks > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _detect_mesh_pattern(self, gray: np.ndarray) -> float:
        """Detect mesh/net patterns"""
        try:
            # Mesh patterns have regular holes/gaps
            # Look for regular dark spots (holes) surrounded by lighter areas
            
            # Apply threshold to find potential holes
            threshold = np.percentile(gray, 30)  # Bottom 30% are potential holes
            dark_areas = gray < threshold
            
            # Count clusters of dark areas (potential holes)
            from scipy.ndimage import label
            labeled_holes, num_holes = label(dark_areas)
            
            # Calculate hole density and regularity
            total_pixels = gray.shape[0] * gray.shape[1]
            hole_density = num_holes / total_pixels * 10000  # Scale factor
            
            # Also check for regular spacing by looking at gradient patterns
            grid_regularity = self._detect_grid_crossings(gray)
            
            # Combine factors
            mesh_confidence = min((hole_density * 0.7 + grid_regularity * 0.3), 1.0)
            
            return mesh_confidence
            
        except Exception:
            return 0.0
    
    def _detect_corduroy_pattern(self, gray: np.ndarray) -> float:
        """Detect corduroy patterns (vertical ridges)"""
        try:
            # Corduroy has strong vertical lines/ridges
            # Analyze vertical frequency content
            v_profile = np.mean(gray, axis=1)  # Average across rows (vertical analysis)
            
            # Apply FFT to find regular vertical patterns
            v_fft = np.fft.fft(v_profile)
            v_freq_strength = np.max(np.abs(v_fft[1:len(v_fft)//4]))
            
            # Normalize
            v_normalized = v_freq_strength / (len(v_profile) * 255)
            
            # Check for predominantly vertical gradients
            grad_x = np.abs(np.gradient(gray.astype(float), axis=1))
            grad_y = np.abs(np.gradient(gray.astype(float), axis=0))
            
            # Vertical patterns should have stronger horizontal gradients than vertical
            horizontal_grad_strength = np.mean(grad_x)
            vertical_grad_strength = np.mean(grad_y)
            
            vertical_dominance = horizontal_grad_strength / (vertical_grad_strength + 1e-6)
            vertical_dominance = min(vertical_dominance / 3.0, 1.0)  # Normalize
            
            # Combine frequency and gradient analysis
            corduroy_confidence = (v_normalized * 5 * 0.6 + vertical_dominance * 0.4)
            
            return min(corduroy_confidence, 1.0)
            
        except Exception:
            return 0.0
    
    def _analyze_style_features(self, labels_data: Dict, objects_data: Dict) -> Dict[str, any]:
        """Analyze style and garment features"""
        try:
            style_scores = {}
            garment_features = {}
            
            all_text = []
            
            # Collect all descriptions
            for label in labels_data.get('all_labels', []):
                all_text.append(label['description'].lower())
            
            for obj in objects_data.get('all_objects', []):
                all_text.append(obj['name'].lower())
            
            combined_text = ' '.join(all_text)
            
            # Analyze style keywords
            for style, keywords in self.style_keywords.items():
                score = 0
                matches = 0
                for keyword in keywords:
                    if keyword in combined_text:
                        matches += 1
                        score += 0.8  # Base score for keyword match
                
                if matches > 0:
                    style_scores[style] = min(score / len(keywords), 1.0)
            
            # Analyze garment features
            for feature_type, keywords in self.garment_features.items():
                detected_features = []
                for keyword in keywords:
                    if keyword in combined_text:
                        detected_features.append(keyword)
                
                if detected_features:
                    garment_features[feature_type] = detected_features
            
            # Calculate formality score
            formality_score = self._calculate_formality_score(style_scores, garment_features)
            
            # Determine occasion suitability
            occasion_suitability = self._determine_occasion_suitability(style_scores, formality_score)
            
            return {
                'detected_styles': style_scores,
                'primary_style': max(style_scores.items(), key=lambda x: x[1])[0] if style_scores else 'unknown',
                'garment_features': garment_features,
                'formality_score': formality_score,
                'occasion_suitability': occasion_suitability,
                'total_styles': len(style_scores)
            }
            
        except Exception as e:
            return {
                'detected_styles': {},
                'primary_style': 'unknown',
                'garment_features': {},
                'formality_score': 0.5,
                'occasion_suitability': [],
                'total_styles': 0,
                'error': str(e)
            }
    
    def _calculate_formality_score(self, style_scores: Dict[str, float], garment_features: Dict) -> float:
        """Calculate formality level (0=very casual, 1=very formal)"""
        try:
            formal_indicators = ['formal', 'business', 'elegant', 'sophisticated']
            casual_indicators = ['casual', 'sporty', 'relaxed', 'streetwear']
            
            formal_score = sum(style_scores.get(style, 0) for style in formal_indicators)
            casual_score = sum(style_scores.get(style, 0) for style in casual_indicators)
            
            # Adjust based on garment features
            formal_features = ['button-up', 'collar', 'blazer', 'dress shirt']
            casual_features = ['hoodie', 'sneakers', 'shorts', 'distressed']
            
            for feature_list in garment_features.values():
                for feature in feature_list:
                    if any(formal_feat in feature for formal_feat in formal_features):
                        formal_score += 0.2
                    elif any(casual_feat in feature for casual_feat in casual_features):
                        casual_score += 0.2
            
            # Normalize to 0-1 scale
            total_score = formal_score + casual_score
            if total_score > 0:
                formality = formal_score / total_score
            else:
                formality = 0.5  # Default middle value
            
            return min(max(formality, 0.0), 1.0)
            
        except Exception:
            return 0.5
    
    def _determine_occasion_suitability(self, style_scores: Dict[str, float], formality_score: float) -> List[str]:
        """Determine suitable occasions based on style and formality"""
        try:
            occasions = []
            
            # Map formality to occasions
            if formality_score >= 0.8:
                occasions.extend(['business', 'formal events', 'professional'])
            elif formality_score >= 0.6:
                occasions.extend(['business casual', 'date night', 'dinner'])
            elif formality_score >= 0.4:
                occasions.extend(['casual', 'weekend', 'everyday'])
            else:
                occasions.extend(['very casual', 'lounging', 'exercise'])
            
            # Add specific occasions based on style
            if style_scores.get('sporty', 0) > 0.5:
                occasions.extend(['gym', 'sports', 'outdoor activities'])
            
            if style_scores.get('romantic', 0) > 0.5:
                occasions.extend(['date', 'romantic dinner'])
            
            if style_scores.get('edgy', 0) > 0.5:
                occasions.extend(['nightlife', 'concerts', 'parties'])
            
            if style_scores.get('bohemian', 0) > 0.5:
                occasions.extend(['festivals', 'art events', 'creative gatherings'])
            
            # Remove duplicates and return
            return list(set(occasions))
            
        except Exception:
            return ['everyday']
    
    def _extract_comprehensive_features(self, analysis_results) -> Dict[str, any]:
        """Extract clothing-specific features from analysis results"""
        features = []
        confidence_scores = {}
        suggested_category = 'unknown'
        
        # Extract features from labels
        for label in analysis_results['labels']['clothing_related']:
            feature = label['description']
            features.append(feature)
            confidence_scores[feature] = label['score']
        
        # Extract color features with confidence weighting
        for color_info in analysis_results['colors']['dominant']:
            color_feature = color_info['color_name']
            if color_feature != 'unknown' and color_info['confidence'] > 0.6:
                features.append(color_feature)
                confidence_scores[color_feature] = color_info['confidence']
        
        # Add primary color if it's high confidence
        primary_color = analysis_results['colors']['primary_color']
        if primary_color != 'unknown' and primary_color not in features:
            # Find the confidence for primary color
            for color_info in analysis_results['colors']['dominant']:
                if color_info['color_name'] == primary_color:
                    if color_info['confidence'] > 0.7:
                        features.append(primary_color)
                        confidence_scores[primary_color] = color_info['confidence']
                    break
        
        # Extract pattern features from advanced analysis
        for pattern, confidence in analysis_results.get('patterns', {}).get('detected_patterns', {}).items():
            if confidence > 0.4:
                features.append(pattern)
                confidence_scores[pattern] = confidence
        
        # Extract texture features from advanced analysis
        for texture, confidence in analysis_results.get('textures', {}).get('detected_textures', {}).items():
            if confidence > 0.4:
                features.append(texture)
                confidence_scores[texture] = confidence
        
        # Extract style features
        for style, confidence in analysis_results.get('style_features', {}).get('detected_styles', {}).items():
            if confidence > 0.5:
                features.append(style)
                confidence_scores[style] = confidence
        
        # Extract pattern features from labels (fallback)
        for label in analysis_results['labels']['all_labels']:
            for pattern, keywords in self.pattern_keywords.items():
                if any(keyword in label['description'].lower() for keyword in keywords):
                    if pattern not in features:
                        features.append(pattern)
                        confidence_scores[pattern] = label['score']
        
        # Extract texture features from labels (fallback)
        for label in analysis_results['labels']['all_labels']:
            for texture, keywords in self.texture_keywords.items():
                if any(keyword in label['description'].lower() for keyword in keywords):
                    if texture not in features:
                        features.append(texture)
                        confidence_scores[texture] = label['score']
        
        # Suggest category based on detected objects and labels
        suggested_category = self._suggest_category(analysis_results)
        
        # Remove duplicates while preserving order
        features = list(dict.fromkeys(features))
        
        # Filter features by confidence (only keep high-confidence features)
        filtered_features = []
        filtered_confidence_scores = {}
        
        for feature in features:
            confidence = confidence_scores.get(feature, 0)
            # Keep features with confidence > 0.5 for comprehensive analysis
            if confidence > 0.5:
                filtered_features.append(feature)
                filtered_confidence_scores[feature] = confidence
        
        # If no high-confidence features, keep top 5 features
        if not filtered_features and features:
            sorted_features = sorted(features, key=lambda x: confidence_scores.get(x, 0), reverse=True)
            filtered_features = sorted_features[:5]
            filtered_confidence_scores = {f: confidence_scores.get(f, 0) for f in filtered_features}
        
        return {
            'features': filtered_features,
            'confidence_scores': filtered_confidence_scores,
            'suggested_category': suggested_category,
            'feature_count': len(filtered_features),
            'average_confidence': sum(filtered_confidence_scores.values()) / len(filtered_confidence_scores) if filtered_confidence_scores else 0
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
        """
        Convert RGB values to color name using HSV color space for better accuracy
        """
        # Normalize RGB values to 0-1 range
        r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
        
        # Convert RGB to HSV
        max_val = max(r_norm, g_norm, b_norm)
        min_val = min(r_norm, g_norm, b_norm)
        diff = max_val - min_val
        
        # Calculate brightness (Value)
        value = max_val
        
        # Calculate saturation
        saturation = 0 if max_val == 0 else diff / max_val
        
        # Calculate hue
        if diff == 0:
            hue = 0
        elif max_val == r_norm:
            hue = (60 * ((g_norm - b_norm) / diff) + 360) % 360
        elif max_val == g_norm:
            hue = (60 * ((b_norm - r_norm) / diff) + 120) % 360
        else:  # max_val == b_norm
            hue = (60 * ((r_norm - g_norm) / diff) + 240) % 360
        
        # Classify color based on HSV values
        color_name = self._hsv_to_color_name(hue, saturation, value)
        return self._normalize_color_name(color_name)
    
    def _normalize_color_name(self, color_name: str) -> str:
        """Normalize color names to standard fashion terms"""
        color_mappings = {
            'powder-blue': 'light blue',
            'sky blue': 'blue',  # Map sky blue to standard blue for fashion
            'sage': 'mint',  # Consolidate green variants
        }
        return color_mappings.get(color_name, color_name)
    
    def _hsv_to_color_name(self, hue: float, saturation: float, value: float) -> str:
        """
        Convert HSV values to accurate color names
        """
        # Handle grayscale colors (low saturation)
        if saturation < 0.15:  # Slightly more permissive for gray detection
            if value > 0.9:
                return 'white'
            elif value > 0.75:
                return 'light-gray'
            elif value > 0.45:
                return 'gray'
            elif value > 0.25:
                return 'dark-gray'
            elif value > 0.1:
                return 'charcoal'
            else:
                return 'black'
        
        # Handle very dark colors
        if value < 0.15:
            return 'black'
        
        # Handle light colors but with enough saturation to be chromatic
        if value > 0.85 and saturation > 0.2 and saturation < 0.8:  # Only for less saturated light colors
            # Light but saturated colors
            if hue >= 0 and hue < 30 or hue >= 330:
                return 'pink'
            elif hue >= 30 and hue < 60:
                return 'cream' if saturation < 0.4 else 'yellow'
            elif hue >= 60 and hue < 120:
                return 'mint' if saturation < 0.5 else 'green'
            elif hue >= 180 and hue < 240:
                return 'powder-blue' if saturation < 0.5 else 'blue'
            elif hue >= 240 and hue < 300:
                return 'lavender' if saturation < 0.5 else 'purple'
        
        # Handle very light colors with low saturation (beige, cream, off-white)
        if value > 0.85 and saturation < 0.3:
            if saturation > 0.05 and hue >= 30 and hue <= 70:  # Yellowish tinge
                return 'beige'
            elif saturation > 0.05 and hue >= 15 and hue <= 30:  # More orange tinge
                return 'cream'
            elif saturation > 0.05:  # Some color tinge but very light
                return 'cream'
            else:
                return 'white'
        
        # Classify chromatic colors by hue
        if saturation >= 0.15:  # Slightly lower threshold for chromatic colors
            if hue >= 0 and hue < 15 or hue >= 345:
                return self._get_red_variant(saturation, value)
            elif hue >= 15 and hue < 45:
                return self._get_orange_brown_variant(hue, saturation, value)
            elif hue >= 45 and hue < 75:
                return self._get_yellow_variant(saturation, value)
            elif hue >= 75 and hue < 150:
                return self._get_green_variant(hue, saturation, value)  # Pass hue for olive detection
            elif hue >= 150 and hue < 190:  # Cyan/turquoise range
                return self._get_cyan_variant(saturation, value)
            elif hue >= 190 and hue < 270:  # Blue range
                return self._get_blue_variant(hue, saturation, value)
            elif hue >= 270 and hue < 345:
                return self._get_purple_variant(saturation, value)
        
        return 'gray'
    
    def _get_orange_brown_variant(self, hue: float, saturation: float, value: float) -> str:
        """Get specific orange/brown color variant - better distinction"""
        # Brown: low value OR high saturation with low value
        if value < 0.6:  # Darker colors are more likely brown
            return 'brown'
        elif saturation > 0.7 and value < 0.7:  # High saturation, medium darkness
            return 'brown'
        elif saturation < 0.5:  # Low saturation oranges
            if value > 0.7:
                return 'tan'
            else:
                return 'brown'
        elif hue < 25:  # More red-orange
            if value > 0.8:
                return 'peach'
            else:
                return 'orange'
        else:  # More yellow-orange
            return 'orange'
    
    def _get_red_variant(self, saturation: float, value: float) -> str:
        """Get specific red color variant"""
        if value < 0.3:
            return 'maroon'
        elif saturation > 0.8 and value > 0.8:  # Pure, bright red
            return 'red'
        elif saturation > 0.7 and value > 0.7:  # Still quite red but not pure
            return 'red'
        elif value > 0.7 and saturation < 0.6:  # Light and less saturated = pink
            return 'pink'
        elif saturation < 0.5:
            return 'pink' if value > 0.6 else 'burgundy'
        else:
            return 'red'
    
    def _get_orange_variant(self, saturation: float, value: float) -> str:
        """Get specific orange color variant"""
        if value > 0.8 and saturation < 0.6:
            return 'peach'
        elif saturation > 0.7:
            return 'orange'
        else:
            return 'rust'
    
    def _get_yellow_variant(self, saturation: float, value: float) -> str:
        """Get specific yellow color variant"""
        if saturation > 0.8 and value > 0.8:  # Pure, bright yellow
            return 'yellow'
        elif value > 0.8 and saturation < 0.5:  # Light yellow
            return 'cream'
        elif saturation > 0.6 and value > 0.6:  # Rich yellow
            return 'yellow'
        elif saturation < 0.4:  # Very pale
            return 'beige'
        else:
            return 'yellow'
    
    def _get_green_variant(self, hue: float, saturation: float, value: float) -> str:
        """Get specific green color variant"""
        # Olive detection for yellow-green hues
        if hue >= 60 and hue <= 75 and saturation > 0.3 and value < 0.7:
            return 'olive'
        elif hue >= 75 and hue <= 90 and saturation > 0.4 and value < 0.6:
            return 'olive'
        # Dark greens
        elif value < 0.4:
            return 'olive' if saturation < 0.7 else 'green'
        # Light greens and mint
        elif value > 0.8 and saturation < 0.6:
            return 'mint'
        elif saturation > 0.7 and value > 0.6:
            return 'green'
        elif saturation < 0.5:
            return 'sage'
        else:
            return 'green'
    
    def _get_cyan_variant(self, saturation: float, value: float) -> str:
        """Get specific cyan color variant"""
        if saturation > 0.7:
            return 'teal'
        else:
            return 'mint'
    
    def _get_blue_variant(self, hue: float, saturation: float, value: float) -> str:
        """Get specific blue color variant"""
        if value < 0.3:
            return 'navy'
        # Navy blue - darker blues with good saturation
        elif hue >= 210 and hue <= 250 and saturation > 0.5 and value < 0.6:
            return 'navy'
        # Light blue - high value, lower saturation
        elif value > 0.7 and saturation < 0.6:
            return 'light blue'
        # Pure blue - high saturation and value
        elif saturation > 0.8 and value > 0.8:
            return 'blue'
        # Sky blue - medium blue tones
        elif hue >= 180 and hue <= 210:
            return 'sky blue'
        else:
            return 'blue'
    
    def _get_purple_variant(self, saturation: float, value: float) -> str:
        """Get specific purple color variant"""
        if value > 0.8 and saturation < 0.5:
            return 'lavender'
        elif saturation > 0.8:
            return 'purple'
        else:
            return 'plum'
    
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
        # This could be extended to fetch and analyze images from URLs
        # For now, return empty suggestions
        return {
            'suggested_features': [],
            'confidence_scores': {},
            'suggested_category': 'unknown'
        }
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