"""
Core scoring algorithm for quiz results
"""
import uuid
import logging
import random
from typing import Dict, List, Optional, Any
from collections import Counter

from app.models.quiz import QuizItem

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for calculating quiz scores and style assignments"""
    
    # 10 female style categories
    FEMALE_CATEGORIES = [
        "Bohemian",
        "Streetwear",
        "Classic",
        "Feminine",
        "Edgy",
        "Athleisure",
        "Vintage",
        "Glamorous",
        "Eclectic",
        "Minimalist"
    ]
    
    # Male categories (to be defined later)
    MALE_CATEGORIES = []
    
    @staticmethod
    def calculate_style_scores(
        selected_items: List[QuizItem]
    ) -> Dict[str, Any]:
        """
        Calculate style scores from selected quiz items
        
        Algorithm:
        - 5 questions total (pants, shirt, shorts, overlayer, shoes)
        - Each question contributes 1 point to the selected item's style category
        - Primary style = category with most points
        - Secondary style = category with 2nd most points (random pick if tie)
        - Edge case: If all 5 selections are same category, no secondary style
        
        Args:
            selected_items: List of 5 QuizItem objects
            
        Returns:
            {
                'primary_style': 'Bohemian',
                'secondary_style': 'Classic' or None,
                'style_message': 'Bohemian with a hint of Classic',
                'scores': {'Bohemian': 3, 'Classic': 1, 'Streetwear': 1}
            }
        """
        if len(selected_items) != 5:
            raise ValueError(f"Expected 5 selected items, got {len(selected_items)}")
        
        # Count occurrences of each style category
        category_counts = Counter(item.style_category for item in selected_items)
        
        # Get sorted list of (category, count) tuples
        sorted_categories = category_counts.most_common()
        
        # Get primary style (highest count)
        primary_style = sorted_categories[0][0]
        primary_count = sorted_categories[0][1]
        
        # Determine secondary style
        secondary_style = None
        if len(sorted_categories) > 1 and primary_count < 5:
            # Get all categories tied for 2nd place
            second_place_count = sorted_categories[1][1]
            tied_for_second = [
                cat for cat, count in sorted_categories[1:]
                if count == second_place_count
            ]
            
            # Pick randomly if there's a tie
            secondary_style = random.choice(tied_for_second) if tied_for_second else None
        
        # Create style message
        style_message = ScoringService.format_style_message(
            primary_style,
            secondary_style
        )
        
        # Convert Counter to regular dict for JSON serialization
        scores = dict(category_counts)
        
        logger.info(
            f"Calculated style scores: primary={primary_style}, "
            f"secondary={secondary_style}, scores={scores}"
        )
        
        return {
            'primary_style': primary_style,
            'secondary_style': secondary_style,
            'style_message': style_message,
            'scores': scores
        }
    
    @staticmethod
    def format_style_message(
        primary: str,
        secondary: Optional[str]
    ) -> str:
        """
        Format a user-friendly style message
        
        Examples:
            - "Bohemian with a hint of Classic"
            - "Pure Minimalist"
        """
        if secondary:
            return f"{primary} with a hint of {secondary}"
        else:
            return f"Pure {primary}"
    
    @staticmethod
    def validate_selections(
        selections: Dict[str, uuid.UUID],
        gender: str
    ) -> List[str]:
        """
        Validate that all required question types are present
        
        Returns:
            List of error messages (empty if valid)
        """
        required_questions = ['pants', 'shirt', 'shorts', 'overlayer', 'shoes']
        errors = []
        
        # Check for missing questions
        missing = set(required_questions) - set(selections.keys())
        if missing:
            errors.append(f"Missing selections for: {', '.join(missing)}")
        
        # Check for extra questions
        extra = set(selections.keys()) - set(required_questions)
        if extra:
            errors.append(f"Unexpected selections: {', '.join(extra)}")
        
        return errors
    
    @staticmethod
    def get_categories_for_gender(gender: str) -> List[str]:
        """Get the list of style categories for a given gender"""
        if gender == "female":
            return ScoringService.FEMALE_CATEGORIES
        elif gender == "male":
            return ScoringService.MALE_CATEGORIES
        else:
            raise ValueError(f"Invalid gender: {gender}")
