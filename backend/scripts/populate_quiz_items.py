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
    
    # Sample items for each category
    sample_items = {
        'top': [
            {
                'name': 'Classic White T-Shirt',
                'features': ['casual', 'versatile', 'cotton', 'crew_neck'],
                'image_url': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=400&fit=crop'
            },
            {
                'name': 'Silk Blouse',
                'features': ['formal', 'elegant', 'silk', 'button_up'],
                'image_url': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=400&fit=crop'
            },
            {
                'name': 'Striped Long Sleeve',
                'features': ['casual', 'nautical', 'cotton', 'stripes'],
                'image_url': 'https://images.unsplash.com/photo-1571945153237-4929e783af4a?w=400&h=400&fit=crop'
            },
            {
                'name': 'Cozy Sweater',
                'features': ['warm', 'casual', 'knit', 'oversized'],
                'image_url': 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&h=400&fit=crop'
            }
        ],
        'bottom': [
            {
                'name': 'Dark Wash Jeans',
                'features': ['casual', 'denim', 'versatile', 'straight_leg'],
                'image_url': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400&h=400&fit=crop'
            },
            {
                'name': 'Black Trousers',
                'features': ['formal', 'professional', 'tailored', 'straight_leg'],
                'image_url': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=400&fit=crop'
            },
            {
                'name': 'Flowy Skirt',
                'features': ['feminine', 'flowy', 'midi_length', 'chiffon'],
                'image_url': 'https://images.unsplash.com/photo-1583496661160-fb5886a13d53?w=400&h=400&fit=crop'
            },
            {
                'name': 'High-Waisted Shorts',
                'features': ['casual', 'high_waisted', 'cotton', 'summer'],
                'image_url': 'https://images.unsplash.com/photo-1591195853828-11db59a44f6b?w=400&h=400&fit=crop'
            }
        ],
        'shoes': [
            {
                'name': 'White Sneakers',
                'features': ['casual', 'comfortable', 'versatile', 'leather'],
                'image_url': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop'
            },
            {
                'name': 'Black Heels',
                'features': ['formal', 'elegant', 'pointed_toe', 'leather'],
                'image_url': 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400&h=400&fit=crop'
            },
            {
                'name': 'Brown Boots',
                'features': ['casual', 'leather', 'ankle_height', 'versatile'],
                'image_url': 'https://images.unsplash.com/photo-1544966503-7cc5ac882d5f?w=400&h=400&fit=crop'
            },
            {
                'name': 'Ballet Flats',
                'features': ['comfortable', 'feminine', 'versatile', 'leather'],
                'image_url': 'https://images.unsplash.com/photo-1535043934128-cf0b28d52f95?w=400&h=400&fit=crop'
            }
        ],
        'layering': [
            {
                'name': 'Denim Jacket',
                'features': ['casual', 'denim', 'versatile', 'classic'],
                'image_url': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=400&fit=crop'
            },
            {
                'name': 'Black Blazer',
                'features': ['formal', 'structured', 'professional', 'versatile'],
                'image_url': 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&h=400&fit=crop'
            },
            {
                'name': 'Cardigan',
                'features': ['cozy', 'soft', 'knit', 'button_up'],
                'image_url': 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&h=400&fit=crop'
            },
            {
                'name': 'Leather Jacket',
                'features': ['edgy', 'leather', 'modern', 'statement'],
                'image_url': 'https://images.unsplash.com/photo-1520975916090-3105956dac38?w=400&h=400&fit=crop'
            }
        ],
        'accessory': [
            {
                'name': 'Silk Scarf',
                'features': ['elegant', 'silk', 'pattern', 'versatile'],
                'image_url': 'https://images.unsplash.com/photo-1601924638867-985c6d427917?w=400&h=400&fit=crop'
            },
            {
                'name': 'Leather Handbag',
                'features': ['professional', 'leather', 'structured', 'classic'],
                'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop'
            },
            {
                'name': 'Statement Necklace',
                'features': ['bold', 'statement', 'metal', 'decorative'],
                'image_url': 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=400&h=400&fit=crop'
            },
            {
                'name': 'Canvas Tote',
                'features': ['casual', 'canvas', 'practical', 'eco_friendly'],
                'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop'
            }
        ],
        'complete_outfit': [
            {
                'name': 'Business Casual Set',
                'features': ['professional', 'polished', 'coordinated', 'versatile'],
                'image_url': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=400&fit=crop'
            },
            {
                'name': 'Weekend Casual Look',
                'features': ['relaxed', 'comfortable', 'effortless', 'casual'],
                'image_url': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=400&h=400&fit=crop'
            },
            {
                'name': 'Date Night Outfit',
                'features': ['elegant', 'romantic', 'stylish', 'sophisticated'],
                'image_url': 'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=400&fit=crop'
            },
            {
                'name': 'Athleisure Set',
                'features': ['sporty', 'comfortable', 'modern', 'versatile'],
                'image_url': 'https://images.unsplash.com/photo-1506629905607-edb8913e2842?w=400&h=400&fit=crop'
            }
        ]
    }
    
    # Create items for both male and female
    created_items = []
    for gender in ['male', 'female']:
        for category, items in sample_items.items():
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
        {
            'name': 'Classic Minimalist',
            'gender': 'female',
            'features': ['clean_lines', 'neutral_colors', 'simple', 'timeless'],
            'description': 'Clean, simple lines with neutral colors and timeless pieces'
        },
        {
            'name': 'Romantic Feminine',
            'gender': 'female', 
            'features': ['flowy', 'soft', 'feminine', 'delicate'],
            'description': 'Soft, flowing fabrics with feminine details and romantic touches'
        },
        {
            'name': 'Modern Professional',
            'gender': 'female',
            'features': ['structured', 'tailored', 'professional', 'polished'],
            'description': 'Tailored pieces perfect for the modern professional woman'
        },
        {
            'name': 'Casual Chic',
            'gender': 'female',
            'features': ['effortless', 'relaxed', 'stylish', 'comfortable'],
            'description': 'Effortlessly stylish pieces that are both comfortable and chic'
        },
        # Male categories
        {
            'name': 'Classic Gentleman',
            'gender': 'male',
            'features': ['tailored', 'classic', 'sophisticated', 'timeless'],
            'description': 'Timeless, well-tailored pieces for the classic gentleman'
        },
        {
            'name': 'Modern Casual',
            'gender': 'male',
            'features': ['relaxed', 'contemporary', 'versatile', 'comfortable'],
            'description': 'Contemporary casual wear with a modern edge'
        },
        {
            'name': 'Urban Professional',
            'gender': 'male',
            'features': ['sharp', 'professional', 'modern', 'polished'],
            'description': 'Sharp, professional attire for the urban businessman'
        },
        {
            'name': 'Relaxed Contemporary',
            'gender': 'male',
            'features': ['laid_back', 'modern', 'comfortable', 'stylish'],
            'description': 'Laid-back yet stylish pieces for everyday wear'
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
