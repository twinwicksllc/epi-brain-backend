"""
Voice API Endpoints - Using OpenAI TTS

Simple HTTP-based TTS using OpenAI's reliable API instead of Deepgram WebSocket.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.models.voice_usage import VoiceUsage
from app.services.voice_tracking import VoiceUsageTracker
from app.services.openai_tts_service import OpenAITTSService
from app.services.elevenlabs_tts_service import ElevenLabsTTSService
from app.services.hybrid_tts_service import HybridTTSService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
# Use ElevenLabs for high-quality voices with free tier
tts_service = ElevenLabsTTSService()


class VoiceRequest(BaseModel):
    """Request model for TTS generation"""
    text: str
    personality: str = "personal_friend"
    gender: str = "female"
    model: Optional[str] = "eleven_multilingual_v2"
    output_format: Optional[str] = "mp3"
    instructions: Optional[str] = None


class VoiceStatsResponse(BaseModel):
    """Response model for voice usage statistics"""
    user_id: str
    tier: str
    daily_usage: int
    daily_limit: Optional[int]  # None for unlimited
    remaining: Optional[Union[int, str]]  # None or "unlimited" for unlimited
    total_usage: int
    voice_model: str


@router.get("/stats")
async def get_voice_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VoiceStatsResponse:
    """
    Get voice usage statistics for current user
    
    Returns daily usage, limits, and tier information.
    """
    try:
        # Get voice usage from tracker
        tracker = VoiceUsageTracker(db)
        stats = tracker.get_user_stats(current_user.id)
        
        # Check if user is admin
        is_admin = (current_user.is_admin.lower() == "true") if current_user.is_admin else False
        
        # Get daily limit based on tier and admin status
        daily_limit = tracker.get_daily_limit(current_user.tier, is_admin)
        
        # Calculate remaining
        daily_usage = stats.get("daily_usage", 0)
        if daily_limit is None or is_admin:
            remaining = "unlimited"
        else:
            remaining = max(0, daily_limit - daily_usage)
        
        return VoiceStatsResponse(
            user_id=str(current_user.id),
            tier=current_user.tier,
            daily_usage=daily_usage,
            daily_limit=daily_limit,
            remaining=remaining,
            total_usage=stats.get("total_usage", 0),
            voice_model=settings.VOICE_TTS_MODEL,
        )
    except Exception as e:
        logger.error(f"Error getting voice stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get voice statistics")


@router.get("/available-voices")
async def get_available_voices():
    """
    Get list of available voices and their descriptions
    """
    try:
        voices = tts_service.get_available_voices()
        return {
            "voices": voices,
            "personality_mappings": tts_service.PERSONALITY_VOICES,
        }
    except Exception as e:
        logger.error(f"Error getting available voices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get available voices")


@router.post("/generate")
async def generate_voice(
    request: VoiceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate audio from text using OpenAI TTS
    
    Simple HTTP endpoint - returns audio file directly.
    No WebSocket complexity needed.
    """
    try:
        # Check if user has exceeded voice limit
        tracker = VoiceUsageTracker(db)
        await tracker.check_voice_limit(db, current_user.id)
        
        # Validate text length
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) > 4096:
            raise HTTPException(status_code=400, detail="Text too long (max 4096 characters)")
        
        # Validate gender
        if request.gender not in ["male", "female"]:
            raise HTTPException(status_code=400, detail="Gender must be 'male' or 'female'")
        
        # Validate output format
        valid_formats = ["mp3", "wav", "opus", "aac", "flac", "pcm"]
        if request.output_format not in valid_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
            )
        
        logger.info(f"Generating TTS for user {current_user.id}: {len(request.text)} chars")
        
        # Generate speech using OpenAI TTS
        audio_data = await tts_service.generate_speech_for_personality(
            text=request.text,
            personality=request.personality,
            gender=request.gender,
            model=request.model or settings.VOICE_TTS_MODEL,
            output_format=request.output_format or settings.VOICE_TTS_FORMAT,
            instructions=request.instructions,
        )
        
        # Track usage
        tracker = VoiceUsageTracker(db)
        voice_model = tts_service.get_voice_for_personality(request.personality, request.gender)
        
        # Calculate cost (OpenAI TTS: $0.015 per minute, assume 2.5 chars per second)
        estimated_duration_seconds = len(request.text) / 2.5
        estimated_duration_minutes = estimated_duration_seconds / 60
        cost = estimated_duration_minutes * 0.015
        
        tracker.record_usage(
            user_id=current_user.id,
            personality=request.personality,
            voice_gender=request.gender,
            character_count=len(request.text),
            cost=cost,
            duration_seconds=estimated_duration_seconds,
        )
        
        logger.info(f"TTS generated successfully: {len(audio_data)} bytes")
        
        # Return audio as streaming response
        media_type = f"audio/{request.output_format}"
        return StreamingResponse(
            iter([audio_data]),
            media_type=media_type,
            headers={
                "Content-Length": str(len(audio_data)),
                "Cache-Control": "no-cache",
            }
        )
        
    except ValueError as e:
        logger.error(f"Voice limit error: {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate speech: {str(e)}")


# WebSocket endpoint removed - using simple HTTP POST /generate instead
# This is much more reliable and easier to implement