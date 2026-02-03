"""
User Note Model
Store quick notes, drafts, reflections, and thoughts for users
"""

from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


class UserNote(Base):
    """Store user notes, drafts, and reflections"""
    
    __tablename__ = "user_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Note categorization
    note_type = Column(String(50), nullable=False, index=True)  # quick_note, draft, reflection, thought
    title = Column(String(255), nullable=True)  # Optional title
    content = Column(Text, nullable=False)  # Main note content
    
    # Context & Metadata
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Link to conversation if applicable
    personality_mode = Column(String(50), nullable=True)  # Which AI personality created this
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_user_notes_user_type', 'user_id', 'note_type'),
        Index('ix_user_notes_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<UserNote id={self.id} user={self.user_id} type={self.note_type}>"
