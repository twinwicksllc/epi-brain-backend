"""
Exposure Hierarchy Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class ExposureStatus(str, Enum):
    """Exposure status types"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class ExposureHierarchyBase(BaseModel):
    """Base exposure hierarchy schema"""
    hierarchy_group: str = Field(..., description="Name of the hierarchy group (e.g., 'Social Anxiety')")
    feared_situation: str = Field(..., description="Description of the feared situation")
    difficulty_level: int = Field(..., ge=0, le=100, description="Difficulty level (0-100)")
    anxiety_before: Optional[int] = Field(None, ge=0, le=100, description="Anxiety before exposure (0-100)")
    anxiety_during: Optional[int] = Field(None, ge=0, le=100, description="Anxiety during exposure (0-100)")
    anxiety_after: Optional[int] = Field(None, ge=0, le=100, description="Anxiety after exposure (0-100)")
    notes: Optional[str] = Field(None, description="Additional notes")


class ExposureHierarchyCreate(ExposureHierarchyBase):
    """Schema for creating an exposure hierarchy step"""
    conversation_id: Optional[UUID] = Field(None, description="Associated conversation ID")


class ExposureHierarchyUpdate(BaseModel):
    """Schema for updating an exposure hierarchy step"""
    hierarchy_group: Optional[str] = None
    feared_situation: Optional[str] = None
    difficulty_level: Optional[int] = Field(None, ge=0, le=100)
    anxiety_before: Optional[int] = Field(None, ge=0, le=100)
    anxiety_during: Optional[int] = Field(None, ge=0, le=100)
    anxiety_after: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    status: Optional[ExposureStatus] = None


class ExposureHierarchyResponse(ExposureHierarchyBase):
    """Schema for exposure hierarchy response"""
    id: UUID
    user_id: UUID
    conversation_id: Optional[UUID]
    status: ExposureStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    anxiety_reduction: Optional[int]
    difficulty_category: str
    
    class Config:
        from_attributes = True


class ExposureHierarchyAnalytics(BaseModel):
    """Schema for exposure hierarchy analytics"""
    total_steps: int
    completed_steps: int
    completion_rate: float
    average_anxiety_before: float
    average_anxiety_after: float
    average_anxiety_reduction: float
    hierarchy_groups: list