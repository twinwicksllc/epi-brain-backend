"""
Paddle Payment Service
Handles subscription management and webhook processing
"""

from typing import Optional, Dict, Any
import hmac
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging

from app.config import settings
from app.models.user import User, PlanTier

logger = logging.getLogger(__name__)


class PaddleService:
    """Service for Paddle payment integration"""
    
    def __init__(self):
        self.webhook_secret = settings.PADDLE_WEBHOOK_SECRET
        self.vendor_id = settings.PADDLE_VENDOR_ID
        
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Verify Paddle webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Signature from Paddle
            
        Returns:
            True if signature is valid
        """
        try:
            # Paddle uses HMAC-SHA256
            computed_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(computed_signature, signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def handle_subscription_created(
        self,
        db: Session,
        webhook_data: Dict[str, Any]
    ) -> User:
        """
        Handle subscription_created webhook
        
        Args:
            db: Database session
            webhook_data: Webhook payload from Paddle
            
        Returns:
            Updated user object
        """
        try:
            # Extract data from webhook
            email = webhook_data.get('email')
            subscription_id = webhook_data.get('subscription_id')
            plan_id = webhook_data.get('subscription_plan_id')
            
            # Find user by email
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User not found: {email}"
                )
            
            # Map Paddle plan_id to our PlanTier
            plan_tier = self._map_plan_id_to_tier(plan_id)
            
            # Update user
            user.plan_tier = plan_tier
            user.paddle_subscription_id = subscription_id
            user.paddle_customer_id = webhook_data.get('customer_id')
            
            db.commit()
            db.refresh(user)
            
            logger.info(
                f"Subscription created for user {user.id}: "
                f"tier={plan_tier}, subscription_id={subscription_id}"
            )
            
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error handling subscription_created: {e}")
            raise
    
    def handle_payment_succeeded(
        self,
        db: Session,
        webhook_data: Dict[str, Any]
    ) -> User:
        """
        Handle payment_succeeded webhook
        
        Args:
            db: Database session
            webhook_data: Webhook payload from Paddle
            
        Returns:
            Updated user object
        """
        try:
            subscription_id = webhook_data.get('subscription_id')
            
            # Find user by subscription_id
            user = db.query(User).filter(
                User.paddle_subscription_id == subscription_id
            ).first()
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User not found for subscription: {subscription_id}"
                )
            
            # Reset monthly usage counters on successful payment
            user.message_count = "0"
            user.last_message_reset = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(
                f"Payment succeeded for user {user.id}: "
                f"subscription_id={subscription_id}"
            )
            
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error handling payment_succeeded: {e}")
            raise
    
    def handle_subscription_cancelled(
        self,
        db: Session,
        webhook_data: Dict[str, Any]
    ) -> User:
        """
        Handle subscription_cancelled webhook
        
        Args:
            db: Database session
            webhook_data: Webhook payload from Paddle
            
        Returns:
            Updated user object
        """
        try:
            subscription_id = webhook_data.get('subscription_id')
            
            user = db.query(User).filter(
                User.paddle_subscription_id == subscription_id
            ).first()
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User not found for subscription: {subscription_id}"
                )
            
            # Downgrade to free tier
            user.plan_tier = PlanTier.FREE
            user.paddle_subscription_id = None
            
            db.commit()
            db.refresh(user)
            
            logger.info(
                f"Subscription cancelled for user {user.id}"
            )
            
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error handling subscription_cancelled: {e}")
            raise
    
    def _map_plan_id_to_tier(self, plan_id: str) -> PlanTier:
        """
        Map Paddle plan ID to internal PlanTier
        
        Args:
            plan_id: Paddle plan ID
            
        Returns:
            PlanTier enum value
        """
        # Map your Paddle plan IDs to tiers
        plan_mapping = {
            settings.PADDLE_PLAN_ID_PREMIUM: PlanTier.PREMIUM,
            settings.PADDLE_PLAN_ID_ENTERPRISE: PlanTier.ENTERPRISE,
        }
        
        return plan_mapping.get(plan_id, PlanTier.FREE)
