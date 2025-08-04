"""
Outfit recommendation model for AI-generated fashion suggestions
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, UUID, JSON, Integer, Table, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


# Association table for many-to-many relationship between OutfitRecommendation and ClothingItem
outfit_clothing_items = Table(
    "outfit_clothing_items",
    Base.metadata,
    Column("outfit_id", UUID(as_uuid=True), ForeignKey("outfit_recommendations.id", ondelete="CASCADE"), primary_key=True),
    Column("clothing_item_id", UUID(as_uuid=True), ForeignKey("clothing_items.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)


class OutfitRecommendation(Base):
    """Outfit recommendation model for storing AI-generated fashion suggestions"""
    
    __tablename__ = "outfit_recommendations"
    
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
    
    # User's original prompt
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    
    # AI model response
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Parsed outfit components from AI response
    outfit_components: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # AI model used for this recommendation
    ai_model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Recommendation metadata
    occasion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    weather: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    season: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # User feedback
    feedback_score: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )  # 1-5 rating scale
    
    feedback_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Recommendation status
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Processing metadata
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    similarity_scores: Mapped[Optional[Dict[str, float]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
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
    user: Mapped["User"] = relationship("User", back_populates="outfit_recommendations")
    
    recommended_items: Mapped[List["ClothingItem"]] = relationship(
        "ClothingItem",
        secondary=outfit_clothing_items,
        back_populates="outfit_recommendations"
    )
    
    feedback_entries: Mapped[List["RecommendationFeedback"]] = relationship(
        "RecommendationFeedback",
        back_populates="recommendation",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<OutfitRecommendation(id={self.id}, user_id={self.user_id}, model={self.ai_model_used})>"
    
    def add_clothing_item(self, clothing_item: "ClothingItem") -> None:
        """Add a clothing item to this recommendation"""
        if clothing_item not in self.recommended_items:
            self.recommended_items.append(clothing_item)
            clothing_item.increment_recommendation_count()
    
    def remove_clothing_item(self, clothing_item: "ClothingItem") -> None:
        """Remove a clothing item from this recommendation"""
        if clothing_item in self.recommended_items:
            self.recommended_items.remove(clothing_item)
    
    def get_items_by_category(self, category: str) -> List["ClothingItem"]:
        """Get recommended items filtered by category"""
        return [item for item in self.recommended_items if item.category == category]
    
    def set_feedback(self, score: int, comments: Optional[str] = None) -> None:
        """Set user feedback for this recommendation"""
        if not 1 <= score <= 5:
            raise ValueError("Feedback score must be between 1 and 5")
        self.feedback_score = score
        self.feedback_comments = comments
    
    @property
    def has_feedback(self) -> bool:
        """Check if recommendation has user feedback"""
        return self.feedback_score is not None
    
    @property
    def item_count(self) -> int:
        """Get count of recommended items"""
        return len(self.recommended_items)
    
    @property
    def categories_covered(self) -> List[str]:
        """Get list of clothing categories in this recommendation"""
        return list(set(item.category for item in self.recommended_items))


class RecommendationFeedback(Base):
    """Detailed feedback model for outfit recommendations"""
    
    __tablename__ = "recommendation_feedback"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("outfit_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Feedback details
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 scale
    
    feedback_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        default="general"  # general, item_specific, style_mismatch, etc.
    )
    
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Specific feedback categories
    style_accuracy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    item_matching: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 1-5
    occasion_appropriateness: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    
    # Additional metadata
    feedback_tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    recommendation: Mapped["OutfitRecommendation"] = relationship(
        "OutfitRecommendation",
        back_populates="feedback_entries"
    )
    
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<RecommendationFeedback(id={self.id}, rating={self.rating})>"


from sqlalchemy import Boolean