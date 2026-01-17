"""
Goals API Endpoints

Provides endpoints for managing user goals, check-ins, and milestones.
"""

from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.models.goal import Goal, CheckIn, Milestone
from app.core.dependencies import get_current_active_user
from app.services.goal_service import GoalService

router = APIRouter()


# Pydantic schemas for request/response
class GoalCreate(BaseModel):
    """Schema for creating a new goal"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    target_date: Optional[date] = None
    accountability_style: str = Field(default="adaptive")
    check_in_frequency: str = Field(default="weekly")
    specific: Optional[str] = None
    measurable: Optional[str] = None
    achievable: Optional[str] = None
    relevant: Optional[str] = None
    time_bound: Optional[str] = None


class GoalUpdate(BaseModel):
    """Schema for updating a goal"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    target_date: Optional[date] = None
    accountability_style: Optional[str] = None
    check_in_frequency: Optional[str] = None
    status: Optional[str] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)


class GoalResponse(BaseModel):
    """Schema for goal response"""
    id: str
    user_id: str
    title: str
    description: str
    category: str
    status: str
    progress_percentage: float
    streak_days: int
    completion_rate: float
    accountability_style: str
    check_in_frequency: str
    target_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class CheckInCreate(BaseModel):
    """Schema for creating a check-in"""
    progress_notes: str = Field(..., min_length=1)
    mood: Optional[str] = None
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)


class CheckInResponse(BaseModel):
    """Schema for check-in response"""
    id: str
    goal_id: str
    user_id: str
    progress_notes: str
    mood: Optional[str]
    energy_level: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class MilestoneCreate(BaseModel):
    """Schema for creating a milestone"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    target_date: Optional[date] = None


class MilestoneResponse(BaseModel):
    """Schema for milestone response"""
    id: str
    goal_id: str
    user_id: str
    title: str
    description: str
    target_date: Optional[date]
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Goal endpoints

@router.post("/", response_model=GoalResponse, status_code=201)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new goal
    
    Args:
        goal_data: Goal creation data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created goal
    """
    service = GoalService(db)
    
    goal = service.create_goal(
        user_id=str(current_user.id),
        title=goal_data.title,
        description=goal_data.description,
        category=goal_data.category,
        target_date=goal_data.target_date,
        accountability_style=goal_data.accountability_style,
        check_in_frequency=goal_data.check_in_frequency,
        specific=goal_data.specific,
        measurable=goal_data.measurable,
        achievable=goal_data.achievable,
        relevant=goal_data.relevant,
        time_bound=goal_data.time_bound
    )
    
    return goal


@router.get("/", response_model=List[GoalResponse])
async def get_goals(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all goals for the current user
    
    Args:
        status: Optional status filter
        category: Optional category filter
        limit: Maximum number of goals to return
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of goals
    """
    service = GoalService(db)
    
    goals = service.get_user_goals(
        user_id=str(current_user.id),
        status=status,
        category=category,
        limit=limit
    )
    
    return goals


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific goal
    
    Args:
        goal_id: Goal ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Goal data
    """
    service = GoalService(db)
    
    goal = service.get_goal(goal_id, str(current_user.id))
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    goal_data: GoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a goal
    
    Args:
        goal_id: Goal ID
        goal_data: Goal update data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Updated goal
    """
    service = GoalService(db)
    
    # Filter out None values
    updates = {k: v for k, v in goal_data.model_dump().items() if v is not None}
    
    goal = service.update_goal(
        goal_id=goal_id,
        user_id=str(current_user.id),
        **updates
    )
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return goal


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a goal
    
    Args:
        goal_id: Goal ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    service = GoalService(db)
    
    deleted = service.delete_goal(goal_id, str(current_user.id))
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return {"message": "Goal deleted successfully"}


@router.get("/{goal_id}/progress")
async def get_goal_progress(
    goal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive progress information for a goal
    
    Args:
        goal_id: Goal ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Progress statistics
    """
    service = GoalService(db)
    
    progress = service.get_goal_progress(goal_id, str(current_user.id))
    
    if not progress:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return progress


# Check-in endpoints

@router.post("/{goal_id}/check-ins", response_model=CheckInResponse, status_code=201)
async def create_check_in(
    goal_id: str,
    check_in_data: CheckInCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a check-in for a goal
    
    Args:
        goal_id: Goal ID
        check_in_data: Check-in data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created check-in
    """
    service = GoalService(db)
    
    try:
        check_in = service.create_check_in(
            goal_id=goal_id,
            user_id=str(current_user.id),
            progress_notes=check_in_data.progress_notes,
            mood=check_in_data.mood,
            energy_level=check_in_data.energy_level,
            progress_percentage=check_in_data.progress_percentage
        )
        
        return check_in
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{goal_id}/check-ins", response_model=List[CheckInResponse])
async def get_check_ins(
    goal_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all check-ins for a goal
    
    Args:
        goal_id: Goal ID
        limit: Maximum number of check-ins to return
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of check-ins
    """
    service = GoalService(db)
    
    check_ins = service.get_check_ins(goal_id, str(current_user.id), limit)
    
    return check_ins


# Milestone endpoints

@router.post("/{goal_id}/milestones", response_model=MilestoneResponse, status_code=201)
async def create_milestone(
    goal_id: str,
    milestone_data: MilestoneCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a milestone for a goal
    
    Args:
        goal_id: Goal ID
        milestone_data: Milestone data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created milestone
    """
    service = GoalService(db)
    
    try:
        milestone = service.create_milestone(
            goal_id=goal_id,
            user_id=str(current_user.id),
            title=milestone_data.title,
            description=milestone_data.description,
            target_date=milestone_data.target_date
        )
        
        return milestone
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{goal_id}/milestones", response_model=List[MilestoneResponse])
async def get_milestones(
    goal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all milestones for a goal
    
    Args:
        goal_id: Goal ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of milestones
    """
    service = GoalService(db)
    
    milestones = service.get_milestones(goal_id, str(current_user.id))
    
    return milestones


@router.put("/{goal_id}/milestones/{milestone_id}/complete", response_model=MilestoneResponse)
async def complete_milestone(
    goal_id: str,
    milestone_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mark a milestone as completed
    
    Args:
        goal_id: Goal ID
        milestone_id: Milestone ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Updated milestone
    """
    service = GoalService(db)
    
    milestone = service.complete_milestone(milestone_id, str(current_user.id))
    
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    return milestone