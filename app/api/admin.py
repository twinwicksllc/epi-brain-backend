"""
Admin API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User, UserTier
from app.schemas.user import UserResponse
from app.core.dependencies import get_current_active_user
from app.core.security import verify_admin_key

router = APIRouter()


# Pydantic schemas for cleanup requests
class CleanupRequest(BaseModel):
    """Request model for conversation cleanup"""
    days_threshold: int = Field(default=30, ge=1, le=365, description="Days threshold for old conversations")
    dry_run: bool = Field(default=False, description="If true, only show what would be deleted")
    batch_size: int = Field(default=100, ge=1, le=1000, description="Batch size for deletion")


class CleanupResponse(BaseModel):
    """Response model for conversation cleanup"""
    success: bool
    total_deleted: int
    total_messages_deleted: int
    batches_processed: int
    cutoff_date: str
    dry_run: bool
    message: str


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

# Voice Cost Tracking Endpoints

@router.get("/voice-stats/today")
async def get_voice_stats_today(
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Get voice usage statistics for today (Admin only)
    
    Args:
        admin_key: Admin API key for authentication
        db: Database session
    
    Returns:
        Today's voice statistics including total cost, top users, usage by personality
    """
    monitor = VoiceCostMonitor(db)
    
    total_cost_today = monitor.get_total_cost_today()
    top_users = monitor.get_top_users_today(limit=10)
    usage_by_personality = monitor.get_usage_by_personality(days=1)
    
    return {
        "date": "today",
        "total_cost": round(total_cost_today, 4),
        "top_users": top_users,
        "usage_by_personality": usage_by_personality
    }


@router.get("/voice-stats/month")
async def get_voice_stats_month(
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Get voice usage statistics for this month (Admin only)
    
    Args:
        admin_key: Admin API key for authentication
        db: Database session
    
    Returns:
        This month's voice statistics
    """
    monitor = VoiceCostMonitor(db)
    
    total_cost_month = monitor.get_total_cost_this_month()
    usage_by_personality = monitor.get_usage_by_personality(days=30)
    projection = monitor.get_cost_projection(days_to_project=30)
    
    return {
        "period": "this_month",
        "total_cost": round(total_cost_month, 4),
        "usage_by_personality": usage_by_personality,
        "projection": projection
    }


@router.get("/voice-stats/user/{user_id}")
async def get_user_voice_stats(
    user_id: str,
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Get voice usage statistics for a specific user (Admin only)
    
    Args:
        user_id: User ID to get stats for
        admin_key: Admin API key for authentication
        db: Database session
    
    Returns:
        User's voice usage statistics
    """
    from app.services.voice_tracking import VoiceUsageTracker
    
    tracker = VoiceUsageTracker(db)
    stats = tracker.get_user_stats(user_id)
    
    return {
        "status": "success",
        "data": stats
    }


@router.get("/voice-stats/projection")
async def get_voice_cost_projection(
    days: int = 30,
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Get voice cost projection for the next N days (Admin only)
    
    Args:
        days: Number of days to project (default: 30)
        admin_key: Admin API key for authentication
        db: Database session
    
    Returns:
        Cost projection data
    """
    monitor = VoiceCostMonitor(db)
    projection = monitor.get_cost_projection(days_to_project=days)
    
    return {
        "status": "success",
        "data": projection
    }


# Conversation Cleanup Endpoints

@router.post("/conversations/cleanup", response_model=CleanupResponse)
async def cleanup_old_conversations(
    request: CleanupRequest,
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Clean up conversations older than specified days (Admin only)
    
    Args:
        request: Cleanup request with days_threshold, dry_run, and batch_size
        admin_key: Admin API key for authentication
        db: Database session
    
    Returns:
        Cleanup statistics
    """
    from app.services.conversation_cleanup import ConversationCleanupService
    
    try:
        cleanup_service = ConversationCleanupService(days_threshold=request.days_threshold)
        
        # First, count what we have
        count = cleanup_service.count_old_conversations(db)
        
        if count == 0:
            return CleanupResponse(
                success=True,
                total_deleted=0,
                total_messages_deleted=0,
                batches_processed=0,
                cutoff_date=cleanup_service.get_cutoff_date().isoformat(),
                dry_run=request.dry_run,
                message="No old conversations found"
            )
        
        # Perform cleanup
        stats = cleanup_service.cleanup_old_conversations(
            db,
            batch_size=request.batch_size,
            dry_run=request.dry_run
        )
        
        message = f"{'Would delete' if request.dry_run else 'Deleted'} {stats['total_deleted']} conversations and {stats['total_messages_deleted']} messages"
        
        return CleanupResponse(
            success=True,
            total_deleted=stats['total_deleted'],
            total_messages_deleted=stats['total_messages_deleted'],
            batches_processed=stats['batches_processed'],
            cutoff_date=stats['cutoff_date'],
            dry_run=request.dry_run,
            message=message
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get("/conversations/count-old")
async def count_old_conversations(
    days: int = 30,
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Count conversations older than specified days (Admin only)
    
    Args:
        days: Number of days threshold (default: 30)
        admin_key: Admin API key for authentication
        db: Database session
    
    Returns:
        Count of old conversations
    """
    from app.services.conversation_cleanup import ConversationCleanupService
    
    try:
        cleanup_service = ConversationCleanupService(days_threshold=days)
        count = cleanup_service.count_old_conversations(db)
        cutoff_date = cleanup_service.get_cutoff_date()
        
        return {
            "count": count,
            "cutoff_date": cutoff_date.isoformat(),
            "days_threshold": days
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Count failed: {str(e)}")


@router.post("/conversations/cleanup-user/{user_id}", response_model=CleanupResponse)
async def cleanup_user_conversations(
    user_id: str,
    days: int = 30,
    dry_run: bool = False,
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db)
):
    """
    Clean up old conversations for a specific user (Admin only)
    
    Args:
        user_id: User ID to clean up conversations for
        days: Number of days threshold (default: 30)
        dry_run: If true, only show what would be deleted
        admin_key: Admin API key for authentication
        db: Database session
    
    Returns:
        Cleanup statistics
    """
    from app.services.conversation_cleanup import ConversationCleanupService
    
    try:
        cleanup_service = ConversationCleanupService(days_threshold=days)
        stats = cleanup_service.cleanup_conversations_for_user(
            db,
            user_id=user_id,
            dry_run=dry_run
        )
        
        message = f"{'Would delete' if dry_run else 'Deleted'} {stats['total_deleted']} conversations and {stats['total_messages_deleted']} messages for user {user_id}"
        
        return CleanupResponse(
            success=True,
            total_deleted=stats['total_deleted'],
            total_messages_deleted=stats['total_messages_deleted'],
            batches_processed=1,
            cutoff_date=stats['cutoff_date'],
            dry_run=dry_run,
            message=message
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User cleanup failed: {str(e)}")
