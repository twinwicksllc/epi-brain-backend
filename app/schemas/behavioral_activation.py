"""
Behavioral Activation Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class ActivityStatus(str, Enum):
    """Activity status types"""
    PLANNED = "planned"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class BehavioralActivationBase(BaseModel):
    """Base behavioral activation schema"""
    activity_name: str = Field(..., description="Name of the activity")
    category: str = Field(..., description="Activity category (e.g., social, exercise, creative)")
    planned_date: Optional[datetime] = Field(None, description="Planned date for activity")
    mood_before: Optional[int] = Field(None, ge=1, le=10, description="Mood before activity (1-10)")
    mood_after: Optional[int] = Field(None, ge=1, le=10, description="Mood after activity (1-10)")
    difficulty_rating: Optional[int] = Field(None, ge=1, le=10, description="Difficulty rating (1-10)")
    notes: Optional[str] = Field(None, description="Additional notes")


class BehavioralActivationCreate(BehavioralActivationBase):
    """Schema for creating a behavioral activation activity"""
    conversation_id: Optional[UUID] = Field(None, description="Associated conversation ID")


class BehavioralActivationUpdate(BaseModel):
    """Schema for updating a behavioral activation activity"""
    activity_name: Optional[str] = None
    category: Optional[str] = None
    planned_date: Optional[datetime] = None
    mood_before: Optional[int] = Field(None, ge=1, le=10)
    mood_after: Optional[int] = Field(None, ge=1, le=10)
    difficulty_rating: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None
    status: Optional[ActivityStatus] = None


class BehavioralActivationResponse(BehavioralActivationBase):
    """Schema for behavioral activation response"""
    id: UUID
    user_id: UUID
    conversation_id: Optional[UUID]
    status: ActivityStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    mood_improvement: Optional[int]
    is_completed: bool
    is_planned: bool
    
    class Config:
        from_attributes = True


class BehavioralActivationAnalytics(BaseModel):
    """Schema for behavioral activation analytics"""
    total_activities: int
    completed_activities: int
    completion_rate: float
    average_mood_before: float
    average_mood_after: float
    average_mood_improvement: float
    most_effective_categories: dict