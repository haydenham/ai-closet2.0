"""
Quiz system models for visual style assessment and feature-based matching
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, UUID, JSON, Integer, Boolean, DECIMAL, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class QuizClothingItem(Base):
    """Clothing items used in the visual style quiz"""
    
    __tablename__ = "quiz_clothing_items"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    gender: Mapped[str] = mapped_column(
        String(10), 
        nullable=False,
        index=True
    )
    
    category: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        index=True
    )
    
    # Key-value feature system
    features: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
    
    # Auto-extracted features from computer vision
    auto_extracted_features: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )
    
    # Confidence scores for each feature
    feature_confidence_scores: Mapped[Optional[Dict[str, float]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Usage tracking
    selection_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # User satisfaction when this item is selected
    satisfaction_score: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(3, 2),
        nullable=True
    )
    
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
    
    # Relationships
    quiz_responses: Mapped[List["QuizResponse"]] = relationship(
        "QuizResponse",
        secondary="quiz_response_items",
        back_populates="selected_items"
    )
    
    feature_learning_data: Mapped[List["FeatureLearningData"]] = relationship(
        "FeatureLearningData",
        back_populates="item"
    )
    
    __table_args__ = (
        CheckConstraint("gender IN ('male', 'female')", name='check_gender'),
    )
    
    def __repr__(self) -> str:
        return f"<QuizClothingItem(id={self.id}, name={self.name}, gender={self.gender})>"
    
    def has_feature(self, feature: str) -> bool:
        """Check if item has a specific feature"""
        return feature in (self.features or [])
    
    def add_feature(self, feature: str) -> None:
        """Add a feature to the item"""
        if self.features is None:
            self.features = []
        if feature not in self.features:
            self.features.append(feature)
    
    def remove_feature(self, feature: str) -> None:
        """Remove a feature from the item"""
        if self.features and feature in self.features:
            self.features.remove(feature)
    
    def increment_selection_count(self) -> None:
        """Increment selection count when item is chosen in quiz"""
        self.selection_count += 1
    
    def update_satisfaction_score(self, new_rating: int) -> None:
        """Update satisfaction score with new user rating"""
        if self.satisfaction_score is None:
            self.satisfaction_score = Decimal(str(new_rating))
        else:
            # Calculate running average
            current_count = self.selection_count or 1
            current_total = float(self.satisfaction_score) * (current_count - 1)
            new_average = (current_total + new_rating) / current_count
            self.satisfaction_score = Decimal(str(round(new_average, 2)))


class StyleCategory(Base):
    """Style categories for user classification"""
    
    __tablename__ = "style_categories"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    gender: Mapped[str] = mapped_column(
        String(10), 
        nullable=False,
        index=True
    )
    
    # Features that define this style category
    features: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
    
    # AI theme prompt for personalized recommendations
    ai_theme_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    
    # Relationships
    quiz_responses: Mapped[List["QuizResponse"]] = relationship(
        "QuizResponse",
        back_populates="assigned_category_obj"
    )
    
    __table_args__ = (
        CheckConstraint("gender IN ('male', 'female')", name='check_category_gender'),
    )
    
    def __repr__(self) -> str:
        return f"<StyleCategory(id={self.id}, name={self.name}, gender={self.gender})>"
    
    def has_feature(self, feature: str) -> bool:
        """Check if category includes a specific feature"""
        return feature in (self.features or [])
    
    def calculate_match_score(self, selected_features: List[str]) -> float:
        """Calculate how well selected features match this category"""
        if not selected_features or not self.features:
            return 0.0
        
        matching_features = set(selected_features) & set(self.features)
        return (len(matching_features) / len(selected_features)) * 100


class QuizResponse(Base):
    """User responses to the visual style quiz"""
    
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
    
    # Selected items stored as item IDs
    selected_item_ids: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
    
    # Calculated scores for each style category
    calculated_scores: Mapped[Dict[str, float]] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )
    
    assigned_category: Mapped[str] = mapped_column(String(100), nullable=False)
    
    assigned_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("style_categories.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Algorithm confidence in the assignment
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(3, 2),
        nullable=True
    )
    
    # User feedback
    user_satisfaction_rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    user_feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    assigned_category_obj: Mapped[Optional["StyleCategory"]] = relationship(
        "StyleCategory",
        back_populates="quiz_responses"
    )
    
    selected_items: Mapped[List["QuizClothingItem"]] = relationship(
        "QuizClothingItem",
        secondary="quiz_response_items",
        back_populates="quiz_responses"
    )
    
    __table_args__ = (
        CheckConstraint("user_satisfaction_rating >= 1 AND user_satisfaction_rating <= 5", 
                       name='check_satisfaction_rating'),
    )
    
    def __repr__(self) -> str:
        return f"<QuizResponse(id={self.id}, user_id={self.user_id}, category={self.assigned_category})>"


class QuizResponseItem(Base):
    """Association table for quiz responses and selected clothing items"""
    
    __tablename__ = "quiz_response_items"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    quiz_response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_responses.id", ondelete="CASCADE"),
        nullable=False
    )
    
    clothing_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_clothing_items.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Question context (e.g., "top", "bottom", "complete_outfit")
    question_category: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Weight for scoring algorithm
    weight: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(3, 2),
        nullable=True,
        default=Decimal('1.0')
    )
    
    def __repr__(self) -> str:
        return f"<QuizResponseItem(quiz_id={self.quiz_response_id}, item_id={self.clothing_item_id})>"


class FeatureLearningData(Base):
    """Data for smart feature learning system"""
    
    __tablename__ = "feature_learning_data"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_clothing_items.id", ondelete="CASCADE"),
        nullable=False
    )
    
    source: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        index=True
    )
    
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(3, 2),
        nullable=True
    )
    
    validation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejection_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    item: Mapped["QuizClothingItem"] = relationship(
        "QuizClothingItem",
        back_populates="feature_learning_data"
    )
    
    __table_args__ = (
        CheckConstraint("source IN ('manual', 'cv_auto', 'user_suggested', 'algorithm_discovered')", 
                       name='check_feature_source'),
    )
    
    def __repr__(self) -> str:
        return f"<FeatureLearningData(id={self.id}, feature={self.feature_name}, source={self.source})>"
    
    @property
    def validation_ratio(self) -> float:
        """Calculate validation ratio (positive validations / total validations)"""
        total = self.validation_count + self.rejection_count
        return self.validation_count / total if total > 0 else 0.0


class FeatureCorrelation(Base):
    """Feature correlation data for discovering feature relationships"""
    
    __tablename__ = "feature_correlations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    feature_a: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    feature_b: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Correlation strength (-1 to 1)
    correlation_strength: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(3, 2),
        nullable=True
    )
    
    co_occurrence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_occurrences: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<FeatureCorrelation(id={self.id}, {self.feature_a} <-> {self.feature_b})>"
    
    @property
    def co_occurrence_rate(self) -> float:
        """Calculate co-occurrence rate"""
        return self.co_occurrence_count / self.total_occurrences if self.total_occurrences > 0 else 0.0


class StyleAssignmentFeedback(Base):
    """User feedback on style assignments for algorithm improvement"""
    
    __tablename__ = "style_assignment_feedback"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    quiz_response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_responses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # User's assessment of the assigned style
    accuracy_rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    # User's preferred style if different from assigned
    preferred_style: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Specific feedback on what was wrong/right
    feedback_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Which aspects were most/least accurate
    feature_feedback: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    quiz_response: Mapped["QuizResponse"] = relationship("QuizResponse")
    user: Mapped["User"] = relationship("User")
    
    __table_args__ = (
        CheckConstraint("accuracy_rating >= 1 AND accuracy_rating <= 5", 
                       name='check_accuracy_rating'),
        CheckConstraint("feedback_type IN ('too_broad', 'too_narrow', 'completely_wrong', 'mostly_right', 'perfect')", 
                       name='check_feedback_type'),
    )
    
    def __repr__(self) -> str:
        return f"<StyleAssignmentFeedback(id={self.id}, rating={self.accuracy_rating}, type={self.feedback_type})>"