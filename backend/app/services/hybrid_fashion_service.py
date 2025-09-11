"""
Hybrid Fashion Analysis Service
Combines Fashion-CLIP (categories, styles, features) with GCP Vision (colors, brands)
for comprehensive clothing item analysis.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
import time

from app.services.fashion_clip_service import get_fashion_clip_service
from app.services.gcp_color_brand_service import get_gcp_color_brand_service

logger = logging.getLogger(__name__)

class HybridFashionService:
    """
    Hybrid service that combines the best of both worlds:
    - Fashion-CLIP: Categories, styles, fabric features, embeddings
    - GCP Vision: Colors, brand detection
    
    This provides comprehensive fashion analysis for the clothing upload system.
    """
    
    def __init__(self):
        self.fashion_clip_service = get_fashion_clip_service()
        self.gcp_service = get_gcp_color_brand_service()
        
        # Validate services
        if not self.fashion_clip_service:
            logger.warning("Fashion-CLIP service not available")
        if not self.gcp_service:
            logger.warning("GCP Color & Brand service not available")
        
        logger.info(f"Hybrid Fashion service initialized - Fashion-CLIP: {self.fashion_clip_service is not None}, GCP: {self.gcp_service is not None}")
    
    async def analyze_clothing_item(self, image_data: bytes) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a clothing item.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Complete analysis combining Fashion-CLIP and GCP Vision results
        """
        start_time = time.time()
        
        try:
            # Run both analyses in parallel for speed
            tasks = []
            
            if self.fashion_clip_service:
                tasks.append(self._run_fashion_clip_analysis(image_data))
            
            if self.gcp_service:
                tasks.append(self._run_gcp_analysis(image_data))
            
            if not tasks:
                return self._create_error_response("No analysis services available")
            
            # Execute analyses
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            fashion_clip_result = None
            gcp_result = None
            
            result_index = 0
            if self.fashion_clip_service:
                fashion_clip_result = results[result_index] if not isinstance(results[result_index], Exception) else None
                result_index += 1
            
            if self.gcp_service:
                gcp_result = results[result_index] if result_index < len(results) and not isinstance(results[result_index], Exception) else None
            
            # Combine results
            combined_result = self._combine_analyses(fashion_clip_result, gcp_result)
            combined_result['processing_time_ms'] = int((time.time() - start_time) * 1000)
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Hybrid fashion analysis failed: {str(e)}")
            return self._create_error_response(str(e))
    
    async def _run_fashion_clip_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """Run Fashion-CLIP analysis."""
        try:
            result = await self.fashion_clip_service.analyze_fashion_item(image_data)
            logger.debug(f"Fashion-CLIP analysis completed: {result.get('success', False)}")
            return result
        except Exception as e:
            logger.error(f"Fashion-CLIP analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _run_gcp_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """Run GCP Vision analysis."""
        try:
            result = await self.gcp_service.analyze_colors_and_brands(image_data)
            logger.debug(f"GCP analysis completed: {result.get('success', False)}")
            return result
        except Exception as e:
            logger.error(f"GCP analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _combine_analyses(self, fashion_clip_result: Optional[Dict], gcp_result: Optional[Dict]) -> Dict[str, Any]:
        """Combine results from both analyses into a comprehensive response."""
        
        # Base response structure
        response = {
            'success': False,
            'analysis_sources': [],
            'category': 'unknown',
            'style': [],
            'features': [],
            'colors': {},
            'brands': {},
            'embedding': None,
            'confidence_scores': {},
            'errors': []
        }
        
        # Process Fashion-CLIP results
        if fashion_clip_result and fashion_clip_result.get('success'):
            response['analysis_sources'].append('fashion-clip')
            response['category'] = fashion_clip_result.get('category', 'unknown')
            response['style'] = fashion_clip_result.get('style', [])
            response['features'] = fashion_clip_result.get('features', [])
            response['embedding'] = fashion_clip_result.get('embedding')
            response['confidence_scores'] = fashion_clip_result.get('confidence_scores', {})
            response['success'] = True
        elif fashion_clip_result and not fashion_clip_result.get('success'):
            response['errors'].append(f"Fashion-CLIP: {fashion_clip_result.get('error', 'Unknown error')}")
        
        # Process GCP Vision results
        if gcp_result and gcp_result.get('success'):
            response['analysis_sources'].append('gcp-vision')
            response['colors'] = gcp_result.get('colors', {})
            response['brands'] = gcp_result.get('brands', {})
            response['success'] = True
        elif gcp_result and not gcp_result.get('success'):
            response['errors'].append(f"GCP Vision: {gcp_result.get('error', 'Unknown error')}")
        
        # Enhanced analysis combining both sources
        if 'fashion-clip' in response['analysis_sources'] and 'gcp-vision' in response['analysis_sources']:
            response['enhanced_analysis'] = self._create_enhanced_analysis(fashion_clip_result, gcp_result)
        
        # Add metadata
        response['total_sources'] = len(response['analysis_sources'])
        response['has_embedding'] = response['embedding'] is not None
        response['has_colors'] = bool(response['colors'])
        response['has_brands'] = bool(response['brands'].get('detected_brands', []))
        
        return response
    
    def _create_enhanced_analysis(self, fashion_clip_result: Dict, gcp_result: Dict) -> Dict[str, Any]:
        """Create enhanced analysis by combining insights from both services."""
        enhanced = {}
        
        # Color-aware style enhancement
        primary_color = gcp_result.get('colors', {}).get('primary_color')
        styles = fashion_clip_result.get('style', [])
        
        if primary_color and primary_color != 'unknown':
            enhanced['color_style_combination'] = f"{primary_color} {styles[0] if styles else 'clothing'}"
        
        # Brand-category validation
        detected_brands = gcp_result.get('brands', {}).get('detected_brands', [])
        category = fashion_clip_result.get('category', 'unknown')
        
        if detected_brands and category != 'unknown':
            enhanced['brand_category'] = {
                'category': category,
                'brands': [b['brand'] for b in detected_brands[:3]],  # Top 3 brands
                'confidence': 'high' if detected_brands[0].get('confidence', 0) > 0.8 else 'medium'
            }
        
        # Color dominance insights
        color_percentages = gcp_result.get('colors', {}).get('color_percentages', {})
        if color_percentages:
            total_colors = len(color_percentages)
            enhanced['color_complexity'] = {
                'total_colors': total_colors,
                'complexity': 'simple' if total_colors <= 2 else 'complex' if total_colors >= 5 else 'moderate',
                'dominant_colors': list(color_percentages.keys())[:3]
            }
        
        # Feature-color matching
        features = fashion_clip_result.get('features', [])
        if features and primary_color:
            enhanced['material_color'] = {
                'materials': features,
                'primary_color': primary_color,
                'suggested_tags': [f"{primary_color} {feature}" for feature in features[:2]]
            }
        
        return enhanced
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            'success': False,
            'analysis_sources': [],
            'category': 'unknown',
            'style': [],
            'features': [],
            'colors': {},
            'brands': {},
            'embedding': None,
            'confidence_scores': {},
            'errors': [error_message],
            'processing_time_ms': 0
        }
    
    async def get_embedding_only(self, image_data: bytes) -> Optional[List[float]]:
        """Get just the embedding for similarity calculations."""
        if not self.fashion_clip_service:
            return None
        
        try:
            result = await self.fashion_clip_service.generate_embedding(image_data)
            return result.get('embedding') if result.get('success') else None
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            return None
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate similarity between two embeddings."""
        if not self.fashion_clip_service:
            return 0.0
        
        return self.fashion_clip_service.calculate_similarity(embedding1, embedding2)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all underlying services."""
        return {
            'fashion_clip_available': self.fashion_clip_service is not None,
            'gcp_vision_available': self.gcp_service is not None,
            'fashion_clip_info': self.fashion_clip_service.get_model_info() if self.fashion_clip_service else None,
            'hybrid_ready': self.fashion_clip_service is not None or self.gcp_service is not None,
            'full_analysis_available': self.fashion_clip_service is not None and self.gcp_service is not None
        }


# Global service instance
hybrid_fashion_service = None

def get_hybrid_fashion_service() -> Optional[HybridFashionService]:
    """Get the global Hybrid Fashion service instance."""
    global hybrid_fashion_service
    
    if hybrid_fashion_service is None:
        try:
            hybrid_fashion_service = HybridFashionService()
            logger.info("Hybrid Fashion service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Hybrid Fashion service: {str(e)}")
            hybrid_fashion_service = None
    
    return hybrid_fashion_service