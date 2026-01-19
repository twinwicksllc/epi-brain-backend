"""
User API Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserUsageResponse
from app.core.dependencies import get_current_active_user
from app.config import settings

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile data
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    
    Args:
        user_update: User update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user profile
    """
    # Update user fields
    if user_update.voice_preference is not None:
        current_user.voice_preference = user_update.voice_preference
    
    if user_update.primary_mode is not None:
        current_user.primary_mode = user_update.primary_mode
    
    # Phase 3: Update accountability style
    if user_update.accountability_style is not None:
        # Validate accountability style
        valid_styles = ['tactical', 'grace', 'analyst', 'adaptive']
        if user_update.accountability_style in valid_styles:
            current_user.accountability_style = user_update.accountability_style
        else:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail=f"Invalid accountability style. Must be one of: {', '.join(valid_styles)}"
            )
    
    # Phase 3: Update sentiment and depth sensitivity settings
    if user_update.sentiment_override_enabled is not None:
        current_user.sentiment_override_enabled = user_update.sentiment_override_enabled
    
    if user_update.depth_sensitivity_enabled is not None:
        current_user.depth_sensitivity_enabled = user_update.depth_sensitivity_enabled
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/me/usage", response_model=UserUsageResponse)
async def get_user_usage(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user usage statistics
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User usage statistics
    """
    from datetime import datetime
    
    message_count = int(current_user.message_count)
    
    # Calculate days until reset
    if current_user.last_message_reset:
        days_since_reset = (datetime.utcnow() - current_user.last_message_reset).days
        days_until_reset = 30 - days_since_reset
    else:
        days_until_reset = 30
    
    return {
        "message_count": message_count,
        "message_limit": settings.FREE_TIER_MESSAGE_LIMIT if current_user.is_free_tier else -1,
        "has_unlimited": current_user.has_unlimited_messages,
        "tier": current_user.tier,
        "days_until_reset": days_until_reset if current_user.is_free_tier else -1
    }


@router.delete("/me")
async def delete_user_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user account
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    db.delete(current_user)
    db.commit()
    
    return {"message": "Account successfully deleted"}