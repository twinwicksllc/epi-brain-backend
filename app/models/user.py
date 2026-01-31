"""
User Model
"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class UserTier(str, enum.Enum):
    """User subscription tiers"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class VoicePreference(str, enum.Enum):
    """Voice preferences"""
    MALE = "male"
    FEMALE = "female"
    NONE = "none"


class User(Base):
    """User model for authentication and profile management"""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Subscription
    tier = Column(SQLEnum(UserTier), default=UserTier.FREE, nullable=False)
    stripe_customer_id = Column(String(255), unique=True, nullable=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True)
    
    # Preferences
    voice_preference = Column(SQLEnum(VoicePreference), default=VoicePreference.NONE)
    primary_mode = Column(String(50), default="personal_friend")
    
    # Usage tracking
    message_count = Column(String, default="0")  # Monthly message count
    last_message_reset = Column(DateTime, default=datetime.utcnow)
    
    # Admin flag
    is_admin = Column(String, default="false", nullable=False)  # Stored as string for SQLite compatibility
    
    # Referral system
    referral_code = Column(String(20), unique=True, nullable=True)
    referred_by = Column(UUID(as_uuid=True), nullable=True)
    referral_credits = Column(String, default="0")
    
    # Memory system
    global_memory = Column(JSON, default={}, nullable=False)  # Persistent cross-session memory
    
    # Subscription tracking
    subscribed_personalities = Column(JSON, default=["personal_friend", "discovery_mode"], nullable=False)
    
    # Accountability preferences
    accountability_style = Column(String(50), default="adaptive", nullable=False)  # tactical, grace, analyst, adaptive
    sentiment_override_enabled = Column(Boolean, default=True, nullable=False)  # Allow AI to adjust based on mood
    depth_sensitivity_enabled = Column(Boolean, default=True, nullable=False)  # Allow tone adjustment based on depth
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    thought_records = relationship("ThoughtRecord", back_populates="user", cascade="all, delete-orphan")
    behavioral_activations = relationship("BehavioralActivation", back_populates="user", cascade="all, delete-orphan")
    exposure_hierarchies = relationship("ExposureHierarchy", back_populates="user", cascade="all, delete-orphan")
    learning_patterns = relationship("LearningPattern", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def is_free_tier(self) -> bool:
        """Check if user is on free tier"""
        return self.tier == UserTier.FREE
    
    @property
    def is_pro_tier(self) -> bool:
        """Check if user is on pro tier"""
        return self.tier == UserTier.PRO
    
    @property
    def is_enterprise_tier(self) -> bool:
        """Check if user is on enterprise tier"""
        return self.tier == UserTier.ENTERPRISE
    
    @property
    def has_unlimited_messages(self) -> bool:
        """Check if user has unlimited messages"""
        return self.tier in [UserTier.PRO, UserTier.ENTERPRISE]