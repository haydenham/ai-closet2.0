#!/usr/bin/env python3
"""
Update quiz item image URLs after manually uploading to GCS.
Use this if you uploaded images via GCP Console instead of the upload script.

Usage:
    python scripts/update_quiz_urls_from_gcs.py
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_sync_session
from app.models.quiz import QuizItem
from app.core.config import settings

BUCKET_NAME = settings.gcs_bucket_name or "nomi-closet-uploads"
FOLDER_PREFIX = "quiz-items/"


def parse_filename(filename: str) -> tuple[str, str]:
    """Parse GCS filename to extract style and type"""
    name_without_ext = filename.rsplit('.', 1)[0]
    parts = name_without_ext.lower().split('_')
    
    if len(parts) != 2:
        return None, None
    
    style_raw, type_raw = parts
    return style_raw.capitalize(), type_raw


def update_urls_from_gcs():
    """Update database with GCS URLs based on expected naming convention"""
    db = next(get_sync_session())
    
    try:
        items = db.query(QuizItem).filter(QuizItem.gender == "female").all()
        
        print(f"📝 Updating {len(items)} quiz items with GCS URLs...\n")
        
        updated = 0
        for item in items:
            # Generate expected GCS URL
            style_lower = item.style_category.lower()
            filename = f"{style_lower}_{item.question_type}.jpg"
            gcs_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{FOLDER_PREFIX}{filename}"
            
            old_url = item.image_url
            item.image_url = gcs_url
            
            print(f"✅ {item.name}")
            print(f"   {gcs_url}")
            updated += 1
        
        db.commit()
        print(f"\n✨ Updated {updated} items!")
        
    finally:
        db.close()


if __name__ == "__main__":
    update_urls_from_gcs()
