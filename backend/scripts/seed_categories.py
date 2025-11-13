"""
Seed style categories into the database for the quiz system.
Creates 10 female style categories with descriptions and AI theme prompts.
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_sync_session
from app.services.quiz import CategoryService

# Female style categories with detailed descriptions
FEMALE_CATEGORIES = [
    {
        "name": "Bohemian",
        "gender": "female",
        "description": "Free-spirited, artistic style with flowing fabrics, earthy tones, and eclectic patterns",
        "ai_theme_prompt": "Boho-chic outfits with flowing maxi dresses, peasant tops, fringe details, ethnic prints, and natural materials"
    },
    {
        "name": "Streetwear",
        "gender": "female",
        "description": "Urban, edgy style inspired by skate and hip-hop culture with oversized fits and bold graphics",
        "ai_theme_prompt": "Streetwear outfits with oversized hoodies, graphic tees, joggers, sneakers, and urban-inspired pieces"
    },
    {
        "name": "Classic",
        "gender": "female",
        "description": "Timeless, elegant style with tailored pieces, neutral colors, and refined silhouettes",
        "ai_theme_prompt": "Classic sophisticated outfits with blazers, trench coats, pencil skirts, button-down shirts, and timeless pieces"
    },
    {
        "name": "Feminine",
        "gender": "female",
        "description": "Soft, romantic style with delicate details, pastel colors, and graceful silhouettes",
        "ai_theme_prompt": "Feminine romantic outfits with floral prints, lace details, soft pastels, ruffles, and delicate fabrics"
    },
    {
        "name": "Edgy",
        "gender": "female",
        "description": "Bold, rebellious style with leather, studs, dark colors, and statement pieces",
        "ai_theme_prompt": "Edgy bold outfits with leather jackets, studded details, ripped denim, dark colors, and rock-inspired pieces"
    },
    {
        "name": "Athleisure",
        "gender": "female",
        "description": "Sporty, comfortable style blending athletic wear with everyday fashion",
        "ai_theme_prompt": "Athleisure outfits with yoga pants, sports bras, athletic jackets, sneakers, and performance fabrics"
    },
    {
        "name": "Vintage",
        "gender": "female",
        "description": "Retro-inspired style drawing from past decades with classic cuts and nostalgic details",
        "ai_theme_prompt": "Vintage retro outfits with A-line dresses, high-waisted pants, cat-eye sunglasses, and era-specific details"
    },
    {
        "name": "Glamorous",
        "gender": "female",
        "description": "Luxurious, sophisticated style with sparkle, sequins, and statement accessories",
        "ai_theme_prompt": "Glamorous luxury outfits with sequined dresses, silk blouses, statement jewelry, and elegant evening wear"
    },
    {
        "name": "Eclectic",
        "gender": "female",
        "description": "Mix-and-match style combining different eras, patterns, and unexpected combinations",
        "ai_theme_prompt": "Eclectic mixed outfits with pattern mixing, vintage meets modern, unique combinations, and artistic flair"
    },
    {
        "name": "Minimalist",
        "gender": "female",
        "description": "Clean, simple style with neutral colors, streamlined silhouettes, and quality basics",
        "ai_theme_prompt": "Minimalist clean outfits with neutral colors, simple lines, quality basics, and understated elegance"
    }
]


def seed_categories():
    """Seed style categories into the database"""
    db = next(get_sync_session())
    
    try:
        print("🌱 Seeding style categories...")
        
        created_count = 0
        skipped_count = 0
        
        for category_data in FEMALE_CATEGORIES:
            # Check if category already exists
            existing = CategoryService.get_category_by_name(
                db=db,
                name=category_data["name"],
                gender=category_data["gender"]
            )
            
            if existing:
                print(f"⏭️  Skipping {category_data['name']} - already exists")
                skipped_count += 1
                continue
            
            # Create new category
            category = CategoryService.create_category(
                db=db,
                name=category_data["name"],
                gender=category_data["gender"],
                description=category_data["description"],
                ai_theme_prompt=category_data["ai_theme_prompt"]
            )
            
            print(f"✅ Created category: {category.name} ({category.gender})")
            created_count += 1
        
        print(f"\n✨ Seeding complete!")
        print(f"   Created: {created_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Total: {len(FEMALE_CATEGORIES)}")
        
    except Exception as e:
        print(f"❌ Error seeding categories: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_categories()
