"""
Habit Formation Service

Handles habit management, completion tracking, and streak calculation.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.habit import Habit, HabitCompletion

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
            category=category,
            trigger=trigger,
            routine=routine,
            reward=reward,
            target_days=target_days,
            is_active=True,
            streak_days=0,
            completion_rate=0.0,
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
            is_active: Optional active status filter
            category: Optional category filter
            limit: Maximum number of habits to return
            
        Returns:
            List of Habit objects
        """
        query = self.db.query(Habit).filter(Habit.user_id == user_id)
        
        if is_active is not None:
            query = query.filter(Habit.is_active == is_active)
        
        if category:
            query = query.filter(Habit.category == category)
        
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
        
        if completed_at is None:
            completed_at = datetime.utcnow()
        
        # Create completion record
        completion = HabitCompletion(
            habit_id=habit_id,
            user_id=user_id,
            completed_at=completed_at,
            notes=notes
        )
        
        try:
            self.db.add(completion)
            
            # Update habit statistics
            self._update_habit_stats(habit)
            
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
        today = date.today()
        current_weekday = today.weekday()
        
        habits = self.get_user_habits(user_id, is_active=True)
        due_habits = []
        
        for habit in habits:
            if self._is_habit_due_today(habit, today, current_weekday):
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
        if habit.created_at:
            days_active = (datetime.utcnow() - habit.created_at).days
            expected_completions = self._calculate_expected_completions(habit, days_active)
            completion_rate = (total_completions / expected_completions) * 100 if expected_completions > 0 else 0
        else:
            completion_rate = 0.0
        
        # Calculate best streak
        best_streak = self._calculate_best_streak(completions, habit.frequency)
        
        # Calculate completions in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_completions = [c for c in completions if c.completed_at >= thirty_days_ago]
        
        return {
            'habit_id': habit_id,
            'name': habit.name,
            'description': habit.description,
            'frequency': habit.frequency,
            'is_active': habit.is_active,
            'streak_days': habit.streak_days,
            'best_streak': best_streak,
            'completion_rate': round(completion_rate, 1),
            'total_completions': total_completions,
            'completions_last_30_days': len(recent_completions),
            'trigger': habit.trigger,
            'routine': habit.routine,
            'reward': habit.reward
        }
    
    # Helper methods
    
    def _is_habit_due_today(
        self,
        habit: Habit,
        today: date,
        current_weekday: int
    ) -> bool:
        """Check if a habit is due today"""
        frequency = habit.frequency
        
        if frequency == 'daily':
            return True
        elif frequency == 'weekdays':
            return current_weekday < 5  # Monday-Friday
        elif frequency == 'weekends':
            return current_weekday >= 5  # Saturday-Sunday
        elif frequency == 'weekly':
            # Check if last completion was at least 7 days ago
            last_completion = self.db.query(HabitCompletion).filter(
                HabitCompletion.habit_id == habit.id
            ).order_by(desc(HabitCompletion.completed_at)).first()
            
            if not last_completion:
                return True
            
            days_since_last = (today - last_completion.completed_at.date()).days
            return days_since_last >= 7
        elif frequency == 'custom' and habit.target_days:
            # Check if today is in target days
            target_days = [int(d.strip()) for d in habit.target_days.split(',')]
            return current_weekday in target_days
        
        return False
    
    def _calculate_expected_completions(
        self,
        habit: Habit,
        days_active: int
    ) -> int:
        """Calculate expected completions based on frequency"""
        if days_active <= 0:
            return 0
        
        frequency = habit.frequency
        
        if frequency == 'daily':
            return days_active
        elif frequency == 'weekdays':
            # Approximate 5/7 of days are weekdays
            return int(days_active * 5 / 7)
        elif frequency == 'weekends':
            # Approximate 2/7 of days are weekends
            return int(days_active * 2 / 7)
        elif frequency == 'weekly':
            return max(1, days_active // 7)
        elif frequency == 'custom' and habit.target_days:
            # Count how many target days in the period
            target_days = [int(d.strip()) for d in habit.target_days.split(',')]
            return int(days_active * len(target_days) / 7)
        
        return days_active
    
    def _update_habit_stats(self, habit: Habit):
        """Update habit statistics (streak, completion rate)"""
        completions = self.get_habit_completions(str(habit.id), str(habit.user_id))
        
        # Update current streak
        habit.streak_days = self._calculate_current_streak(completions, habit.frequency)
        
        # Update completion rate
        if habit.created_at:
            days_active = (datetime.utcnow() - habit.created_at).days
            expected = self._calculate_expected_completions(habit, days_active)
            habit.completion_rate = (len(completions) / expected) * 100 if expected > 0 else 0.0
        else:
            habit.completion_rate = 0.0
    
    def _calculate_current_streak(
        self,
        completions: List[HabitCompletion],
        frequency: str
    ) -> int:
        """Calculate current streak based on frequency"""
        if not completions:
            return 0
        
        interval_days = HABIT_FREQUENCIES.get(frequency, {}).get('interval_days', 1)
        
        current_date = datetime.utcnow()
        streak = 0
        
        for completion in completions:
            days_diff = (current_date - completion.completed_at).days
            
            if days_diff <= interval_days:
                streak += 1
                current_date = completion.completed_at
            else:
                break
        
        return streak
    
    def _calculate_best_streak(
        self,
        completions: List[HabitCompletion],
        frequency: str
    ) -> int:
        """Calculate the best streak ever achieved"""
        if not completions:
            return 0
        
        # Sort by date ascending
        sorted_completions = sorted(completions, key=lambda c: c.completed_at)
        
        interval_days = HABIT_FREQUENCIES.get(frequency, {}).get('interval_days', 1)
        
        best_streak = 0
        current_streak = 0
        last_date = None
        
        for completion in sorted_completions:
            if last_date is None:
                current_streak = 1
            else:
                days_diff = (completion.completed_at - last_date).days
                if days_diff <= interval_days:
                    current_streak += 1
                else:
                    current_streak = 1
            
            if current_streak > best_streak:
                best_streak = current_streak
            
            last_date = completion.completed_at
        
        return best_streak