#!/usr/bin/env python3
"""
Manual test script for Gemini service integration.
Run this script after setting up GCP credentials to test the Gemini API.

Usage:
    python test_gemini_manual.py
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.gemini_service import gemini_service


async def test_gemini_service():
    """Test the Gemini service with various scenarios."""
    
    print("🧪 Testing Gemini Service Integration")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Professional Women's Outfit",
            "gender": "women",
            "style": "classic",
            "weather": "cold",
            "occasion": "work",
            "request": "I need a professional outfit for an important client meeting"
        },
        {
            "name": "Casual Men's Weekend Look",
            "gender": "men",
            "style": "casual",
            "weather": "warm",
            "occasion": "weekend",
            "request": "Something comfortable for a weekend brunch with friends"
        },
        {
            "name": "Trendy Date Night Outfit",
            "gender": "women",
            "style": "trendy",
            "weather": "mild",
            "occasion": "date",
            "request": "A stylish outfit for dinner at a nice restaurant"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            # Test input validation first
            print("✓ Validating inputs...")
            gemini_service.validate_inputs(
                gender=test_case["gender"],
                style=test_case["style"],
                weather=test_case["weather"],
                occasion=test_case["occasion"]
            )
            
            # Generate recommendation
            print("🤖 Calling Gemini API...")
            result = await gemini_service.generate_outfit_recommendation(
                gender=test_case["gender"],
                style=test_case["style"],
                weather=test_case["weather"],
                occasion=test_case["occasion"],
                user_request=test_case["request"]
            )
            
            # Display results
            print("✅ Success! Recommendation received:")
            print(f"   Request: {test_case['request']}")
            print(f"   Context: {test_case['gender']} | {test_case['style']} | {test_case['weather']} | {test_case['occasion']}")
            
            if result.top:
                print(f"   👔 Top: {result.top.type} - {', '.join(result.top.features)}")
            if result.bottom:
                print(f"   👖 Bottom: {result.bottom.type} - {', '.join(result.bottom.features)}")
            if result.shoes:
                print(f"   👠 Shoes: {result.shoes.type} - {', '.join(result.shoes.features)}")
            if result.outerwear:
                print(f"   🧥 Outerwear: {result.outerwear.type} - {', '.join(result.outerwear.features)}")
            if result.accessories:
                for acc in result.accessories:
                    print(f"   💍 Accessory: {acc.type} - {', '.join(acc.features)}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {success_count}/{len(test_cases)} tests passed")
    
    if success_count == len(test_cases):
        print("🎉 All tests passed! Gemini integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check your GCP credentials and endpoint configuration.")
        return False


async def test_configuration():
    """Test the configuration setup."""
    print("🔧 Testing Configuration")
    print("-" * 30)
    
    try:
        from app.core.config import settings
        
        print(f"✓ GCP Project ID: {settings.GCP_PROJECT_ID}")
        print(f"✓ GCP Location: {settings.GCP_LOCATION}")
        print(f"✓ Gemini Endpoint ID: {settings.GEMINI_ENDPOINT_ID}")
        
        if not settings.GCP_PROJECT_ID:
            print("❌ GCP_PROJECT_ID is not set")
            return False
        
        if not settings.GEMINI_ENDPOINT_ID:
            print("❌ GEMINI_ENDPOINT_ID is not set")
            return False
        
        print("✅ Configuration looks good!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        return False


async def main():
    """Main test function."""
    print("🚀 Gemini Service Manual Test")
    print("=" * 50)
    
    # Test configuration first
    config_ok = await test_configuration()
    if not config_ok:
        print("\n❌ Configuration test failed. Please check your settings.")
        return
    
    # Test the service
    service_ok = await test_gemini_service()
    
    if service_ok:
        print("\n🎉 All tests completed successfully!")
        print("The Gemini service is ready for production use.")
    else:
        print("\n⚠️  Some tests failed.")
        print("Please check your GCP credentials and try again.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        print(f"Error type: {type(e).__name__}")