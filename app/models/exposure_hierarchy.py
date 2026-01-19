"""
Exposure Hierarchy Model for CBT (Cognitive Behavioral Therapy)
Tracks gradual exposure to feared situations to reduce anxiety
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
import enum


class ExposureStatus(str, enum.Enum):
    """Status of exposure step"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    AVOIDED = "avoided"
    POSTPONED = "postponed"


class ExposureHierarchy(Base):
    """
    Exposure Hierarchy for gradual exposure to feared situations
    
    CBT Technique: Exposure Hierarchy
    Purpose: Rank feared situations by difficulty, gradually expose to
    reduce anxiety, track anxiety levels, and celebrate progress
    """
    __tablename__ = "exposure_hierarchies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True)
    
    # Hierarchy group (multiple steps can belong to same fear/hierarchy)
    hierarchy_group = Column(String(100), nullable=False)
    
    # The feared situation
    feared_situation = Column(Text, nullable=False)
    
    # Difficulty level (Subjective Units of Distress Scale)
    difficulty_level = Column(Integer, nullable=False)  # 0-100 scale
    
    # Anxiety levels
    anxiety_before = Column(Integer, nullable=False)  # 1-10 scale
    anxiety_during = Column(Integer, nullable=True)  # 1-10 scale
    anxiety_after = Column(Integer, nullable=True)  # 1-10 scale
    
    # Completion status
    status = Column(
        SQLEnum(ExposureStatus),
        default=ExposureStatus.NOT_STARTED,
        nullable=False
    )
    
    # Timing
    scheduled_for = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="exposure_hierarchies")
    conversation = relationship("Conversation", back_populates="exposure_hierarchies")
    
    def __repr__(self):
        return f"<ExposureHierarchy(id={self.id}, situation={self.feared_situation[:30]}, level={self.difficulty_level})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "hierarchy_group": self.hierarchy_group,
            "feared_situation": self.feared_situation,
            "difficulty_level": self.difficulty_level,
            "anxiety_before": self.anxiety_before,
            "anxiety_during": self.anxiety_during,
            "anxiety_after": self.anxiety_after,
            "status": self.status.value,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_minutes": self.duration_minutes,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def anxiety_reduction(self):
        """Calculate anxiety reduction from exposure"""
        if self.anxiety_after and self.anxiety_before:
            return self.anxiety_before - self.anxiety_after
        return None
    
    @property
    def is_completed(self):
        """Check if exposure was completed"""
        return self.status == ExposureStatus.COMPLETED
    
    @property
    def is_in_progress(self):
        """Check if exposure is in progress"""
        return self.status == ExposureStatus.IN_PROGRESS
    
    @property
    def is_avoided(self):
        """Check if exposure was avoided"""
        return self.status == ExposureStatus.AVOIDED
    
    @property
    def difficulty_category(self):
        """Categorize difficulty level"""
        if self.difficulty_level < 30:
            return "easy"
        elif self.difficulty_level < 50:
            return "moderate"
        elif self.difficulty_level < 70:
            return "challenging"
        else:
            return "difficult"
