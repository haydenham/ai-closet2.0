"""
Pydantic schemas for ClothingItem model validation
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator, HttpUrl


class ClothingCategoryBase(BaseModel):
    """Base clothing category schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ClothingCategoryCreate(ClothingCategoryBase):
    """Schema for clothing category creation"""
    parent_category_id: Optional[uuid.UUID] = None


class ClothingCategoryUpdate(BaseModel):
    """Schema for clothing category updates"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parent_category_id: Optional[uuid.UUID] = None


class ClothingCategoryResponse(ClothingCategoryBase):
    """Schema for clothing category response"""
    id: uuid.UUID
    parent_category_id: Optional[uuid.UUID]
    
    class Config:
        from_attributes = True


class ClothingItemBase(BaseModel):
    """Base clothing item schema"""
    category: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)


class ClothingItemCreate(ClothingItemBase):
    """Schema for clothing item creation"""
    original_filename: str = Field(..., min_length=1, max_length=255)
    category_id: Optional[uuid.UUID] = None
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags list"""
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError('Tags must be a list')
        # Remove duplicates and empty strings
        return list(set(tag.strip() for tag in v if tag and tag.strip()))


class ClothingItemUpdate(BaseModel):
    """Schema for clothing item updates"""
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    category_id: Optional[uuid.UUID] = None
    color: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags list"""
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError('Tags must be a list')
        # Remove duplicates and empty strings
        return list(set(tag.strip() for tag in v if tag and tag.strip()))


class ClothingItemResponse(ClothingItemBase):
    """Schema for clothing item response"""
    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    original_filename: str
    image_url: str
    category_id: Optional[uuid.UUID]
    image_width: Optional[int]
    image_height: Optional[int]
    file_size: Optional[int]
    times_recommended: int
    last_recommended: Optional[datetime]
    upload_date: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
    @property
    def file_extension(self) -> str:
        """Get file extension from filename"""
        return self.filename.split('.')[-1].lower() if '.' in self.filename else ''
    
    @property
    def is_image(self) -> bool:
        """Check if file is an image based on extension"""
        image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
        return self.file_extension in image_extensions


class ClothingItemUpload(BaseModel):
    """Schema for clothing item file upload"""
    category: str = Field(..., min_length=1, max_length=100)
    category_id: Optional[uuid.UUID] = None
    color: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags list"""
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError('Tags must be a list')
        # Remove duplicates and empty strings
        return list(set(tag.strip() for tag in v if tag and tag.strip()))


class ClothingItemSearch(BaseModel):
    """Schema for clothing item search"""
    category: Optional[str] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    size: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ClothingItemStats(BaseModel):
    """Schema for clothing item statistics"""
    total_items: int
    items_by_category: dict
    items_by_color: dict
    most_recommended_items: List[ClothingItemResponse]
    recent_uploads: List[ClothingItemResponse]
    
    class Config:
        from_attributes = True


class EmbeddingResponse(BaseModel):
    """Schema for embedding response"""
    item_id: uuid.UUID
    embedding: List[float]
    embedding_model: str = "CLIP"
    created_at: datetime
    
    @validator('embedding')
    def validate_embedding(cls, v):
        """Validate embedding vector"""
        if not isinstance(v, list):
            raise ValueError('Embedding must be a list of floats')
        if not v:
            raise ValueError('Embedding cannot be empty')
        if not all(isinstance(x, (int, float)) for x in v):
            raise ValueError('All embedding values must be numeric')
        return v