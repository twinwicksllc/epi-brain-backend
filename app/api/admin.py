"""
Admin API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User, UserTier
from app.schemas.user import UserResponse
from app.core.dependencies import get_current_active_user
from app.core.security import verify_admin_key

router = APIRouter()


@router.post("/users/{user_id}/upgrade-tier", response_model=UserResponse)
async def upgrade_user_tier(
    user_id: str,
    tier: UserTier,
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Upgrade a user's tier (Admin only)
    
    Args:
        user_id: User ID to upgrade
        tier: New tier (FREE, PRO, ENTERPRISE)
        admin_key: Admin API key for authentication
        db: Database session
    
    Returns:
        Updated user object
    
    Raises:
        HTTPException: If user not found or admin key invalid
    """
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update tier
    user.tier = tier
    
    # Reset message count for PRO/ENTERPRISE tiers
    if tier in [UserTier.PRO, UserTier.ENTERPRISE]:
        user.message_count = 0
    
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (Admin only)
    
    Args:
        user_id: User ID to retrieve
        admin_key: Admin API key for authentication
        db: Database session
    
    Returns:
        User object
    
    Raises:
        HTTPException: If user not found or admin key invalid
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    List all users (Admin only)
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        admin_key: Admin API key for authentication
        db: Database session
    
    Returns:
        List of user objects
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/stats")
async def get_admin_stats(
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Get platform statistics (Admin only)
    
    Args:
        admin_key: Admin API key for authentication
        db: Database session
    
    Returns:
        Platform statistics
    """
    total_users = db.query(User).count()
    free_users = db.query(User).filter(User.tier == UserTier.FREE).count()
    pro_users = db.query(User).filter(User.tier == UserTier.PRO).count()
    enterprise_users = db.query(User).filter(User.tier == UserTier.ENTERPRISE).count()
    
    return {
        "total_users": total_users,
        "free_users": free_users,
        "pro_users": pro_users,
        "enterprise_users": enterprise_users,
        "conversion_rate": (pro_users + enterprise_users) / total_users * 100 if total_users > 0 else 0
    }