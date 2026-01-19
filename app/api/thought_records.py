"""
Thought Records API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_active_user
from app.services.thought_record_service import ThoughtRecordService
from app.schemas.thought_record import (
    ThoughtRecordCreate,
    ThoughtRecordUpdate,
    ThoughtRecordResponse,
    ThoughtRecordAnalytics,
    CognitiveDistortionType
)

router = APIRouter()


@router.post("/", response_model=ThoughtRecordResponse)
async def create_thought_record(
    thought_record: ThoughtRecordCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new thought record
    
    Args:
        thought_record: Thought record data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created thought record
    """
    service = ThoughtRecordService(db)
    return service.create_thought_record(
        user_id=current_user.id,
        conversation_id=thought_record.conversation_id,
        situation=thought_record.situation,
        automatic_thought=thought_record.automatic_thought,
        emotion=thought_record.emotion,
        intensity=thought_record.intensity,
        cognitive_distortion=thought_record.cognitive_distortion,
        evidence_for=thought_record.evidence_for,
        evidence_against=thought_record.evidence_against,
        challenging_thought=thought_record.challenging_thought,
        outcome_emotion=thought_record.outcome_emotion,
        outcome_intensity=thought_record.outcome_intensity
    )


@router.get("/", response_model=List[ThoughtRecordResponse])
async def get_thought_records(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all thought records for current user
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of thought records
    """
    service = ThoughtRecordService(db)
    return service.get_user_thought_records(current_user.id, skip=skip, limit=limit)


@router.get("/{thought_record_id}", response_model=ThoughtRecordResponse)
async def get_thought_record(
    thought_record_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific thought record
    
    Args:
        thought_record_id: Thought record ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Thought record
    """
    service = ThoughtRecordService(db)
    thought_record = service.get_thought_record(thought_record_id)
    
    if not thought_record or thought_record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thought record not found")
    
    return thought_record


@router.put("/{thought_record_id}", response_model=ThoughtRecordResponse)
async def update_thought_record(
    thought_record_id: UUID,
    thought_record_update: ThoughtRecordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a thought record
    
    Args:
        thought_record_id: Thought record ID
        thought_record_update: Updated thought record data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated thought record
    """
    service = ThoughtRecordService(db)
    thought_record = service.get_thought_record(thought_record_id)
    
    if not thought_record or thought_record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thought record not found")
    
    return service.update_thought_record(thought_record_id, **thought_record_update.dict(exclude_unset=True))


@router.delete("/{thought_record_id}")
async def delete_thought_record(
    thought_record_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a thought record
    
    Args:
        thought_record_id: Thought record ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    service = ThoughtRecordService(db)
    thought_record = service.get_thought_record(thought_record_id)
    
    if not thought_record or thought_record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thought record not found")
    
    service.delete_thought_record(thought_record_id)
    return {"message": "Thought record deleted successfully"}


@router.get("/analytics/distortions", response_model=ThoughtRecordAnalytics)
async def get_distortion_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get analytics on cognitive distortion patterns
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Distortion analytics
    """
    service = ThoughtRecordService(db)
    return service.get_distortion_patterns(current_user.id)


@router.get("/analytics/emotions", response_model=dict)
async def get_emotion_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get analytics on emotion trends
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Emotion analytics
    """
    service = ThoughtRecordService(db)
    return service.get_emotion_trends(current_user.id)


@router.get("/insights/recent", response_model=List[str])
async def get_recent_insights(
    limit: int = 5,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get recent insights from thought records
    
    Args:
        limit: Maximum number of insights to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of insights
    """
    service = ThoughtRecordService(db)
    return service.get_insights(current_user.id, limit=limit)


@router.get("/challenging-questions/{distortion_type}", response_model=List[str])
async def get_challenging_questions(
    distortion_type: CognitiveDistortionType,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get challenging questions for a specific cognitive distortion
    
    Args:
        distortion_type: Type of cognitive distortion
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of challenging questions
    """
    service = ThoughtRecordService(db)
    return service.get_challenging_questions(distortion_type)