"""
Message Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from uuid import UUID

from app.models.message import MessageRole
from app.prompts.discovery_mode import DISCOVERY_MODE_ID


class MessageBase(BaseModel):
    """Base message schema"""
    content: str = Field(..., min_length=1, max_length=10000)


class MessageCreate(MessageBase):
    """Schema for creating a message"""
    conversation_id: UUID
    role: MessageRole = MessageRole.USER


class MessageResponse(MessageBase):
    """Schema for message response"""
    id: UUID
    conversation_id: UUID
    role: MessageRole
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[UUID] = None
    mode: str = Field(default=DISCOVERY_MODE_ID, description="Personality mode")
    stream: bool = Field(default=False, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Schema for chat response"""
    message_id: Optional[UUID] = None  # None for unauthenticated discovery mode
    conversation_id: Optional[UUID] = None  # None for unauthenticated discovery mode
    content: str
    mode: str
    created_at: datetime
    tokens_used: Optional[int] = None
    response_time_ms: Optional[int] = None
    depth: Optional[float] = None  # Current conversation depth (0.0-1.0)
    metadata: Optional[Dict[str, str]] = None
    limit_reached: bool = False  # True if user hit discovery mode limit