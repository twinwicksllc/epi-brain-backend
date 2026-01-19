"""
Exposure Hierarchy API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_active_user
from app.services.exposure_hierarchy_service import ExposureHierarchyService
from app.schemas.exposure_hierarchy import (
    ExposureHierarchyCreate,
    ExposureHierarchyUpdate,
    ExposureHierarchyResponse,
    ExposureHierarchyAnalytics
)

router = APIRouter()


@router.post("/", response_model=ExposureHierarchyResponse)
async def create_exposure_step(
    exposure: ExposureHierarchyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new exposure hierarchy step
    
    Args:
        exposure: Exposure step data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created exposure step
    """
    service = ExposureHierarchyService(db)
    return service.create_exposure_step(
        user_id=current_user.id,
        conversation_id=exposure.conversation_id,
        hierarchy_group=exposure.hierarchy_group,
        feared_situation=exposure.feared_situation,
        difficulty_level=exposure.difficulty_level,
        anxiety_before=exposure.anxiety_before,
        anxiety_during=exposure.anxiety_during,
        anxiety_after=exposure.anxiety_after,
        notes=exposure.notes
    )


@router.get("/", response_model=List[ExposureHierarchyResponse])
async def get_exposure_steps(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all exposure steps for current user
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of exposure steps
    """
    service = ExposureHierarchyService(db)
    return service.get_user_exposure_steps(current_user.id, skip=skip, limit=limit)


@router.get("/groups", response_model=List[str])
async def get_hierarchy_groups(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all hierarchy groups for current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of hierarchy group names
    """
    service = ExposureHierarchyService(db)
    return service.get_hierarchy_groups(current_user.id)


@router.get("/groups/{group_name}", response_model=List[ExposureHierarchyResponse])
async def get_group_steps(
    group_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all steps in a specific hierarchy group
    
    Args:
        group_name: Hierarchy group name
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of exposure steps in the group
    """
    service = ExposureHierarchyService(db)
    return service.get_hierarchy_by_group(current_user.id, group_name)


@router.get("/next-step/{group_name}", response_model=ExposureHierarchyResponse)
async def get_next_step(
    group_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the next recommended step in a hierarchy group
    
    Args:
        group_name: Hierarchy group name
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Next recommended exposure step
    """
    service = ExposureHierarchyService(db)
    next_step = service.get_next_step(current_user.id, group_name)
    
    if not next_step:
        raise HTTPException(status_code=404, detail="No next step found")
    
    return next_step


@router.get("/{exposure_id}", response_model=ExposureHierarchyResponse)
async def get_exposure_step(
    exposure_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific exposure step
    
    Args:
        exposure_id: Exposure step ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Exposure step
    """
    service = ExposureHierarchyService(db)
    exposure = service.get_exposure_step(exposure_id)
    
    if not exposure or exposure.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Exposure step not found")
    
    return exposure


@router.put("/{exposure_id}", response_model=ExposureHierarchyResponse)
async def update_exposure_step(
    exposure_id: UUID,
    exposure_update: ExposureHierarchyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an exposure step
    
    Args:
        exposure_id: Exposure step ID
        exposure_update: Updated exposure data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated exposure step
    """
    service = ExposureHierarchyService(db)
    exposure = service.get_exposure_step(exposure_id)
    
    if not exposure or exposure.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Exposure step not found")
    
    return service.update_exposure_step(exposure_id, **exposure_update.dict(exclude_unset=True))


@router.post("/{exposure_id}/complete", response_model=ExposureHierarchyResponse)
async def complete_exposure(
    exposure_id: UUID,
    anxiety_during: int,
    anxiety_after: int,
    notes: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mark an exposure step as completed
    
    Args:
        exposure_id: Exposure step ID
        anxiety_during: Anxiety level during exposure (0-100)
        anxiety_after: Anxiety level after exposure (0-100)
        notes: Optional completion notes
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated exposure step
    """
    service = ExposureHierarchyService(db)
    exposure = service.get_exposure_step(exposure_id)
    
    if not exposure or exposure.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Exposure step not found")
    
    return service.complete_exposure(exposure_id, anxiety_during, anxiety_after, notes)


@router.delete("/{exposure_id}")
async def delete_exposure_step(
    exposure_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an exposure step
    
    Args:
        exposure_id: Exposure step ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    service = ExposureHierarchyService(db)
    exposure = service.get_exposure_step(exposure_id)
    
    if not exposure or exposure.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Exposure step not found")
    
    service.delete_exposure_step(exposure_id)
    return {"message": "Exposure step deleted successfully"}


@router.get("/analytics/anxiety-trends", response_model=ExposureHierarchyAnalytics)
async def get_anxiety_trends(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get anxiety trend analytics
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Anxiety trend analytics
    """
    service = ExposureHierarchyService(db)
    return service.get_anxiety_trends(current_user.id)


@router.get("/analytics/progress/{group_name}", response_model=dict)
async def get_group_progress(
    group_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get progress analytics for a specific hierarchy group
    
    Args:
        group_name: Hierarchy group name
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Progress analytics
    """
    service = ExposureHierarchyService(db)
    return service.get_exposure_progress(current_user.id, group_name)