"""
Voice API Endpoints
WebSocket and REST endpoints for text-to-speech functionality
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.database import get_db
from app.services.deepgram_service import deepgram_tts, DeepgramVoiceModel
from app.services.voice_tracking import VoiceUsageTracker
from app.models.user import User
from app.core.security import get_current_user_from_token

router = APIRouter()


@router.websocket("/stream")
async def voice_stream(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for streaming TTS audio
    
    Client should send messages with format:
    {
        "type": "speak",
        "text": "text to speak",
        "personality": "personal_friend",
        "gender": "female"
    }
    """
    await websocket.accept()
    
    try:
        # Authenticate user from token
        if not token:
            await websocket.send_json({
                "type": "error",
                "message": "Authentication token required"
            })
            await websocket.close()
            return
        
        db = next(get_db())
        
        try:
            user = get_current_user_from_token(token, db)
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": f"Authentication failed: {str(e)}"
            })
            await websocket.close()
            return
        
        # Initialize usage tracker
        tracker = VoiceUsageTracker(db)
        
        # Check voice limits
        can_use, reason = tracker.can_use_voice(str(user.id), user.tier)
        
        if not can_use:
            await websocket.send_json({
                "type": "error",
                "message": reason,
                "error_code": "limit_exceeded"
            })
            await websocket.close()
            return
        
        await websocket.send_json({
            "type": "connected",
            "message": "Voice stream connected",
            "user_id": str(user.id),
            "tier": user.tier,
            "voice_preference": user.voice_preference.value if user.voice_preference else "female"
        })
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "speak":
                text = message.get("text", "")
                personality = message.get("personality", "personal_friend")
                gender = message.get("gender", user.voice_preference.value if user.voice_preference else "female")
                
                # Validate personality
                if personality not in DeepgramVoiceModel.get_available_personalities():
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Invalid personality: {personality}"
                    })
                    continue
                
                # Check if voice is enabled for personality
                if not deepgram_tts.is_voice_enabled(personality):
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Voice not enabled for {personality}",
                        "error_code": "voice_disabled"
                    })
                    continue
                
                # Get voice model
                voice_model = deepgram_tts.get_voice_model(personality, gender)
                
                await websocket.send_json({
                    "type": "speak_start",
                    "voice_model": voice_model,
                    "personality": personality,
                    "gender": gender
                })
                
                # Stream TTS audio
                try:
                    async for audio_chunk in deepgram_tts.stream_tts(
                        text=text,
                        personality=personality,
                        gender=gender,
                        user_id=str(user.id)
                    ):
                        # Send audio chunk to client
                        await websocket.send_bytes(audio_chunk)
                    
                    await websocket.send_json({
                        "type": "speak_complete",
                        "message": "Audio generation complete"
                    })
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"TTS error: {str(e)}"
                    })
            
            elif message.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong"
                })
            
            elif message.get("type") == "close":
                await websocket.send_json({
                    "type": "closing",
                    "message": "Closing connection"
                })
                break
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: user_id={user.id if 'user' in locals() else 'unknown'}")
    
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Server error: {str(e)}"
            })
        except:
            pass
    
    finally:
        if 'db' in locals():
            db.close()


@router.get("/stats")
async def get_voice_stats(
    token: str,
    db: Session = Depends(get_db)
):
    """Get voice usage statistics for current user"""
    try:
        user = get_current_user_from_token(token, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    
    tracker = VoiceUsageTracker(db)
    stats = tracker.get_user_stats(str(user.id))
    
    return {
        "status": "success",
        "data": stats
    }


@router.get("/available-voices")
async def get_available_voices():
    """Get list of available voices for each personality"""
    return {
        "status": "success",
        "data": {
            "female_voices": DeepgramVoiceModel.FEMALE_VOICES,
            "male_voices": DeepgramVoiceModel.MALE_VOICES,
            "disabled_personalities": deepgram_tts.VOICE_DISABLED_PERSONALITIES
        }
    }


@router.get("/can-use-voice")
async def check_voice_access(
    token: str,
    db: Session = Depends(get_db)
):
    """Check if user can use voice feature"""
    try:
        user = get_current_user_from_token(token, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    
    tracker = VoiceUsageTracker(db)
    can_use, reason = tracker.can_use_voice(str(user.id), user.tier)
    
    return {
        "status": "success",
        "data": {
            "can_use_voice": can_use,
            "reason": reason,
            "tier": user.tier,
            "voice_preference": user.voice_preference.value if user.voice_preference else "none"
        }
    }