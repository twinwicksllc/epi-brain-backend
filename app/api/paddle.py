"""
Paddle Webhook Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.services.paddle_service import PaddleService

logger = logging.getLogger(__name__)
router = APIRouter()
paddle_service = PaddleService()


@router.post("/webhooks/paddle")
async def paddle_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Paddle webhooks
    
    Handles:
    - subscription_created
    - subscription_payment_succeeded
    - subscription_cancelled
    - subscription_updated
    """
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get('x-paddle-signature')
        
        if not signature:
            raise HTTPException(
                status_code=400,
                detail="Missing webhook signature"
            )
        
        # Verify signature
        if not paddle_service.verify_webhook_signature(body, signature):
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )
        
        # Parse webhook data
        webhook_data = await request.json()
        event_type = webhook_data.get('alert_name')
        
        logger.info(f"Received Paddle webhook: {event_type}")
        
        # Handle different webhook types
        if event_type == 'subscription_created':
            user = paddle_service.handle_subscription_created(db, webhook_data)
            return {
                "status": "success",
                "message": "Subscription created",
                "user_id": str(user.id)
            }
        
        elif event_type == 'subscription_payment_succeeded':
            user = paddle_service.handle_payment_succeeded(db, webhook_data)
            return {
                "status": "success",
                "message": "Payment processed",
                "user_id": str(user.id)
            }
        
        elif event_type == 'subscription_cancelled':
            user = paddle_service.handle_subscription_cancelled(db, webhook_data)
            return {
                "status": "success",
                "message": "Subscription cancelled",
                "user_id": str(user.id)
            }
        
        elif event_type == 'subscription_updated':
            # Handle plan changes
            user = paddle_service.handle_subscription_created(db, webhook_data)
            return {
                "status": "success",
                "message": "Subscription updated",
                "user_id": str(user.id)
            }
        
        else:
            logger.warning(f"Unhandled webhook type: {event_type}")
            return {
                "status": "ignored",
                "message": f"Webhook type not handled: {event_type}"
            }
        
    except Exception as e:
        logger.error(f"Error processing Paddle webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing webhook: {str(e)}"
        )
