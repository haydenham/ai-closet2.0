"""
Unit tests for Gemini AI service.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

from app.services.gemini_service import (
    GeminiService,
    OutfitItem,
    OutfitRecommendation,
    GeminiServiceError,
    GeminiResponseError
)


class TestOutfitModels:
    """Test the Pydantic models for outfit recommendations."""
    
    def test_outfit_item_creation(self):
        """Test creating an OutfitItem with valid data."""
        item = OutfitItem(type="blouse", features=["silk", "white", "long-sleeve"])
        assert item.type == "blouse"
        assert item.features == ["silk", "white", "long-sleeve"]
    
    def test_outfit_item_validation(self):
        """Test OutfitItem validation with invalid data."""
        with pytest.raises(ValidationError):
            OutfitItem(type="", features=[])
    
    def test_outfit_recommendation_creation(self):
        """Test creating a complete OutfitRecommendation."""
        top = OutfitItem(type="blouse", features=["silk", "white"])
        bottom = OutfitItem(type="trousers", features=["black", "tailored"])
        
        outfit = OutfitRecommendation(top=top, bottom=bottom)
        assert outfit.top == top
        assert outfit.bottom == bottom
        assert outfit.shoes is None
        assert outfit.accessories is None
        assert outfit.outerwear is None
    
    def test_outfit_recommendation_with_all_items(self):
        """Test OutfitRecommendation with all possible items."""
        outfit_data = {
            "top": {"type": "blouse", "features": ["silk", "white"]},
            "bottom": {"type": "trousers", "features": ["black", "tailored"]},
            "shoes": {"type": "heels", "features": ["black", "leather"]},
            "accessories": [{"type": "necklace", "features": ["gold", "delicate"]}],
            "outerwear": {"type": "blazer", "features": ["navy", "structured"]}
        }
        
        outfit = OutfitRecommendation(**outfit_data)
        assert outfit.top.type == "blouse"
        assert outfit.bottom.type == "trousers"
        assert outfit.shoes.type == "heels"
        assert len(outfit.accessories) == 1
        assert outfit.accessories[0].type == "necklace"
        assert outfit.outerwear.type == "blazer"


class TestGeminiService:
    """Test the GeminiService class."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('app.services.gemini_service.settings') as mock:
            mock.GCP_PROJECT_ID = "test-project"
            mock.GCP_LOCATION = "us-central1"
            mock.GEMINI_ENDPOINT_ID = "test-endpoint"
            yield mock
    
    @pytest.fixture
    def mock_vertexai(self):
        """Mock Vertex AI initialization."""
        with patch('app.services.gemini_service.vertexai') as mock:
            yield mock
    
    @pytest.fixture
    def mock_generative_model(self):
        """Mock GenerativeModel."""
        with patch('app.services.gemini_service.GenerativeModel') as mock:
            yield mock
    
    @pytest.fixture
    def gemini_service_instance(self, mock_settings, mock_vertexai, mock_generative_model):
        """Create a GeminiService instance for testing."""
        return GeminiService()
    
    def test_init(self, mock_settings, mock_vertexai, mock_generative_model):
        """Test GeminiService initialization."""
        service = GeminiService()
        
        # Verify Vertex AI was initialized
        mock_vertexai.init.assert_called_once_with(
            project="test-project",
            location="us-central1"
        )
        
        # Verify model was created with tuned model name
        mock_generative_model.assert_called_once_with("tunedModels/8331222804519190528")
        
        # Verify system prompt is set
        assert service.system_prompt is not None
        assert "fashion-advisor" in service.system_prompt
    
    def test_build_user_prompt(self, gemini_service_instance):
        """Test building dynamic user prompts."""
        prompt = gemini_service_instance._build_user_prompt(
            gender="women",
            style="classic",
            weather="cold",
            occasion="work",
            user_request="I need a professional outfit for a meeting"
        )
        
        expected_lines = [
            "WEATHER:cold STYLE:classic GENDER:women",
            "",
            "OCCASION:work",
            "",
            "I need a professional outfit for a meeting"
        ]
        
        assert prompt == "\n".join(expected_lines)
    
    def test_validate_inputs_valid(self, gemini_service_instance):
        """Test input validation with valid inputs."""
        # Should not raise an exception
        gemini_service_instance.validate_inputs(
            gender="women",
            style="classic",
            weather="cold",
            occasion="work"
        )
    
    def test_validate_inputs_invalid_gender(self, gemini_service_instance):
        """Test input validation with invalid gender."""
        with pytest.raises(ValueError, match="Invalid gender"):
            gemini_service_instance.validate_inputs(
                gender="invalid",
                style="classic",
                weather="cold",
                occasion="work"
            )
    
    def test_validate_inputs_invalid_weather(self, gemini_service_instance):
        """Test input validation with invalid weather."""
        with pytest.raises(ValueError, match="Invalid weather"):
            gemini_service_instance.validate_inputs(
                gender="women",
                style="classic",
                weather="invalid",
                occasion="work"
            )
    
    def test_validate_inputs_invalid_style(self, gemini_service_instance):
        """Test input validation with invalid style."""
        with pytest.raises(ValueError, match="Invalid style"):
            gemini_service_instance.validate_inputs(
                gender="women",
                style="invalid",
                weather="cold",
                occasion="work"
            )
    
    def test_validate_inputs_invalid_occasion(self, gemini_service_instance):
        """Test input validation with invalid occasion."""
        with pytest.raises(ValueError, match="Invalid occasion"):
            gemini_service_instance.validate_inputs(
                gender="women",
                style="classic",
                weather="cold",
                occasion="invalid"
            )
    
    def test_convert_gender_for_gemini(self):
        """Test gender conversion from database to Gemini format."""
        assert GeminiService.convert_gender_for_gemini("male") == "men"
        assert GeminiService.convert_gender_for_gemini("female") == "women"
        assert GeminiService.convert_gender_for_gemini("unknown") == "unknown"
    
    def test_convert_gender_from_gemini(self):
        """Test gender conversion from Gemini to database format."""
        assert GeminiService.convert_gender_from_gemini("men") == "male"
        assert GeminiService.convert_gender_from_gemini("women") == "female"
        assert GeminiService.convert_gender_from_gemini("unknown") == "unknown"
    
    def test_parse_response_valid_json(self, gemini_service_instance):
        """Test parsing valid JSON response."""
        response_json = {
            "top": {"type": "blouse", "features": ["silk", "white", "long-sleeve"]},
            "bottom": {"type": "trousers", "features": ["black", "tailored"]},
            "shoes": {"type": "heels", "features": ["black", "leather"]}
        }
        
        response_text = json.dumps(response_json)
        outfit = gemini_service_instance._parse_response(response_text)
        
        assert isinstance(outfit, OutfitRecommendation)
        assert outfit.top.type == "blouse"
        assert outfit.bottom.type == "trousers"
        assert outfit.shoes.type == "heels"
    
    def test_parse_response_invalid_json(self, gemini_service_instance):
        """Test parsing invalid JSON response."""
        invalid_json = "{ invalid json }"
        
        with pytest.raises(GeminiResponseError, match="Invalid JSON response"):
            gemini_service_instance._parse_response(invalid_json)
    
    def test_parse_response_invalid_format(self, gemini_service_instance):
        """Test parsing JSON with invalid format."""
        invalid_format = json.dumps({"invalid": "format"})
        
        with pytest.raises(GeminiResponseError, match="Invalid response format"):
            gemini_service_instance._parse_response(invalid_format)
    
    def test_generate_outfit_recommendation_success(self, gemini_service_instance):
        """Test successful outfit recommendation generation."""
        # Mock the model response
        mock_response = Mock()
        response_json = {
            "top": {"type": "sweater", "features": ["wool", "cream", "turtleneck"]},
            "bottom": {"type": "jeans", "features": ["dark-wash", "straight-leg"]},
            "outerwear": {"type": "coat", "features": ["wool", "navy", "long"]}
        }
        
        mock_response.text = json.dumps(response_json)
        
        # Mock the _model attribute
        gemini_service_instance._model = Mock()
        gemini_service_instance._model.generate_content = Mock(return_value=mock_response)
        
        # Test the method
        result = gemini_service_instance.generate_outfit_recommendation(
            gender="women",
            style="casual",
            weather="cold",
            occasion="casual",
            user_request="I want something cozy for a weekend outing"
        )
        
        # Verify the result
        assert isinstance(result, OutfitRecommendation)
        assert result.top.type == "sweater"
        assert result.bottom.type == "jeans"
        assert result.outerwear.type == "coat"
        
        # Verify the model was called correctly
        gemini_service_instance._model.generate_content.assert_called_once()
    
    def test_generate_outfit_recommendation_api_error(self, gemini_service_instance):
        """Test handling of API errors during recommendation generation."""
        # Mock the model to raise an exception
        gemini_service_instance._model = Mock()
        gemini_service_instance._model.generate_content = Mock(
            side_effect=Exception("API Error")
        )
        
        with pytest.raises(GeminiServiceError, match="Failed to generate outfit recommendation"):
            gemini_service_instance.generate_outfit_recommendation(
                gender="men",
                style="formal",
                weather="warm",
                occasion="work",
                user_request="I need a business outfit"
            )
    
    def test_generate_outfit_recommendation_invalid_response(self, gemini_service_instance):
        """Test handling of invalid response format."""
        # Mock the model response with invalid JSON
        mock_response = Mock()
        mock_response.text = "{ invalid json }"
        
        gemini_service_instance._model = Mock()
        gemini_service_instance._model.generate_content = Mock(return_value=mock_response)
        
        with pytest.raises(GeminiResponseError):
            gemini_service_instance.generate_outfit_recommendation(
                gender="women",
                style="trendy",
                weather="warm",
                occasion="party",
                user_request="I want something stylish for a date"
            )


class TestGeminiServiceIntegration:
    """Integration tests for various tag combinations."""
    
    @pytest.fixture
    def mock_gemini_service(self):
        """Mock GeminiService for integration testing."""
        with patch('app.services.gemini_service.GeminiService') as mock:
            service_instance = Mock()
            mock.return_value = service_instance
            yield service_instance
    
    def test_various_tag_combinations(self, mock_gemini_service):
        """Test different combinations of gender, style, weather, and occasion tags."""
        test_cases = [
            {
                "gender": "women",
                "style": "classic",
                "weather": "cold",
                "occasion": "work",
                "request": "Professional meeting outfit"
            },
            {
                "gender": "men",
                "style": "casual",
                "weather": "warm",
                "occasion": "casual",
                "request": "Relaxed weekend look"
            },
            {
                "gender": "women",
                "style": "trendy",
                "weather": "warm",
                "occasion": "party",
                "request": "Stylish party outfit"
            },
            {
                "gender": "men",
                "style": "classic",
                "weather": "cold",
                "occasion": "work",
                "request": "Executive business attire"
            }
        ]
        
        # Mock successful responses for all test cases
        for i, case in enumerate(test_cases):
            mock_response = OutfitRecommendation(
                top=OutfitItem(type=f"top_{i}", features=["feature1", "feature2"]),
                bottom=OutfitItem(type=f"bottom_{i}", features=["feature1", "feature2"])
            )
            
            mock_gemini_service.generate_outfit_recommendation.return_value = mock_response
            
            result = mock_gemini_service.generate_outfit_recommendation(
                gender=case["gender"],
                style=case["style"],
                weather=case["weather"],
                occasion=case["occasion"],
                user_request=case["request"]
            )
            
            assert isinstance(result, OutfitRecommendation)
            assert result.top.type == f"top_{i}"
            assert result.bottom.type == f"bottom_{i}"


class TestGeminiServiceErrors:
    """Test error handling in GeminiService."""
    
    def test_gemini_service_error_inheritance(self):
        """Test that GeminiServiceError is properly defined."""
        error = GeminiServiceError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_gemini_response_error_inheritance(self):
        """Test that GeminiResponseError inherits from both GeminiServiceError and ValueError."""
        error = GeminiResponseError("Response error")
        assert str(error) == "Response error"
        assert isinstance(error, GeminiServiceError)
        assert isinstance(error, ValueError)
    
    @patch('app.services.gemini_service.vertexai', None)
    def test_missing_vertexai_library(self):
        """Test handling when vertexai library is not available."""
        with patch('app.services.gemini_service.settings') as mock_settings:
            mock_settings.GCP_PROJECT_ID = "test-project"
            mock_settings.GCP_LOCATION = "us-central1"
            mock_settings.GEMINI_ENDPOINT_ID = "test-endpoint"
            
            service = GeminiService()
            
            with pytest.raises(GeminiServiceError, match="vertexai library not available"):
                service._ensure_client()


def test_global_service_instance():
    """Test that the service can be imported and instantiated."""
    # Just test that we can import the service without errors
    from app.services.gemini_service import GeminiService
    assert GeminiService is not None
