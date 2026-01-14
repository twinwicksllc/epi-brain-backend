"""
User Schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.user import UserTier, VoicePreference


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100)
    voice_preference: Optional[VoicePreference] = VoicePreference.NONE


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    voice_preference: Optional[VoicePreference] = None
    primary_mode: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    tier: UserTier
    voice_preference: VoicePreference
    primary_mode: str
    message_count: str
    referral_code: Optional[str]
    referral_credits: str
    created_at: datetime
    last_login: Optional[datetime]
    global_memory: dict = {}  # Phase 1: Global memory
    is_admin: str = "false"  # Admin flag
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[UUID] = None
    email: Optional[str] = None


class UserUsageResponse(BaseModel):
    """Schema for user usage statistics"""
    message_count: int
    message_limit: int
    has_unlimited: bool
    tier: UserTier
    days_until_reset: int