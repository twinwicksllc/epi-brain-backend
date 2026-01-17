"""
Habits API Endpoints

Provides endpoints for managing user habits and completions.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.models.habit import Habit, HabitCompletion
from app.core.dependencies import get_current_active_user
from app.services.habit_service import HabitService

router = APIRouter()


# Pydantic schemas for request/response
class HabitCreate(BaseModel):
    """Schema for creating a new habit"""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    frequency: str = Field(default="daily")
    category: str = Field(default="general")
    trigger: Optional[str] = None
    routine: Optional[str] = None
    reward: Optional[str] = None
    target_days: Optional[str] = None


class HabitUpdate(BaseModel):
    """Schema for updating a habit"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    frequency: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    trigger: Optional[str] = None
    routine: Optional[str] = None
    reward: Optional[str] = None
    target_days: Optional[str] = None


class HabitResponse(BaseModel):
    """Schema for habit response"""
    id: str
    user_id: str
    name: str
    description: str
    category: str
    frequency: str
    is_active: bool
    streak_days: int
    completion_rate: float
    trigger: Optional[str]
    routine: Optional[str]
    reward: Optional[str]
    target_days: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class HabitCompletionCreate(BaseModel):
    """Schema for creating a habit completion"""
    notes: Optional[str] = None


class HabitCompletionResponse(BaseModel):
    """Schema for habit completion response"""
    id: str
    habit_id: str
    user_id: str
    completed_at: str
    notes: Optional[str]

    class Config:
        from_attributes = True


# Habit endpoints

@router.post("/", response_model=HabitResponse, status_code=201)
async def create_habit(
    habit_data: HabitCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new habit
    
    Args:
        habit_data: Habit creation data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created habit
    """
    service = HabitService(db)
    
    habit = service.create_habit(
        user_id=str(current_user.id),
        name=habit_data.name,
        description=habit_data.description,
        frequency=habit_data.frequency,
        category=habit_data.category,
        trigger=habit_data.trigger,
        routine=habit_data.routine,
        reward=habit_data.reward,
        target_days=habit_data.target_days
    )
    
    return habit


@router.get("/", response_model=List[HabitResponse])
async def get_habits(
    is_active: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all habits for the current user
    
    Args:
        is_active: Optional active status filter
        category: Optional category filter
        limit: Maximum number of habits to return
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of habits
    """
    service = HabitService(db)
    
    habits = service.get_user_habits(
        user_id=str(current_user.id),
        is_active=is_active,
        category=category,
        limit=limit
    )
    
    return habits


@router.get("/due", response_model=List[HabitResponse])
async def get_due_habits(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get habits that are due today
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of due habits
    """
    service = HabitService(db)
    
    habits = service.get_due_habits(str(current_user.id))
    
    return habits


@router.get("/{habit_id}", response_model=HabitResponse)
async def get_habit(
    habit_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific habit
    
    Args:
        habit_id: Habit ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Habit data
    """
    service = HabitService(db)
    
    habit = service.get_habit(habit_id, str(current_user.id))
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    return habit


@router.put("/{habit_id}", response_model=HabitResponse)
async def update_habit(
    habit_id: str,
    habit_data: HabitUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a habit
    
    Args:
        habit_id: Habit ID
        habit_data: Habit update data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Updated habit
    """
    service = HabitService(db)
    
    # Filter out None values
    updates = {k: v for k, v in habit_data.model_dump().items() if v is not None}
    
    habit = service.update_habit(
        habit_id=habit_id,
        user_id=str(current_user.id),
        **updates
    )
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    return habit


@router.delete("/{habit_id}")
async def delete_habit(
    habit_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a habit
    
    Args:
        habit_id: Habit ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    service = HabitService(db)
    
    deleted = service.delete_habit(habit_id, str(current_user.id))
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    return {"message": "Habit deleted successfully"}


@router.get("/{habit_id}/summary")
async def get_habit_summary(
    habit_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive summary for a habit
    
    Args:
        habit_id: Habit ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Habit summary statistics
    """
    service = HabitService(db)
    
    summary = service.get_habit_summary(habit_id, str(current_user.id))
    
    if not summary:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    return summary


# Habit completion endpoints

@router.post("/{habit_id}/completions", response_model=HabitCompletionResponse, status_code=201)
async def complete_habit(
    habit_id: str,
    completion_data: HabitCompletionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Record a habit completion
    
    Args:
        habit_id: Habit ID
        completion_data: Completion data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created completion record
    """
    service = HabitService(db)
    
    try:
        completion = service.complete_habit(
            habit_id=habit_id,
            user_id=str(current_user.id),
            notes=completion_data.notes
        )
        
        return completion
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{habit_id}/completions", response_model=List[HabitCompletionResponse])
async def get_habit_completions(
    habit_id: str,
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all completions for a habit
    
    Args:
        habit_id: Habit ID
        limit: Maximum number of completions to return
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of completions
    """
    service = HabitService(db)
    
    completions = service.get_habit_completions(habit_id, str(current_user.id), limit)
    
    return completions