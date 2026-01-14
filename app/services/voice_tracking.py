"""
Voice Usage Tracking Service
Manages voice limits, usage tracking, and cost monitoring
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.voice_usage import VoiceUsage
from app.models.user import User
from app.config import settings


class VoiceUsageTracker:
    """Track and manage voice usage for users"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_daily_usage(self, user_id: str) -> List[VoiceUsage]:
        """Get voice usage for current day"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        return self.db.query(VoiceUsage).filter(
            VoiceUsage.user_id == user_id,
            VoiceUsage.date >= today_start
        ).all()
    
    def get_daily_count(self, user_id: str) -> int:
        """Get number of voice responses used today"""
        return len(self.get_daily_usage(user_id))
    
    def get_daily_cost(self, user_id: str) -> float:
        """Get total cost for today"""
        usage = self.get_daily_usage(user_id)
        return sum(record.cost for record in usage)
    
    def get_daily_characters(self, user_id: str) -> int:
        """Get total character count for today"""
        usage = self.get_daily_usage(user_id)
        return sum(record.character_count for record in usage)
    
    def can_use_voice(self, user_id: str, user_tier: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user can use voice feature
        
        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        # Check if voice is globally enabled
        if not settings.VOICE_ENABLED:
            return False, "Voice feature is currently disabled"
        
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        # Admin users have unlimited voice
        if user.is_admin and user.is_admin.lower() == "true":
            return True, None
        
        # PRO and Enterprise tiers have unlimited voice
        if user_tier in ["pro", "enterprise"]:
            return True, None
        
        # FREE tier has daily limit
        if user_tier == "free":
            daily_count = self.get_daily_count(user_id)
            limit = settings.VOICE_FREE_LIMIT
            
            if daily_count >= limit:
                return False, f"Daily voice limit reached ({limit} responses)"
            
            remaining = limit - daily_count
            return True, f"{remaining} voice responses remaining today"
        
        return False, "Invalid user tier"
    
    async def check_voice_limit(self, db: Session, user_id: str):
        """
        Check voice limit and raise HTTPException if exceeded.
        
        This is the method called by the voice API endpoint.
        """
        # Get user's tier
        user = db.query(User).filter(User.id == user_id).first()
        user_tier = user.tier if user else "free"
        
        # Check if user can use voice
        can_use, error_message = self.can_use_voice(user_id, user_tier)
        
        if not can_use:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail=error_message or "Voice limit exceeded"
            )
    
    def get_daily_limit(self, user_tier: str) -> int:
        """
        Get daily limit for a user tier.
        
        Returns:
            Daily limit (or None for unlimited)
        """
        # Admin users have unlimited
        if user_tier == "admin":
            return None
        # PRO and Enterprise tiers have unlimited
        if user_tier in ["pro", "enterprise"]:
            return settings.VOICE_PRO_LIMIT
        else:
            return settings.VOICE_FREE_LIMIT
    
    def record_usage(
        self,
        user_id: str,
        personality: str,
        voice_gender: str,
        character_count: int,
        cost: float,
        duration_seconds: float
    ):
        """Record a voice usage event"""
        voice_usage = VoiceUsage(
            user_id=user_id,
            personality_mode=personality,
            voice_gender=voice_gender,
            character_count=character_count,
            cost=cost,
            duration_seconds=duration_seconds,
            date=datetime.utcnow()
        )
        
        self.db.add(voice_usage)
        self.db.commit()
    
    def get_user_stats(self, user_id: str) -> dict:
        """Get comprehensive voice usage statistics for a user"""
        daily_usage = self.get_daily_usage(user_id)
        daily_count = len(daily_usage)
        daily_cost = sum(record.cost for record in daily_usage)
        daily_characters = sum(record.character_count for record in daily_usage)
        daily_duration = sum(record.duration_seconds or 0 for record in daily_usage)
        
        # Get user tier
        user = self.db.query(User).filter(User.id == user_id).first()
        user_tier = user.tier if user else "free"
        is_admin = (user.is_admin.lower() == "true") if user and user.is_admin else False
        
        # Calculate limit
        if is_admin or user_tier in ["pro", "enterprise"]:
            limit = None  # Unlimited
            remaining = "unlimited"
        else:
            limit = settings.VOICE_FREE_LIMIT
            remaining = max(0, limit - daily_count)
        
        return {
            "user_id": user_id,
            "user_tier": user_tier,
            "is_admin": is_admin,
            "daily_count": daily_count,
            "daily_limit": limit,
            "remaining": remaining,
            "daily_cost": round(daily_cost, 4),
            "daily_characters": daily_characters,
            "daily_duration_minutes": round(daily_duration / 60, 2),
        }


class VoiceCostMonitor:
    """Monitor voice costs across all users"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_total_cost_today(self) -> float:
        """Get total cost for all users today"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = self.db.query(func.sum(VoiceUsage.cost)).filter(
            VoiceUsage.date >= today_start
        ).scalar()
        
        return result or 0.0
    
    def get_total_cost_this_month(self) -> float:
        """Get total cost for this month"""
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        result = self.db.query(func.sum(VoiceUsage.cost)).filter(
            VoiceUsage.date >= month_start
        ).scalar()
        
        return result or 0.0
    
    def get_top_users_today(self, limit: int = 10) -> List[dict]:
        """Get top users by voice usage today"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        results = self.db.query(
            VoiceUsage.user_id,
            func.count(VoiceUsage.id).label('count'),
            func.sum(VoiceUsage.character_count).label('characters'),
            func.sum(VoiceUsage.cost).label('cost'),
            func.sum(VoiceUsage.duration_seconds).label('duration')
        ).filter(
            VoiceUsage.date >= today_start
        ).group_by(
            VoiceUsage.user_id
        ).order_by(
            func.count(VoiceUsage.id).desc()
        ).limit(limit).all()
        
        return [
            {
                "user_id": user_id,
                "count": count,
                "characters": characters,
                "cost": round(cost, 4),
                "duration_minutes": round((duration or 0) / 60, 2)
            }
            for user_id, count, characters, cost, duration in results
        ]
    
    def get_usage_by_personality(self, days: int = 7) -> List[dict]:
        """Get usage breakdown by personality over the last N days"""
        date_start = datetime.utcnow() - timedelta(days=days)
        
        results = self.db.query(
            VoiceUsage.personality_mode,
            func.count(VoiceUsage.id).label('count'),
            func.sum(VoiceUsage.character_count).label('characters'),
            func.sum(VoiceUsage.cost).label('cost')
        ).filter(
            VoiceUsage.date >= date_start
        ).group_by(
            VoiceUsage.personality_mode
        ).order_by(
            func.count(VoiceUsage.id).desc()
        ).all()
        
        return [
            {
                "personality": personality,
                "count": count,
                "characters": characters,
                "cost": round(cost, 4)
            }
            for personality, count, characters, cost in results
        ]
    
    def get_cost_projection(self, days_to_project: int = 30) -> dict:
        """Project costs for the next N days based on recent usage"""
        # Get last 7 days of data
        last_7_days = datetime.utcnow() - timedelta(days=7)
        
        results = self.db.query(
            func.sum(VoiceUsage.cost).label('total_cost'),
            func.count(VoiceUsage.id).label('total_count')
        ).filter(
            VoiceUsage.date >= last_7_days
        ).first()
        
        total_cost = results.total_cost or 0
        total_count = results.total_count or 0
        
        # Calculate daily averages
        avg_daily_cost = total_cost / 7
        avg_daily_count = total_count / 7
        
        # Project
        projected_cost = avg_daily_cost * days_to_project
        projected_count = avg_daily_count * days_to_project
        
        return {
            "period_days": days_to_project,
            "avg_daily_cost": round(avg_daily_cost, 4),
            "avg_daily_count": round(avg_daily_count, 2),
            "projected_cost": round(projected_cost, 2),
            "projected_count": round(projected_count, 2),
            "alert_threshold": settings.VOICE_ALERT_THRESHOLD,
            "will_exceed_threshold": projected_cost > settings.VOICE_ALERT_THRESHOLD
        }