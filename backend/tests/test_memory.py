#!/usr/bin/env python3
"""
Quick memory test for the updated Fashion-CLIP service.
"""
import requests
import base64
import json
from PIL import Image, ImageDraw
import io

# Create a test image
img = Image.new('RGB', (400, 600), color='white')
draw = ImageDraw.Draw(img)
draw.rectangle([100, 100, 300, 500], outline='black', width=3)

img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_data = img_bytes.getvalue()

# Test the service
print("🧪 Testing memory-optimized Fashion-CLIP service...")

img_b64 = base64.b64encode(img_data).decode('utf-8')
payload = {
    "image": img_b64,
    "return_features": True
}

try:
    response = requests.post(
        "https://fashion-clip-service-ykugaatrca-uc.a.run.app/embed",
        json=payload,
        timeout=90,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Memory test successful!")
        print(f"   - Category: {result.get('category')}")
        print(f"   - Style: {result.get('style', [])}")
        print(f"   - Features: {result.get('features', [])}")
        print(f"   - Model: {result.get('model_name')}")
        print(f"   - Processing time: {result.get('processing_time_ms')}ms")
    else:
        print(f"❌ Test failed: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Test error: {e}")

print("\n🔍 Check Cloud Run logs for memory usage...")
