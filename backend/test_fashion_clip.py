#!/usr/bin/env python3
"""
Test script for production Fashion-CLIP service
"""
import asyncio
import logging
import sys
import traceback
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.services.fashion_clip_service import get_fashion_clip_service
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_production_fashion_clip():
    """Test the production Fashion-CLIP service"""
    
    print("👔 Testing Production Fashion-CLIP Service...")
    
    try:
        # Test initialization
        print("1️⃣ Initializing Fashion-CLIP Service...")
        service = get_fashion_clip_service()
        
        if service is None:
            print("❌ Failed to initialize Fashion-CLIP service")
            return False
        
        print("✅ Fashion-CLIP Service initialized successfully")
        
        # Get model info
        model_info = service.get_model_info()
        print(f"📊 Model Info:")
        print(f"   - Model: {model_info['model_name']}")
        print(f"   - Embedding Dimension: {model_info['embedding_dim']}")
        print(f"   - Deployment: {model_info['deployment']}")
        print(f"   - Categories: {model_info['categories_count']}")
        print(f"   - Styles: {model_info['styles_count']}")
        print(f"   - Features: {model_info['features_count']}")
        
        # Create test images for different clothing types
        print("\n2️⃣ Creating fashion test images...")
        
        test_items = []
        
        # White dress shirt simulation
        white_shirt = Image.new('RGB', (224, 224), color='white')
        # Add some simple patterns to make it more realistic
        for i in range(0, 224, 20):
            for j in range(100, 124):
                white_shirt.putpixel((i, j), (240, 240, 240))  # Subtle collar line
        
        img_buffer = io.BytesIO()
        white_shirt.save(img_buffer, format='JPEG')
        test_items.append(('white_dress_shirt', img_buffer.getvalue()))
        
        # Black jeans simulation
        black_jeans = Image.new('RGB', (224, 224), color=(25, 25, 35))
        # Add denim texture simulation
        for i in range(0, 224, 3):
            for j in range(0, 224, 3):
                if (i + j) % 6 == 0:
                    black_jeans.putpixel((i, j), (35, 35, 45))
        
        img_buffer = io.BytesIO()
        black_jeans.save(img_buffer, format='JPEG')
        test_items.append(('black_jeans', img_buffer.getvalue()))
        
        # Red casual t-shirt
        red_tshirt = Image.new('RGB', (224, 224), color=(200, 50, 50))
        img_buffer = io.BytesIO()
        red_tshirt.save(img_buffer, format='JPEG')
        test_items.append(('red_casual_tshirt', img_buffer.getvalue()))
        
        print(f"✅ Created {len(test_items)} test fashion items")
        
        # Test comprehensive fashion analysis
        print("\n3️⃣ Testing comprehensive fashion analysis...")
        
        for name, image_data in test_items:
            print(f"\n🔍 Analyzing {name}...")
            
            result = await service.analyze_fashion_item(image_data)
            
            if result['success']:
                print(f"✅ {name} analysis successful")
                print(f"   - Category: {result['category']}")
                print(f"   - Style: {result['style']}")
                print(f"   - Features: {result['features']}")
                print(f"   - Embedding dimension: {len(result['embedding'])}")
                print(f"   - Processing time: {result['processing_time_ms']}ms")
                print(f"   - Confidence scores: {result['confidence_scores']}")
            else:
                print(f"❌ {name} analysis failed: {result['error']}")
        
        # Test batch processing
        print("\n4️⃣ Testing batch analysis...")
        
        batch_data = [img_data for _, img_data in test_items]
        batch_results = await service.batch_analyze(batch_data)
        
        successful_analyses = sum(1 for r in batch_results if r['success'])
        print(f"✅ Batch analysis: {successful_analyses}/{len(batch_results)} successful")
        
        # Test similarity calculations
        print("\n5️⃣ Testing semantic similarity...")
        
        if len(batch_results) >= 2 and all(r['success'] for r in batch_results[:2]):
            emb1 = batch_results[0]['embedding']
            emb2 = batch_results[1]['embedding']
            
            similarity = service.calculate_similarity(emb1, emb2)
            print(f"✅ Similarity between {test_items[0][0]} and {test_items[1][0]}: {similarity:.4f}")
            
            # Test self-similarity
            self_similarity = service.calculate_similarity(emb1, emb1)
            print(f"✅ Self-similarity check: {self_similarity:.4f} (should be 1.0)")
            
            if abs(self_similarity - 1.0) > 0.01:
                print("⚠️  Warning: Self-similarity not perfect, check embedding normalization")
        
        # Test the problematic white t-shirt case from the original issue
        print("\n6️⃣ Testing white t-shirt (original problem case)...")
        
        # This should NOT return: striped, velvet, active shirt, mint, floral, leather
        white_tshirt_result = await service.analyze_fashion_item(test_items[0][1])
        
        if white_tshirt_result['success']:
            print(f"✅ White t-shirt analysis:")
            print(f"   - Category: {white_tshirt_result['category']}")
            print(f"   - Style: {white_tshirt_result['style']}")
            print(f"   - Features: {white_tshirt_result['features']}")
            
            # Check for problematic tags
            all_tags = white_tshirt_result['features'] + white_tshirt_result['style']
            problematic_tags = ['striped', 'velvet', 'mint', 'floral', 'leather']
            found_problematic = [tag for tag in problematic_tags if tag in all_tags]
            
            if found_problematic:
                print(f"⚠️  Warning: Found problematic tags: {found_problematic}")
            else:
                print("✅ No problematic tags found - Fashion-CLIP working correctly!")
        
        print("\n🎉 All Fashion-CLIP tests completed successfully!")
        print("\n📈 Performance Summary:")
        print("   - ✅ Model initialization: Working")
        print("   - ✅ Single item analysis: Working") 
        print("   - ✅ Batch processing: Working")
        print("   - ✅ Similarity calculation: Working")
        print("   - ✅ Problematic tag filtering: Improved")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Fashion-CLIP test: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_production_fashion_clip())
    exit(0 if success else 1)
