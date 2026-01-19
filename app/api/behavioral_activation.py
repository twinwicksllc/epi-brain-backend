"""
Behavioral Activation API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_active_user
from app.services.behavioral_activation_service import BehavioralActivationService
from app.schemas.behavioral_activation import (
    BehavioralActivationCreate,
    BehavioralActivationUpdate,
    BehavioralActivationResponse,
    BehavioralActivationAnalytics
)

router = APIRouter()


@router.post("/", response_model=BehavioralActivationResponse)
async def create_activity(
    activity: BehavioralActivationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new behavioral activation activity
    
    Args:
        activity: Activity data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created activity
    """
    service = BehavioralActivationService(db)
    return service.create_activity(
        user_id=current_user.id,
        conversation_id=activity.conversation_id,
        activity_name=activity.activity_name,
        category=activity.category,
        planned_date=activity.planned_date,
        mood_before=activity.mood_before,
        mood_after=activity.mood_after,
        difficulty_rating=activity.difficulty_rating,
        notes=activity.notes
    )


@router.get("/", response_model=List[BehavioralActivationResponse])
async def get_activities(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all activities for current user
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of activities
    """
    service = BehavioralActivationService(db)
    return service.get_user_activities(current_user.id, skip=skip, limit=limit)


@router.get("/planned", response_model=List[BehavioralActivationResponse])
async def get_planned_activities(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get planned activities for current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of planned activities
    """
    service = BehavioralActivationService(db)
    return service.get_planned_activities(current_user.id)


@router.get("/{activity_id}", response_model=BehavioralActivationResponse)
async def get_activity(
    activity_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific activity
    
    Args:
        activity_id: Activity ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Activity
    """
    service = BehavioralActivationService(db)
    activity = service.get_activity(activity_id)
    
    if not activity or activity.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    return activity


@router.put("/{activity_id}", response_model=BehavioralActivationResponse)
async def update_activity(
    activity_id: UUID,
    activity_update: BehavioralActivationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an activity
    
    Args:
        activity_id: Activity ID
        activity_update: Updated activity data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated activity
    """
    service = BehavioralActivationService(db)
    activity = service.get_activity(activity_id)
    
    if not activity or activity.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    return service.update_activity(activity_id, **activity_update.dict(exclude_unset=True))


@router.post("/{activity_id}/complete", response_model=BehavioralActivationResponse)
async def complete_activity(
    activity_id: UUID,
    mood_after: int,
    notes: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mark an activity as completed
    
    Args:
        activity_id: Activity ID
        mood_after: Mood rating after activity (1-10)
        notes: Optional completion notes
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated activity
    """
    service = BehavioralActivationService(db)
    activity = service.get_activity(activity_id)
    
    if not activity or activity.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    return service.complete_activity(activity_id, mood_after, notes)


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an activity
    
    Args:
        activity_id: Activity ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    service = BehavioralActivationService(db)
    activity = service.get_activity(activity_id)
    
    if not activity or activity.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    service.delete_activity(activity_id)
    return {"message": "Activity deleted successfully"}


@router.get("/analytics/mood-trends", response_model=BehavioralActivationAnalytics)
async def get_mood_trends(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get mood trend analytics
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Mood trend analytics
    """
    service = BehavioralActivationService(db)
    return service.get_mood_trends(current_user.id)


@router.get("/analytics/categories", response_model=dict)
async def get_category_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get activity category analytics
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Category analytics
    """
    service = BehavioralActivationService(db)
    return service.get_activity_categories(current_user.id)


@router.get("/suggestions/activities", response_model=List[str])
async def get_activity_suggestions(
    mood: int,
    limit: int = 5,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get activity suggestions based on current mood
    
    Args:
        mood: Current mood rating (1-10)
        limit: Maximum number of suggestions
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of activity suggestions
    """
    service = BehavioralActivationService(db)
    return service.suggest_activities(current_user.id, mood, limit=limit)