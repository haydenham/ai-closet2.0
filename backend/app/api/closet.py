"""
Closet management API endpoints with GCP Vision integration
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select

from app.core.database import get_async_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.clothing_item import ClothingItem, ClothingCategory
from app.schemas.clothing_item import (
    ClothingItemResponse,
    ClothingItemUpdate,
    ClothingItemUpload,
    ClothingItemSearch,
    ClothingItemStats,
    ClothingCategoryResponse,
    ClothingCategoryCreate,
    ClothingCategoryUpdate
)
from app.services.gcp_storage_service import GCPStorageService
from app.services.gcp_vision_service import GCPVisionService

router = APIRouter(prefix="/closet", tags=["closet"])

# Initialize services (with error handling for testing)
try:
    storage_service = GCPStorageService()
    vision_service = GCPVisionService()
except ImportError:
    # For testing environments without GCP dependencies
    storage_service = None
    vision_service = None


@router.post("/upload", response_model=ClothingItemResponse)
async def upload_clothing_item(
    file: UploadFile = File(...),
    category: str = Form(...),
    category_id: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string of tags
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a clothing item with automatic feature extraction using GCP Vision API
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read file data
    file_data = await file.read()
    
    try:
        # Check if services are available
        if not storage_service or not vision_service:
            raise HTTPException(status_code=503, detail="GCP services not available")
        
        # Upload to GCP Storage
        image_url, stored_filename = storage_service.upload_user_image(
            file_data=file_data,
            user_id=str(current_user.id),
            filename=file.filename,
            content_type=file.content_type
        )
        
        # Analyze image with GCP Vision API for automatic feature extraction
        vision_analysis = vision_service.analyze_clothing_image(file_data)
        
        # Parse tags from form data
        parsed_tags = []
        if tags:
            import json
            try:
                parsed_tags = json.loads(tags)
            except json.JSONDecodeError:
                parsed_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Merge user-provided tags with extracted features
        extracted_features = vision_analysis.get('extracted_features', [])
        all_tags = list(set(parsed_tags + extracted_features))
        
        # Use suggested category if user didn't provide one or if Vision API has high confidence
        final_category = category
        suggested_category = vision_analysis.get('suggested_category', 'unknown')
        if suggested_category != 'unknown' and not category:
            final_category = suggested_category
        
        # Use detected colors if not provided
        final_color = color
        if not color and vision_analysis.get('dominant_colors'):
            dominant_color = vision_analysis['dominant_colors'][0]
            final_color = dominant_color.get('color_name', 'unknown')
        
        # Create clothing item
        clothing_item = ClothingItem(
            user_id=current_user.id,
            filename=stored_filename,
            original_filename=file.filename,
            image_url=image_url,
            category=final_category,
            category_id=uuid.UUID(category_id) if category_id else None,
            color=final_color,
            brand=brand,
            size=size,
            description=description,
            tags=all_tags,
            file_size=len(file_data)
        )
        
        db.add(clothing_item)
        await db.commit()
        await db.refresh(clothing_item)
        
        return clothing_item
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload clothing item: {str(e)}")


@router.get("/items", response_model=List[ClothingItemResponse])
async def get_closet_items(
    category: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    size: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's closet items with filtering and pagination
    """
    query = select(ClothingItem).filter(ClothingItem.user_id == current_user.id)
    
    # Apply filters
    if category:
        query = query.filter(ClothingItem.category.ilike(f"%{category}%"))
    if color:
        query = query.filter(ClothingItem.color.ilike(f"%{color}%"))
    if brand:
        query = query.filter(ClothingItem.brand.ilike(f"%{brand}%"))
    if size:
        query = query.filter(ClothingItem.size.ilike(f"%{size}%"))
    if tags:
        # Filter items that have any of the specified tags
        for tag in tags:
            query = query.filter(ClothingItem.tags.op('?')(tag))
    
    # Order by most recent first
    query = query.order_by(desc(ClothingItem.upload_date))
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return items


@router.get("/items/{item_id}", response_model=ClothingItemResponse)
async def get_clothing_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific clothing item by ID
    """
    query = select(ClothingItem).filter(
        ClothingItem.id == item_id,
        ClothingItem.user_id == current_user.id
    )
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Clothing item not found")
    
    return item


@router.put("/items/{item_id}", response_model=ClothingItemResponse)
async def update_clothing_item(
    item_id: uuid.UUID,
    item_update: ClothingItemUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update a clothing item with automatic feature re-extraction if needed
    """
    query = select(ClothingItem).filter(
        ClothingItem.id == item_id,
        ClothingItem.user_id == current_user.id
    )
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Clothing item not found")
    
    # Update fields
    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    # If category changed significantly, re-analyze with Vision API
    if item_update.category and item_update.category != item.category:
        try:
            # Re-analyze the image for better feature extraction
            if vision_service:
                import requests
                response = requests.get(item.image_url)
                if response.status_code == 200:
                    vision_analysis = vision_service.analyze_clothing_image(response.content)
                
                # Update tags with new extracted features
                extracted_features = vision_analysis.get('extracted_features', [])
                existing_tags = item.tags or []
                
                # Merge existing user tags with new extracted features
                all_tags = list(set(existing_tags + extracted_features))
                item.tags = all_tags
                
        except Exception:
            # If re-analysis fails, continue with user updates
            pass
    
    await db.commit()
    await db.refresh(item)
    
    return item


@router.delete("/items/{item_id}")
async def delete_clothing_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a clothing item and its associated image from storage
    """
    query = select(ClothingItem).filter(
        ClothingItem.id == item_id,
        ClothingItem.user_id == current_user.id
    )
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Clothing item not found")
    
    try:
        # Delete from GCP Storage
        if storage_service:
            storage_service.delete_image(item.filename, bucket_type="uploads")
        
        # Delete from database
        await db.delete(item)
        await db.commit()
        
        return {"message": "Clothing item deleted successfully"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete clothing item: {str(e)}")


@router.get("/categories", response_model=List[ClothingCategoryResponse])
async def get_clothing_categories(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get all clothing categories organized hierarchically
    """
    query = select(ClothingCategory).order_by(ClothingCategory.name)
    result = await db.execute(query)
    categories = result.scalars().all()
    return categories


@router.post("/categories", response_model=ClothingCategoryResponse)
async def create_clothing_category(
    category_data: ClothingCategoryCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new clothing category
    """
    # Check if category already exists
    query = select(ClothingCategory).filter(ClothingCategory.name == category_data.name)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    category = ClothingCategory(**category_data.dict())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return category


@router.get("/stats", response_model=ClothingItemStats)
async def get_closet_statistics(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive closet statistics with feature-based analytics
    """
    # Total items count
    total_query = select(func.count(ClothingItem.id)).filter(
        ClothingItem.user_id == current_user.id
    )
    total_result = await db.execute(total_query)
    total_items = total_result.scalar()
    
    # Items by category
    category_query = select(
        ClothingItem.category,
        func.count(ClothingItem.id).label('count')
    ).filter(
        ClothingItem.user_id == current_user.id
    ).group_by(ClothingItem.category)
    
    category_result = await db.execute(category_query)
    category_stats = category_result.all()
    items_by_category = {stat.category: stat.count for stat in category_stats}
    
    # Items by color
    color_query = select(
        ClothingItem.color,
        func.count(ClothingItem.id).label('count')
    ).filter(
        ClothingItem.user_id == current_user.id,
        ClothingItem.color.isnot(None)
    ).group_by(ClothingItem.color)
    
    color_result = await db.execute(color_query)
    color_stats = color_result.all()
    items_by_color = {stat.color: stat.count for stat in color_stats}
    
    # Most recommended items
    most_recommended_query = select(ClothingItem).filter(
        ClothingItem.user_id == current_user.id
    ).order_by(desc(ClothingItem.times_recommended)).limit(5)
    
    most_recommended_result = await db.execute(most_recommended_query)
    most_recommended = most_recommended_result.scalars().all()
    
    # Recent uploads
    recent_query = select(ClothingItem).filter(
        ClothingItem.user_id == current_user.id
    ).order_by(desc(ClothingItem.upload_date)).limit(5)
    
    recent_result = await db.execute(recent_query)
    recent_uploads = recent_result.scalars().all()
    
    return ClothingItemStats(
        total_items=total_items,
        items_by_category=items_by_category,
        items_by_color=items_by_color,
        most_recommended_items=most_recommended,
        recent_uploads=recent_uploads
    )


@router.get("/organize")
async def organize_closet_by_features(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Organize closet items by GCP Vision API extracted features and suggest improvements
    """
    # Get all user's items
    query = select(ClothingItem).filter(ClothingItem.user_id == current_user.id)
    result = await db.execute(query)
    items = result.scalars().all()
    
    organization_suggestions = {
        'by_color': {},
        'by_pattern': {},
        'by_texture': {},
        'by_style': {},
        'missing_features': [],
        'suggested_categories': {}
    }
    
    for item in items:
        tags = item.tags or []
        
        # Organize by color
        color_tags = [tag for tag in tags if tag in ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 'black', 'white', 'gray']]
        for color in color_tags:
            if color not in organization_suggestions['by_color']:
                organization_suggestions['by_color'][color] = []
            organization_suggestions['by_color'][color].append({
                'id': str(item.id),
                'category': item.category,
                'image_url': item.image_url
            })
        
        # Organize by pattern
        pattern_tags = [tag for tag in tags if tag in ['striped', 'polka-dot', 'floral', 'geometric', 'plaid', 'solid']]
        for pattern in pattern_tags:
            if pattern not in organization_suggestions['by_pattern']:
                organization_suggestions['by_pattern'][pattern] = []
            organization_suggestions['by_pattern'][pattern].append({
                'id': str(item.id),
                'category': item.category,
                'image_url': item.image_url
            })
        
        # Organize by texture
        texture_tags = [tag for tag in tags if tag in ['smooth', 'rough', 'knit', 'woven', 'leather', 'denim']]
        for texture in texture_tags:
            if texture not in organization_suggestions['by_texture']:
                organization_suggestions['by_texture'][texture] = []
            organization_suggestions['by_texture'][texture].append({
                'id': str(item.id),
                'category': item.category,
                'image_url': item.image_url
            })
        
        # Check for items with minimal feature extraction
        if len(tags) < 3:
            organization_suggestions['missing_features'].append({
                'id': str(item.id),
                'category': item.category,
                'current_tags': tags,
                'suggestion': 'Consider re-analyzing this item for better feature extraction'
            })
    
    return organization_suggestions


@router.post("/items/{item_id}/reanalyze")
async def reanalyze_clothing_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Re-analyze a clothing item with GCP Vision API to update features
    """
    query = select(ClothingItem).filter(
        ClothingItem.id == item_id,
        ClothingItem.user_id == current_user.id
    )
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Clothing item not found")
    
    try:
        # Check if vision service is available
        if not vision_service:
            raise HTTPException(status_code=503, detail="GCP Vision service not available")
        
        # Download image from URL
        import requests
        response = requests.get(item.image_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Could not access item image")
        
        # Re-analyze with Vision API
        vision_analysis = vision_service.analyze_clothing_image(response.content)
        
        # Update item with new analysis
        extracted_features = vision_analysis.get('extracted_features', [])
        suggested_category = vision_analysis.get('suggested_category', item.category)
        
        # Preserve user-added tags and merge with new extracted features
        existing_tags = item.tags or []
        user_tags = [tag for tag in existing_tags if tag not in extracted_features]
        all_tags = list(set(user_tags + extracted_features))
        
        item.tags = all_tags
        
        # Update category if Vision API suggests a better one
        if suggested_category != 'unknown' and suggested_category != item.category:
            item.category = suggested_category
        
        # Update color if detected and not set
        if not item.color and vision_analysis.get('dominant_colors'):
            dominant_color = vision_analysis['dominant_colors'][0]
            item.color = dominant_color.get('color_name', item.color)
        
        await db.commit()
        await db.refresh(item)
        
        return {
            'message': 'Item re-analyzed successfully',
            'updated_item': item,
            'analysis_results': {
                'extracted_features': extracted_features,
                'suggested_category': suggested_category,
                'dominant_colors': vision_analysis.get('dominant_colors', []),
                'confidence_scores': vision_analysis.get('confidence_scores', {})
            }
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to re-analyze item: {str(e)}")


@router.get("/analytics/features")
async def get_feature_analytics(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed analytics about extracted features across the user's closet
    """
    query = select(ClothingItem).filter(ClothingItem.user_id == current_user.id)
    result = await db.execute(query)
    items = result.scalars().all()
    
    feature_analytics = {
        'total_items_analyzed': len(items),
        'feature_frequency': {},
        'color_distribution': {},
        'pattern_distribution': {},
        'texture_distribution': {},
        'category_feature_mapping': {},
        'items_needing_reanalysis': []
    }
    
    for item in items:
        tags = item.tags or []
        category = item.category
        
        # Count feature frequency
        for tag in tags:
            feature_analytics['feature_frequency'][tag] = feature_analytics['feature_frequency'].get(tag, 0) + 1
        
        # Categorize features
        colors = [tag for tag in tags if tag in ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 'black', 'white', 'gray']]
        patterns = [tag for tag in tags if tag in ['striped', 'polka-dot', 'floral', 'geometric', 'plaid', 'solid']]
        textures = [tag for tag in tags if tag in ['smooth', 'rough', 'knit', 'woven', 'leather', 'denim']]
        
        for color in colors:
            feature_analytics['color_distribution'][color] = feature_analytics['color_distribution'].get(color, 0) + 1
        
        for pattern in patterns:
            feature_analytics['pattern_distribution'][pattern] = feature_analytics['pattern_distribution'].get(pattern, 0) + 1
        
        for texture in textures:
            feature_analytics['texture_distribution'][texture] = feature_analytics['texture_distribution'].get(texture, 0) + 1
        
        # Map features to categories
        if category not in feature_analytics['category_feature_mapping']:
            feature_analytics['category_feature_mapping'][category] = {}
        
        for tag in tags:
            if tag not in feature_analytics['category_feature_mapping'][category]:
                feature_analytics['category_feature_mapping'][category][tag] = 0
            feature_analytics['category_feature_mapping'][category][tag] += 1
        
        # Identify items that might need reanalysis (few features)
        if len(tags) < 2:
            feature_analytics['items_needing_reanalysis'].append({
                'id': str(item.id),
                'category': category,
                'current_features': tags,
                'upload_date': item.upload_date.isoformat()
            })
    
    return feature_analytics