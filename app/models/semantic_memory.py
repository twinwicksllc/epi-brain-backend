"""
Semantic Memory Model

Stores cross-conversation context and memories for AI modes.
Uses pgvector for semantic similarity search.
"""

from sqlalchemy import Column, String, DateTime, Float, Text, Index, func, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base

# Try to import VECTOR from pgvector, fallback to TEXT for SQLite
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_TYPE = Vector(1536)
except ImportError:
    # Fallback for SQLite/non-pgvector databases
    VECTOR_TYPE = Text


class SemanticMemory(Base):
    """
    Semantic memory for AI modes to remember important facts across conversations
    
    Stores memories with vector embeddings for semantic similarity search.
    Each memory is scoped to a specific user and mode for isolation.
    """
    
    __tablename__ = "semantic_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Mode scoping - memories don't leak between modes
    mode = Column(String(50), nullable=False, index=True)
    
    # Vector embedding for semantic search
    # 1536 dimensions for OpenAI text-embedding-3-small
    # Uses TEXT for SQLite, will use VECTOR for PostgreSQL with pgvector
    embedding = Column(VECTOR_TYPE, nullable=False)
    
    # The memory content (human-readable)
    content = Column(Text, nullable=False)
    
    # Importance score (0.0 to 1.0) - higher = more important
    importance_score = Column(Float, default=0.5, nullable=False, index=True)
    
    # Memory category for organization
    category = Column(String(50), nullable=True, index=True)  # e.g., 'personal', 'goal', 'preference'
    
    # Source of the memory
    source_conversation_id = Column(UUID(as_uuid=True), nullable=True)
    source_message_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)  # Optional expiration
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_count = Column(Float, default=0.0, nullable=False)
    
    # Metadata for filtering
    tags = Column(Text, nullable=True)  # JSON array of tags
    is_sensitive = Column(String(10), default='false', nullable=False)  # For privacy
    
    def __repr__(self):
        return f"<SemanticMemory {self.id} - {self.mode} - {self.content[:50]}...>"
    
    @property
    def is_expired(self) -> bool:
        """Check if memory has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def tags_list(self) -> list:
        """Parse tags JSON string to list"""
        import json
        if not self.tags:
            return []
        try:
            return json.loads(self.tags)
        except:
            return []
    
    def record_access(self):
        """Record that this memory was accessed"""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1


# Modes that support semantic memory
SEMANTIC_MEMORY_MODES = [
    'personal_friend',
    'christian_companion',
    'psychology_expert',
    'business_mentor',
    'weight_loss_coach',
    'kids_learning',
]

# Modes that should NOT have semantic memory
NO_SEMANTIC_MEMORY_MODES = [
    'student_tutor',
    'business_training',
    'sales_agent',
    'customer_service',
]


def is_semantic_memory_enabled(mode: str) -> bool:
    """Check if semantic memory is enabled for a mode"""
    return mode in SEMANTIC_MEMORY_MODES