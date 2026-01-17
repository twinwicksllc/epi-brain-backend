"""
Goal Model

Stores user goals with tracking, milestones, and progress.
"""

from sqlalchemy import Column, String, DateTime, Float, Text, Boolean, Enum as SQLEnum, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class GoalStatus(str, enum.Enum):
    """Goal status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    BEHIND = "behind"
    AT_RISK = "at_risk"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class GoalCategory(str, enum.Enum):
    """Goal categories"""
    HEALTH = "health"
    CAREER = "career"
    RELATIONSHIPS = "relationships"
    FINANCE = "finance"
    PERSONAL_GROWTH = "personal_growth"
    SPIRITUAL = "spiritual"
    EDUCATION = "education"
    OTHER = "other"


class GoalPriority(str, enum.Enum):
    """Goal priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Goal(Base):
    """
    User goal with tracking and milestones
    
    Goals can be short-term (days/weeks) or long-term (months/years).
    Each goal has check-ins, milestones, and progress tracking.
    """
    
    __tablename__ = "goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Goal details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(GoalCategory), nullable=False, index=True)
    priority = Column(SQLEnum(GoalPriority), default=GoalPriority.MEDIUM, nullable=False)
    
    # Goal status and progress
    status = Column(SQLEnum(GoalStatus), default=GoalStatus.NOT_STARTED, nullable=False, index=True)
    progress_percentage = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0
    
    # SMART goal components
    specific_description = Column(Text, nullable=True)  # What exactly will be accomplished
    measurable_criteria = Column(Text, nullable=True)  # How will you know it's achieved
    achievable_proof = Column(Text, nullable=True)  # Why is this realistic
    relevance_reasoning = Column(Text, nullable=True)  # Why does this matter
    time_bound_deadline = Column(DateTime, nullable=True)  # When will it be completed
    
    # Tracking
    current_streak_days = Column(Integer, default=0, nullable=False)
    longest_streak_days = Column(Integer, default=0, nullable=False)
    total_check_ins = Column(Integer, default=0, nullable=False)
    successful_check_ins = Column(Integer, default=0, nullable=False)
    
    # Accountability style for this goal
    accountability_style = Column(String(50), default="adaptive", nullable=False)  # tactical, grace, analyst, adaptive
    
    # Mode that created/owns this goal
    created_by_mode = Column(String(50), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    check_ins = relationship("CheckIn", back_populates="goal", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="goal", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Goal {self.id} - {self.title} - {self.status}>"
    
    @property
    def completion_rate(self) -> float:
        """Calculate check-in completion rate"""
        if self.total_check_ins == 0:
            return 0.0
        return (self.successful_check_ins / self.total_check_ins) * 100.0
    
    @property
    def days_since_start(self) -> int:
        """Days since goal was started"""
        if not self.started_at:
            return 0
        delta = datetime.utcnow() - self.started_at
        return delta.days
    
    @property
    def days_until_deadline(self) -> int:
        """Days until deadline (negative if overdue)"""
        if not self.time_bound_deadline:
            return None
        delta = self.time_bound_deadline - datetime.utcnow()
        return delta.days
    
    def update_progress(self, successful: bool):
        """Update goal progress after a check-in"""
        self.total_check_ins += 1
        if successful:
            self.successful_check_ins += 1
            self.current_streak_days += 1
            if self.current_streak_days > self.longest_streak_days:
                self.longest_streak_days = self.current_streak_days
        else:
            self.current_streak_days = 0
        
        # Update status based on streak and progress
        self._update_status()
    
    def _update_status(self):
        """Update goal status based on current state"""
        if self.progress_percentage >= 100.0:
            self.status = GoalStatus.COMPLETED
            if not self.completed_at:
                self.completed_at = datetime.utcnow()
        elif self.status == GoalStatus.NOT_STARTED and self.started_at:
            self.status = GoalStatus.IN_PROGRESS
        elif self.current_streak_days == 0 and self.total_check_ins > 0:
            self.status = GoalStatus.BEHIND
        elif self.current_streak_days >= 3:
            self.status = GoalStatus.ON_TRACK
        elif self.days_until_deadline and self.days_until_deadline < 7:
            self.status = GoalStatus.AT_RISK


class CheckIn(Base):
    """
    Check-in for goal tracking
    
    Users check in on their goals periodically (daily, weekly, etc.)
    to report progress, challenges, and successes.
    """
    
    __tablename__ = "check_ins"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Check-in details
    notes = Column(Text, nullable=True)
    mood = Column(String(20), nullable=True)  # great, good, okay, bad, terrible
    energy_level = Column(Integer, nullable=True)  # 1-10
    successful = Column(Boolean, default=False, nullable=False)
    
    # Progress update
    progress_update = Column(Text, nullable=True)  # What progress was made
    obstacles_faced = Column(Text, nullable=True)  # What challenges occurred
    next_steps = Column(Text, nullable=True)  # What's the plan
    
    # Metrics
    metrics = Column(Text, nullable=True)  # JSON with custom metrics
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    goal = relationship("Goal", back_populates="check_ins")
    
    def __repr__(self):
        return f"<CheckIn {self.id} - {self.goal_id} - {self.mood}>"


class Milestone(Base):
    """
    Milestone for goal tracking
    
    Break down large goals into smaller milestones.
    """
    
    __tablename__ = "milestones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Milestone details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_value = Column(Float, nullable=True)  # Numeric target
    current_value = Column(Float, default=0.0, nullable=False)
    
    # Completion
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    target_date = Column(DateTime, nullable=True)
    
    # Order for display
    order = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    goal = relationship("Goal", back_populates="milestones")
    
    @property
    def progress_percentage(self) -> float:
        """Calculate milestone progress"""
        if not self.target_value or self.target_value == 0:
            return 0.0
        return (self.current_value / self.target_value) * 100.0
    
    def __repr__(self):
        return f"<Milestone {self.id} - {self.title} - {self.progress_percentage}%>"