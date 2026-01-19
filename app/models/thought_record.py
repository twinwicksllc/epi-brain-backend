"""
Thought Record Model for CBT (Cognitive Behavioral Therapy)
Tracks user's cognitive distortions and thought patterns
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
import enum


class CognitiveDistortionType(str, enum.Enum):
    """Types of cognitive distortions based on CBT"""
    ALL_OR_NOTHING = "all_or_nothing"  # Black and white thinking
    OVERGENERALIZATION = "overgeneralization"  # Seeing patterns based on one event
    MENTAL_FILTER = "mental_filter"  # Focusing only on negatives
    DISQUALIFYING_POSITIVE = "disqualifying_positive"  # Rejecting positive experiences
    JUMPING_CONCLUSIONS = "jumping_conclusions"  # Mind reading or fortune telling
    MAGNIFICATION = "magnification"  # Blowing things out of proportion
    MINIMIZATION = "minimization"  # Shrinking importance
    EMOTIONAL_REASONING = "emotional_reasoning"  # Feelings determine reality
    SHOULD_STATEMENTS = "should_statements"  # Rigid rules about behavior
    LABELING = "labeling"  # Overgeneralizing with labels
    PERSONALIZATION = "personalization"  # Taking things personally


class ThoughtRecord(Base):
    """
    Thought Record for tracking and challenging cognitive distortions
    
    CBT Technique: Cognitive Restructuring
    Purpose: Identify automatic negative thoughts, challenge them with evidence,
    and develop balanced alternative thoughts
    """
    __tablename__ = "thought_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True)
    
    # The situation that triggered the thought
    situation = Column(Text, nullable=False)
    
    # The automatic negative thought
    automatic_thought = Column(Text, nullable=False)
    
    # Emotional response
    emotion = Column(String(100), nullable=False)
    emotion_intensity = Column(Integer, nullable=False)  # 1-10 scale
    
    # Cognitive distortion type
    cognitive_distortion = Column(
        SQLEnum(CognitiveDistortionType),
        nullable=False
    )
    
    # Evidence for the thought
    evidence_for = Column(Text, nullable=True)
    
    # Evidence against the thought
    evidence_against = Column(Text, nullable=True)
    
    # Balanced alternative thought
    challenging_thought = Column(Text, nullable=True)
    
    # Outcome after challenging the thought
    outcome = Column(Text, nullable=True)
    outcome_intensity = Column(Integer, nullable=True)  # 1-10 scale
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="thought_records")
    conversation = relationship("Conversation", back_populates="thought_records")
    
    def __repr__(self):
        return f"<ThoughtRecord(id={self.id}, emotion={self.emotion}, distortion={self.cognitive_distortion})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "situation": self.situation,
            "automatic_thought": self.automatic_thought,
            "emotion": self.emotion,
            "emotion_intensity": self.emotion_intensity,
            "cognitive_distortion": self.cognitive_distortion.value if self.cognitive_distortion else None,
            "evidence_for": self.evidence_for,
            "evidence_against": self.evidence_against,
            "challenging_thought": self.challenging_thought,
            "outcome": self.outcome,
            "outcome_intensity": self.outcome_intensity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_complete(self):
        """Check if thought record is complete (has challenging thought)"""
        return self.challenging_thought is not None and len(self.challenging_thought.strip()) > 0
    
    @property
    def intensity_change(self):
        """Calculate change in emotion intensity"""
        if self.outcome_intensity and self.emotion_intensity:
            return self.outcome_intensity - self.emotion_intensity
        return None
