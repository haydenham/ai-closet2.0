#!/usr/bin/env python3
"""
Script to populate quiz database with sample clothing items
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_sync_session
from app.models.quiz_system import QuizClothingItem, StyleCategory
from app.services.quiz_service import QuizClothingItemService, StyleCategoryService


def create_sample_clothing_items(db: Session):
    """Create sample clothing items for the quiz"""
    
    # Gender-specific items
    female_items = {
        'top': [
            {
                'name': 'Silk Blouse',
                'features': ['elegant', 'silk', 'button_up', 'feminine'],
                'image_url': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=400&fit=crop'
            },
            {
                'name': 'Flowing Tank Top',
                'features': ['casual', 'flowy', 'cotton', 'relaxed'],
                'image_url': 'https://images.unsplash.com/photo-1571945153237-4929e783af4a?w=400&h=400&fit=crop'
            },
            {
                'name': 'Cropped Sweater',
                'features': ['cozy', 'soft', 'knit', 'trendy'],
                'image_url': 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&h=400&fit=crop'
            },
            {
                'name': 'Off-Shoulder Top',
                'features': ['romantic', 'feminine', 'trendy', 'cotton'],
                'image_url': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=400&fit=crop'
            }
        ],
        'bottom': [
            {
                'name': 'High-Waisted Jeans',
                'features': ['trendy', 'flattering', 'denim', 'versatile'],
                'image_url': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400&h=400&fit=crop'
            },
            {
                'name': 'Flowy Midi Skirt',
                'features': ['feminine', 'elegant', 'midi_length', 'flowy'],
                'image_url': 'https://images.unsplash.com/photo-1583496661160-fb5886a13d53?w=400&h=400&fit=crop'
            },
            {
                'name': 'Wide-Leg Trousers',
                'features': ['sophisticated', 'comfortable', 'professional', 'flowing'],
                'image_url': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=400&fit=crop'
            },
            {
                'name': 'Denim Shorts',
                'features': ['casual', 'summer', 'high_waisted', 'versatile'],
                'image_url': 'https://images.unsplash.com/photo-1591195853828-11db59a44f6b?w=400&h=400&fit=crop'
            }
        ],
        'shoes': [
            {
                'name': 'Block Heels',
                'features': ['elegant', 'comfortable', 'versatile', 'leather'],
                'image_url': 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400&h=400&fit=crop'
            },
            {
                'name': 'White Sneakers',
                'features': ['casual', 'comfortable', 'versatile', 'modern'],
                'image_url': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop'
            },
            {
                'name': 'Ankle Boots',
                'features': ['edgy', 'versatile', 'leather', 'stylish'],
                'image_url': 'https://images.unsplash.com/photo-1544966503-7cc5ac882d5f?w=400&h=400&fit=crop'
            },
            {
                'name': 'Ballet Flats',
                'features': ['feminine', 'comfortable', 'classic', 'elegant'],
                'image_url': 'https://images.unsplash.com/photo-1535043934128-cf0b28d52f95?w=400&h=400&fit=crop'
            }
        ],
        'layering': [
            {
                'name': 'Cropped Blazer',
                'features': ['structured', 'professional', 'fitted', 'modern'],
                'image_url': 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&h=400&fit=crop'
            },
            {
                'name': 'Knit Cardigan',
                'features': ['cozy', 'soft', 'oversized', 'comfortable'],
                'image_url': 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&h=400&fit=crop'
            },
            {
                'name': 'Denim Jacket',
                'features': ['casual', 'classic', 'versatile', 'timeless'],
                'image_url': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=400&fit=crop'
            },
            {
                'name': 'Leather Jacket',
                'features': ['edgy', 'bold', 'modern', 'statement'],
                'image_url': 'https://images.unsplash.com/photo-1520975916090-3105956dac38?w=400&h=400&fit=crop'
            }
        ],
        'accessory': [
            {
                'name': 'Statement Earrings',
                'features': ['bold', 'jewelry', 'decorative', 'feminine'],
                'image_url': 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=400&h=400&fit=crop'
            },
            {
                'name': 'Silk Scarf',
                'features': ['elegant', 'versatile', 'pattern', 'sophisticated'],
                'image_url': 'https://images.unsplash.com/photo-1601924638867-985c6d427917?w=400&h=400&fit=crop'
            },
            {
                'name': 'Chain Handbag',
                'features': ['trendy', 'structured', 'elegant', 'versatile'],
                'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop'
            },
            {
                'name': 'Canvas Tote',
                'features': ['casual', 'practical', 'eco_friendly', 'spacious'],
                'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop'
            }
        ],
        'complete_outfit': [
            {
                'name': 'Office Chic',
                'features': ['professional', 'polished', 'coordinated', 'sophisticated'],
                'image_url': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=400&fit=crop'
            },
            {
                'name': 'Boho Casual',
                'features': ['relaxed', 'flowy', 'artistic', 'comfortable'],
                'image_url': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=400&h=400&fit=crop'
            },
            {
                'name': 'Date Night Glam',
                'features': ['elegant', 'romantic', 'stylish', 'feminine'],
                'image_url': 'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=400&fit=crop'
            },
            {
                'name': 'Weekend Athleisure',
                'features': ['sporty', 'comfortable', 'modern', 'active'],
                'image_url': 'https://images.unsplash.com/photo-1506629905607-edb8913e2842?w=400&h=400&fit=crop'
            }
        ]
    }

    male_items = {
        'top': [
            {
                'name': 'Classic White Shirt',
                'features': ['professional', 'versatile', 'cotton', 'button_down'],
                'image_url': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=400&fit=crop'
            },
            {
                'name': 'Henley T-Shirt',
                'features': ['casual', 'comfortable', 'cotton', 'relaxed'],
                'image_url': 'https://images.unsplash.com/photo-1571945153237-4929e783af4a?w=400&h=400&fit=crop'
            },
            {
                'name': 'Crew Neck Sweater',
                'features': ['warm', 'classic', 'knit', 'versatile'],
                'image_url': 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&h=400&fit=crop'
            },
            {
                'name': 'Polo Shirt',
                'features': ['smart_casual', 'cotton', 'collar', 'sporty'],
                'image_url': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=400&fit=crop'
            }
        ],
        'bottom': [
            {
                'name': 'Dark Wash Jeans',
                'features': ['casual', 'versatile', 'denim', 'straight_leg'],
                'image_url': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400&h=400&fit=crop'
            },
            {
                'name': 'Tailored Chinos',
                'features': ['smart_casual', 'fitted', 'cotton', 'versatile'],
                'image_url': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=400&fit=crop'
            },
            {
                'name': 'Dress Trousers',
                'features': ['formal', 'professional', 'tailored', 'wool'],
                'image_url': 'https://images.unsplash.com/photo-1583496661160-fb5886a13d53?w=400&h=400&fit=crop'
            },
            {
                'name': 'Cargo Shorts',
                'features': ['casual', 'practical', 'cotton', 'summer'],
                'image_url': 'https://images.unsplash.com/photo-1591195853828-11db59a44f6b?w=400&h=400&fit=crop'
            }
        ],
        'shoes': [
            {
                'name': 'Leather Dress Shoes',
                'features': ['formal', 'professional', 'leather', 'classic'],
                'image_url': 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400&h=400&fit=crop'
            },
            {
                'name': 'White Sneakers',
                'features': ['casual', 'comfortable', 'versatile', 'modern'],
                'image_url': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop'
            },
            {
                'name': 'Desert Boots',
                'features': ['casual', 'suede', 'versatile', 'comfortable'],
                'image_url': 'https://images.unsplash.com/photo-1544966503-7cc5ac882d5f?w=400&h=400&fit=crop'
            },
            {
                'name': 'Boat Shoes',
                'features': ['preppy', 'leather', 'casual', 'classic'],
                'image_url': 'https://images.unsplash.com/photo-1535043934128-cf0b28d52f95?w=400&h=400&fit=crop'
            }
        ],
        'layering': [
            {
                'name': 'Navy Blazer',
                'features': ['professional', 'versatile', 'structured', 'classic'],
                'image_url': 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&h=400&fit=crop'
            },
            {
                'name': 'Quarter-Zip Pullover',
                'features': ['sporty', 'comfortable', 'casual', 'modern'],
                'image_url': 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&h=400&fit=crop'
            },
            {
                'name': 'Bomber Jacket',
                'features': ['trendy', 'casual', 'modern', 'versatile'],
                'image_url': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=400&fit=crop'
            },
            {
                'name': 'Leather Jacket',
                'features': ['edgy', 'bold', 'classic', 'statement'],
                'image_url': 'https://images.unsplash.com/photo-1520975916090-3105956dac38?w=400&h=400&fit=crop'
            }
        ],
        'accessory': [
            {
                'name': 'Classic Watch',
                'features': ['timeless', 'sophisticated', 'metal', 'professional'],
                'image_url': 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=400&h=400&fit=crop'
            },
            {
                'name': 'Leather Belt',
                'features': ['classic', 'versatile', 'leather', 'essential'],
                'image_url': 'https://images.unsplash.com/photo-1601924638867-985c6d427917?w=400&h=400&fit=crop'
            },
            {
                'name': 'Messenger Bag',
                'features': ['professional', 'practical', 'leather', 'structured'],
                'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop'
            },
            {
                'name': 'Baseball Cap',
                'features': ['casual', 'sporty', 'cotton', 'relaxed'],
                'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop'
            }
        ],
        'complete_outfit': [
            {
                'name': 'Business Professional',
                'features': ['formal', 'sophisticated', 'coordinated', 'sharp'],
                'image_url': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=400&fit=crop'
            },
            {
                'name': 'Smart Casual',
                'features': ['polished', 'relaxed', 'versatile', 'modern'],
                'image_url': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=400&h=400&fit=crop'
            },
            {
                'name': 'Weekend Casual',
                'features': ['comfortable', 'laid_back', 'effortless', 'stylish'],
                'image_url': 'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=400&fit=crop'
            },
            {
                'name': 'Athletic Wear',
                'features': ['sporty', 'functional', 'comfortable', 'modern'],
                'image_url': 'https://images.unsplash.com/photo-1506629905607-edb8913e2842?w=400&h=400&fit=crop'
            }
        ]
    }
    
    # Create items for both genders with appropriate items
    created_items = []
    gender_items = {'female': female_items, 'male': male_items}
    
    for gender, item_categories in gender_items.items():
        for category, items in item_categories.items():
            for item_data in items:
                # Check if item already exists
                existing = db.query(QuizClothingItem).filter(
                    QuizClothingItem.name == item_data['name'],
                    QuizClothingItem.gender == gender,
                    QuizClothingItem.category == category
                ).first()
                
                if not existing:
                    item = QuizClothingItem(
                        name=item_data['name'],
                        gender=gender,
                        category=category,
                        features=item_data['features'],
                        image_url=item_data['image_url'],
                        is_active=True,
                        selection_count=0
                    )
                    db.add(item)
                    created_items.append(f"{gender} {category}: {item_data['name']}")
    
    db.commit()
    return created_items


def create_sample_style_categories(db: Session):
    """Create sample style categories"""
    
    style_categories = [
        # Female categories (10)
        {
            "name": "bohemian",
            "description": "Free-spirited style with flowing fabrics and artistic touches",
            "gender": "female",  # Updated to match database schema
            "features": ["boho", "flowy", "prints", "crochet", "indie", "artistic", "free-spirited"]
        },
        {
            "name": "minimalist",
            "description": "Clean, minimal aesthetic with sophisticated modern touches",
            "gender": "female",  # Updated to match database schema
            "features": ["minimal", "modern", "clean", "sophisticated", "neutral", "sleek"]
        },
        {
            "name": "y2k",
            "description": "Fashion-forward style with trendy Y2K and statement pieces",
            "gender": "female",  # Updated to match database schema
            "features": ["trendy", "y2k", "micro", "baby-tee", "mesh", "bold", "statement"]
        },
        {
            "name": "vintage",
            "description": "Retro-inspired looks with thrifted and vintage aesthetic",
            "gender": "female",  # Updated to match database schema
            "features": ["vintage", "thrift", "70s", "90s", "corsets", "mom-jeans", "retro"]
        },
        {
            "name": "athletic",
            "description": "Athletic-inspired comfortable wear for active lifestyles",
            "gender": "female",  # Updated to match database schema
            "features": ["athletic", "sporty", "comfortable", "activewear", "casual", "performance"]
        },
        {
            "name": "classic",
            "description": "Timeless, refined style with polished and tailored pieces",
            "gender": "female",  # Updated to match database schema
            "features": ["elegant", "timeless", "tailored", "refined", "classic", "polished"]
        },
        {
            "name": "workwear",
            "description": "Professional style with structured and business-appropriate pieces",
            "gender": "female",  # Updated to match database schema
            "features": ["professional", "structured", "business", "formal", "polished", "tailored"]
        },
        {
            "name": "romantic",
            "description": "Soft, delicate style with romantic details and pretty pastels",
            "gender": "female",  # Updated to match database schema
            "features": ["romantic", "feminine", "pastels", "ruffles", "soft", "delicate", "pretty"]
        },
        {
            "name": "preppy",
            "description": "Collegiate-inspired style with refined traditional elements",
            "gender": "female",  # Updated to match database schema
            "features": ["preppy", "collegiate", "polo", "refined", "traditional", "clean"]
        },
        {
            "name": "streetwear",
            "description": "Urban-inspired style with oversized fits and bold statements",
            "gender": "female",  # Updated to match database schema
            "features": ["oversized", "graphic", "sneakers", "urban", "bold", "edgy", "casual"]
        },
        
        # Male categories (10)
        {
            "name": "bohemian",
            "description": "Free-spirited style with artistic and unconventional touches",
            "gender": "male",  # Updated to match database schema
            "features": ["boho", "artistic", "unconventional", "flowing", "indie", "creative"]
        },
        {
            "name": "minimalist",
            "description": "Clean, minimal aesthetic with neutral colors and simple fits",
            "gender": "male",  # Updated to match database schema
            "features": ["clean", "minimal", "neutral", "simple", "fitted", "monochrome"]
        },
        {
            "name": "y2k",
            "description": "Trendy style with Y2K and statement pieces",
            "gender": "male",  # Updated to match database schema
            "features": ["trendy", "y2k", "bold", "statement", "modern", "fashion-forward"]
        },
        {
            "name": "vintage",
            "description": "Nostalgic style with vintage and throwback influences",
            "gender": "male",  # Updated to match database schema
            "features": ["vintage", "retro", "70s", "80s", "90s", "nostalgic", "throwback"]
        },
        {
            "name": "athletic",
            "description": "Athletic-inspired comfortable wear for active lifestyles",
            "gender": "male",  # Updated to match database schema
            "features": ["athletic", "sporty", "comfortable", "activewear", "casual", "performance"]
        },
        {
            "name": "classic",
            "description": "Traditional business and formal wear with structured fits",
            "gender": "male",  # Updated to match database schema
            "features": ["tailored", "business", "formal", "structured", "classic", "professional"]
        },
        {
            "name": "workwear",
            "description": "Rugged, utilitarian style with heritage and workwear influences",
            "gender": "male",  # Updated to match database schema
            "features": ["denim", "rugged", "heritage", "workwear", "boots", "utilitarian", "sturdy"]
        },
        {
            "name": "romantic",
            "description": "Soft, refined style with delicate and sophisticated touches",
            "gender": "male",  # Updated to match database schema
            "features": ["soft", "refined", "sophisticated", "delicate", "gentle", "elegant"]
        },
        {
            "name": "preppy",
            "description": "Collegiate-inspired style with refined traditional elements",
            "gender": "male",  # Updated to match database schema
            "features": ["preppy", "collegiate", "polo", "chino", "loafers", "traditional", "refined"]
        },
        {
            "name": "streetwear",
            "description": "Urban style with oversized fits and graphic elements",
            "gender": "male",  # Updated to match database schema
            "features": ["graphic", "oversized", "sneakers", "urban", "bold", "casual", "baggy"]
        }
    ]
    
    created_categories = []
    for cat_data in style_categories:
        # Check if category already exists
        existing = db.query(StyleCategory).filter(
            StyleCategory.name == cat_data['name'],
            StyleCategory.gender == cat_data['gender']
        ).first()
        
        if not existing:
            category = StyleCategory(
                name=cat_data['name'],
                gender=cat_data['gender'],
                features=cat_data['features'],
                description=cat_data['description'],
                is_active=True
            )
            db.add(category)
            created_categories.append(f"{cat_data['gender']}: {cat_data['name']}")
    
    db.commit()
    return created_categories


def main():
    """Main function to populate quiz data"""
    print("🎯 Populating quiz database with sample data...")
    
    # Get database session
    db = next(get_sync_session())
    
    try:
        # Create style categories first
        print("\n📝 Creating style categories...")
        created_categories = create_sample_style_categories(db)
        if created_categories:
            print(f"✅ Created {len(created_categories)} style categories:")
            for cat in created_categories:
                print(f"   - {cat}")
        else:
            print("ℹ️  All style categories already exist")
        
        # Create clothing items
        print("\n👕 Creating clothing items...")
        created_items = create_sample_clothing_items(db)
        if created_items:
            print(f"✅ Created {len(created_items)} clothing items:")
            for item in created_items[:10]:  # Show first 10
                print(f"   - {item}")
            if len(created_items) > 10:
                print(f"   ... and {len(created_items) - 10} more")
        else:
            print("ℹ️  All clothing items already exist")
        
        # Show current counts
        print("\n📊 Current database counts:")
        categories_count = db.query(StyleCategory).count()
        items_count = db.query(QuizClothingItem).count()
        print(f"   - Style Categories: {categories_count}")
        print(f"   - Clothing Items: {items_count}")
        
        print("\n🎉 Quiz database populated successfully!")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
