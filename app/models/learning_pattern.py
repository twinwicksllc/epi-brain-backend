"""
Learning Pattern Model
For neural learning system to track user patterns and preferences
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class LearningPattern(Base):
    """Learning pattern model for neural learning system"""
    
    __tablename__ = "learning_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Pattern details
    mode = Column(String(50), nullable=False, index=True)  # personality mode
    pattern_type = Column(String(50), nullable=False)  # e.g., "response_length", "topic_preference", "emotional_tone"
    
    # Pattern data
    success_score = Column(Float, nullable=False)  # 0.0 to 1.0
    pattern_metadata = Column(JSON, nullable=True)  # Additional pattern data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="learning_patterns")
    
    def __repr__(self):
        return f"<LearningPattern {self.pattern_type} - {self.mode}>"