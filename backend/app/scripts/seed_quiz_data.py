"""
Script to seed quiz system with initial style categories and sample clothing items
"""
import asyncio
import uuid
from sqlalchemy.orm import Session

from app.core.database import get_sync_session
from app.models.quiz_system import StyleCategory, QuizClothingItem
from app.services.quiz_service import StyleCategoryService, QuizClothingItemService


# Style categories as defined in the design document
STYLE_CATEGORIES = {
    "male": [
        {
            "name": "Minimalist / Clean-Cut",
            "features": ["clean", "minimal", "neutral", "simple", "fitted", "monochrome"],
            "ai_theme_prompt": "Focus on clean lines, neutral colors, and minimalist aesthetic. Emphasize simplicity and sophistication.",
            "description": "Clean, minimal style with neutral colors and simple silhouettes"
        },
        {
            "name": "Classic Tailored",
            "features": ["tailored", "business", "formal", "structured", "classic", "professional"],
            "ai_theme_prompt": "Emphasize traditional menswear, tailored fits, and professional appearance. Think business attire and formal wear.",
            "description": "Traditional, well-tailored clothing suitable for professional settings"
        },
        {
            "name": "Streetwear",
            "features": ["graphic", "oversized", "sneakers", "urban", "bold", "casual", "baggy"],
            "ai_theme_prompt": "Focus on urban street style with bold graphics, oversized fits, and contemporary casual wear.",
            "description": "Urban street style with bold graphics and relaxed fits"
        },
        {
            "name": "Workwear / Heritage",
            "features": ["denim", "rugged", "heritage", "workwear", "boots", "utilitarian", "sturdy"],
            "ai_theme_prompt": "Emphasize durable, functional clothing with heritage appeal. Think workwear-inspired pieces and rugged materials.",
            "description": "Durable, functional clothing with heritage and workwear influences"
        },
        {
            "name": "Techwear / Utility",
            "features": ["technical", "performance", "muted", "functional", "modern", "utility"],
            "ai_theme_prompt": "Focus on technical fabrics, functional design, and modern utility. Emphasize performance and innovation.",
            "description": "Technical, functional clothing with modern utility features"
        },
        {
            "name": "Preppy / Ivy",
            "features": ["preppy", "collegiate", "polo", "chino", "loafers", "traditional", "refined"],
            "ai_theme_prompt": "Emphasize traditional American collegiate style with refined, preppy elements. Think Ivy League aesthetic.",
            "description": "Traditional collegiate style with refined, preppy elements"
        },
        {
            "name": "Athleisure / Sport Casual",
            "features": ["athletic", "sporty", "comfortable", "activewear", "casual", "performance"],
            "ai_theme_prompt": "Focus on athletic-inspired casual wear that's comfortable and performance-oriented.",
            "description": "Athletic-inspired casual wear for active lifestyles"
        },
        {
            "name": "Retro / Vintage",
            "features": ["vintage", "retro", "70s", "80s", "90s", "nostalgic", "throwback"],
            "ai_theme_prompt": "Emphasize vintage and retro styles from past decades. Focus on nostalgic and throwback elements.",
            "description": "Vintage-inspired clothing with retro and nostalgic elements"
        }
    ],
    "female": [
        {
            "name": "Minimalist / Modern Chic",
            "features": ["minimal", "modern", "clean", "sophisticated", "neutral", "sleek"],
            "ai_theme_prompt": "Focus on clean, modern lines with sophisticated neutral tones. Emphasize sleek and minimalist aesthetic.",
            "description": "Clean, modern style with sophisticated neutral tones"
        },
        {
            "name": "Classic Elegance",
            "features": ["elegant", "timeless", "tailored", "refined", "classic", "polished"],
            "ai_theme_prompt": "Emphasize timeless elegance with refined, tailored pieces. Focus on classic and polished looks.",
            "description": "Timeless, elegant style with refined and tailored pieces"
        },
        {
            "name": "Streetwear",
            "features": ["oversized", "graphic", "sneakers", "urban", "bold", "edgy", "casual"],
            "ai_theme_prompt": "Focus on urban street style with bold graphics, oversized fits, and edgy casual wear.",
            "description": "Urban street style with bold graphics and edgy elements"
        },
        {
            "name": "Bohemian / Indie",
            "features": ["boho", "flowy", "prints", "crochet", "indie", "artistic", "free-spirited"],
            "ai_theme_prompt": "Emphasize bohemian and indie aesthetics with flowy fabrics, artistic prints, and free-spirited elements.",
            "description": "Bohemian style with flowy fabrics and artistic, free-spirited elements"
        },
        {
            "name": "Romantic / Feminine",
            "features": ["romantic", "feminine", "pastels", "ruffles", "soft", "delicate", "pretty"],
            "ai_theme_prompt": "Focus on romantic, feminine elements with soft pastels, delicate details, and pretty silhouettes.",
            "description": "Romantic, feminine style with soft colors and delicate details"
        },
        {
            "name": "Athleisure / Sport Casual",
            "features": ["athletic", "sporty", "comfortable", "activewear", "casual", "performance"],
            "ai_theme_prompt": "Focus on athletic-inspired casual wear that's comfortable and performance-oriented.",
            "description": "Athletic-inspired casual wear for active lifestyles"
        },
        {
            "name": "Trend-Driven / Y2K",
            "features": ["trendy", "y2k", "micro", "baby-tee", "mesh", "bold", "statement"],
            "ai_theme_prompt": "Emphasize current trends and Y2K revival elements. Focus on bold, statement pieces and micro trends.",
            "description": "Trend-focused style with Y2K revival and bold statement pieces"
        },
        {
            "name": "Vintage Revival",
            "features": ["vintage", "thrift", "70s", "90s", "corsets", "mom-jeans", "retro"],
            "ai_theme_prompt": "Focus on vintage revival with thrifted aesthetics, retro elements from various decades.",
            "description": "Vintage revival style with thrifted and retro elements"
        }
    ]
}


# Sample clothing items for testing
SAMPLE_CLOTHING_ITEMS = {
    "male": {
        "top": [
            {
                "name": "Classic White T-Shirt",
                "image_url": "/images/quiz/mens/tops/white_tshirt_001.jpg",
                "features": ["t-shirt", "cotton", "white", "neutral", "casual", "basic", "fitted", "minimalist"]
            },
            {
                "name": "Graphic Streetwear Tee",
                "image_url": "/images/quiz/mens/tops/graphic_tee_001.jpg",
                "features": ["t-shirt", "graphic", "oversized", "cotton", "bold", "streetwear", "casual", "urban"]
            },
            {
                "name": "Business Dress Shirt",
                "image_url": "/images/quiz/mens/tops/dress_shirt_001.jpg",
                "features": ["dress-shirt", "formal", "tailored", "business", "professional", "structured", "classic"]
            }
        ],
        "bottom": [
            {
                "name": "Dark Wash Jeans",
                "image_url": "/images/quiz/mens/bottoms/dark_jeans_001.jpg",
                "features": ["jeans", "denim", "dark-wash", "casual", "fitted", "versatile", "cotton"]
            },
            {
                "name": "Chino Pants",
                "image_url": "/images/quiz/mens/bottoms/chinos_001.jpg",
                "features": ["chinos", "preppy", "tailored", "casual", "refined", "cotton", "versatile"]
            },
            {
                "name": "Cargo Pants",
                "image_url": "/images/quiz/mens/bottoms/cargo_pants_001.jpg",
                "features": ["cargo", "utilitarian", "functional", "workwear", "pockets", "sturdy", "casual"]
            }
        ],
        "shoes": [
            {
                "name": "White Sneakers",
                "image_url": "/images/quiz/mens/shoes/white_sneakers_001.jpg",
                "features": ["sneakers", "white", "casual", "versatile", "comfortable", "minimalist", "athletic"]
            },
            {
                "name": "Leather Dress Shoes",
                "image_url": "/images/quiz/mens/shoes/dress_shoes_001.jpg",
                "features": ["dress-shoes", "leather", "formal", "business", "professional", "classic", "polished"]
            },
            {
                "name": "Work Boots",
                "image_url": "/images/quiz/mens/shoes/work_boots_001.jpg",
                "features": ["boots", "leather", "workwear", "rugged", "heritage", "sturdy", "utilitarian"]
            }
        ]
    },
    "female": {
        "top": [
            {
                "name": "Silk Blouse",
                "image_url": "/images/quiz/womens/tops/silk_blouse_001.jpg",
                "features": ["blouse", "silk", "elegant", "refined", "classic", "sophisticated", "timeless"]
            },
            {
                "name": "Crop Top",
                "image_url": "/images/quiz/womens/tops/crop_top_001.jpg",
                "features": ["crop-top", "trendy", "casual", "fitted", "modern", "youthful", "statement"]
            },
            {
                "name": "Flowy Bohemian Top",
                "image_url": "/images/quiz/womens/tops/boho_top_001.jpg",
                "features": ["blouse", "flowy", "boho", "prints", "artistic", "free-spirited", "comfortable"]
            }
        ],
        "bottom": [
            {
                "name": "High-Waisted Jeans",
                "image_url": "/images/quiz/womens/bottoms/high_waist_jeans_001.jpg",
                "features": ["jeans", "high-waisted", "denim", "fitted", "versatile", "casual", "modern"]
            },
            {
                "name": "Flowy Maxi Skirt",
                "image_url": "/images/quiz/womens/bottoms/maxi_skirt_001.jpg",
                "features": ["skirt", "maxi", "flowy", "feminine", "romantic", "comfortable", "bohemian"]
            },
            {
                "name": "Tailored Trousers",
                "image_url": "/images/quiz/womens/bottoms/tailored_trousers_001.jpg",
                "features": ["trousers", "tailored", "professional", "structured", "elegant", "business", "refined"]
            }
        ],
        "shoes": [
            {
                "name": "White Sneakers",
                "image_url": "/images/quiz/womens/shoes/white_sneakers_001.jpg",
                "features": ["sneakers", "white", "casual", "comfortable", "athletic", "versatile", "minimalist"]
            },
            {
                "name": "Heeled Ankle Boots",
                "image_url": "/images/quiz/womens/shoes/ankle_boots_001.jpg",
                "features": ["boots", "heeled", "ankle", "leather", "sophisticated", "versatile", "modern"]
            },
            {
                "name": "Ballet Flats",
                "image_url": "/images/quiz/womens/shoes/ballet_flats_001.jpg",
                "features": ["flats", "ballet", "comfortable", "feminine", "classic", "versatile", "elegant"]
            }
        ]
    }
}


def seed_style_categories(db: Session):
    """Seed the database with style categories"""
    print("Seeding style categories...")
    
    for gender, categories in STYLE_CATEGORIES.items():
        for category_data in categories:
            # Check if category already exists
            existing = db.query(StyleCategory).filter(
                StyleCategory.name == category_data["name"],
                StyleCategory.gender == gender
            ).first()
            
            if not existing:
                category = StyleCategoryService.create_style_category(
                    db=db,
                    name=category_data["name"],
                    gender=gender,
                    features=category_data["features"],
                    ai_theme_prompt=category_data["ai_theme_prompt"],
                    description=category_data["description"]
                )
                print(f"Created category: {category.name} ({gender})")
            else:
                print(f"Category already exists: {category_data['name']} ({gender})")


def seed_sample_clothing_items(db: Session):
    """Seed the database with sample clothing items"""
    print("Seeding sample clothing items...")
    
    for gender, categories in SAMPLE_CLOTHING_ITEMS.items():
        for category, items in categories.items():
            for item_data in items:
                # Check if item already exists
                existing = db.query(QuizClothingItem).filter(
                    QuizClothingItem.name == item_data["name"],
                    QuizClothingItem.gender == gender,
                    QuizClothingItem.category == category
                ).first()
                
                if not existing:
                    item = QuizClothingItemService.create_clothing_item(
                        db=db,
                        name=item_data["name"],
                        image_url=item_data["image_url"],
                        gender=gender,
                        category=category,
                        features=item_data["features"]
                    )
                    print(f"Created item: {item.name} ({gender} {category})")
                else:
                    print(f"Item already exists: {item_data['name']} ({gender} {category})")


def main():
    """Main seeding function"""
    print("Starting quiz data seeding...")
    
    # Get database session
    db = next(get_sync_session())
    
    try:
        # Seed style categories
        seed_style_categories(db)
        
        # Seed sample clothing items
        seed_sample_clothing_items(db)
        
        print("Quiz data seeding completed successfully!")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()