#!/usr/bin/env python3
"""
Test script for the Hybrid Fashion Service
Tests the integration of Fashion-CLIP and GCP Vision services
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_hybrid_service():
    """Test the hybrid fashion service with a sample image."""
    try:
        from app.services.hybrid_fashion_service import get_hybrid_fashion_service
        
        # Initialize the service
        print("🔄 Initializing Hybrid Fashion Service...")
        service = get_hybrid_fashion_service()
        
        if not service:
            print("❌ Failed to initialize hybrid service")
            return
        
        # Check service status
        print("\n📊 Service Status:")
        status = service.get_service_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        if not status.get('hybrid_ready'):
            print("❌ Hybrid service not ready - no underlying services available")
            return
        
        # Test with a sample image (you can replace this with an actual image file)
        sample_image_path = "/Users/haydenhamilton/AI-CLOSET-PRODUCTION/ai-closet2.0/backend/test_images/sample_shirt.jpg"
        
        # If no test image exists, create a small test image
        if os.path.exists(sample_image_path):
            with open(sample_image_path, 'rb') as f:
                image_data = f.read()
                print(f"📷 Using test image: {sample_image_path}")
        else:
            print("📁 No test image found, using placeholder...")
            # Create a minimal test image data (this won't work for real analysis but tests the pipeline)
            image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Test comprehensive analysis
        print("\n🔍 Running comprehensive analysis...")
        start_time = asyncio.get_event_loop().time()
        
        result = await service.analyze_clothing_item(image_data)
        
        end_time = asyncio.get_event_loop().time()
        total_time = int((end_time - start_time) * 1000)
        
        print(f"\n📈 Analysis Results (took {total_time}ms):")
        print(f"  Success: {result.get('success')}")
        print(f"  Sources: {result.get('analysis_sources', [])}")
        print(f"  Category: {result.get('category')}")
        print(f"  Style: {result.get('style', [])}")
        print(f"  Features: {result.get('features', [])}")
        
        # Colors
        colors = result.get('colors', {})
        if colors:
            print(f"  Primary Color: {colors.get('primary_color')}")
            color_percentages = colors.get('color_percentages', {})
            if color_percentages:
                print(f"  Color Breakdown: {dict(list(color_percentages.items())[:3])}")
        
        # Brands
        brands = result.get('brands', {})
        detected_brands = brands.get('detected_brands', [])
        if detected_brands:
            print(f"  Detected Brands: {[b.get('brand') for b in detected_brands[:3]]}")
        
        # Enhanced analysis
        enhanced = result.get('enhanced_analysis', {})
        if enhanced:
            print(f"  Enhanced Analysis:")
            for key, value in enhanced.items():
                print(f"    {key}: {value}")
        
        # Embedding test
        print(f"  Has Embedding: {result.get('has_embedding', False)}")
        
        # Errors
        errors = result.get('errors', [])
        if errors:
            print(f"  Errors: {errors}")
        
        # Test embedding generation separately
        if status.get('fashion_clip_available'):
            print("\n🎯 Testing embedding generation...")
            embedding = await service.get_embedding_only(image_data)
            if embedding:
                print(f"  Embedding length: {len(embedding)}")
                print(f"  First 5 values: {embedding[:5]}")
            else:
                print("  No embedding generated")
        
        print(f"\n✅ Hybrid service test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_individual_services():
    """Test individual services to diagnose issues."""
    print("\n🔧 Testing Individual Services:")
    
    # Test Fashion-CLIP service
    try:
        from app.services.fashion_clip_service import get_fashion_clip_service
        fashion_service = get_fashion_clip_service()
        if fashion_service:
            print("  ✅ Fashion-CLIP service available")
            model_info = fashion_service.get_model_info()
            print(f"     Model: {model_info.get('model_name')}")
            print(f"     Status: {model_info.get('status')}")
        else:
            print("  ❌ Fashion-CLIP service not available")
    except Exception as e:
        print(f"  ❌ Fashion-CLIP service error: {str(e)}")
    
    # Test GCP service
    try:
        from app.services.gcp_color_brand_service import get_gcp_color_brand_service
        gcp_service = get_gcp_color_brand_service()
        if gcp_service:
            print("  ✅ GCP Color & Brand service available")
        else:
            print("  ❌ GCP Color & Brand service not available")
    except Exception as e:
        print(f"  ❌ GCP Color & Brand service error: {str(e)}")

if __name__ == "__main__":
    print("🧪 Hybrid Fashion Service Test")
    print("=" * 50)
    
    # Test individual services first
    asyncio.run(test_individual_services())
    
    # Test hybrid service
    asyncio.run(test_hybrid_service())
