#!/usr/bin/env python3
"""
Update quiz item URLs to point to static files in the codebase.

This replaces the Unsplash placeholder URLs with local static file URLs.

Usage:
    PYTHONPATH=/path/to/backend python scripts/update_quiz_to_static_urls.py
    
After running this, copy your 50 images to:
    backend/static/quiz-items/
    
With filenames like:
    bohemian_pants.jpg
    streetwear_shirt.jpg
    etc.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_sync_session
from app.models.quiz import QuizItem
from app.core.config import settings


def update_to_static_urls(base_url: str = None):
    """
    Update all quiz item image URLs to point to static files
    
    Args:
        base_url: Base URL for static files (defaults to localhost:8000 for dev)
    """
    if base_url is None:
        # Use localhost for development
        base_url = "http://localhost:8000"
    
    db = next(get_sync_session())
    
    try:
        items = db.query(QuizItem).filter(QuizItem.gender == "female").all()
        
        print(f"📝 Updating {len(items)} quiz items to use static file URLs...\n")
        
        updated = 0
        for item in items:
            # Generate static file URL
            style_lower = item.style_category.lower()
            filename = f"{style_lower}_{item.question_type}.jpg"
            static_url = f"{base_url}/static/quiz-items/{filename}"
            
            old_url = item.image_url
            item.image_url = static_url
            
            print(f"✅ {item.name}")
            print(f"   Old: {old_url[:60]}...")
            print(f"   New: {static_url}")
            print()
            updated += 1
        
        db.commit()
        
        print("=" * 70)
        print(f"✨ Updated {updated} items!")
        print()
        print("📁 Next steps:")
        print("   1. Copy your 50 images to: backend/static/quiz-items/")
        print("   2. Name them using the pattern: {style}_{type}.jpg")
        print()
        print("📋 Expected filenames:")
        print("   bohemian_pants.jpg, bohemian_shirt.jpg, bohemian_shorts.jpg, ...")
        print("   streetwear_pants.jpg, streetwear_shirt.jpg, ...")
        print("   etc. (see static/quiz-items/README.md for full list)")
        print()
        print("🚀 After copying images, restart the backend:")
        print("   cd backend && make dev")
        print()
        print("✅ Images will be served at:")
        print(f"   {base_url}/static/quiz-items/{{filename}}")
        
    finally:
        db.close()


if __name__ == "__main__":
    # Check if custom base URL provided
    base_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    if base_url:
        print(f"Using custom base URL: {base_url}")
    else:
        print("Using default base URL: http://localhost:8000")
        print("(Pass a different URL as argument if needed)")
    
    print()
    update_to_static_urls(base_url)
