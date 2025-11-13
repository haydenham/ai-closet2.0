#!/usr/bin/env python3
"""
Upload quiz images from local machine to GCP Storage and update database.

Usage:
    python scripts/upload_quiz_images.py /path/to/your/downloads/folder

Expected folder structure:
    /downloads/
        bohemian_pants.jpg
        streetwear_pants.jpg
        classic_pants.jpg
        ... (50 images total)

Naming convention:
    {style}_{type}.jpg
    Examples: bohemian_pants.jpg, classic_shirt.jpg, edgy_shoes.jpg
"""
import sys
import os
from pathlib import Path
from typing import Dict, List

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from google.cloud import storage
from app.core.database import get_sync_session
from app.models.quiz import QuizItem
from app.core.config import settings


# GCP Configuration
BUCKET_NAME = settings.gcs_bucket_name or "nomi-closet-uploads"
FOLDER_PREFIX = "quiz-items/"  # Store quiz images in their own folder


def upload_file_to_gcs(local_path: Path, destination_name: str) -> str:
    """
    Upload a file to GCS and return the public URL
    
    Args:
        local_path: Path to local file
        destination_name: Name in GCS bucket (e.g., 'quiz-items/bohemian_pants.jpg')
    
    Returns:
        Public URL of uploaded file
    """
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_name)
    
    # Upload file
    print(f"  Uploading {local_path.name}...", end=" ")
    blob.upload_from_filename(str(local_path))
    
    # Make public
    blob.make_public()
    
    print(f"✅")
    return blob.public_url


def parse_filename(filename: str) -> tuple[str, str]:
    """
    Parse filename to extract style and type
    
    Expected format: {style}_{type}.{ext}
    Examples: bohemian_pants.jpg, classic_shirt.png
    
    Returns:
        (style, type) tuple, e.g., ("Bohemian", "pants")
    """
    # Remove extension
    name_without_ext = filename.rsplit('.', 1)[0]
    
    # Split on underscore
    parts = name_without_ext.lower().split('_')
    
    if len(parts) != 2:
        raise ValueError(
            f"Invalid filename format: {filename}\n"
            f"Expected: {{style}}_{{type}}.{{ext}} (e.g., bohemian_pants.jpg)"
        )
    
    style_raw, type_raw = parts
    
    # Capitalize style name
    style = style_raw.capitalize()
    
    # Validate type
    valid_types = ['pants', 'shirt', 'shorts', 'overlayer', 'shoes']
    if type_raw not in valid_types:
        raise ValueError(
            f"Invalid type '{type_raw}' in filename: {filename}\n"
            f"Valid types: {', '.join(valid_types)}"
        )
    
    return style, type_raw


def find_quiz_item(db, style: str, question_type: str) -> QuizItem:
    """Find the quiz item in database matching style and type"""
    item = db.query(QuizItem).filter(
        QuizItem.style_category == style,
        QuizItem.question_type == question_type,
        QuizItem.gender == "female"
    ).first()
    
    if not item:
        raise ValueError(f"No quiz item found for {style} {question_type}")
    
    return item


def update_item_image_url(db, item: QuizItem, new_url: str):
    """Update the image URL for a quiz item"""
    old_url = item.image_url
    item.image_url = new_url
    db.commit()
    
    print(f"  📝 Updated database: {item.name}")
    print(f"     Old: {old_url[:60]}...")
    print(f"     New: {new_url[:60]}...")


def upload_quiz_images(images_folder: Path):
    """
    Main function to upload images and update database
    
    Args:
        images_folder: Path to folder containing quiz images
    """
    if not images_folder.exists():
        print(f"❌ Folder not found: {images_folder}")
        return
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    image_files = [
        f for f in images_folder.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    if not image_files:
        print(f"❌ No image files found in {images_folder}")
        print(f"   Looking for: {', '.join(image_extensions)}")
        return
    
    print(f"📁 Found {len(image_files)} image files in {images_folder}")
    print(f"🪣 Uploading to GCS bucket: {BUCKET_NAME}")
    print()
    
    db = next(get_sync_session())
    uploaded_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        for image_file in sorted(image_files):
            print(f"📸 Processing: {image_file.name}")
            
            try:
                # Parse filename
                style, question_type = parse_filename(image_file.name)
                
                # Find matching quiz item in database
                item = find_quiz_item(db, style, question_type)
                
                # Upload to GCS
                destination = f"{FOLDER_PREFIX}{image_file.name}"
                public_url = upload_file_to_gcs(image_file, destination)
                
                # Update database
                update_item_image_url(db, item, public_url)
                
                uploaded_count += 1
                print()
                
            except ValueError as e:
                print(f"  ⚠️  Skipped: {e}")
                skipped_count += 1
                print()
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                error_count += 1
                print()
        
        print("=" * 60)
        print(f"✨ Upload complete!")
        print(f"   Uploaded: {uploaded_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Errors: {error_count}")
        print(f"   Total processed: {len(image_files)}")
        
        if uploaded_count > 0:
            print(f"\n🎉 Successfully updated {uploaded_count} quiz items with new images!")
            print(f"   Images are now stored in: gs://{BUCKET_NAME}/{FOLDER_PREFIX}")
        
    finally:
        db.close()


def show_expected_files():
    """Show the expected file naming structure"""
    styles = ["bohemian", "streetwear", "classic", "feminine", "edgy", 
              "athleisure", "vintage", "glamorous", "eclectic", "minimalist"]
    types = ["pants", "shirt", "shorts", "overlayer", "shoes"]
    
    print("\n📋 Expected file names (50 total):\n")
    for style in styles:
        for q_type in types:
            print(f"   {style}_{q_type}.jpg")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Error: No folder path provided")
        print("\n📖 Usage:")
        print(f"   python {sys.argv[0]} /path/to/your/downloads/folder")
        print("\n📁 Example folder structure:")
        print("   /Users/you/Downloads/quiz-images/")
        print("      bohemian_pants.jpg")
        print("      streetwear_pants.jpg")
        print("      classic_shirt.jpg")
        print("      ...")
        show_expected_files()
        sys.exit(1)
    
    folder_path = Path(sys.argv[1])
    upload_quiz_images(folder_path)
