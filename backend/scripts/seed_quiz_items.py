#!/usr/bin/env python3
"""
Script to seed female quiz data with 50 items (10 categories × 5 questions)
Uses Unsplash API for placeholder images until real images are uploaded.

Usage:
    PYTHONPATH=/Users/haydenhamilton/PERSONAL-PROJECTS/ai-closet2.0/backend python scripts/seed_quiz_items.py
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_sync_session
from app.services.quiz import QuizItemService, CategoryService


# Image URL template using Unsplash for placeholder images
# Format: https://source.unsplash.com/400x600/?{query}
def get_placeholder_image(style: str, item_type: str) -> str:
    """
    Generate placeholder image URL from Unsplash.
    Args:
        style: Style category name (e.g., "Bohemian")
        item_type: Clothing type (e.g., "pants", "shirt")
    Returns:
        Unsplash image URL
    """
    query = f"{style.lower()},{item_type},fashion,women"
    return f"https://source.unsplash.com/400x600/?{query}"


# Female quiz items structure: 5 questions × 10 categories = 50 items
QUIZ_STRUCTURE = {
    "pants": ["Bohemian", "Streetwear", "Classic", "Feminine", "Edgy", "Athleisure", "Vintage", "Glamorous", "Eclectic", "Minimalist"],
    "shirt": ["Bohemian", "Streetwear", "Classic", "Feminine", "Edgy", "Athleisure", "Vintage", "Glamorous", "Eclectic", "Minimalist"],
    "shorts": ["Bohemian", "Streetwear", "Classic", "Feminine", "Edgy", "Athleisure", "Vintage", "Glamorous", "Eclectic", "Minimalist"],
    "overlayer": ["Bohemian", "Streetwear", "Classic", "Feminine", "Edgy", "Athleisure", "Vintage", "Glamorous", "Eclectic", "Minimalist"],
    "shoes": ["Bohemian", "Streetwear", "Classic", "Feminine", "Edgy", "Athleisure", "Vintage", "Glamorous", "Eclectic", "Minimalist"]
}


# Better item descriptions
ITEM_DESCRIPTIONS = {
    "pants": {
        "Bohemian": "Flowy wide-leg pants with ethnic print",
        "Streetwear": "Baggy cargo pants with multiple pockets",
        "Classic": "Tailored dress pants with clean lines",
        "Feminine": "High-waisted pants with soft pleats",
        "Edgy": "Leather or faux leather pants with zippers",
        "Athleisure": "Performance leggings with mesh panels",
        "Vintage": "High-waisted retro trousers",
        "Glamorous": "Silky palazzo pants with elegant drape",
        "Eclectic": "Patchwork pants with mixed patterns",
        "Minimalist": "Simple straight-leg pants in neutral tone"
    },
    "shirt": {
        "Bohemian": "Embroidered peasant blouse with tassels",
        "Streetwear": "Oversized graphic t-shirt",
        "Classic": "Crisp white button-down shirt",
        "Feminine": "Floral blouse with ruffled sleeves",
        "Edgy": "Black band tee with leather accents",
        "Athleisure": "Moisture-wicking sports tank",
        "Vintage": "Retro polka dot blouse",
        "Glamorous": "Silk camisole with lace trim",
        "Eclectic": "Color-blocked asymmetric top",
        "Minimalist": "Simple crew neck t-shirt"
    },
    "shorts": {
        "Bohemian": "Crochet-trim denim cutoffs",
        "Streetwear": "Basketball shorts with bold stripe",
        "Classic": "Tailored Bermuda shorts",
        "Feminine": "Flowy shorts with bow detail",
        "Edgy": "Distressed black denim shorts",
        "Athleisure": "Running shorts with built-in liner",
        "Vintage": "High-waisted denim shorts",
        "Glamorous": "Sequined dressy shorts",
        "Eclectic": "Printed patchwork shorts",
        "Minimalist": "Clean-cut neutral shorts"
    },
    "overlayer": {
        "Bohemian": "Fringed suede vest",
        "Streetwear": "Oversized bomber jacket",
        "Classic": "Tailored blazer",
        "Feminine": "Soft cardigan with pearl buttons",
        "Edgy": "Motorcycle leather jacket",
        "Athleisure": "Zip-up athletic jacket",
        "Vintage": "Retro denim jacket",
        "Glamorous": "Faux fur coat",
        "Eclectic": "Colorful kimono jacket",
        "Minimalist": "Simple trench coat"
    },
    "shoes": {
        "Bohemian": "Strappy leather sandals",
        "Streetwear": "High-top sneakers",
        "Classic": "Black leather pumps",
        "Feminine": "Ballet flats with bow",
        "Edgy": "Combat boots with studs",
        "Athleisure": "Running sneakers",
        "Vintage": "Mary Jane heels",
        "Glamorous": "Sparkly stiletto heels",
        "Eclectic": "Mixed-material platform shoes",
        "Minimalist": "White leather sneakers"
    }
}


def seed_quiz_items():
    """Seed quiz items with placeholder images"""
    db = next(get_sync_session())
    
    try:
        print("🌱 Seeding quiz items...")
        print(f"📊 Expected: 50 items (5 questions × 10 categories)\n")
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for question_type, categories in QUIZ_STRUCTURE.items():
            print(f"\n📋 Processing {question_type}:")
            
            for style_name in categories:
                # Get the style category from database to verify it exists
                category = CategoryService.get_category_by_name(
                    db=db,
                    name=style_name,
                    gender="female"
                )
                
                if not category:
                    print(f"  ❌ Category not found: {style_name} - run seed_categories.py first!")
                    error_count += 1
                    continue
                
                # Check if item already exists
                existing_items = QuizItemService.get_all_items(
                    db=db,
                    gender="female",
                    question_type=question_type,
                    style_category=style_name
                )
                
                if existing_items:
                    print(f"  ⏭️  {style_name} {question_type} - already exists")
                    skipped_count += 1
                    continue
                
                # Create the quiz item with placeholder image
                image_url = get_placeholder_image(style_name, question_type)
                description = ITEM_DESCRIPTIONS[question_type][style_name]
                
                try:
                    item = QuizItemService.create_item(
                        db=db,
                        name=f"{style_name} {question_type.title()}",
                        image_url=image_url,
                        question_type=question_type,
                        style_category=style_name,
                        gender="female"
                    )
                    print(f"  ✅ Created {style_name} {question_type}")
                    created_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Error creating {style_name} {question_type}: {e}")
                    error_count += 1
        
        print(f"\n✨ Seeding complete!")
        print(f"   Created: {created_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Errors: {error_count}")
        print(f"   Expected: 50")
        
        if created_count + skipped_count != 50:
            print(f"\n⚠️  Warning: Total items ({created_count + skipped_count}) doesn't match expected (50)")
        
        print(f"\n💡 Note: Using Unsplash placeholder images.")
        print(f"   Replace with actual images by updating image_url in quiz_items table.")
        
    except Exception as e:
        print(f"\n❌ Fatal error seeding quiz items: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_quiz_items()
