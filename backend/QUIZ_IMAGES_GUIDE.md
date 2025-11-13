# Adding Quiz Images to Your Codebase

## Overview
Quiz images are static assets that live in your codebase at `backend/static/quiz-items/`. They're served directly by FastAPI and committed to Git, not stored in GCP Storage.

---

## Quick Start

### 1. Copy Your Images
```bash
# Copy your 50 downloaded images to:
cp ~/Downloads/quiz-images/* backend/static/quiz-items/
```

### 2. Rename to Match Expected Format
Images should be named: `{style}_{type}.jpg`

**Examples:**
- `bohemian_pants.jpg`
- `streetwear_shirt.jpg`
- `classic_shorts.jpg`
- `edgy_overlayer.jpg`
- `minimalist_shoes.jpg`

### 3. Check What You Have
```bash
cd backend
python scripts/check_quiz_images.py
```

This will show you:
- ✅ Which images are present
- ❌ Which images are missing
- 📋 Expected filenames

### 4. Update Database URLs
```bash
cd backend
PYTHONPATH=$(pwd) python scripts/update_quiz_to_static_urls.py
```

This updates all quiz items in the database to point to your local static files.

### 5. Restart Backend
```bash
make dev
```

---

## File Structure

```
backend/
├── static/
│   └── quiz-items/
│       ├── README.md          # Documentation
│       ├── .gitkeep           # Git tracking
│       ├── bohemian_pants.jpg
│       ├── bohemian_shirt.jpg
│       ├── bohemian_shorts.jpg
│       ├── bohemian_overlayer.jpg
│       ├── bohemian_shoes.jpg
│       ├── streetwear_pants.jpg
│       ├── ... (50 total)
│       └── minimalist_shoes.jpg
└── scripts/
    ├── check_quiz_images.py           # Check which images exist
    └── update_quiz_to_static_urls.py  # Update database URLs
```

---

## Complete List of Required Files (50 total)

### Bohemian (5)
- bohemian_pants.jpg
- bohemian_shirt.jpg
- bohemian_shorts.jpg
- bohemian_overlayer.jpg
- bohemian_shoes.jpg

### Streetwear (5)
- streetwear_pants.jpg
- streetwear_shirt.jpg
- streetwear_shorts.jpg
- streetwear_overlayer.jpg
- streetwear_shoes.jpg

### Classic (5)
- classic_pants.jpg
- classic_shirt.jpg
- classic_shorts.jpg
- classic_overlayer.jpg
- classic_shoes.jpg

### Feminine (5)
- feminine_pants.jpg
- feminine_shirt.jpg
- feminine_shorts.jpg
- feminine_overlayer.jpg
- feminine_shoes.jpg

### Edgy (5)
- edgy_pants.jpg
- edgy_shirt.jpg
- edgy_shorts.jpg
- edgy_overlayer.jpg
- edgy_shoes.jpg

### Athleisure (5)
- athleisure_pants.jpg
- athleisure_shirt.jpg
- athleisure_shorts.jpg
- athleisure_overlayer.jpg
- athleisure_shoes.jpg

### Vintage (5)
- vintage_pants.jpg
- vintage_shirt.jpg
- vintage_shorts.jpg
- vintage_overlayer.jpg
- vintage_shoes.jpg

### Glamorous (5)
- glamorous_pants.jpg
- glamorous_shirt.jpg
- glamorous_shorts.jpg
- glamorous_overlayer.jpg
- glamorous_shoes.jpg

### Eclectic (5)
- eclectic_pants.jpg
- eclectic_shirt.jpg
- eclectic_shorts.jpg
- eclectic_overlayer.jpg
- eclectic_shoes.jpg

### Minimalist (5)
- minimalist_pants.jpg
- minimalist_shirt.jpg
- minimalist_shorts.jpg
- minimalist_overlayer.jpg
- minimalist_shoes.jpg

---

## How It Works

### Static File Serving
FastAPI serves files from `backend/static/` at the `/static/` URL path:

```python
# In app/main.py
app.mount("/static", StaticFiles(directory="static"), name="static")
```

### Image URLs
Images are accessible at:
```
http://localhost:8000/static/quiz-items/bohemian_pants.jpg
http://localhost:8000/static/quiz-items/streetwear_shirt.jpg
etc.
```

### Database Storage
The `quiz_items` table stores these URLs:
```sql
SELECT name, image_url FROM quiz_items LIMIT 3;

-- Results:
-- "Bohemian Pants" | "http://localhost:8000/static/quiz-items/bohemian_pants.jpg"
-- "Streetwear Pants" | "http://localhost:8000/static/quiz-items/streetwear_pants.jpg"
-- "Classic Pants" | "http://localhost:8000/static/quiz-items/classic_pants.jpg"
```

---

## Image Requirements

### Format
- **Accepted**: JPG, PNG, WebP
- **Recommended**: JPG for photos
- **Naming**: lowercase with underscores (e.g., `bohemian_pants.jpg`)

### Size
- **Recommended dimensions**: 400x600px (portrait orientation)
- **Max file size**: 2MB per image
- **Aspect ratio**: 2:3 works best for clothing items

### Content
- Should clearly represent the style category
- Professional or high-quality product photos preferred
- Consistent lighting/background across images is nice but not required

---

## Troubleshooting

### "Images not loading in frontend"
1. Check files exist: `ls backend/static/quiz-items/`
2. Check backend is running: `curl http://localhost:8000/static/quiz-items/bohemian_pants.jpg`
3. Check database URLs are correct:
   ```bash
   cd backend
   python -c "from app.core.database import get_sync_session; from app.models.quiz import QuizItem; db = next(get_sync_session()); item = db.query(QuizItem).first(); print(item.image_url); db.close()"
   ```

### "Wrong filenames"
Run the check script to see what's expected:
```bash
python scripts/check_quiz_images.py
```

### "Need to rename many files"
Use a batch rename tool or script:
```bash
# Example: rename spaces to underscores and lowercase
cd backend/static/quiz-items/
for f in *.jpg; do
  new=$(echo "$f" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
  mv "$f" "$new"
done
```

---

## For Production

When deploying to production, you have two options:

### Option 1: Commit images to Git (Recommended for quiz images)
✅ Simple - images deploy with code
✅ Fast - no external API calls
✅ Free - no storage costs
⚠️ Repo size increases (50 images × ~100KB = ~5MB)

Just commit the images:
```bash
git add backend/static/quiz-items/*.jpg
git commit -m "Add quiz images"
```

Update the URL script for production:
```bash
python scripts/update_quiz_to_static_urls.py https://your-production-domain.com
```

### Option 2: Serve from CDN
If repo size is a concern, upload to CDN:
1. Upload images to Cloudflare R2, AWS S3, or similar
2. Update database URLs to CDN paths
3. Images load faster globally

---

## Scripts Reference

### check_quiz_images.py
Shows which images exist and which are missing
```bash
python scripts/check_quiz_images.py
```

### update_quiz_to_static_urls.py
Updates database to use static file URLs
```bash
# Development (localhost)
PYTHONPATH=$(pwd) python scripts/update_quiz_to_static_urls.py

# Production
PYTHONPATH=$(pwd) python scripts/update_quiz_to_static_urls.py https://your-domain.com
```

---

## Summary

**This approach is perfect for quiz images because:**
1. ✅ **Simple**: Just copy files to a folder
2. ✅ **No cloud costs**: Served directly by your app
3. ✅ **Fast**: No external API calls
4. ✅ **Version controlled**: Images tracked in Git
5. ✅ **Portable**: Works in dev and production

**The only storage you need GCP for is user-uploaded closet photos!**
