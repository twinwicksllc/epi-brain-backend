"""
Usage Log Model
Track every chat message and token cost for analytics and billing
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


class UsageLog(Base):
    """Track usage for every chat message"""
    
    __tablename__ = "usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User & Account Info
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    plan_tier = Column(String(50), nullable=False, index=True)  # free, premium, enterprise
    is_enterprise_account = Column(Boolean, default=False, nullable=False, index=True)
    enterprise_account_id = Column(String(255), nullable=True, index=True)  # For tracking enterprise usage
    
    # Message Info
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), nullable=False)
    personality_mode = Column(String(50), nullable=False, index=True)  # Which AI personality
    
    # Token Accounting
    tokens_input = Column(Integer, nullable=False, default=0)  # User message tokens
    tokens_output = Column(Integer, nullable=False, default=0)  # AI response tokens
    tokens_total = Column(Integer, nullable=False, default=0)  # Total tokens
    token_cost = Column(Float, nullable=False, default=0.0)  # Cost in USD
    
    # LLM Model Info
    llm_model = Column(String(100), nullable=False, index=True)  # e.g., "llama-3.3-70b-versatile"
    llm_provider = Column(String(50), nullable=False)  # e.g., "groq", "openai"
    
    # Response Metrics
    response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds
    success = Column(Boolean, default=True, nullable=False)  # Did the request succeed?
    error_message = Column(Text, nullable=True)  # Error details if failed
    
    # Additional Context
    metadata = Column(JSON, default={}, nullable=False)  # Store extra info (e.g., features used)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return (
            f"<UsageLog user={self.user_id} mode={self.personality_mode} "
            f"tokens={self.tokens_total} cost=${self.token_cost:.6f}>"
        )
    
    @property
    def cost_per_1k_tokens(self) -> float:
        """Calculate cost per 1000 tokens"""
        if self.tokens_total == 0:
            return 0.0
        return (self.token_cost / self.tokens_total) * 1000
