"""
Thought Record Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class CognitiveDistortionType(str, Enum):
    """Cognitive distortion types"""
    ALL_OR_NOTHING = "all_or_nothing"
    OVERGENERALIZATION = "overgeneralization"
    MENTAL_FILTER = "mental_filter"
    DISQUALIFYING_POSITIVE = "disqualifying_positive"
    JUMPING_TO_CONCLUSIONS = "jumping_to_conclusions"
    MAGNIFICATION = "magnification"
    EMOTIONAL_REASONING = "emotional_reasoning"
    SHOULD_STATEMENTS = "should_statements"
    LABELING = "labeling"
    PERSONALIZATION = "personalization"
    FORTUNE_TELLING = "fortune_telling"
    MIND_READING = "mind_reading"


class ThoughtRecordBase(BaseModel):
    """Base thought record schema"""
    situation: str = Field(..., description="Description of the situation")
    automatic_thought: str = Field(..., description="Automatic thought that occurred")
    emotion: str = Field(..., description="Emotion experienced")
    intensity: int = Field(..., ge=1, le=10, description="Emotion intensity (1-10)")
    cognitive_distortion: Optional[CognitiveDistortionType] = Field(None, description="Type of cognitive distortion")
    evidence_for: Optional[str] = Field(None, description="Evidence supporting the thought")
    evidence_against: Optional[str] = Field(None, description="Evidence against the thought")
    challenging_thought: Optional[str] = Field(None, description="Alternative, balanced thought")
    outcome_emotion: Optional[str] = Field(None, description="Emotion after challenging")
    outcome_intensity: Optional[int] = Field(None, ge=1, le=10, description="Emotion intensity after challenging")


class ThoughtRecordCreate(ThoughtRecordBase):
    """Schema for creating a thought record"""
    conversation_id: Optional[UUID] = Field(None, description="Associated conversation ID")


class ThoughtRecordUpdate(BaseModel):
    """Schema for updating a thought record"""
    situation: Optional[str] = None
    automatic_thought: Optional[str] = None
    emotion: Optional[str] = None
    intensity: Optional[int] = Field(None, ge=1, le=10)
    cognitive_distortion: Optional[CognitiveDistortionType] = None
    evidence_for: Optional[str] = None
    evidence_against: Optional[str] = None
    challenging_thought: Optional[str] = None
    outcome_emotion: Optional[str] = None
    outcome_intensity: Optional[int] = Field(None, ge=1, le=10)


class ThoughtRecordResponse(ThoughtRecordBase):
    """Schema for thought record response"""
    id: UUID
    user_id: UUID
    conversation_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    is_complete: bool
    intensity_change: Optional[int]
    
    class Config:
        from_attributes = True


class ThoughtRecordAnalytics(BaseModel):
    """Schema for thought record analytics"""
    total_records: int
    most_common_distortions: dict
    average_intensity_before: float
    average_intensity_after: float
    average_intensity_reduction: float
    completion_rate: float