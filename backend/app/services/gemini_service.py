"""
Gemini AI service for generating fashion recommendations using Vertex AI.
"""
import json
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ValidationError
from vertexai.generative_models import GenerativeModel
import vertexai

from app.core.config import settings

logger = logging.getLogger(__name__)


class OutfitItem(BaseModel):
    """Model for individual outfit items in the response."""
    type: str
    features: List[str]


class OutfitRecommendation(BaseModel):
    """Model for the complete outfit recommendation response."""
    top: Optional[OutfitItem] = None
    bottom: Optional[OutfitItem] = None
    shoes: Optional[OutfitItem] = None
    accessories: Optional[List[OutfitItem]] = None
    outerwear: Optional[OutfitItem] = None


class GeminiServiceError(Exception):
    """Base exception for Gemini service errors"""


class GeminiResponseError(GeminiServiceError, ValueError):
    """Raised when the model response is invalid or cannot be parsed (also a ValueError for test expectations)"""


class GeminiService:
    """Service for interacting with Gemini model via Vertex AI."""

    
    def __init__(self):
        """Initialize the Gemini service with Vertex AI configuration."""
        self.project_id = settings.GCP_PROJECT_ID
        self.location = settings.GCP_LOCATION
        self.endpoint_id = settings.GEMINI_ENDPOINT_ID
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        
        # Try the tuned model first, fallback to endpoint if needed
        try:
            # Use the tuned model format we discovered from the tuning job details
            self.model = GenerativeModel(model_name="tunedModels/8331222804519190528")
            logger.info("Initialized with tuned model: tunedModels/8331222804519190528")
        except Exception as e:
            logger.warning(f"Failed to initialize tuned model: {e}")
            # Fallback to endpoint approach
            try:
                self.model = GenerativeModel(
                    model_name=f"projects/{self.project_id}/locations/{self.location}/endpoints/{self.endpoint_id}"
                )
                logger.info(f"Initialized with endpoint: {self.endpoint_id}")
            except Exception as e2:
                logger.error(f"Failed to initialize with endpoint: {e2}")
                raise GeminiServiceError(f"Failed to initialize Gemini model: {e2}")
        
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the fashion advisor."""
        return """You are a fashion-advisor assistant that provides personalized outfit recommendations based on user preferences and context.

Your task is to analyze the user's request including their gender, style preferences, weather conditions, and occasion, then recommend a complete outfit.

You must respond with a valid JSON object in the following format:
{
    "top": {"type": "item_type", "features": ["feature1", "feature2", "feature3"]},
    "bottom": {"type": "item_type", "features": ["feature1", "feature2", "feature3"]},
    "shoes": {"type": "item_type", "features": ["feature1", "feature2", "feature3"]},
    "accessories": [{"type": "item_type", "features": ["feature1", "feature2"]}],
    "outerwear": {"type": "item_type", "features": ["feature1", "feature2", "feature3"]}
}

Guidelines:
- Include only relevant clothing categories for the outfit
- Features should be descriptive (colors, patterns, materials, styles)
- Consider weather appropriateness
- Match the user's style preferences
- Ensure gender-appropriate recommendations
- Focus on practical, wearable combinations"""

    def _build_user_prompt(
        self,
        gender: str,
        style: str,
        weather: str,
        occasion: str,
        user_request: str
    ) -> str:
        """Build the dynamic user prompt with context tags."""
        prompt_parts = [
            f"GENDER:{gender}",
            f"STYLE:{style}",
            f"WEATHER:{weather}",
            f"OCCASION:{occasion}",
            "",
            user_request
        ]
        return "\n".join(prompt_parts)
    
    async def generate_outfit_recommendation(
        self,
        gender: str,
        style: str,
        weather: str,
        occasion: str,
        user_request: str
    ) -> OutfitRecommendation:
        """
        Generate outfit recommendation using Gemini model.
        
        Args:
            gender: User's gender (male/female)
            style: User's style preference (classic, casual, trendy, etc.)
            weather: Weather condition (hot/cold)
            occasion: Occasion type (work, party, casual, etc.)
            user_request: User's specific request or prompt
            
        Returns:
            OutfitRecommendation object with structured outfit data
            
        Raises:
            ValueError: If the model response is invalid
            Exception: If the API call fails
        """
        try:
            # Build the dynamic user prompt
            user_prompt = self._build_user_prompt(
                gender=gender,
                style=style,
                weather=weather,
                occasion=occasion,
                user_request=user_request
            )
            
            logger.info(f"Generating outfit recommendation with prompt: {user_prompt[:100]}...")
            
            # Combine system prompt with user prompt
            full_prompt = f"{self.system_prompt}\n\nUser Request:\n{user_prompt}"
            
            # Generate content using the model
            response = self.model.generate_content(
                contents=[full_prompt],
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Extract the response text
            response_text = response.candidates[0].content.parts[0].text
            logger.info(f"Received response from Gemini: {response_text[:200]}...")
            
            # Parse and validate the JSON response
            return self._parse_response(response_text)
            
        except Exception as e:
            logger.error(f"Error generating outfit recommendation: {str(e)}")
            raise GeminiServiceError(f"Failed to generate outfit recommendation: {str(e)}")

    
    def _parse_response(self, response_text: str) -> OutfitRecommendation:
        """
        Parse and validate the JSON response from Gemini.
        
        Args:
            response_text: Raw JSON response from the model
            
        Returns:
            Validated OutfitRecommendation object
            
        Raises:
            ValueError: If the response format is invalid
        """
        try:
            # Parse JSON
            response_data = json.loads(response_text)
            
            # Validate and create OutfitRecommendation object
            outfit = OutfitRecommendation(**response_data)
            
            logger.info("Successfully parsed outfit recommendation")
            return outfit
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {response_text}")
            raise GeminiResponseError(f"Invalid JSON response from model: {str(e)}")
        
        except ValidationError as e:
            logger.error(f"Invalid response format: {response_text}")
            raise GeminiResponseError(f"Invalid response format: {str(e)}")
    
    def validate_inputs(
        self,
        gender: str,
        style: str,
        weather: str,
        occasion: str
    ) -> bool:
        """
        Validate input parameters.
        
        Args:
            gender: User's gender
            style: User's style preference
            weather: Weather condition
            occasion: Occasion type
            
        Returns:
            True if all inputs are valid
            
        Raises:
            ValueError: If any input is invalid
        """
        valid_genders = ["male", "female", "men", "women", "unisex"]
        valid_weather = ["hot", "cold", "warm", "mild"]
        
        if gender.lower() not in valid_genders:
            raise ValueError(f"Invalid gender: {gender}. Must be one of {valid_genders}")
        
        if weather.lower() not in valid_weather:
            raise ValueError(f"Invalid weather: {weather}. Must be one of {valid_weather}")
        
        if not style or not style.strip():
            raise ValueError("Style cannot be empty")
        
        if not occasion or not occasion.strip():
            raise ValueError("Occasion cannot be empty")
        
        return True

    def convert_gender_for_gemini(self, gender: str) -> str:
        """
        Convert gender parameter to format expected by Gemini model.
        
        Args:
            gender: Gender from database ("male" or "female")
            
        Returns:
            Gender format for Gemini ("men" or "women")
        """
        gender_mapping = {
            "male": "men",
            "female": "women",
            "men": "men",
            "women": "women"
        }
        
        converted = gender_mapping.get(gender.lower(), "unisex")
        logger.debug(f"Converted gender '{gender}' to '{converted}' for Gemini")
        return converted

# Global service instance
gemini_service = GeminiService()