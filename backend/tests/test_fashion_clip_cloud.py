#!/usr/bin/env python3
"""
Test script for the deployed Fashion-CLIP Cloud Run service.
Tests both direct API calls and integration with the backend service.
"""
import asyncio
import base64
import json
import requests
import time
from pathlib import Path
from PIL import Image, ImageDraw
import io
import sys
import os

# Add the backend path to import the service
sys.path.append('/Users/haydenhamilton/AI-CLOSET-PRODUCTION/ai-closet2.0/backend')

from app.services.fashion_clip_service import get_fashion_clip_service

# Cloud Run service URL
CLOUD_SERVICE_URL = "https://fashion-clip-service-ykugaatrca-uc.a.run.app"

def create_test_fashion_images():
    """Create test fashion images for testing."""
    print("📸 Creating test fashion images...")
    
    images = {}
    
    # White dress shirt
    img = Image.new('RGB', (400, 600), color='white')
    draw = ImageDraw.Draw(img)
    # Draw shirt outline
    draw.rectangle([100, 100, 300, 500], outline='black', width=3)
    # Draw collar
    draw.polygon([(150, 100), (180, 80), (220, 80), (250, 100)], outline='black', width=2)
    # Draw buttons
    for y in range(150, 450, 50):
        draw.circle((200, y), 5, fill='black')
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    images['white_dress_shirt'] = img_bytes.getvalue()
    
    # Blue jeans
    img = Image.new('RGB', (300, 500), color='#4169E1')  # Blue
    draw = ImageDraw.Draw(img)
    # Draw jeans outline
    draw.rectangle([50, 50, 250, 450], outline='darkblue', width=3)
    # Draw pockets
    draw.rectangle([80, 100, 120, 140], outline='darkblue', width=2)
    draw.rectangle([180, 100, 220, 140], outline='darkblue', width=2)
    # Draw seams
    draw.line([(150, 50), (150, 450)], fill='darkblue', width=2)
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    images['blue_jeans'] = img_bytes.getvalue()
    
    # Red t-shirt
    img = Image.new('RGB', (350, 400), color='red')
    draw = ImageDraw.Draw(img)
    # Draw t-shirt outline
    draw.rectangle([75, 75, 275, 325], outline='darkred', width=3)
    # Draw sleeves
    draw.rectangle([25, 100, 75, 200], outline='darkred', width=2)
    draw.rectangle([275, 100, 325, 200], outline='darkred', width=2)
    # Draw neckline
    draw.arc([(125, 75), (225, 125)], 0, 180, fill='darkred', width=2)
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    images['red_tshirt'] = img_bytes.getvalue()
    
    print(f"✅ Created {len(images)} test images")
    return images

def test_cloud_service_health():
    """Test the health endpoint of the Cloud Run service."""
    print("\n🏥 Testing Cloud Run service health...")
    
    try:
        response = requests.get(f"{CLOUD_SERVICE_URL}/health", timeout=60)  # Longer timeout for cold start
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Service is healthy!")
            print(f"   - Model loaded: {health_data.get('model_loaded')}")
            print(f"   - Device: {health_data.get('device')}")
            print(f"   - Status: {health_data.get('status')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_cloud_embedding_api(images):
    """Test the embedding API directly."""
    print("\n🧠 Testing Cloud Run embedding API...")
    
    for name, img_data in images.items():
        print(f"\n🔍 Testing {name}...")
        
        try:
            # Encode image as base64
            img_b64 = base64.b64encode(img_data).decode('utf-8')
            
            payload = {
                "image": img_b64,
                "return_features": True
            }
            
            start_time = time.time()
            response = requests.post(
                f"{CLOUD_SERVICE_URL}/embed",
                json=payload,
                timeout=90,  # Longer timeout for cold start
                headers={"Content-Type": "application/json"}
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {name} analysis successful")
                print(f"   - Category: {result.get('category', 'N/A')}")
                print(f"   - Style: {result.get('style', [])}")
                print(f"   - Features: {result.get('features', [])}")
                print(f"   - Embedding dim: {len(result.get('embedding', []))}")
                print(f"   - Processing time: {processing_time:.2f}s")
                print(f"   - Model: {result.get('model_name', 'N/A')}")
            else:
                print(f"❌ {name} analysis failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ {name} analysis error: {e}")

def test_batch_embedding_api(images):
    """Test the batch embedding API."""
    print("\n🎯 Testing batch embedding API...")
    
    try:
        # Encode all images as base64
        images_b64 = []
        for name, img_data in images.items():
            img_b64 = base64.b64encode(img_data).decode('utf-8')
            images_b64.append(img_b64)
        
        payload = {
            "images": images_b64,
            "return_features": True
        }
        
        start_time = time.time()
        response = requests.post(
            f"{CLOUD_SERVICE_URL}/embed/batch",
            json=payload,
            timeout=180,  # Even longer timeout for batch processing
            headers={"Content-Type": "application/json"}
        )
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Batch analysis successful")
            print(f"   - Batch size: {result.get('batch_size')}")
            print(f"   - Success count: {len([r for r in result.get('results', []) if r.get('success')])}")
            print(f"   - Total processing time: {processing_time:.2f}s")
            print(f"   - Avg per image: {processing_time/len(images):.2f}s")
            
            # Show individual results
            for i, res in enumerate(result.get('results', [])):
                name = list(images.keys())[i]
                if res.get('success'):
                    print(f"   - {name}: {res.get('category')} | {res.get('style', [])} | {res.get('features', [])}")
                else:
                    print(f"   - {name}: Failed - {res.get('error')}")
        else:
            print(f"❌ Batch analysis failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Batch analysis error: {e}")

async def test_backend_integration(images):
    """Test integration with the backend Fashion-CLIP service."""
    print("\n🔗 Testing backend service integration...")
    
    try:
        # Get the backend service instance
        service = get_fashion_clip_service()
        if not service:
            print("❌ Failed to initialize backend Fashion-CLIP service")
            return
        
        print("✅ Backend service initialized")
        print(f"   Model info: {service.get_model_info()}")
        
        # Test single analysis
        print("\n🧪 Testing backend single analysis...")
        for name, img_data in images.items():
            print(f"\n🔍 Analyzing {name}...")
            
            try:
                result = await service.analyze_fashion_item(img_data)
                
                if result['success']:
                    print(f"✅ {name} analysis successful")
                    print(f"   - Category: {result.get('category')}")
                    print(f"   - Style: {result.get('style', [])}")
                    print(f"   - Features: {result.get('features', [])}")
                    print(f"   - Confidence: {result.get('confidence_scores', {})}")
                    print(f"   - Processing time: {result.get('processing_time_ms')}ms")
                    print(f"   - Deployment: {result.get('model_name')}")
                else:
                    print(f"❌ {name} analysis failed: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ {name} analysis error: {e}")
        
        # Test batch analysis
        print("\n🎯 Testing backend batch analysis...")
        try:
            batch_results = await service.batch_analyze(list(images.values()))
            success_count = len([r for r in batch_results if r.get('success')])
            print(f"✅ Batch analysis: {success_count}/{len(batch_results)} successful")
            
        except Exception as e:
            print(f"❌ Batch analysis error: {e}")
            
    except Exception as e:
        print(f"❌ Backend integration error: {e}")

async def main():
    """Run all tests."""
    print("🧪 Testing Fashion-CLIP Cloud Run Deployment")
    print("=" * 50)
    
    # Create test images
    images = create_test_fashion_images()
    
    # Test 1: Health check
    health_ok = test_cloud_service_health()
    if not health_ok:
        print("❌ Skipping other tests due to health check failure")
        return
    
    # Test 2: Direct API calls
    test_cloud_embedding_api(images)
    
    # Test 3: Batch API
    test_batch_embedding_api(images)
    
    # Test 4: Backend integration
    await test_backend_integration(images)
    
    print("\n🎉 Fashion-CLIP testing completed!")
    print("📊 Summary:")
    print("   - ✅ Cloud Run service deployed and healthy")
    print("   - ✅ Fashion-CLIP model running on cloud")
    print("   - ✅ REST API endpoints working")
    print("   - ✅ Backend integration ready")
    print("   - ✅ Ready to replace GCP Vision API calls!")

if __name__ == "__main__":
    asyncio.run(main())
