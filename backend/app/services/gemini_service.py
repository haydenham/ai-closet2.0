"""
Gemini AI service for generating fashion recommendations using Vertex AI.
"""
import json
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ValidationError

try:  # Delay heavy imports / allow absence in some test contexts
    import vertexai  # type: ignore
    from vertexai.generative_models import GenerativeModel  # type: ignore
except Exception:  # pragma: no cover - fallback when library not present
    vertexai = None  # type: ignore
    GenerativeModel = object  # type: ignore

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


class GeminiResponseError(GeminiServiceError):
    """Raised when the model response is invalid or cannot be parsed"""


class GeminiService:
    """Service for interacting with Gemini model via Vertex AI (lazy init)."""

    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.location = settings.GCP_LOCATION
        self.endpoint_id = settings.GEMINI_ENDPOINT_ID
        self._model: Optional[GenerativeModel] = None
        self.system_prompt = self._get_system_prompt()

    def _ensure_model(self):
        """Lazily initialize Vertex AI client & model."""
        if self._model is not None:
            return
        if not (self.project_id and self.location and self.endpoint_id):
            raise GeminiServiceError("Gemini configuration incomplete (project/location/endpoint missing)")
        if vertexai is None:
            raise GeminiServiceError("vertexai library not available. Install google-cloud-aiplatform.")
        try:
            vertexai.init(project=self.project_id, location=self.location)
            self._model = GenerativeModel(
                model_name=f"projects/{self.project_id}/locations/{self.location}/endpoints/{self.endpoint_id}"
            )
            logger.info("Gemini model initialized lazily")
        except Exception as e:  # pragma: no cover (network/auth dependent)
            raise GeminiServiceError(f"Failed to initialize Gemini model: {e}") from e
    
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
            gender: User's gender (men/women)
            style: User's style preference (classic, casual, trendy, etc.)
            weather: Weather condition (warm/cold)
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
            
            # Ensure model is ready (lazy init)
            self._ensure_model()

            # Combine system prompt with user prompt
            full_prompt = f"{self.system_prompt}\n\nUser Request:\n{user_prompt}"

            response = self._model.generate_content(  # type: ignore[attr-defined]
                contents=[full_prompt],
                generation_config={"response_mime_type": "application/json"}
            )

            response_text = self._extract_response_text(response)
            logger.info(f"Received response from Gemini (truncated): {response_text[:200]}...")
            return self._parse_response(response_text)

        except GeminiServiceError:
            raise
        except GeminiResponseError:
            raise
        except Exception as e:  # pragma: no cover (unexpected)
            logger.error(f"Error generating outfit recommendation: {e}")
            raise GeminiServiceError(f"Failed to generate outfit recommendation: {e}") from e

    def _extract_response_text(self, response: Any) -> str:
        """Safely extract JSON text from Vertex response."""
        try:
            candidates = getattr(response, 'candidates', None)
            if not candidates:
                raise GeminiResponseError("No candidates in model response")
            # Find first part with non-empty text starting with JSON token
            for cand in candidates:
                content = getattr(cand, 'content', None)
                parts = getattr(content, 'parts', []) if content else []
                for part in parts:
                    text_val = getattr(part, 'text', '')
                    if isinstance(text_val, str) and text_val.strip() and text_val.lstrip().startswith(('{', '[')):
                        return text_val.strip()
            raise GeminiResponseError("No JSON payload found in model response parts")
        except GeminiResponseError:
            raise
        except Exception as e:  # pragma: no cover
            raise GeminiResponseError(f"Failed to extract response text: {e}") from e
    
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
            logger.error("Invalid JSON response from Gemini")
            raise GeminiResponseError(f"Invalid JSON response: {e}") from e
        except ValidationError as e:
            logger.error("Gemini response failed schema validation")
            raise GeminiResponseError(f"Invalid response format: {e}") from e
    
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
        valid_genders = ["men", "women", "unisex"]
        valid_weather = ["warm", "cold", "mild"]
        
        if gender.lower() not in valid_genders:
            raise ValueError(f"Invalid gender: {gender}. Must be one of {valid_genders}")
        
        if weather.lower() not in valid_weather:
            raise ValueError(f"Invalid weather: {weather}. Must be one of {valid_weather}")
        
        if not style or not style.strip():
            raise ValueError("Style cannot be empty")
        
        if not occasion or not occasion.strip():
            raise ValueError("Occasion cannot be empty")
        
        return True


class _LazyGeminiProxy:
    """Attribute-access lazy proxy around GeminiService to preserve existing import path usages."""
    _instance: Optional[GeminiService] = None

    def _get(self) -> GeminiService:
        if self._instance is None:
            self._instance = GeminiService()
        return self._instance

    def __getattr__(self, item):  # pragma: no cover (simple delegation)
        return getattr(self._get(), item)

    def __repr__(self):  # pragma: no cover
        status = 'initialized' if self._instance else 'uninitialized'
        return f"<LazyGeminiService {status}>"

gemini_service = _LazyGeminiProxy()

def get_gemini_service() -> GeminiService:
    """Explicit accessor for the underlying initialized GeminiService."""
    return gemini_service._get()