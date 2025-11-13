#!/usr/bin/env python3
"""
Helper script to show which quiz images are missing from static folder.

Usage:
    python scripts/check_quiz_images.py
"""
import sys
from pathlib import Path

# Static files location
STATIC_DIR = Path(__file__).parent.parent / "static" / "quiz-items"

# Expected files
STYLES = ["bohemian", "streetwear", "classic", "feminine", "edgy", 
          "athleisure", "vintage", "glamorous", "eclectic", "minimalist"]
TYPES = ["pants", "shirt", "shorts", "overlayer", "shoes"]

EXPECTED_FILES = [
    f"{style}_{qtype}.jpg" 
    for style in STYLES 
    for qtype in TYPES
]


def check_images():
    """Check which images exist and which are missing"""
    
    if not STATIC_DIR.exists():
        print(f"❌ Static directory not found: {STATIC_DIR}")
        print(f"   Run: mkdir -p {STATIC_DIR}")
        return
    
    # Get existing files
    existing_files = {
        f.name for f in STATIC_DIR.iterdir() 
        if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']
    }
    
    # Also accept .png and .webp versions
    existing_basenames = {f.rsplit('.', 1)[0] for f in existing_files}
    
    missing = []
    found = []
    
    for expected in EXPECTED_FILES:
        basename = expected.rsplit('.', 1)[0]
        if basename in existing_basenames:
            found.append(expected)
        else:
            missing.append(expected)
    
    # Display results
    print("=" * 70)
    print(f"📊 Quiz Images Status")
    print("=" * 70)
    print(f"✅ Found: {len(found)}/50")
    print(f"❌ Missing: {len(missing)}/50")
    print()
    
    if found:
        print(f"✅ Found images ({len(found)}):")
        for f in sorted(found):
            print(f"   ✓ {f}")
        print()
    
    if missing:
        print(f"❌ Missing images ({len(missing)}):")
        for f in sorted(missing):
            # Parse to show style
            style, qtype = f.replace('.jpg', '').split('_')
            print(f"   ✗ {f:30} ({style.capitalize()} {qtype})")
        print()
        print("💡 Tip: Copy your images to:")
        print(f"   {STATIC_DIR}")
        print()
        print("   Rename them to match the expected filenames above")
    
    if len(found) == 50:
        print("🎉 All images found! Ready to go!")
        print()
        print("🚀 Next steps:")
        print("   1. Run update script:")
        print("      cd backend")
        print("      PYTHONPATH=$(pwd) python scripts/update_quiz_to_static_urls.py")
        print()
        print("   2. Restart backend:")
        print("      make dev")
    
    print("=" * 70)


if __name__ == "__main__":
    check_images()
