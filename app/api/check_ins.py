"""
Check-ins API Endpoints

Provides endpoints for managing check-ins, daily summaries, and trends.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_active_user
from app.services.check_in_service import CheckInService

router = APIRouter()


# Pydantic schemas for request/response
class CheckInCreate(BaseModel):
    """Schema for creating a check-in"""
    item_type: str = Field(..., description="'goal' or 'habit'")
    item_id: str = Field(..., description="ID of the goal or habit")
    progress_notes: Optional[str] = None
    notes: Optional[str] = None
    mood: Optional[str] = None
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)


class DailySummaryResponse(BaseModel):
    """Schema for daily summary response"""
    date: str
    pending_goals: int
    pending_habits: int
    completed_goals_today: int
    completed_habits_today: int
    total_active_goals: int
    average_goal_progress: float
    recent_moods: dict
    total_pending: int


class WeeklyTrendsResponse(BaseModel):
    """Schema for weekly trends response"""
    goal_check_in_trends: dict
    habit_completion_trends: dict
    average_energy_level: Optional[float]
    period: str


class OverdueItemsResponse(BaseModel):
    """Schema for overdue items response"""
    overdue_goals: int
    overdue_habits: int
    total_overdue: int


# Check-in endpoints

@router.post("/", status_code=201)
async def create_check_in(
    check_in_data: CheckInCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a check-in for a goal or habit
    
    Args:
        check_in_data: Check-in data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Check-in result
    """
    service = CheckInService(db)
    
    try:
        result = service.create_check_in(
            user_id=str(current_user.id),
            item_type=check_in_data.item_type,
            item_id=check_in_data.item_id,
            progress_notes=check_in_data.progress_notes,
            mood=check_in_data.mood,
            energy_level=check_in_data.energy_level,
            progress_percentage=check_in_data.progress_percentage,
            notes=check_in_data.notes
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/summary", response_model=DailySummaryResponse)
async def get_daily_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get daily summary of goals and habits
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Daily summary data
    """
    service = CheckInService(db)
    
    summary = service.get_daily_summary(str(current_user.id))
    
    return summary


@router.get("/trends/weekly", response_model=WeeklyTrendsResponse)
async def get_weekly_trends(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get weekly trends for goals and habits
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Weekly trends data
    """
    service = CheckInService(db)
    
    trends = service.get_weekly_trends(str(current_user.id))
    
    return trends


@router.get("/overdue", response_model=OverdueItemsResponse)
async def get_overdue_items(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get overdue goals and habits
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Overdue items data
    """
    service = CheckInService(db)
    
    overdue = service.get_overdue_items(str(current_user.id))
    
    return {
        "overdue_goals": len(overdue["overdue_goals"]),
        "overdue_habits": len(overdue["overdue_habits"]),
        "total_overdue": overdue["total_overdue"]
    }