"""
Simplified quiz system models for style assessment
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, UUID, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class StyleCategory(Base):
    """Style categories for quiz system"""
    
    __tablename__ = "style_categories"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_theme_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
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
    
    def __repr__(self) -> str:
        return f"<StyleCategory(name='{self.name}', gender='{self.gender}')>"


class QuizItem(Base):
    """Quiz items (clothing images) for style assessment"""
    
    __tablename__ = "quiz_items"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Question type: pants, shirt, shorts, overlayer, shoes
    question_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Style category this item represents
    style_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    gender: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    display_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
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
    
    def __repr__(self) -> str:
        return f"<QuizItem(question='{self.question_type}', category='{self.style_category}')>"


class QuizResponse(Base):
    """User quiz responses and calculated style results"""
    
    __tablename__ = "quiz_responses"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # User's selections: {pants: uuid, shirt: uuid, shorts: uuid, overlayer: uuid, shoes: uuid}
    selected_items: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Calculated results
    primary_style: Mapped[str] = mapped_column(String(100), nullable=False)
    secondary_style: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    style_message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Score breakdown: {Bohemian: 3, Classic: 1, Streetwear: 1, ...}
    scores: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="quiz_responses")
    
    def __repr__(self) -> str:
        return f"<QuizResponse(user_id='{self.user_id}', primary='{self.primary_style}')>"
