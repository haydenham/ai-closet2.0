"""
Style profile model for user fashion preferences and AI model assignment
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, UUID, JSON, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class StyleProfile(Base):
    """Style profile model for storing user fashion preferences and AI model assignment"""
    
    __tablename__ = "style_profiles"
    
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
        unique=True,  # One style profile per user
        index=True
    )
    
    # Quiz responses stored as JSON
    quiz_responses: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )
    
    # AI model assignment based on quiz results
    assigned_model: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Style preferences derived from quiz
    style_preferences: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
    
    # Additional profile metadata
    fashion_goals: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )
    
    preferred_colors: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )
    
    body_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    lifestyle: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    budget_range: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
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
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="style_profile")
    
    def __repr__(self) -> str:
        return f"<StyleProfile(id={self.id}, user_id={self.user_id}, model={self.assigned_model})>"
    
    def get_quiz_response(self, question_key: str) -> Any:
        """Get a specific quiz response by key"""
        return self.quiz_responses.get(question_key)
    
    def update_quiz_response(self, question_key: str, response: Any) -> None:
        """Update a specific quiz response"""
        if self.quiz_responses is None:
            self.quiz_responses = {}
        self.quiz_responses[question_key] = response
    
    def has_preference(self, preference: str) -> bool:
        """Check if user has a specific style preference"""
        return preference in (self.style_preferences or [])
    
    def add_preference(self, preference: str) -> None:
        """Add a style preference"""
        if self.style_preferences is None:
            self.style_preferences = []
        if preference not in self.style_preferences:
            self.style_preferences.append(preference)
    
    def remove_preference(self, preference: str) -> None:
        """Remove a style preference"""
        if self.style_preferences and preference in self.style_preferences:
            self.style_preferences.remove(preference)


class QuizQuestion(Base):
    """Quiz question model for style assessment"""
    
    __tablename__ = "quiz_questions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    question_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    question_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        default="multiple_choice"  # multiple_choice, single_choice, scale, text
    )
    
    options: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )
    
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    
    order_index: Mapped[int] = mapped_column(nullable=False, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
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
    
    def __repr__(self) -> str:
        return f"<QuizQuestion(id={self.id}, key={self.question_key})>"


