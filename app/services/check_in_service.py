"""
Check-in Scheduler Service

Handles scheduled check-ins, progress collection, and mood/energy tracking.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.goal import Goal, CheckIn
from app.models.habit import Habit, HabitCompletion

logger = logging.getLogger(__name__)


class CheckInService:
    """Service for managing scheduled check-ins and progress tracking"""
    
    def __init__(self, db: Session, goal_service=None, habit_service=None):
        """
        Initialize the check-in service
        
        Args:
            db: SQLAlchemy database session
            goal_service: Optional GoalService instance
            habit_service: Optional HabitService instance
        """
        self.db = db
        self.goal_service = goal_service
        self.habit_service = habit_service
    
    # Check-in Scheduling
    
    def get_pending_check_ins(self, user_id: str) -> Dict[str, Any]:
        """
        Get all goals and habits that are due for check-in
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with due goals and habits
        """
        from app.services.goal_service import GoalService
        from app.services.habit_service import HabitService
        
        if not self.goal_service:
            self.goal_service = GoalService(self.db)
        if not self.habit_service:
            self.habit_service = HabitService(self.db)
        
        # Get active goals
        goals = self.goal_service.get_user_goals(
            user_id=user_id,
            status='in_progress'
        )
        
        # Filter goals that need check-in
        due_goals = []
        for goal in goals:
            if self._is_goal_due_for_check_in(goal):
                due_goals.append(goal)
        
        # Get habits due today
        due_habits = self.habit_service.get_due_habits(user_id)
        
        return {
            'due_goals': due_goals,
            'due_habits': due_habits,
            'total_due': len(due_goals) + len(due_habits)
        }
    
    def create_check_in(
        self,
        user_id: str,
        item_type: str,  # 'goal' or 'habit'
        item_id: str,
        progress_notes: str,
        mood: Optional[str] = None,
        energy_level: Optional[int] = None,
        progress_percentage: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a check-in for a goal or habit
        
        Args:
            user_id: The user's ID
            item_type: Type of item ('goal' or 'habit')
            item_id: ID of the goal or habit
            progress_notes: Notes about progress
            mood: Current mood
            energy_level: Energy level (1-10)
            progress_percentage: Progress update for goals
            notes: Alternative notes parameter for habits
            
        Returns:
            Dictionary with check-in result
        """
        from app.services.goal_service import GoalService
        from app.services.habit_service import HabitService
        
        if not self.goal_service:
            self.goal_service = GoalService(self.db)
        if not self.habit_service:
            self.habit_service = HabitService(self.db)
        
        if item_type == 'goal':
            # Use notes parameter if progress_notes is not provided
            notes_to_use = progress_notes or notes or ""
            
            check_in = self.goal_service.create_check_in(
                goal_id=item_id,
                user_id=user_id,
                progress_notes=notes_to_use,
                mood=mood,
                energy_level=energy_level,
                progress_percentage=progress_percentage
            )
            
            return {
                'type': 'goal',
                'check_in': check_in,
                'message': 'Goal check-in recorded successfully'
            }
        
        elif item_type == 'habit':
            # Use notes parameter if progress_notes is not provided
            notes_to_use = notes or progress_notes or ""
            
            completion = self.habit_service.complete_habit(
                habit_id=item_id,
                user_id=user_id,
                notes=notes_to_use
            )
            
            # Refresh habit to get updated stats
            habit = self.habit_service.get_habit(item_id, user_id)
            
            return {
                'type': 'habit',
                'completion': completion,
                'habit': habit,
                'message': 'Habit completion recorded successfully'
            }
        
        else:
            raise ValueError(f"Invalid item_type: {item_type}")
    
    def get_daily_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a daily summary of goals and habits
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with daily summary
        """
        from app.services.goal_service import GoalService
        from app.services.habit_service import HabitService
        
        if not self.goal_service:
            self.goal_service = GoalService(self.db)
        if not self.habit_service:
            self.habit_service = HabitService(self.db)
        
        # Get pending check-ins
        pending = self.get_pending_check_ins(user_id)
        
        # Get completed today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        completed_habits = self.db.query(HabitCompletion).join(Habit).filter(
            and_(
                Habit.user_id == user_id,
                HabitCompletion.completed_at >= today_start
            )
        ).all()
        
        completed_goals = self.db.query(CheckIn).filter(
            and_(
                CheckIn.user_id == user_id,
                CheckIn.created_at >= today_start
            )
        ).all()
        
        # Calculate overall progress
        all_goals = self.goal_service.get_user_goals(user_id)
        active_goals = [g for g in all_goals if g.status in ['in_progress', 'on_track', 'behind', 'at_risk']]
        
        avg_progress = 0
        if active_goals:
            avg_progress = sum(g.progress_percentage for g in active_goals) / len(active_goals)
        
        # Mood summary
        recent_moods = self.db.query(CheckIn).filter(
            CheckIn.user_id == user_id
        ).order_by(desc(CheckIn.created_at)).limit(7).all()
        
        mood_counts = {}
        for ci in recent_moods:
            if ci.mood:
                mood_counts[ci.mood] = mood_counts.get(ci.mood, 0) + 1
        
        return {
            'date': today_start.date().isoformat(),
            'pending_goals': len(pending['due_goals']),
            'pending_habits': len(pending['due_habits']),
            'completed_goals_today': len(completed_goals),
            'completed_habits_today': len(completed_habits),
            'total_active_goals': len(active_goals),
            'average_goal_progress': round(avg_progress, 1),
            'recent_moods': mood_counts,
            'total_pending': pending['total_due']
        }
    
    def get_weekly_trends(self, user_id: str) -> Dict[str, Any]:
        """
        Get weekly trends for goals and habits
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with weekly trends
        """
        from app.services.goal_service import GoalService
        
        if not self.goal_service:
            self.goal_service = GoalService(self.db)
        
        # Get data for last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Goal check-ins per day
        goal_check_ins = self.db.query(
            func.date(CheckIn.created_at).label('date'),
            func.count(CheckIn.id).label('count')
        ).filter(
            and_(
                CheckIn.user_id == user_id,
                CheckIn.created_at >= week_ago
            )
        ).group_by(func.date(CheckIn.created_at)).all()
        
        goal_trends = {str(row.date): row.count for row in goal_check_ins}
        
        # Habit completions per day
        habit_completions = self.db.query(
            func.date(HabitCompletion.completed_at).label('date'),
            func.count(HabitCompletion.id).label('count')
        ).join(Habit).filter(
            and_(
                Habit.user_id == user_id,
                HabitCompletion.completed_at >= week_ago
            )
        ).group_by(func.date(HabitCompletion.completed_at)).all()
        
        habit_trends = {str(row.date): row.count for row in habit_completions}
        
        # Energy level trends
        energy_data = self.db.query(
            CheckIn.energy_level,
            CheckIn.created_at
        ).filter(
            and_(
                CheckIn.user_id == user_id,
                CheckIn.created_at >= week_ago,
                CheckIn.energy_level.isnot(None)
            )
        ).all()
        
        if energy_data:
            avg_energy = sum(e[0] for e in energy_data) / len(energy_data)
        else:
            avg_energy = None
        
        return {
            'goal_check_in_trends': goal_trends,
            'habit_completion_trends': habit_trends,
            'average_energy_level': avg_energy,
            'period': 'last_7_days'
        }
    
    def get_overdue_items(self, user_id: str) -> Dict[str, Any]:
        """
        Get goals and habits that are overdue for check-in
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with overdue items
        """
        from app.services.goal_service import GoalService
        
        if not self.goal_service:
            self.goal_service = GoalService(self.db)
        
        # Get active goals
        goals = self.goal_service.get_user_goals(
            user_id=user_id,
            status='in_progress'
        )
        
        overdue_goals = []
        for goal in goals:
            if self._is_goal_overdue(goal):
                overdue_goals.append(goal)
        
        # Get habits that are due today but not completed
        if not self.habit_service:
            from app.services.habit_service import HabitService
            self.habit_service = HabitService(self.db)
        
        due_habits = self.habit_service.get_due_habits(user_id)
        
        # Filter out habits completed today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        overdue_habits = []
        for habit in due_habits:
            completed_today = self.db.query(HabitCompletion).filter(
                and_(
                    HabitCompletion.habit_id == habit.id,
                    HabitCompletion.completed_at >= today_start
                )
            ).first()
            
            if not completed_today:
                overdue_habits.append(habit)
        
        return {
            'overdue_goals': overdue_goals,
            'overdue_habits': overdue_habits,
            'total_overdue': len(overdue_goals) + len(overdue_habits)
        }
    
    # Helper methods
    
    def _is_goal_due_for_check_in(self, goal: Goal) -> bool:
        """Check if a goal is due for check-in based on its frequency"""
        if goal.status == 'completed':
            return False
        
        if not goal.created_at:
            return True
        
        # Get last check-in
        last_check_in = self.db.query(CheckIn).filter(
            CheckIn.goal_id == goal.id
        ).order_by(desc(CheckIn.created_at)).first()
        
        if not last_check_in:
            # Goals should have check-in within first day
            return (datetime.utcnow() - goal.created_at).days >= 1
        
        # Calculate days since last check-in
        days_since_last = (datetime.utcnow() - last_check_in.created_at).days
        
        # Get expected interval based on check-in frequency
        from app.services.goal_service import CHECK_IN_INTERVALS
        interval = CHECK_IN_INTERVALS.get(goal.check_in_frequency, 7)
        
        return days_since_last >= interval
    
    def _is_goal_overdue(self, goal: Goal) -> bool:
        """Check if a goal is overdue for check-in"""
        if goal.status == 'completed':
            return False
        
        if not goal.created_at:
            return False
        
        # Get last check-in
        last_check_in = self.db.query(CheckIn).filter(
            CheckIn.goal_id == goal.id
        ).order_by(desc(CheckIn.created_at)).first()
        
        if not last_check_in:
            # Goals overdue if no check-in in 3 days
            return (datetime.utcnow() - goal.created_at).days > 3
        
        # Calculate days since last check-in
        days_since_last = (datetime.utcnow() - last_check_in.created_at).days
        
        # Get expected interval
        from app.services.goal_service import CHECK_IN_INTERVALS
        interval = CHECK_IN_INTERVALS.get(goal.check_in_frequency, 7)
        
        # Overdue if past interval by more than 1 day
        return days_since_last > (interval + 1)