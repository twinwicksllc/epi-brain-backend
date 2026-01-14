"""
Message Model
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
# from pgvector.sqlalchemy import Vector  # Commented out for SQLite compatibility
from datetime import datetime
import uuid
import enum

from app.database import Base


class MessageRole(str, enum.Enum):
    """Message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    """Message model for chat messages"""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message content
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Neural learning - vector embedding for semantic search
    # embedding = Column(Vector(384), nullable=True)  # Commented out for SQLite compatibility
    
    # Metadata
    tokens_used = Column(String, nullable=True)  # Track API usage
    response_time_ms = Column(String, nullable=True)  # Track performance
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Depth tracking (for analytics/debugging)
    turn_score = Column(Float, nullable=True)
    scoring_source = Column(String(20), nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.id} - {self.role}>"
    
    @property
    def is_user_message(self) -> bool:
        """Check if message is from user"""
        return self.role == MessageRole.USER
    
    @property
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant"""
        return self.role == MessageRole.ASSISTANT