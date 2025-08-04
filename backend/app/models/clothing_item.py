"""
Clothing item model for closet management
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, UUID, JSON, Float, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY

from app.core.database import Base


class ClothingCategory(Base):
    """Clothing category model for organizing items"""
    
    __tablename__ = "clothing_categories"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    parent_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clothing_categories.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Self-referential relationship for hierarchical categories
    parent_category: Mapped[Optional["ClothingCategory"]] = relationship(
        "ClothingCategory",
        remote_side=[id],
        back_populates="subcategories"
    )
    
    subcategories: Mapped[List["ClothingCategory"]] = relationship(
        "ClothingCategory",
        back_populates="parent_category"
    )
    
    # Relationship to clothing items
    clothing_items: Mapped[List["ClothingItem"]] = relationship(
        "ClothingItem",
        back_populates="category_obj"
    )
    
    def __repr__(self) -> str:
        return f"<ClothingCategory(id={self.id}, name={self.name})>"


class ClothingItem(Base):
    """Clothing item model for user's closet"""
    
    __tablename__ = "clothing_items"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Item metadata
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clothing_categories.id", ondelete="SET NULL"),
        nullable=True
    )
    
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Additional metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # CLIP embedding for similarity search
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Image processing metadata
    image_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    image_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in bytes
    
    # Usage tracking
    times_recommended: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_recommended: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Timestamps
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="clothing_items")
    
    category_obj: Mapped[Optional["ClothingCategory"]] = relationship(
        "ClothingCategory",
        back_populates="clothing_items"
    )
    
    # Many-to-many relationship with outfit recommendations
    outfit_recommendations: Mapped[List["OutfitRecommendation"]] = relationship(
        "OutfitRecommendation",
        secondary="outfit_clothing_items",
        back_populates="recommended_items"
    )
    
    def __repr__(self) -> str:
        return f"<ClothingItem(id={self.id}, category={self.category}, user_id={self.user_id})>"
    
    def has_tag(self, tag: str) -> bool:
        """Check if item has a specific tag"""
        return tag in (self.tags or [])
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the item"""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the item"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def increment_recommendation_count(self) -> None:
        """Increment the recommendation count and update last recommended time"""
        self.times_recommended += 1
        self.last_recommended = datetime.utcnow()
    
    @property
    def file_extension(self) -> str:
        """Get file extension from filename"""
        return self.filename.split('.')[-1].lower() if '.' in self.filename else ''
    
    @property
    def is_image(self) -> bool:
        """Check if file is an image based on extension"""
        image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
        return self.file_extension in image_extensions