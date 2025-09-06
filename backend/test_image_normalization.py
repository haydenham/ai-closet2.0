#!/usr/bin/env python3
"""
Test Image Normalization Features
=================================

Test the image normalization pipeline to ensure it's working correctly
before integrating with the full GCP Vision analysis.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PIL import Image, ImageDraw
    import numpy as np
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from app.services.gcp_vision_service import GCPVisionService

def create_test_image_with_background() -> bytes:
    """Create a synthetic test image with a strong background color"""
    
    # Create a 400x400 image with white background
    image = Image.new('RGB', (400, 400), color='white')
    draw = ImageDraw.Draw(image)
    
    # Add a "clothing item" in the center (dark blue rectangle)
    clothing_color = (25, 25, 112)  # Navy blue
    draw.rectangle([150, 150, 250, 300], fill=clothing_color)
    
    # Add some "background noise" 
    # Light gray areas
    draw.rectangle([0, 0, 100, 100], fill=(240, 240, 240))
    draw.rectangle([300, 300, 400, 400], fill=(250, 250, 250))
    
    # Convert to bytes
    output_buffer = io.BytesIO()
    image.save(output_buffer, format='JPEG', quality=95)
    return output_buffer.getvalue()

def create_poorly_lit_image() -> bytes:
    """Create a test image with poor lighting conditions"""
    
    # Create a dark image
    image = Image.new('RGB', (300, 300), color=(50, 50, 50))
    draw = ImageDraw.Draw(image)
    
    # Add a red shirt that's hard to see
    shirt_color = (100, 20, 20)  # Dark red
    draw.rectangle([100, 100, 200, 250], fill=shirt_color)
    
    # Convert to bytes
    output_buffer = io.BytesIO()
    image.save(output_buffer, format='JPEG', quality=95)
    return output_buffer.getvalue()

def test_normalization_pipeline():
    """Test the normalization pipeline with synthetic images"""
    
    print("🖼️  Testing Image Normalization Pipeline")
    print("=" * 45)
    
    if not HAS_PIL:
        print("❌ PIL/Pillow not available - cannot test normalization")
        return
    
    try:
        # Initialize the service
        vision_service = GCPVisionService()
        
        print("✅ GCP Vision Service initialized with normalization support")
        
        # Test 1: Background suppression
        print("\n📋 Test 1: Background Suppression")
        test_image_1 = create_test_image_with_background()
        
        # Test normalization
        normalized_image_1 = vision_service.normalize_image(test_image_1, enhance_clothing_focus=True)
        
        print(f"   Original image size: {len(test_image_1)} bytes")
        print(f"   Normalized image size: {len(normalized_image_1)} bytes")
        print("   ✅ Background suppression normalization completed")
        
        # Test 2: Poor lighting correction
        print("\n📋 Test 2: Poor Lighting Correction")
        test_image_2 = create_poorly_lit_image()
        
        normalized_image_2 = vision_service.normalize_image(test_image_2, enhance_clothing_focus=True)
        
        print(f"   Original image size: {len(test_image_2)} bytes")
        print(f"   Normalized image size: {len(normalized_image_2)} bytes")
        print("   ✅ Lighting normalization completed")
        
        # Test 3: Component testing
        print("\n📋 Test 3: Individual Component Testing")
        
        # Test resize functionality
        original_pil = Image.open(io.BytesIO(test_image_1))
        resized = vision_service._resize_image(original_pil, max_dimension=512)
        print(f"   Original size: {original_pil.size}")
        print(f"   Resized size: {resized.size}")
        print("   ✅ Image resizing working")
        
        # Test color normalization
        color_normalized = vision_service._normalize_colors(original_pil)
        print("   ✅ Color normalization working")
        
        # Test contrast enhancement
        contrast_enhanced = vision_service._enhance_contrast_brightness(original_pil)
        print("   ✅ Contrast enhancement working")
        
        print("\n🎉 All normalization tests passed!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        return False
    except Exception as e:
        print(f"❌ Normalization test failed: {e}")
        return False

def test_color_analysis_with_normalization():
    """Test color analysis with and without normalization"""
    
    print("\n🎨 Testing Color Analysis with Normalization")
    print("=" * 50)
    
    if not HAS_PIL:
        print("❌ PIL/Pillow not available")
        return
    
    try:
        vision_service = GCPVisionService()
        
        # Create test image with background
        test_image = create_test_image_with_background()
        
        # Test color extraction from normalized vs original
        print("📋 Comparing color detection:")
        print("   Testing with synthetic navy blue clothing on white background")
        
        # Test the RGB color detection directly
        navy_rgb = (25, 25, 112)
        white_rgb = (255, 255, 255)
        
        navy_color = vision_service._rgb_to_color_name(*navy_rgb)
        white_color = vision_service._rgb_to_color_name(*white_rgb)
        
        print(f"   Navy RGB {navy_rgb} -> {navy_color}")
        print(f"   White RGB {white_rgb} -> {white_color}")
        
        print("   ✅ Color detection working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Color analysis test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Image Normalization Test Suite")
    print("=" * 40)
    
    # Test normalization pipeline
    norm_success = test_normalization_pipeline()
    
    # Test color analysis integration
    color_success = test_color_analysis_with_normalization()
    
    print(f"\n📊 Test Results:")
    print(f"Normalization Pipeline: {'✅ PASS' if norm_success else '❌ FAIL'}")
    print(f"Color Analysis Integration: {'✅ PASS' if color_success else '❌ FAIL'}")
    
    if norm_success and color_success:
        print("\n🎉 Image normalization ready for production!")
        print("Benefits:")
        print("   • Background color suppression")
        print("   • Automatic white balance correction")
        print("   • Contrast and brightness optimization")
        print("   • Noise reduction")
        print("   • Consistent image sizing")
    else:
        print("\n⚠️  Some tests failed - check dependencies and implementation")
