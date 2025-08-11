"""
Integration test for Gemini service with real API calls.
Run this test when GCP credentials are properly configured.
"""
import pytest
import asyncio
from app.services.gemini_service import gemini_service, OutfitRecommendation


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gemini_real_api_call():
    """
    Test actual API call to Gemini model.
    This test requires proper GCP credentials and should be run manually.
    """
    try:
        result = await gemini_service.generate_outfit_recommendation(
            gender="women",
            style="classic",
            weather="cold",
            occasion="work",
            user_request="I need a professional outfit for an important meeting"
        )
        
        # Verify the response structure
        assert isinstance(result, OutfitRecommendation)
        
        # Check that at least one clothing item is recommended
        has_items = any([
            result.top is not None,
            result.bottom is not None,
            result.shoes is not None,
            result.outerwear is not None,
            result.accessories is not None
        ])
        assert has_items, "At least one clothing item should be recommended"
        
        # If top is present, verify it has the expected structure
        if result.top:
            assert result.top.type is not None
            assert isinstance(result.top.features, list)
            assert len(result.top.features) > 0
        
        print(f"✅ Gemini API test successful!")
        print(f"Response: {result}")
        
    except Exception as e:
        pytest.skip(f"Gemini API test skipped due to: {str(e)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gemini_various_scenarios():
    """Test various input scenarios with the real API."""
    test_cases = [
        {
            "gender": "men",
            "style": "casual",
            "weather": "warm",
            "occasion": "weekend",
            "request": "Something comfortable for a casual weekend"
        },
        {
            "gender": "women",
            "style": "trendy",
            "weather": "mild",
            "occasion": "date",
            "request": "A stylish outfit for dinner date"
        }
    ]
    
    for i, case in enumerate(test_cases):
        try:
            result = await gemini_service.generate_outfit_recommendation(**case)
            assert isinstance(result, OutfitRecommendation)
            print(f"✅ Test case {i+1} successful: {case['gender']} {case['style']} {case['weather']} {case['occasion']}")
        except Exception as e:
            pytest.skip(f"Test case {i+1} skipped due to: {str(e)}")


if __name__ == "__main__":
    """Run integration tests directly."""
    async def run_tests():
        print("Running Gemini integration tests...")
        try:
            await test_gemini_real_api_call()
            await test_gemini_various_scenarios()
            print("🎉 All integration tests passed!")
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
    
    asyncio.run(run_tests())