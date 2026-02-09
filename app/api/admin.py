"""
Admin API EndpointsUsageLog

"""

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User, UserTier, PlanTier
from app.models.usage_log import UsageLog
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


class UserUsageStats(BaseModel):
    """User usage statistics for admin reporting"""
    user_id: Optional[str] = Field(default=None, description="User ID")
    email: Optional[str] = Field(default=None, description="User email")
    plan_tier: Optional[PlanTier] = Field(default=PlanTier.FREE, description="User plan tier")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    total_tokens_month: Optional[int] = Field(default=0, description="Total tokens consumed this month")
    total_messages_month: Optional[int] = Field(default=0, description="Total messages this month")
    total_cost_month: Optional[float] = Field(default=0.0, description="Total cost this month in USD")
    voice_used_month: Optional[int] = Field(default=0, description="Voice interactions used this month")
    voice_limit: Optional[int] = Field(default=None, description="Voice daily limit (None = unlimited)")
    is_admin: Optional[bool] = Field(default=False, description="Is user an admin")
    created_at: Optional[datetime] = Field(default=None, description="Account creation timestamp")
    
    class Config:
        from_attributes = True


class AdminUsageResponse(BaseModel):
    """Response model for admin usage endpoint"""
    success: Optional[bool] = Field(default=True, description="Whether the request succeeded")
    period_start: Optional[datetime] = Field(default=None, description="Start of reporting period")
    period_end: Optional[datetime] = Field(default=None, description="End of reporting period")
    total_users: Optional[int] = Field(default=0, description="Total number of users returned")
    users: List[UserUsageStats] = Field(default_factory=list, description="List of user usage stats")
    summary: dict = Field(default_factory=dict, description="Aggregate statistics")
    
    class Config:
        from_attributes = True


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


@router.get("/usage", response_model=AdminUsageResponse)
async def get_usage_report(
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db),
    limit: int = 100,
    sort_by: str = "tokens"  # tokens, cost, messages, voice
):
    """
    Get usage report for all users (Admin only)
    
    Returns users sorted by their total token consumption and voice usage for the current month.
    Includes user details like plan_tier, email, and last_login to identify power users.
    
    Args:
        admin_key: Admin API key for authorization
        db: Database session
        limit: Maximum number of users to return (default 100)
        sort_by: Sort field - "tokens", "cost", "messages", or "voice" (default "tokens")
    
    Returns:
        AdminUsageResponse with user statistics sorted by consumption
    """
    try:
        # Calculate current month date range
        now = datetime.utcnow()
        period_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            period_end = datetime(now.year + 1, 1, 1)
        else:
            period_end = datetime(now.year, now.month + 1, 1)
        
        # Query all users with their usage stats for current month
        # Aggregate usage_logs by user_id for the current month
        usage_subquery = db.query(
            UsageLog.user_id,
            func.sum(UsageLog.tokens_total).label('total_tokens'),
            func.count(UsageLog.id).label('total_messages'),
            func.sum(UsageLog.token_cost).label('total_cost')
        ).filter(
            and_(
                UsageLog.created_at >= period_start,
                UsageLog.created_at < period_end
            )
        ).group_by(UsageLog.user_id).subquery()
        
        # Join with users table
        query = db.query(
            User,
            func.coalesce(usage_subquery.c.total_tokens, 0).label('total_tokens_month'),
            func.coalesce(usage_subquery.c.total_messages, 0).label('total_messages_month'),
            func.coalesce(usage_subquery.c.total_cost, 0.0).label('total_cost_month')
        ).outerjoin(
            usage_subquery,
            User.id == usage_subquery.c.user_id
        )
        
        # Sort by requested field
        if sort_by == "cost":
            query = query.order_by(func.coalesce(usage_subquery.c.total_cost, 0.0).desc())
        elif sort_by == "messages":
            query = query.order_by(func.coalesce(usage_subquery.c.total_messages, 0).desc())
        elif sort_by == "voice":
            query = query.order_by(User.voice_used.desc())
        else:  # default to tokens
            query = query.order_by(func.coalesce(usage_subquery.c.total_tokens, 0).desc())
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute query
        results = query.all()
        
        # Build user stats list
        user_stats_list = []
        total_tokens_all = 0
        total_messages_all = 0
        total_cost_all = 0.0
        total_voice_all = 0
        
        for row in results:
            user = row[0]
            total_tokens = int(row[1]) if row[1] is not None else 0
            total_messages = int(row[2]) if row[2] is not None else 0
            total_cost = float(row[3]) if row[3] is not None else 0.0
            
            # Aggregate for summary
            total_tokens_all += total_tokens
            total_messages_all += total_messages
            total_cost_all += total_cost
            total_voice_all += user.voice_used or 0
            
            # Safely convert plan_tier to ensure it's a valid enum value
            plan_tier_value = user.plan_tier
            if plan_tier_value is None:
                plan_tier_value = PlanTier.FREE
            
            # Safely convert is_admin boolean
            is_admin_value = False
            if user.is_admin:
                is_admin_value = str(user.is_admin).lower() == "true"
            
            # Get voice limit (handle errors gracefully)
            try:
                voice_limit_value = user.get_voice_daily_limit()
            except Exception as e:
                voice_limit_value = None
            
            user_stats = UserUsageStats(
                user_id=str(user.id) if user.id else None,
                email=user.email if user.email else None,
                plan_tier=plan_tier_value,
                last_login=user.last_login,
                total_tokens_month=total_tokens,
                total_messages_month=total_messages,
                total_cost_month=round(total_cost, 4),
                voice_used_month=user.voice_used or 0,
                voice_limit=voice_limit_value,
                is_admin=is_admin_value,
                created_at=user.created_at
            )
            user_stats_list.append(user_stats)
        
        # Build summary statistics
        summary = {
            "total_tokens_all_users": total_tokens_all,
            "total_messages_all_users": total_messages_all,
            "total_cost_all_users": round(total_cost_all, 2),
            "total_voice_all_users": total_voice_all,
            "avg_tokens_per_user": round(total_tokens_all / len(results), 2) if results else 0,
            "avg_cost_per_user": round(total_cost_all / len(results), 4) if results else 0,
            "users_by_plan": {
                "free": sum(1 for u in user_stats_list if u.plan_tier == PlanTier.FREE),
                "premium": sum(1 for u in user_stats_list if u.plan_tier == PlanTier.PREMIUM),
                "enterprise": sum(1 for u in user_stats_list if u.plan_tier == PlanTier.ENTERPRISE)
            }
        }
        
        return AdminUsageResponse(
            success=True,
            period_start=period_start,
            period_end=period_end,
            total_users=len(results),
            users=user_stats_list,
            summary=summary
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Usage report failed: {str(e)}")


@router.get("/usage/report", response_model=AdminUsageResponse)
async def get_usage_report_alias(
    admin_key: str = Security(verify_admin_key),
    db: Session = Depends(get_db),
    limit: int = 100,
    sort_by: str = "tokens"  # tokens, cost, messages, voice
):
    """
    Get usage report for all users - Alternative endpoint (Admin only)
    
    This is an alias for /usage to maintain backward compatibility.
    Returns users sorted by their total token consumption and voice usage for the current month.
    
    Args:
        admin_key: Admin API key for authorization
        db: Database session
        limit: Maximum number of users to return (default 100)
        sort_by: Sort field - "tokens", "cost", "messages", or "voice" (default "tokens")
    
    Returns:
        AdminUsageResponse with user statistics sorted by consumption
    """
    # Simply delegate to the main usage report endpoint
    now = datetime.utcnow()
    period_start = datetime(now.year, now.month, 1)
    if now.month == 12:
        period_end = datetime(now.year + 1, 1, 1)
    else:
        period_end = datetime(now.year, now.month + 1, 1)
    
    try:
        # Query all users with their usage stats for current month
        usage_subquery = db.query(
            UsageLog.user_id,
            func.sum(UsageLog.tokens_total).label('total_tokens'),
            func.count(UsageLog.id).label('total_messages'),
            func.sum(UsageLog.token_cost).label('total_cost')
        ).filter(
            and_(
                UsageLog.created_at >= period_start,
                UsageLog.created_at < period_end
            )
        ).group_by(UsageLog.user_id).subquery()
        
        query = db.query(
            User,
            func.coalesce(usage_subquery.c.total_tokens, 0).label('total_tokens_month'),
            func.coalesce(usage_subquery.c.total_messages, 0).label('total_messages_month'),
            func.coalesce(usage_subquery.c.total_cost, 0.0).label('total_cost_month')
        ).outerjoin(
            usage_subquery,
            User.id == usage_subquery.c.user_id
        )
        
        if sort_by == "cost":
            query = query.order_by(func.coalesce(usage_subquery.c.total_cost, 0.0).desc())
        elif sort_by == "messages":
            query = query.order_by(func.coalesce(usage_subquery.c.total_messages, 0).desc())
        elif sort_by == "voice":
            query = query.order_by(User.voice_used.desc())
        else:
            query = query.order_by(func.coalesce(usage_subquery.c.total_tokens, 0).desc())
        
        query = query.limit(limit)
        results = query.all()
        
        user_stats_list = []
        total_tokens_all = 0
        total_messages_all = 0
        total_cost_all = 0.0
        total_voice_all = 0
        
        for row in results:
            user = row[0]
            total_tokens = int(row[1]) if row[1] is not None else 0
            total_messages = int(row[2]) if row[2] is not None else 0
            total_cost = float(row[3]) if row[3] is not None else 0.0
            
            total_tokens_all += total_tokens
            total_messages_all += total_messages
            total_cost_all += total_cost
            total_voice_all += user.voice_used or 0
            
            # Safely convert plan_tier to ensure it's a valid enum value
            plan_tier_value = user.plan_tier
            if plan_tier_value is None:
                plan_tier_value = PlanTier.FREE
            
            # Safely convert is_admin boolean
            is_admin_value = False
            if user.is_admin:
                is_admin_value = str(user.is_admin).lower() == "true"
            
            # Get voice limit (handle errors gracefully)
            try:
                voice_limit_value = user.get_voice_daily_limit()
            except Exception as e:
                voice_limit_value = None
            
            user_stats = UserUsageStats(
                user_id=str(user.id) if user.id else None,
                email=user.email if user.email else None,
                plan_tier=plan_tier_value,
                last_login=user.last_login,
                total_tokens_month=total_tokens,
                total_messages_month=total_messages,
                total_cost_month=round(total_cost, 4),
                voice_used_month=user.voice_used or 0,
                voice_limit=voice_limit_value,
                is_admin=is_admin_value,
                created_at=user.created_at
            )
            user_stats_list.append(user_stats)
        
        summary = {
            "total_tokens_all_users": total_tokens_all,
            "total_messages_all_users": total_messages_all,
            "total_cost_all_users": round(total_cost_all, 2),
            "total_voice_all_users": total_voice_all,
            "avg_tokens_per_user": round(total_tokens_all / len(results), 2) if results else 0,
            "avg_cost_per_user": round(total_cost_all / len(results), 4) if results else 0,
            "users_by_plan": {
                "free": sum(1 for u in user_stats_list if u.plan_tier == PlanTier.FREE),
                "premium": sum(1 for u in user_stats_list if u.plan_tier == PlanTier.PREMIUM),
                "enterprise": sum(1 for u in user_stats_list if u.plan_tier == PlanTier.ENTERPRISE)
            }
        }
        
        return AdminUsageResponse(
            success=True,
            period_start=period_start,
            period_end=period_end,
            total_users=len(results),
            users=user_stats_list,
            summary=summary
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Usage report failed: {str(e)}")
