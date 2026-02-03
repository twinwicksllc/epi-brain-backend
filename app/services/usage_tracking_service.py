"""
Usage Tracking Service
Track token usage and costs for every chat message
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

from app.models.usage_log import UsageLog
from app.models.user import User

logger = logging.getLogger(__name__)


class UsageTrackingService:
    """Service for tracking and analyzing usage"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_message_usage(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
        personality_mode: str,
        tokens_input: int,
        tokens_output: int,
        llm_model: str,
        llm_provider: str = "groq",
        response_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
            chat_metadata: Optional[Dict[str, Any]] = None
        ) -> UsageLog:
        """
        Log a chat message usage event
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            message_id: Message ID
            personality_mode: AI personality used
            tokens_input: Input tokens (user message)
            tokens_output: Output tokens (AI response)
            llm_model: Model used
            llm_provider: Provider (groq, openai, etc.)
            response_time_ms: Response time in ms
            success: Whether request succeeded
            error_message: Error details if failed
            chat_metadata: Additional context
            Created UsageLog entry
        """
        try:
            # Get user info
            user = self.db.query(User).filter(User.id == user_id).first()
            plan_tier = user.plan_tier.value if user else "free"
            
            # Calculate total tokens and cost
            tokens_total = tokens_input + tokens_output
            token_cost = self._calculate_token_cost(
                tokens_input, tokens_output, llm_model, llm_provider
            )
            
            # Create usage log
            usage_log = UsageLog(
                user_id=user_id,
                plan_tier=plan_tier,
                is_enterprise_account=user.is_enterprise_plan if user else False,
                enterprise_account_id=getattr(user, 'enterprise_account_id', None) if user else None,
                conversation_id=conversation_id,
                message_id=message_id,
                personality_mode=personality_mode,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_total=tokens_total,
                token_cost=token_cost,
                llm_model=llm_model,
                llm_provider=llm_provider,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                chat_metadata=chat_metadata or {}
            )
            
            self.db.add(usage_log)
            self.db.commit()
            self.db.refresh(usage_log)
            
            logger.info(
                f"Logged usage for user {user_id}: "
                f"{tokens_total} tokens, ${token_cost:.6f}"
            )
            
            return usage_log
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error logging usage: {e}", exc_info=True)
            raise
    
    def _calculate_token_cost(
        self,
        tokens_input: int,
        tokens_output: int,
        model: str,
        provider: str
    ) -> float:
        """
        Calculate cost based on token usage and model
        
        Args:
            tokens_input: Input tokens
            tokens_output: Output tokens
            model: Model name
            provider: Provider name
            
        Returns:
            Cost in USD
        """
        # Groq pricing (as of 2024)
        groq_pricing = {
            "llama-3.3-70b-versatile": {
                "input": 0.00059,  # per 1K tokens
                "output": 0.00079
            },
            "gpt-oss-20b": {
                "input": 0.00025,
                "output": 0.00025
            },
            "llama-3.1-8b-instant": {
                "input": 0.00005,
                "output": 0.00008
            },
        }
        
        # OpenAI pricing
        openai_pricing = {
            "gpt-4": {
                "input": 0.03,
                "output": 0.06
            },
            "gpt-3.5-turbo": {
                "input": 0.0015,
                "output": 0.002
            },
        }
        
        if provider == "groq":
            pricing = groq_pricing.get(model, {"input": 0.0001, "output": 0.0001})
        elif provider == "openai":
            pricing = openai_pricing.get(model, {"input": 0.001, "output": 0.001})
        else:
            pricing = {"input": 0.0001, "output": 0.0001}
        
        # Calculate cost
        input_cost = (tokens_input / 1000) * pricing["input"]
        output_cost = (tokens_output / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def get_user_usage_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage summary for a user
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Usage summary with tokens, cost, and breakdowns
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query usage logs
        logs = self.db.query(UsageLog).filter(
            UsageLog.user_id == user_id,
            UsageLog.created_at >= start_date
        ).all()
        
        # Calculate totals
        total_tokens = sum(log.tokens_total for log in logs)
        total_cost = sum(log.token_cost for log in logs)
        total_messages = len(logs)
        
        # Breakdown by personality
        personality_breakdown = {}
        for log in logs:
            mode = log.personality_mode
            if mode not in personality_breakdown:
                personality_breakdown[mode] = {
                    "tokens": 0,
                    "cost": 0.0,
                    "messages": 0
                }
            personality_breakdown[mode]["tokens"] += log.tokens_total
            personality_breakdown[mode]["cost"] += log.token_cost
            personality_breakdown[mode]["messages"] += 1
        
        # Breakdown by model
        model_breakdown = {}
        for log in logs:
            model = log.llm_model
            if model not in model_breakdown:
                model_breakdown[model] = {
                    "tokens": 0,
                    "cost": 0.0,
                    "messages": 0
                }
            model_breakdown[model]["tokens"] += log.tokens_total
            model_breakdown[model]["cost"] += log.token_cost
            model_breakdown[model]["messages"] += 1
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 6),
            "avg_tokens_per_message": round(total_tokens / total_messages, 2) if total_messages > 0 else 0,
            "avg_cost_per_message": round(total_cost / total_messages, 6) if total_messages > 0 else 0,
            "personality_breakdown": personality_breakdown,
            "model_breakdown": model_breakdown
        }
    
    def get_enterprise_usage_summary(
        self,
        enterprise_account_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage summary for an enterprise account
        
        Args:
            enterprise_account_id: Enterprise account ID
            days: Number of days to analyze
            
        Returns:
            Enterprise usage summary
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        logs = self.db.query(UsageLog).filter(
            UsageLog.enterprise_account_id == enterprise_account_id,
            UsageLog.created_at >= start_date
        ).all()
        
        # Get unique users
        unique_users = set(log.user_id for log in logs)
        
        # Calculate totals
        total_tokens = sum(log.tokens_total for log in logs)
        total_cost = sum(log.token_cost for log in logs)
        total_messages = len(logs)
        
        return {
            "enterprise_account_id": enterprise_account_id,
            "period_days": days,
            "unique_users": len(unique_users),
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 2),
            "avg_tokens_per_user": round(total_tokens / len(unique_users), 2) if unique_users else 0,
            "avg_cost_per_user": round(total_cost / len(unique_users), 2) if unique_users else 0
        }
