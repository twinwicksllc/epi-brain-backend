"""
Voice Usage Model
Track TTS usage for cost monitoring and limit enforcement
"""

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


class VoiceUsage(Base):
    """Voice usage tracking for TTS cost monitoring"""
    
    __tablename__ = "voice_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    personality_mode = Column(String(50), nullable=False)  # e.g., 'personal_friend'
    voice_gender = Column(String(10), nullable=True)  # 'male' or 'female'
    character_count = Column(Integer, nullable=False)  # Number of characters sent to TTS
    cost = Column(Float, nullable=False)  # Cost in USD
    duration_seconds = Column(Float, nullable=True)  # Audio duration in seconds
    
    # Timestamps
    date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)  # Daily aggregation
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<VoiceUsage {self.user_id} - {self.personality_mode} - ${self.cost:.4f}>"
    
    @property
    def duration_minutes(self) -> float:
        """Duration in minutes"""
        return self.duration_seconds / 60 if self.duration_seconds else 0