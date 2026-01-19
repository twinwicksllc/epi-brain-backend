"""
Behavioral Activation Service for CBT (Cognitive Behavioral Therapy)
Tracks activities and their impact on mood to break avoidance cycles
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid, timedelta
from sqlalchemy.orm import Session
from app.models.behavioral_activation import BehavioralActivation, ActivityCompletionStatus
import logging

logger = logging.getLogger(__name__)


class BehavioralActivationService:
    """Service for managing behavioral activation and mood tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_activity(
        self,
        user_id: uuid.UUID,
        activity: str,
        mood_before: int,
        activity_category: Optional[str] = None,
        difficulty_rating: Optional[int] = None,
        conversation_id: Optional[uuid.UUID] = None,
        scheduled_for: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> BehavioralActivation:
        """
        Create a new behavioral activation activity
        
        Args:
            user_id: User ID
            activity: Activity description
            mood_before: Mood before activity (1-10)
            activity_category: Category (pleasure, mastery, social, exercise, etc.)
            difficulty_rating: Difficulty/avoidance level (1-10)
            conversation_id: Optional conversation ID
            scheduled_for: When the activity is scheduled
            notes: Additional notes
        
        Returns:
            Created activity
        """
        try:
            activity_record = BehavioralActivation(
                user_id=user_id,
                conversation_id=conversation_id,
                activity=activity,
                activity_category=activity_category,
                mood_before=mood_before,
                difficulty_rating=difficulty_rating,
                completion_status=ActivityCompletionStatus.PLANNED,
                scheduled_for=scheduled_for,
                notes=notes
            )
            
            self.db.add(activity_record)
            self.db.commit()
            self.db.refresh(activity_record)
            
            logger.info(f"Created activity {activity_record.id} for user {user_id}")
            return activity_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating activity: {e}")
            raise
    
    def get_activity(self, activity_id: uuid.UUID, user_id: uuid.UUID) -> Optional[BehavioralActivation]:
        """Get a specific activity by ID"""
        return self.db.query(BehavioralActivation).filter(
            BehavioralActivation.id == activity_id,
            BehavioralActivation.user_id == user_id
        ).first()
    
    def get_user_activities(
        self,
        user_id: uuid.UUID,
        status: Optional[ActivityCompletionStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[BehavioralActivation]:
        """Get activities for a user, optionally filtered by status"""
        query = self.db.query(BehavioralActivation).filter(
            BehavioralActivation.user_id == user_id
        )
        
        if status:
            query = query.filter(BehavioralActivation.completion_status == status)
        
        return query.order_by(BehavioralActivation.created_at.desc()).limit(limit).offset(offset).all()
    
    def complete_activity(
        self,
        activity_id: uuid.UUID,
        user_id: uuid.UUID,
        mood_after: int,
        notes: Optional[str] = None
    ) -> Optional[BehavioralActivation]:
        """
        Mark an activity as completed with mood after
        
        Args:
            activity_id: Activity ID
            user_id: User ID
            mood_after: Mood after activity (1-10)
            notes: Optional completion notes
        
        Returns:
            Updated activity
        """
        activity = self.get_activity(activity_id, user_id)
        
        if not activity:
            return None
        
        try:
            activity.mood_after = mood_after
            activity.completion_status = ActivityCompletionStatus.COMPLETED
            activity.completed_at = datetime.utcnow()
            
            if notes:
                activity.notes = notes
            
            self.db.commit()
            self.db.refresh(activity)
            
            logger.info(f"Completed activity {activity_id} for user {user_id}")
            return activity
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing activity: {e}")
            raise
    
    def skip_activity(
        self,
        activity_id: uuid.UUID,
        user_id: uuid.UUID,
        notes: Optional[str] = None
    ) -> Optional[BehavioralActivation]:
        """Mark an activity as skipped"""
        activity = self.get_activity(activity_id, user_id)
        
        if not activity:
            return None
        
        try:
            activity.completion_status = ActivityCompletionStatus.SKIPPED
            
            if notes:
                activity.notes = notes
            
            self.db.commit()
            self.db.refresh(activity)
            
            logger.info(f"Skipped activity {activity_id} for user {user_id}")
            return activity
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error skipping activity: {e}")
            raise
    
    def update_activity(
        self,
        activity_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs
    ) -> Optional[BehavioralActivation]:
        """Update an activity"""
        activity = self.get_activity(activity_id, user_id)
        
        if not activity:
            return None
        
        try:
            for key, value in kwargs.items():
                if hasattr(activity, key) and value is not None:
                    setattr(activity, key, value)
            
            activity.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(activity)
            
            logger.info(f"Updated activity {activity_id}")
            return activity
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating activity: {e}")
            raise
    
    def delete_activity(self, activity_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete an activity"""
        activity = self.get_activity(activity_id, user_id)
        
        if not activity:
            return False
        
        try:
            self.db.delete(activity)
            self.db.commit()
            logger.info(f"Deleted activity {activity_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting activity: {e}")
            raise
    
    def get_mood_trends(
        self,
        user_id: uuid.UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze mood trends from activities
        
        Args:
            user_id: User ID
            days: Number of days to analyze
        
        Returns:
            Dictionary with mood trends
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        activities = self.db.query(BehavioralActivation).filter(
            BehavioralActivation.user_id == user_id,
            BehavioralActivation.created_at >= since_date,
            BehavioralActivation.completion_status == ActivityCompletionStatus.COMPLETED
        ).all()
        
        if not activities:
            return {
                "avg_mood_before": None,
                "avg_mood_after": None,
                "avg_improvement": None,
                "total_activities": 0
            }
        
        avg_before = sum(a.mood_before for a in activities) / len(activities)
        avg_after = sum(a.mood_after for a in activities if a.mood_after) / len([a for a in activities if a.mood_after])
        avg_improvement = sum(a.mood_improvement for a in activities if a.mood_improvement) / len([a for a in activities if a.mood_improvement])
        
        return {
            "avg_mood_before": round(avg_before, 2),
            "avg_mood_after": round(avg_after, 2),
            "avg_improvement": round(avg_improvement, 2),
            "total_activities": len(activities)
        }
    
    def get_activity_categories(
        self,
        user_id: uuid.UUID,
        days: int = 30
    ) -> Dict[str, int]:
        """
        Get activity category breakdown
        
        Args:
            user_id: User ID
            days: Number of days to analyze
        
        Returns:
            Dictionary mapping categories to counts
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        activities = self.db.query(BehavioralActivation).filter(
            BehavioralActivation.user_id == user_id,
            BehavioralActivation.created_at >= since_date,
            BehavioralActivation.completion_status == ActivityCompletionStatus.COMPLETED
        ).all()
        
        categories = {}
        for activity in activities:
            category = activity.activity_category or "uncategorized"
            categories[category] = categories.get(category, 0) + 1
        
        return categories
    
    def get_most_improving_activities(
        self,
        user_id: uuid.UUID,
        days: int = 30,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get activities that provided the most mood improvement
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            limit: Number of activities to return
        
        Returns:
            List of activities with mood improvement
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        activities = self.db.query(BehavioralActivation).filter(
            BehavioralActivation.user_id == user_id,
            BehavioralActivation.created_at >= since_date,
            BehavioralActivation.completion_status == ActivityCompletionStatus.COMPLETED
        ).all()
        
        # Filter activities with mood improvement
        improving_activities = [
            {
                "activity": a.activity,
                "activity_category": a.activity_category,
                "mood_before": a.mood_before,
                "mood_after": a.mood_after,
                "improvement": a.mood_improvement,
                "created_at": a.created_at
            }
            for a in activities
            if a.mood_improvement and a.mood_improvement > 0
        ]
        
        # Sort by improvement and return top N
        sorted_activities = sorted(
            improving_activities,
            key=lambda x: x["improvement"],
            reverse=True
        )
        
        return sorted_activities[:limit]
    
    def get_avoidance_patterns(
        self,
        user_id: uuid.UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze avoidance patterns based on skipped activities
        
        Args:
            user_id: User ID
            days: Number of days to analyze
        
        Returns:
            Dictionary with avoidance insights
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        all_activities = self.db.query(BehavioralActivation).filter(
            BehavioralActivation.user_id == user_id,
            BehavioralActivation.created_at >= since_date
        ).all()
        
        skipped = [a for a in all_activities if a.completion_status == ActivityCompletionStatus.SKIPPED]
        completed = [a for a in all_activities if a.completion_status == ActivityCompletionStatus.COMPLETED]
        
        # Analyze difficulty ratings of skipped activities
        skipped_difficulties = [a.difficulty_rating for a in skipped if a.difficulty_rating]
        avg_skip_difficulty = sum(skipped_difficulties) / len(skipped_difficulties) if skipped_difficulties else None
        
        # Analyze categories of skipped activities
        skipped_categories = {}
        for activity in skipped:
            category = activity.activity_category or "uncategorized"
            skipped_categories[category] = skipped_categories.get(category, 0) + 1
        
        return {
            "total_activities": len(all_activities),
            "completed": len(completed),
            "skipped": len(skipped),
            "skip_rate": round(len(skipped) / len(all_activities) * 100, 1) if all_activities else 0,
            "avg_skip_difficulty": round(avg_skip_difficulty, 2) if avg_skip_difficulty else None,
            "skipped_categories": skipped_categories
        }
    
    def suggest_activities(
        self,
        user_id: uuid.UUID,
        mood: int,
        limit: int = 5
    ) -> List[Dict[str, str]]:
        """
        Suggest activities based on current mood
        
        Args:
            user_id: User ID
            mood: Current mood (1-10)
            limit: Number of suggestions
        
        Returns:
            List of activity suggestions
        """
        # Get past activities that improved mood
        improving_activities = self.get_most_improving_activities(user_id, days=90, limit=20)
        
        # Suggest based on mood level
        suggestions = []
        
        if mood <= 3:
            # Low mood - suggest gentle activities
            gentle_activities = [
                "Take a 5-minute walk outside",
                "Listen to your favorite song",
                "Drink a glass of water",
                "Take 3 deep breaths",
                "Pet an animal or look at cute animal pictures"
            ]
            suggestions.extend([{"activity": a, "reason": "Gentle boost"} for a in gentle_activities[:limit]])
        
        elif mood <= 6:
            # Medium mood - suggest moderate activities
            moderate_activities = [
                "Go for a 15-minute walk",
                "Call a friend or family member",
                "Do a quick stretch routine",
                "Read a chapter of a book",
                "Try a new recipe"
            ]
            suggestions.extend([{"activity": a, "reason": "Moderate engagement"} for a in moderate_activities[:limit]])
        
        else:
            # Good mood - suggest engaging activities
            engaging_activities = [
                "Exercise for 30 minutes",
                "Work on a hobby project",
                "Learn something new",
                "Connect with friends",
                "Tackle a small task you've been avoiding"
            ]
            suggestions.extend([{"activity": a, "reason": "Build on positivity"} for a in engaging_activities[:limit]])
        
        # Add personalized suggestions from past successful activities
        for activity in improving_activities[:limit]:
            if len(suggestions) < limit * 2:
                suggestions.append({
                    "activity": activity["activity"],
                    "reason": f"Improved mood by {activity['improvement']} points before"
                })
        
        return suggestions[:limit]