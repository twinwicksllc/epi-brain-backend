"""
User Schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.user import UserTier, VoicePreference, PlanTier


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100)
    first_name: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)
    voice_preference: Optional[VoicePreference] = VoicePreference.NONE
    silo_id: Optional[str] = Field(default=None, max_length=50)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)
    voice_preference: Optional[VoicePreference] = None
    primary_mode: Optional[str] = None
    accountability_style: Optional[str] = None  # Phase 3: tactical, grace, analyst, adaptive
    sentiment_override_enabled: Optional[bool] = None  # Phase 3: Allow AI to adjust based on mood
    depth_sensitivity_enabled: Optional[bool] = None  # Phase 3: Allow tone adjustment based on depth
    silo_id: Optional[str] = Field(default=None, max_length=50)


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    first_name: Optional[str] = None
    full_name: Optional[str] = None
    tier: Optional[UserTier] = UserTier.FREE
    plan_tier: Optional[PlanTier] = PlanTier.FREE  # Commercial MVP
    paddle_subscription_id: Optional[str] = None  # Commercial MVP
    is_senior: bool = False  # Commercial MVP
    is_military: bool = False  # Commercial MVP
    is_firstresponder: bool = False  # Commercial MVP
    voice_preference: Optional[VoicePreference] = VoicePreference.NONE
    primary_mode: Optional[str] = "personal_friend"
    silo_id: Optional[str] = None
    nebp_phase: Optional[str] = "discovery"
    nebp_clarity_metrics: Optional[dict] = {}
    message_count: Optional[str] = "0"
    referral_code: Optional[str] = None
    referral_credits: Optional[str] = "0"
    voice_limit: Optional[int] = None  # null = unlimited (for admin/pro)
    voice_used: Optional[int] = 0  # Voice messages used today
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    global_memory: Optional[dict] = {}
    is_admin: Optional[str] = "false"  # Admin flag
    subscribed_personalities: Optional[List[str]] = ["personal_friend", "discovery_mode"]  # Subscription tracking
    accountability_style: Optional[str] = "adaptive"  # Phase 3: tactical, grace, analyst, adaptive
    sentiment_override_enabled: Optional[bool] = True  # Phase 3: Allow AI to adjust based on mood
    depth_sensitivity_enabled: Optional[bool] = True  # Phase 3: Allow tone adjustment based on depth
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True


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