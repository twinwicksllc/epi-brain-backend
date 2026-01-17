"""
Habit Formation Service

Handles habit management, completion tracking, and streak calculation.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.habit import Habit, HabitCompletion, HabitStatus

logger = logging.getLogger(__name__)

# Habit frequency configurations
HABIT_FREQUENCIES = {
    'daily': {'interval_days': 1, 'description': 'Every day'},
    'weekly': {'interval_days': 7, 'description': 'Once per week'},
    'weekdays': {'interval_days': 1, 'description': 'Monday-Friday'},
    'weekends': {'interval_days': 1, 'description': 'Saturday-Sunday'},
    'custom': {'interval_days': 1, 'description': 'Custom schedule'},
}

# Days of week mapping
DAYS_OF_WEEK = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday',
}


class HabitService:
    """Service for managing user habits and completion tracking"""
    
    def __init__(self, db: Session):
        """
        Initialize the habit service
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    # CRUD Operations
    
    def create_habit(
        self,
        user_id: str,
        name: str,
        description: str,
        frequency: str,
        category: str = "general",
        trigger: Optional[str] = None,
        routine: Optional[str] = None,
        reward: Optional[str] = None,
        target_days: Optional[str] = None,
        **kwargs
    ) -> Habit:
        """
        Create a new habit for a user
        
        Args:
            user_id: The user's ID
            name: Habit name
            description: Detailed description
            frequency: How often (daily, weekly, weekdays, weekends, custom)
            category: Habit category
            trigger: Cue that triggers the habit (habit loop)
            routine: The habit routine itself
            reward: Reward for completing the habit
            target_days: For custom frequency, comma-separated days (0=Mon,6=Sun)
            **kwargs: Additional habit attributes
            
        Returns:
            Created Habit object
        """
        habit = Habit(
            user_id=user_id,
            name=name,
            description=description,
            frequency=frequency,
            trigger=trigger,
            routine=routine,
            reward=reward,
            custom_days=target_days,
            status=HabitStatus.ACTIVE,
            created_by_mode="personal_friend",  # Default mode
            **kwargs
        )
        
        try:
            self.db.add(habit)
            self.db.commit()
            self.db.refresh(habit)
            logger.info(f"Created habit '{name}' for user {user_id}")
            return habit
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating habit: {e}")
            raise
    
    def get_habit(self, habit_id: str, user_id: str) -> Optional[Habit]:
        """
        Get a specific habit for a user
        
        Args:
            habit_id: The habit's ID
            user_id: The user's ID (for authorization)
            
        Returns:
            Habit object or None
        """
        return self.db.query(Habit).filter(
            and_(
                Habit.id == habit_id,
                Habit.user_id == user_id
            )
        ).first()
    
    def get_user_habits(
        self,
        user_id: str,
        is_active: Optional[bool] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Habit]:
        """
        Get all habits for a user, optionally filtered
        
        Args:
            user_id: The user's ID
            is_active: Optional active status filter (mapped to status)
            category: Optional category filter (not used in current model)
            limit: Maximum number of habits to return
            
        Returns:
            List of Habit objects
        """
        query = self.db.query(Habit).filter(Habit.user_id == user_id)
        
        if is_active is not None:
            if is_active:
                query = query.filter(Habit.status == HabitStatus.ACTIVE)
            else:
                query = query.filter(Habit.status != HabitStatus.ACTIVE)
        
        return query.order_by(desc(Habit.created_at)).limit(limit).all()
    
    def update_habit(
        self,
        habit_id: str,
        user_id: str,
        **updates
    ) -> Optional[Habit]:
        """
        Update a habit
        
        Args:
            habit_id: The habit's ID
            user_id: The user's ID (for authorization)
            **updates: Fields to update
            
        Returns:
            Updated Habit object or None
        """
        habit = self.get_habit(habit_id, user_id)
        
        if not habit:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(habit, key):
                setattr(habit, key, value)
        
        habit.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            self.db.refresh(habit)
            logger.info(f"Updated habit {habit_id}")
            return habit
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating habit: {e}")
            return None
    
    def delete_habit(self, habit_id: str, user_id: str) -> bool:
        """
        Delete a habit
        
        Args:
            habit_id: The habit's ID
            user_id: The user's ID (for authorization)
            
        Returns:
            True if deleted, False otherwise
        """
        habit = self.get_habit(habit_id, user_id)
        
        if not habit:
            return False
        
        try:
            self.db.delete(habit)
            self.db.commit()
            logger.info(f"Deleted habit {habit_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting habit: {e}")
            return False
    
    # Completion Tracking
    
    def complete_habit(
        self,
        habit_id: str,
        user_id: str,
        notes: Optional[str] = None,
        completed_at: Optional[datetime] = None
    ) -> HabitCompletion:
        """
        Record a habit completion
        
        Args:
            habit_id: The habit's ID
            user_id: The user's ID (for authorization)
            notes: Optional notes about the completion
            completed_at: When the habit was completed (defaults to now)
            
        Returns:
            Created HabitCompletion object
        """
        habit = self.get_habit(habit_id, user_id)
        
        if not habit:
            raise ValueError("Habit not found")
        
        # Use the model's built-in record_completion method
        if completed_at is None:
            completion = habit.record_completion()
        else:
            # For custom completed_at, create directly
            completion = HabitCompletion(
                habit_id=habit_id,
                user_id=user_id,
                completed_at=completed_at,
                notes=notes
            )
            self.db.add(completion)
            
            # Update stats manually for custom completion
            habit.total_completions += 1
            habit.current_streak_days += 1
            if habit.current_streak_days > habit.longest_streak_days:
                habit.longest_streak_days = habit.current_streak_days
        
        if completion is None:
            raise ValueError("Habit already completed today")
        
        if notes:
            completion.notes = notes
        
        try:
            if completed_at is None:
                self.db.add(completion)
            
            self.db.commit()
            self.db.refresh(completion)
            logger.info(f"Recorded completion for habit {habit_id}")
            return completion
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording habit completion: {e}")
            raise
    
    def get_habit_completions(
        self,
        habit_id: str,
        user_id: str,
        limit: int = 30
    ) -> List[HabitCompletion]:
        """
        Get all completions for a habit
        
        Args:
            habit_id: The habit's ID
            user_id: The user's ID (for authorization)
            limit: Maximum number of completions to return
            
        Returns:
            List of HabitCompletion objects
        """
        # Verify habit belongs to user
        habit = self.get_habit(habit_id, user_id)
        if not habit:
            return []
        
        return self.db.query(HabitCompletion).filter(
            HabitCompletion.habit_id == habit_id
        ).order_by(desc(HabitCompletion.completed_at)).limit(limit).all()
    
    def get_due_habits(self, user_id: str) -> List[Habit]:
        """
        Get habits that are due today
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of Habit objects that are due today
        """
        # Get active habits
        habits = self.db.query(Habit).filter(
            and_(
                Habit.user_id == user_id,
                Habit.status == HabitStatus.ACTIVE
            )
        ).all()
        
        due_habits = []
        today = date.today()
        
        for habit in habits:
            if habit.is_due_today:
                due_habits.append(habit)
        
        return due_habits
    
    def get_habit_summary(self, habit_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive summary for a habit
        
        Args:
            habit_id: The habit's ID
            user_id: The user's ID (for authorization)
            
        Returns:
            Dictionary with habit statistics
        """
        habit = self.get_habit(habit_id, user_id)
        
        if not habit:
            return {}
        
        completions = self.get_habit_completions(habit_id, user_id)
        
        # Calculate statistics
        total_completions = len(completions)
        
        # Calculate completion rate
        if habit.started_at:
            days_active = (datetime.utcnow() - habit.started_at).days
            expected_completions = self._calculate_expected_completions(habit, days_active)
            completion_rate = (total_completions / expected_completions) * 100 if expected_completions > 0 else 0
        else:
            completion_rate = 0.0
        
        # Use model's streak values
        current_streak = habit.current_streak_days
        best_streak = habit.longest_streak_days
        
        # Calculate completions in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_completions = [c for c in completions if c.completed_at >= thirty_days_ago]
        
        return {
            'habit_id': habit_id,
            'name': habit.name,
            'description': habit.description,
            'frequency': str(habit.frequency),
            'status': str(habit.status),
            'streak_days': current_streak,
            'best_streak': best_streak,
            'completion_rate': round(completion_rate, 1),
            'total_completions': total_completions,
            'completions_last_30_days': len(recent_completions),
            'trigger': habit.trigger,
            'routine': habit.routine,
            'reward': habit.reward
        }
    
    # Helper methods
    
    def _calculate_expected_completions(
        self,
        habit: Habit,
        days_active: int
    ) -> int:
        """Calculate expected completions based on frequency"""
        if days_active <= 0:
            return 0
        
        frequency_str = str(habit.frequency).lower()
        
        if frequency_str == 'daily':
            return days_active
        elif frequency_str == 'weekdays':
            # Approximate 5/7 of days are weekdays
            return int(days_active * 5 / 7)
        elif frequency_str == 'weekends':
            # Approximate 2/7 of days are weekends
            return int(days_active * 2 / 7)
        elif frequency_str == 'weekly':
            return max(1, days_active // 7)
        elif frequency_str == 'custom' and habit.custom_days:
            # Count how many target days in the period
            import json
            try:
                target_days = json.loads(habit.custom_days)
                return int(days_active * len(target_days) / 7)
            except:
                return days_active
        
        return days_active
    
    def _update_habit_stats(self, habit: Habit):
        """Update habit statistics - the model handles streak calculation automatically"""
        # The Habit model handles streak calculation in its record_completion method
        # We just need to ensure the model is updated
        pass