"""
Behavioral Activation Model for CBT (Cognitive Behavioral Therapy)
Tracks activities and their impact on mood to break avoidance cycles
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ActivityCompletionStatus(str, enum.Enum):
    """Status of activity completion"""
    PLANNED = "planned"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class BehavioralActivation(Base):
    """
    Behavioral Activation for tracking mood vs. activity patterns
    
    CBT Technique: Behavioral Activation
    Purpose: Identify activities that improve mood, schedule pleasant/meaningful
    activities, track mood vs. activity patterns, and break avoidance cycles
    """
    __tablename__ = "behavioral_activations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    
    # Activity details
    activity = Column(Text, nullable=False, help_text="Activity description")
    activity_category = Column(String(50), nullable=True, help_text="Category: pleasure, mastery, social, exercise, etc.")
    
    # Mood before activity
    mood_before = Column(Integer, nullable=False, help_text="Mood 1-10 before activity")
    
    # Mood after activity
    mood_after = Column(Integer, nullable=True, help_text="Mood 1-10 after activity")
    
    # Difficulty rating (avoidance level)
    difficulty_rating = Column(Integer, nullable=True, help_text="Difficulty 1-10 (avoidance level)")
    
    # Completion status
    completion_status = Column(
        SQLEnum(ActivityCompletionStatus),
        default=ActivityCompletionStatus.PLANNED,
        nullable=False
    )
    
    # Activity scheduling
    scheduled_for = Column(DateTime, nullable=True, help_text="When is this scheduled?")
    completed_at = Column(DateTime, nullable=True, help_text="When was this completed?")
    
    # Notes
    notes = Column(Text, nullable=True, help_text="Additional notes about the activity")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="behavioral_activations")
    conversation = relationship("Conversation", back_populates="behavioral_activations")
    
    def __repr__(self):
        return f"<BehavioralActivation(id={self.id}, activity={self.activity[:30]}, status={self.completion_status})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "activity": self.activity,
            "activity_category": self.activity_category,
            "mood_before": self.mood_before,
            "mood_after": self.mood_after,
            "difficulty_rating": self.difficulty_rating,
            "completion_status": self.completion_status.value,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def mood_improvement(self):
        """Calculate mood improvement from activity"""
        if self.mood_after and self.mood_before:
            return self.mood_after - self.mood_before
        return None
    
    @property
    def is_completed(self):
        """Check if activity was completed"""
        return self.completion_status == ActivityCompletionStatus.COMPLETED
    
    @property
    def is_planned(self):
        """Check if activity is still planned"""
        return self.completion_status == ActivityCompletionStatus.PLANNED
    
    @property
    def days_since_creation(self):
        """Calculate days since creation"""
        if self.created_at:
            return (datetime.utcnow() - self.created_at).days
        return None