"""
Voice API endpoints for Text-to-Speech functionality.

Provides WebSocket streaming and REST endpoints for voice generation.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import verify_token
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.voice_usage import VoiceUsage
from app.services.deepgram_service import deepgram_service
from app.services.voice_tracking import VoiceUsageTracker
from app.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Voice"])

# Test endpoint to verify voice API is loaded
@router.get("/test")
async def test_voice_api():
    """Test endpoint to verify voice API is loaded."""
    return {"status": "Voice API is loaded and working", "version": "1.0.0"}
voice_tracking = VoiceUsageTracker




@router.get("/stats")
async def get_voice_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get voice usage statistics for the current user."""
    user = current_user
    
    # Get today's usage using VoiceUsageTracker
    tracker = VoiceUsageTracker(db)
    today = datetime.utcnow().date()
    daily_usage = len(tracker.get_daily_usage(user.id))
    
    # Get monthly usage (calculate manually)
    month_start = datetime(today.year, today.month, 1)
    monthly_usage = len(
        db.query(VoiceUsage).filter(
            VoiceUsage.user_id == user.id,
            VoiceUsage.date >= month_start
        ).all()
    )
    
    # Get limits
    if user.tier in ["PRO", "ENTERPRISE"]:
        daily_limit = 999999  # Unlimited
        remaining = "unlimited"
    else:
        daily_limit = 10  # FREE tier limit
        remaining = max(0, daily_limit - daily_usage)
    
    return {
        "user_id": str(user.id),
        "tier": user.tier,
        "daily_usage": daily_usage,
        "daily_limit": daily_limit,
        "remaining": max(0, daily_limit - daily_usage),
        "monthly_usage": monthly_usage,
        "unlimited": user.tier in ["PRO", "ENTERPRISE"]
    }


@router.get("/available-voices")
async def get_available_voices():
    """Get list of available voice models for all personality modes."""
    return {
        "voices": {
            "personal_friend": {
                "male": "aura-arcas-en",
                "female": "aura-asteria-en"
            },
            "sales_agent": {
                "male": "aura-luna-en",
                "female": "aura-asteria-en"
            },
            "student_tutor": {
                "male": "aura-arcas-en",
                "female": "aura-asteria-en"
            },
            "kids_learning": {
                "male": "orca-v2",
                "female": "aura-luna-en"
            },
            "christian_companion": {
                "male": "aura-orion-en",
                "female": "aura-asteria-en"
            },
            "customer_service": {
                "male": "aura-arcas-en",
                "female": "aura-luna-en"
            },
            "psychology_expert": {
                "male": "aura-orion-en",
                "female": "athena"
            },
            "business_mentor": {
                "male": "zeus",
                "female": "athena"
            },
            "weight_loss_coach": {
                "male": "arcas",
                "female": "luna"
            }
        }
    }


@router.websocket("/stream")
async def websocket_voice_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming TTS audio.
    
    Client sends: {"text": "Hello", "gender": "male", "mode": "personal_friend"}
    Server sends: Binary audio chunks (PCM16 format)
    """
    await websocket.accept()
    
    try:
        # Get token from query parameter
        token = websocket.query_params.get("token")
        if not token:
            await websocket.send_json({"error": "Missing token"})
            await websocket.close()
            return
        
        # Verify token and get user
        payload = verify_token(token)
        if not payload:
            await websocket.send_json({"error": "Invalid token"})
            await websocket.close()
            return
        
        user_id = payload.get("sub")
        
        # Receive message from client
        message = await websocket.receive_json()
        text = message.get("text", "")
        gender = message.get("gender", "male")
        mode = message.get("mode", "personal_friend")
        
        if not text:
            await websocket.send_json({"error": "No text provided"})
            await websocket.close()
            return
        
        logger.info(f"WebSocket voice request - User: {user_id}, Mode: {mode}, Gender: {gender}, Text: {text[:50]}...")
        
        # Check voice limits (skip for student_tutor - disabled)
        if mode == "student_tutor":
            logger.info("Voice disabled for student_tutor mode")
            await websocket.send_json({"error": "Voice disabled for this mode"})
            await websocket.close()
            return
        
        # Get user from database for tier checking
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                await websocket.send_json({"error": "User not found"})
                await websocket.close()
                return
            
            # Check daily limits for FREE tier
            if user.tier == "FREE":
                today = datetime.utcnow().date()
                tracker = VoiceUsageTracker(db)
                daily_usage = len(tracker.get_daily_usage(user.id))
                daily_limit = voice_tracking.get_daily_limit(user.tier)
                
                if daily_usage >= daily_limit:
                    await websocket.send_json({"error": f"Daily voice limit reached ({daily_limit} uses)"})
                    await websocket.close()
                    return
        
        finally:
            db.close()
        
        # Stream TTS audio
        try:
            logger.info(f"Starting TTS stream for: {text[:100]}...")
            audio_data = await deepgram_service.stream_tts(text, mode, gender)
            
            if audio_data:
                logger.info(f"Generated {len(audio_data)} bytes of audio, streaming to client")
                
                # Send audio data to client
                await websocket.send_bytes(audio_data)
                logger.info("Audio data sent successfully")
                
                # Track usage
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    tracker = VoiceUsageTracker(db)
                    tracker.record_usage(
                        user_id=user_id,
                        personality=mode,
                        voice_gender=gender,
                        character_count=len(text),
                        cost=len(audio_data) / 1000 * 0.03,  # $0.03 per 1000 characters
                        duration_seconds=0  # TODO: Calculate actual duration
                    )
                    db.commit()
                except Exception as e:
                    logger.error(f"Error tracking voice usage: {e}")
                    db.rollback()
                finally:
                    db.close()
            else:
                logger.error("No audio data received from Deepgram")
                await websocket.send_json({"error": "Failed to generate audio"})
        
        except Exception as e:
            logger.error(f"Error streaming TTS: {e}", exc_info=True)
            await websocket.send_json({"error": f"TTS generation failed: {str(e)}"})
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        await websocket.close()