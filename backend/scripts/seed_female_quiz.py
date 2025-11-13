#!/usr/bin/env python3
"""
Script to seed female quiz data with 50 items (10 categories × 5 questions)

Usage:
    python scripts/seed_female_quiz.py
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_sync_session
from app.services.quiz import QuizItemService, CategoryService


# 10 Female style categories
FEMALE_CATEGORIES = [
    {
        "name": "Bohemian",
        "description": "Free-spirited, artistic style with flowing fabrics and eclectic patterns"
    },
    {
        "name": "Streetwear",
        "description": "Urban, casual style with bold graphics and comfortable fits"
    },
    {
        "name": "Classic",
        "description": "Timeless, elegant style with refined tailoring"
    },
    {
        "name": "Feminine",
        "description": "Romantic, delicate style with soft colors and graceful silhouettes"
    },
    {
        "name": "Edgy",
        "description": "Bold, modern style with leather, dark colors, and statement pieces"
    },
    {
        "name": "Athleisure",
        "description": "Athletic-inspired casual wear that's comfortable and functional"
    },
    {
        "name": "Vintage",
        "description": "Retro-inspired style from past decades with nostalgic charm"
    },
    {
        "name": "Glamorous",
        "description": "Luxurious, sophisticated style with elegant details and rich fabrics"
    },
    {
        "name": "Eclectic",
        "description": "Mixed, unique style combining diverse elements and patterns"
    },
    {
        "name": "Minimalist",
        "description": "Clean, simple style with neutral colors and streamlined silhouettes"
    }
]


# Template for quiz items - YOU NEED TO FILL IN IMAGE URLs
FEMALE_QUIZ_ITEMS = {
    "pants": [
        {"name": "Bohemian Pants", "style_category": "Bohemian", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Streetwear Pants", "style_category": "Streetwear", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Classic Pants", "style_category": "Classic", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Feminine Pants", "style_category": "Feminine", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Edgy Pants", "style_category": "Edgy", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Athleisure Pants", "style_category": "Athleisure", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Vintage Pants", "style_category": "Vintage", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Glamorous Pants", "style_category": "Glamorous", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Eclectic Pants", "style_category": "Eclectic", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Minimalist Pants", "style_category": "Minimalist", "image_url": "YOUR_IMAGE_URL_HERE"},
    ],
    "shirt": [
        {"name": "Bohemian Shirt", "style_category": "Bohemian", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Streetwear Shirt", "style_category": "Streetwear", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Classic Shirt", "style_category": "Classic", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Feminine Shirt", "style_category": "Feminine", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Edgy Shirt", "style_category": "Edgy", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Athleisure Shirt", "style_category": "Athleisure", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Vintage Shirt", "style_category": "Vintage", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Glamorous Shirt", "style_category": "Glamorous", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Eclectic Shirt", "style_category": "Eclectic", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Minimalist Shirt", "style_category": "Minimalist", "image_url": "YOUR_IMAGE_URL_HERE"},
    ],
    "shorts": [
        {"name": "Bohemian Shorts", "style_category": "Bohemian", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Streetwear Shorts", "style_category": "Streetwear", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Classic Shorts", "style_category": "Classic", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Feminine Shorts", "style_category": "Feminine", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Edgy Shorts", "style_category": "Edgy", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Athleisure Shorts", "style_category": "Athleisure", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Vintage Shorts", "style_category": "Vintage", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Glamorous Shorts", "style_category": "Glamorous", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Eclectic Shorts", "style_category": "Eclectic", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Minimalist Shorts", "style_category": "Minimalist", "image_url": "YOUR_IMAGE_URL_HERE"},
    ],
    "overlayer": [
        {"name": "Bohemian Overlayer", "style_category": "Bohemian", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Streetwear Overlayer", "style_category": "Streetwear", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Classic Overlayer", "style_category": "Classic", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Feminine Overlayer", "style_category": "Feminine", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Edgy Overlayer", "style_category": "Edgy", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Athleisure Overlayer", "style_category": "Athleisure", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Vintage Overlayer", "style_category": "Vintage", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Glamorous Overlayer", "style_category": "Glamorous", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Eclectic Overlayer", "style_category": "Eclectic", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Minimalist Overlayer", "style_category": "Minimalist", "image_url": "YOUR_IMAGE_URL_HERE"},
    ],
    "shoes": [
        {"name": "Bohemian Shoes", "style_category": "Bohemian", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Streetwear Shoes", "style_category": "Streetwear", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Classic Shoes", "style_category": "Classic", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Feminine Shoes", "style_category": "Feminine", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Edgy Shoes", "style_category": "Edgy", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Athleisure Shoes", "style_category": "Athleisure", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Vintage Shoes", "style_category": "Vintage", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Glamorous Shoes", "style_category": "Glamorous", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Eclectic Shoes", "style_category": "Eclectic", "image_url": "YOUR_IMAGE_URL_HERE"},
        {"name": "Minimalist Shoes", "style_category": "Minimalist", "image_url": "YOUR_IMAGE_URL_HERE"},
    ]
}


def seed_categories(db: Session):
    """Create style categories"""
    print("Creating style categories...")
    
    for category_data in FEMALE_CATEGORIES:
        # Check if category already exists
        existing = CategoryService.get_category_by_name(
            db,
            category_data["name"],
            "female"
        )
        
        if existing:
            print(f"  ✓ Category '{category_data['name']}' already exists")
            continue
        
        # Create category
        category = CategoryService.create_category(
            db=db,
            name=category_data["name"],
            gender="female",
            description=category_data["description"],
            ai_theme_prompt=None  # Not needed - AI uses category name directly
        )
        print(f"  ✓ Created category: {category.name}")
    
    print(f"✅ Created {len(FEMALE_CATEGORIES)} style categories\n")


def seed_quiz_items(db: Session):
    """Create quiz items"""
    print("Creating quiz items...")
    
    total_created = 0
    total_skipped = 0
    
    for question_type, items in FEMALE_QUIZ_ITEMS.items():
        print(f"\n  {question_type.upper()}:")
        
        for idx, item_data in enumerate(items, 1):
            # Check for placeholder URL
            if item_data["image_url"] == "YOUR_IMAGE_URL_HERE":
                print(f"    ⚠️  Skipped {item_data['name']} - No image URL provided")
                total_skipped += 1
                continue
            
            # Create item
            try:
                item = QuizItemService.create_item(
                    db=db,
                    name=item_data["name"],
                    image_url=item_data["image_url"],
                    question_type=question_type,
                    style_category=item_data["style_category"],
                    gender="female",
                    display_order=idx
                )
                print(f"    ✓ Created: {item.name}")
                total_created += 1
            except Exception as e:
                print(f"    ❌ Error creating {item_data['name']}: {e}")
                total_skipped += 1
    
    print(f"\n✅ Created {total_created} quiz items")
    if total_skipped > 0:
        print(f"⚠️  Skipped {total_skipped} items (missing image URLs)")


def main():
    """Run seeding script"""
    print("=" * 60)
    print("FEMALE QUIZ DATA SEEDING SCRIPT")
    print("=" * 60)
    print()
    
    # Get database session
    db = next(get_sync_session())
    
    try:
        # Step 1: Create categories
        seed_categories(db)
        
        # Step 2: Create quiz items
        seed_quiz_items(db)
        
        print()
        print("=" * 60)
        print("SEEDING COMPLETE!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Update FEMALE_QUIZ_ITEMS with your actual image URLs")
        print("2. Run this script again to populate the items")
        print("3. Test the quiz at GET /api/quiz/questions/female")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
