"""
Goal Management Service

Handles CRUD operations, progress tracking, and streak calculation for user goals.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.goal import Goal, CheckIn, Milestone, GoalStatus, GoalCategory
from app.models.user import User

logger = logging.getLogger(__name__)

# Default check-in intervals (in days) - for calculating due check-ins
CHECK_IN_INTERVALS = {
    'daily': 1,
    'weekly': 7,
    'biweekly': 14,
    'monthly': 30,
}

# Goal status transitions
GOAL_STATUS_TRANSITIONS = {
    'not_started': ['in_progress'],
    'in_progress': ['on_track', 'behind', 'at_risk', 'completed'],
    'on_track': ['in_progress', 'behind', 'completed'],
    'behind': ['in_progress', 'at_risk', 'completed'],
    'at_risk': ['in_progress', 'completed'],
    'completed': []  # No transitions from completed
}

# Default check-in intervals (in days)
CHECK_IN_INTERVALS = {
    'daily': 1,
    'weekly': 7,
    'biweekly': 14,
    'monthly': 30,
}


class GoalService:
    """Service for managing user goals and progress tracking"""
    
    def __init__(self, db: Session):
        """
        Initialize the goal service
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    # CRUD Operations
    
    def create_goal(
        self,
        user_id: str,
        title: str,
        description: str,
        category: str,
        time_bound_deadline: Optional[datetime] = None,
        accountability_style: str = "adaptive",
        created_by_mode: str = "personal_friend",
        **kwargs
    ) -> Goal:
        """
        Create a new goal for a user
        
        Args:
            user_id: The user's ID
            title: Goal title
            description: Detailed description of the goal
            category: Goal category (e.g., 'health', 'career', 'personal')
            time_bound_deadline: Optional target completion datetime
            accountability_style: How to hold user accountable (tactical, grace, analyst, adaptive)
            created_by_mode: Which mode created this goal
            **kwargs: Additional goal attributes
            
        Returns:
            Created Goal object
        """
        goal = Goal(
            user_id=user_id,
            title=title,
            description=description,
            category=GoalCategory(category.upper()) if isinstance(category, str) else category,
            time_bound_deadline=time_bound_deadline,
            accountability_style=accountability_style,
            created_by_mode=created_by_mode,
            status=GoalStatus.NOT_STARTED,
            progress_percentage=0.0,
            **kwargs
        )
        
        try:
            self.db.add(goal)
            self.db.commit()
            self.db.refresh(goal)
            logger.info(f"Created goal '{title}' for user {user_id}")
            return goal
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating goal: {e}")
            raise
    
    def get_goal(self, goal_id: str, user_id: str) -> Optional[Goal]:
        """
        Get a specific goal for a user
        
        Args:
            goal_id: The goal's ID
            user_id: The user's ID (for authorization)
            
        Returns:
            Goal object or None
        """
        return self.db.query(Goal).filter(
            and_(
                Goal.id == goal_id,
                Goal.user_id == user_id
            )
        ).first()
    
    def get_user_goals(
        self,
        user_id: str,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Goal]:
        """
        Get all goals for a user, optionally filtered
        
        Args:
            user_id: The user's ID
            status: Optional status filter
            category: Optional category filter
            limit: Maximum number of goals to return
            
        Returns:
            List of Goal objects
        """
        query = self.db.query(Goal).filter(Goal.user_id == user_id)
        
        if status:
            query = query.filter(Goal.status == status)
        
        if category:
            query = query.filter(Goal.category == category)
        
        return query.order_by(desc(Goal.created_at)).limit(limit).all()
    
    def update_goal(
        self,
        goal_id: str,
        user_id: str,
        **updates
    ) -> Optional[Goal]:
        """
        Update a goal
        
        Args:
            goal_id: The goal's ID
            user_id: The user's ID (for authorization)
            **updates: Fields to update
            
        Returns:
            Updated Goal object or None
        """
        goal = self.get_goal(goal_id, user_id)
        
        if not goal:
            return None
        
        # Validate status transitions
        if 'status' in updates:
            current_status = goal.status
            new_status = updates['status']
            if new_status not in GOAL_STATUS_TRANSITIONS.get(current_status, []):
                logger.warning(f"Invalid status transition: {current_status} -> {new_status}")
                return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(goal, key):
                setattr(goal, key, value)
        
        goal.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            self.db.refresh(goal)
            logger.info(f"Updated goal {goal_id}")
            return goal
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating goal: {e}")
            return None
    
    def delete_goal(self, goal_id: str, user_id: str) -> bool:
        """
        Delete a goal
        
        Args:
            goal_id: The goal's ID
            user_id: The user's ID (for authorization)
            
        Returns:
            True if deleted, False otherwise
        """
        goal = self.get_goal(goal_id, user_id)
        
        if not goal:
            return False
        
        try:
            self.db.delete(goal)
            self.db.commit()
            logger.info(f"Deleted goal {goal_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting goal: {e}")
            return False
    
    # Progress Tracking
    
    def create_check_in(
        self,
        goal_id: str,
        user_id: str,
        progress_notes: str,
        mood: Optional[str] = None,
        energy_level: Optional[int] = None,
        progress_percentage: Optional[float] = None
    ) -> CheckIn:
        """
        Create a check-in for a goal
        
        Args:
            goal_id: The goal's ID
            user_id: The user's ID (for authorization)
            progress_notes: Notes about progress
            mood: Current mood (e.g., 'motivated', 'struggling', 'neutral')
            energy_level: Energy level (1-10)
            progress_percentage: Optional progress update
            
        Returns:
            Created CheckIn object
        """
        goal = self.get_goal(goal_id, user_id)
        
        if not goal:
            raise ValueError("Goal not found")
        
        # Update goal status based on check-in
        self._update_goal_status_from_check_in(goal, mood, energy_level)
        
        # Update progress percentage if provided
        if progress_percentage is not None:
            goal.progress_percentage = max(0, min(100, progress_percentage))
            if goal.progress_percentage >= 100:
                goal.status = 'completed'
                goal.completed_at = datetime.utcnow()
        
        # Update streak
        self._update_streak(goal)
        
        check_in = CheckIn(
            goal_id=goal_id,
            user_id=user_id,
            progress_notes=progress_notes,
            mood=mood,
            energy_level=energy_level
        )
        
        try:
            self.db.add(check_in)
            self.db.commit()
            self.db.refresh(check_in)
            logger.info(f"Created check-in for goal {goal_id}")
            return check_in
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating check-in: {e}")
            raise
    
    def get_check_ins(
        self,
        goal_id: str,
        user_id: str,
        limit: int = 20
    ) -> List[CheckIn]:
        """
        Get all check-ins for a goal
        
        Args:
            goal_id: The goal's ID
            user_id: The user's ID (for authorization)
            limit: Maximum number of check-ins to return
            
        Returns:
            List of CheckIn objects
        """
        # Verify goal belongs to user
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return []
        
        return self.db.query(CheckIn).filter(
            CheckIn.goal_id == goal_id
        ).order_by(desc(CheckIn.created_at)).limit(limit).all()
    
    def get_goal_progress(self, goal_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive progress information for a goal
        
        Args:
            goal_id: The goal's ID
            user_id: The user's ID (for authorization)
            
        Returns:
            Dictionary with progress statistics
        """
        goal = self.get_goal(goal_id, user_id)
        
        if not goal:
            return {}
        
        check_ins = self.get_check_ins(goal_id, user_id)
        
        # Calculate statistics
        total_check_ins = len(check_ins)
        
        # Calculate completion rate (check-ins due vs completed)
        if goal.created_at:
            days_active = (datetime.utcnow() - goal.created_at).days
            expected_check_ins = max(1, days_active // CHECK_IN_INTERVALS.get(goal.check_in_frequency, 7))
            completion_rate = (total_check_ins / expected_check_ins) * 100 if expected_check_ins > 0 else 0
        else:
            completion_rate = 0.0
        
        # Average energy level
        energy_levels = [ci.energy_level for ci in check_ins if ci.energy_level]
        avg_energy = sum(energy_levels) / len(energy_levels) if energy_levels else None
        
        # Mood distribution
        mood_counts = {}
        for ci in check_ins:
            if ci.mood:
                mood_counts[ci.mood] = mood_counts.get(ci.mood, 0) + 1
        
        return {
            'goal_id': goal_id,
            'status': goal.status,
            'progress_percentage': goal.progress_percentage,
            'streak_days': goal.streak_days,
            'completion_rate': round(completion_rate, 1),
            'total_check_ins': total_check_ins,
            'average_energy': avg_energy,
            'mood_distribution': mood_counts,
            'target_date': goal.target_date.isoformat() if goal.target_date else None,
            'days_until_target': (goal.target_date - date.today()).days if goal.target_date else None
        }
    
    # Milestone Management
    
    def create_milestone(
        self,
        goal_id: str,
        user_id: str,
        title: str,
        description: str,
        target_date: Optional[date] = None
    ) -> Milestone:
        """
        Create a milestone for a goal
        
        Args:
            goal_id: The goal's ID
            user_id: The user's ID (for authorization)
            title: Milestone title
            description: Milestone description
            target_date: Optional target date
            
        Returns:
            Created Milestone object
        """
        goal = self.get_goal(goal_id, user_id)
        
        if not goal:
            raise ValueError("Goal not found")
        
        milestone = Milestone(
            goal_id=goal_id,
            user_id=user_id,
            title=title,
            description=description,
            target_date=target_date,
            is_completed=False
        )
        
        try:
            self.db.add(milestone)
            self.db.commit()
            self.db.refresh(milestone)
            logger.info(f"Created milestone '{title}' for goal {goal_id}")
            return milestone
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating milestone: {e}")
            raise
    
    def complete_milestone(
        self,
        milestone_id: str,
        user_id: str
    ) -> Optional[Milestone]:
        """
        Mark a milestone as completed
        
        Args:
            milestone_id: The milestone's ID
            user_id: The user's ID (for authorization)
            
        Returns:
            Updated Milestone object or None
        """
        milestone = self.db.query(Milestone).filter(
            and_(
                Milestone.id == milestone_id,
                Milestone.user_id == user_id
            )
        ).first()
        
        if not milestone:
            return None
        
        milestone.is_completed = True
        milestone.completed_at = datetime.utcnow()
        
        try:
            self.db.commit()
            self.db.refresh(milestone)
            logger.info(f"Completed milestone {milestone_id}")
            return milestone
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing milestone: {e}")
            return None
    
    def get_milestones(self, goal_id: str, user_id: str) -> List[Milestone]:
        """
        Get all milestones for a goal
        
        Args:
            goal_id: The goal's ID
            user_id: The user's ID (for authorization)
            
        Returns:
            List of Milestone objects
        """
        # Verify goal belongs to user
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return []
        
        return self.db.query(Milestone).filter(
            Milestone.goal_id == goal_id
        ).order_by(Milestone.created_at).all()
    
    # Helper methods
    
    def _update_goal_status_from_check_in(
        self,
        goal: Goal,
        mood: Optional[str],
        energy_level: Optional[int]
    ):
        """Update goal status based on check-in data"""
        if goal.status == 'completed':
            return
        
        if mood == 'motivated' and energy_level and energy_level >= 7:
            goal.status = 'on_track'
        elif mood == 'struggling' or (energy_level and energy_level <= 4):
            goal.status = 'at_risk'
        elif mood in ['neutral', 'uncertain']:
            goal.status = 'behind'
        else:
            goal.status = 'in_progress'
    
    def _update_streak(self, goal: Goal):
        """Update streak calculation for a goal"""
        # Get recent check-ins
        recent_check_ins = self.db.query(CheckIn).filter(
            CheckIn.goal_id == goal.id
        ).order_by(desc(CheckIn.created_at)).limit(30).all()
        
        if not recent_check_ins:
            goal.streak_days = 0
            return
        
        # Calculate streak based on check-in frequency
        interval_days = CHECK_IN_INTERVALS.get(goal.check_in_frequency, 7)
        
        current_date = datetime.utcnow()
        streak = 0
        
        for check_in in recent_check_ins:
            days_diff = (current_date - check_in.created_at).days
            
            if days_diff <= interval_days:
                streak += 1
                current_date = check_in.created_at
            else:
                break
        
        goal.streak_days = streak
        goal.completion_rate = self._calculate_completion_rate(goal)
    
    def _calculate_completion_rate(self, goal: Goal) -> float:
        """Calculate overall completion rate for a goal"""
        if not goal.created_at:
            return 0.0
        
        total_check_ins = self.db.query(CheckIn).filter(
            CheckIn.goal_id == goal.id
        ).count()
        
        days_active = (datetime.utcnow() - goal.created_at).days
        expected_check_ins = max(1, days_active // CHECK_IN_INTERVALS.get(goal.check_in_frequency, 7))
        
        return (total_check_ins / expected_check_ins) * 100 if expected_check_ins > 0 else 0.0