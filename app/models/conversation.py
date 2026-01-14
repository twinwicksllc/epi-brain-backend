"""
Conversation Model
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Conversation(Base):
    """Conversation model for chat sessions"""
    
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Conversation details
    mode = Column(String(50), nullable=False)  # personality mode
    title = Column(String(255), nullable=True)  # auto-generated or user-set
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Depth tracking
    depth = Column(Float, default=0.0, nullable=False)
    last_depth_update = Column(DateTime, default=datetime.utcnow, nullable=False)
    depth_enabled = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    def __repr__(self):
        return f"<Conversation {self.id} - {self.mode}>"
    
    @property
    def message_count(self) -> int:
        """Get number of messages in conversation"""
        return len(self.messages)
    
    @property
    def last_message_at(self) -> datetime:
        """Get timestamp of last message"""
        if self.messages:
            return self.messages[-1].created_at
        return self.created_at