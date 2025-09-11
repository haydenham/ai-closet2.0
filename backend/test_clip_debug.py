#!/usr/bin/env python3
"""
Debug script for CLIP classification issues
"""
import asyncio
import logging
from app.services.fashion_clip_service import FashionCLIPService
from PIL import Image, ImageDraw
import io

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_clip():
    print("🔍 Debugging CLIP Classification...")
    
    # Initialize service
    service = FashionCLIPService()
    print("✅ Service initialized")
    
    # Create a simple test image
    img = Image.new('RGB', (224, 224), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 174, 174], fill='blue')
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    
    print(f"📋 Available categories: {len(service.clothing_categories)}")
    print(f"   First 5: {service.clothing_categories[:5]}")
    
    print(f"📋 Available styles: {len(service.style_descriptors)}")
    print(f"   First 5: {service.style_descriptors[:5]}")
    
    print(f"📋 Available features: {len(service.fabric_textures)}")
    print(f"   First 5: {service.fabric_textures[:5]}")
    
    # Test classification directly
    print("\n🧪 Testing direct classification...")
    
    try:
        # Test category classification
        image = Image.open(io.BytesIO(img_bytes))
        category = service._classify_category(image)
        print(f"✅ Category: {category}")
        
        # Test style analysis
        styles = service._analyze_style(image)
        print(f"✅ Styles: {styles}")
        
        # Test feature detection
        features = service._detect_features(image)
        print(f"✅ Features: {features}")
        
    except Exception as e:
        print(f"❌ Direct classification error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test full analysis
    print("\n🧪 Testing full analysis...")
    try:
        result = await service.analyze_fashion_item(img_bytes)
        print(f"✅ Full analysis result: {result}")
    except Exception as e:
        print(f"❌ Full analysis error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_clip())
