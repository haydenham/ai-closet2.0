#!/usr/bin/env python3
"""
Test script to debug GCP Vision API issues
"""
import logging
import sys
import traceback
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.services.gcp_vision_service import GCPVisionService

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_vision_service():
    """Test the GCP Vision service initialization and basic functionality"""
    
    print("🔧 Testing GCP Vision Service...")
    
    try:
        # Test initialization
        print("1️⃣ Initializing GCP Vision Service...")
        vision_service = GCPVisionService()
        print("✅ GCP Vision Service initialized successfully")
        
        # Test with a simple test image (create a small test image)
        print("2️⃣ Creating test image...")
        from PIL import Image
        import io
        
        # Create a simple test image
        test_image = Image.new('RGB', (100, 100), color='red')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='JPEG')
        test_image_data = img_buffer.getvalue()
        
        print("3️⃣ Testing Vision API call...")
        result = vision_service.analyze_clothing_image(test_image_data)
        
        print("✅ Vision API call successful!")
        print(f"📊 Result keys: {list(result.keys())}")
        
        # Check for errors
        if 'error' in result:
            print(f"⚠️  Vision API error: {result['error']}")
        
        print(f"🎯 Extracted features: {result.get('extracted_features', [])}")
        print(f"🎨 Dominant colors: {result.get('dominant_colors', [])}")
        print(f"📝 Suggested category: {result.get('suggested_category', 'unknown')}")
        
        # Print raw analysis for debugging
        print(f"🔍 Raw analysis: {result.get('raw_analysis', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Vision service test: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_vision_service()
    exit(0 if success else 1)
