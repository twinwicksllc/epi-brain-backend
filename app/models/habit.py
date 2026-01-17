"""
Habit Model

Stores habits with frequency tracking and streak management.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class HabitFrequency(str, enum.Enum):
    """Habit frequency options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    WEEKDAYS = "weekdays"  # Mon-Fri
    WEEKENDS = "weekends"  # Sat-Sun
    CUSTOM = "custom"  # Specific days


class HabitStatus(str, enum.Enum):
    """Habit status"""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Habit(Base):
    """
    User habit with tracking and streaks
    
    Habits are recurring behaviors users want to build.
    Track completions, streaks, and patterns.
    """
    
    __tablename__ = "habits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Habit details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Frequency and timing
    frequency = Column(SQLEnum(HabitFrequency), default=HabitFrequency.DAILY, nullable=False)
    custom_days = Column(Text, nullable=True)  # JSON array of days for CUSTOM frequency
    target_time = Column(String(50), nullable=True)  # e.g., "07:00", "evening"
    
    # Trigger and reward (habit loop)
    trigger = Column(Text, nullable=True)  # What triggers the habit
    routine = Column(Text, nullable=True)  # The habit itself
    reward = Column(Text, nullable=True)  # The reward after completion
    
    # Status
    status = Column(SQLEnum(HabitStatus), default=HabitStatus.ACTIVE, nullable=False, index=True)
    
    # Streak tracking
    current_streak_days = Column(Integer, default=0, nullable=False)
    longest_streak_days = Column(Integer, default=0, nullable=False)
    total_completions = Column(Integer, default=0, nullable=False)
    
    # Mode that created this habit
    created_by_mode = Column(String(50), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    
    # Relationships
    completions = relationship("HabitCompletion", back_populates="habit", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Habit {self.id} - {self.name} - {self.current_streak_days} day streak>"
    
    @property
    def is_due_today(self) -> bool:
        """Check if habit is due today"""
        from datetime import date
        today = date.today().weekday()  # 0 = Monday, 6 = Sunday
        
        if self.status != HabitStatus.ACTIVE:
            return False
        
        if self.frequency == HabitFrequency.DAILY:
            return True
        elif self.frequency == HabitFrequency.WEEKLY:
            # Check if completed this week
            week_start = date.today() - datetime.timedelta(days=date.today().weekday())
            completed_this_week = any(
                c.completed_at.date() >= week_start 
                for c in self.completions
            )
            return not completed_this_week
        elif self.frequency == HabitFrequency.WEEKDAYS:
            return today < 5  # Mon-Fri
        elif self.frequency == HabitFrequency.WEEKENDS:
            return today >= 5  # Sat-Sun
        elif self.frequency == HabitFrequency.CUSTOM:
            import json
            if not self.custom_days:
                return False
            custom_days = json.loads(self.custom_days)
            return today in custom_days
        
        return False
    
    def record_completion(self):
        """Record a habit completion"""
        from datetime import date
        today = date.today()
        
        # Check if already completed today
        already_completed = any(
            c.completed_at.date() == today 
            for c in self.completions
        )
        
        if already_completed:
            return False
        
        # Create completion record
        completion = HabitCompletion(
            habit_id=self.id,
            user_id=self.user_id,
            completed_at=datetime.utcnow()
        )
        
        # Update streak
        self.total_completions += 1
        self.current_streak_days += 1
        if self.current_streak_days > self.longest_streak_days:
            self.longest_streak_days = self.current_streak_days
        
        return completion


class HabitCompletion(Base):
    """
    Record of habit completion
    
    Tracks when habits were completed for streak calculation.
    """
    
    __tablename__ = "habit_completions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    habit_id = Column(UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Completion details
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    mood = Column(String(20), nullable=True)
    difficulty = Column(Integer, nullable=True)  # 1-10
    
    def __repr__(self):
        return f"<HabitCompletion {self.id} - {self.completed_at}>"