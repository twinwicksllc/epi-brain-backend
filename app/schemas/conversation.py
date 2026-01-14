"""
Conversation Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ConversationBase(BaseModel):
    """Base conversation schema"""
    mode: str = Field(..., description="Personality mode")
    title: Optional[str] = Field(None, max_length=255)


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation"""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation"""
    title: Optional[str] = Field(None, max_length=255)


class ConversationResponse(ConversationBase):
    """Schema for conversation response"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    message_count: int
    
    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Schema for conversation with messages"""
    messages: List = []
    
    class Config:
        from_attributes = True