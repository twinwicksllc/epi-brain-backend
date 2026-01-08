"""
Deepgram TTS Service
Handles text-to-speech conversion using Deepgram Aura-2 model
"""

import asyncio
import json
from typing import Optional, AsyncGenerator
import websockets
from datetime import datetime

from app.config import settings
from app.models.voice_usage import VoiceUsage
from app.database import get_db
from sqlalchemy.orm import Session


class DeepgramVoiceModel:
    """Voice model mapping for personalities and gender preferences"""
    
    # Female voices (based on Deepgram Aura-2 recommendations)
    FEMALE_VOICES = {
        "personal_friend": "aura-2-helena-en",      # Caring, natural, friendly - perfect for emotional support
        "sales_agent": "aura-2-thalia-en",         # Clear, confident, energetic - ideal for sales
        "christian_companion": "aura-2-helena-en",  # Caring, natural - supportive spiritual guidance
        "psychology_expert": "aura-2-helena-en",   # Caring, natural, friendly - therapeutic empathy
        "business_mentor": "aura-2-athena-en",     # Calm, smooth, professional - business authority
        "weight_loss_coach": "aura-2-thalia-en",   # Clear, confident, energetic - motivational coaching
        "kids_learning": "aura-2-thalia-en",       # Clear, confident, energetic - engaging for children
        "customer_service": "aura-2-thalia-en",    # Clear, confident, energetic - efficient problem-solving
    }
    
    # Male voices (based on Deepgram Aura-2 recommendations)
    MALE_VOICES = {
        "personal_friend": "aura-2-arcas-en",      # Natural, smooth, clear - comfortable conversation
        "sales_agent": "aura-2-arcas-en",         # Natural, smooth, clear - professional sales
        "christian_companion": "aura-2-aries-en", # Warm, energetic, caring - supportive guidance
        "psychology_expert": "aura-2-arcas-en",   # Natural, smooth - therapeutic presence
        "business_mentor": "aura-2-zeus-en",      # Deep, trustworthy, smooth - authority and experience
        "weight_loss_coach": "aura-2-aries-en",   # Warm, energetic, caring - motivational support
        "kids_learning": "aura-2-aries-en",       # Warm, energetic - engaging for children
        "customer_service": "aura-2-arcas-en",    # Natural, smooth, clear - professional support
    }
    
    @classmethod
    def get_voice_model(cls, personality: str, gender: str = "female") -> str:
        """Get the appropriate voice model for personality and gender"""
        gender = gender.lower() if gender else "female"
        
        if gender == "male":
            return cls.MALE_VOICES.get(personality, cls.MALE_VOICES["personal_friend"])
        else:
            return cls.FEMALE_VOICES.get(personality, cls.FEMALE_VOICES["personal_friend"])
    
    @classmethod
    def get_available_personalities(cls) -> list:
        """Get list of personalities that support voice"""
        return list(cls.FEMALE_VOICES.keys())


class DeepgramTTS:
    """Deepgram Text-to-Speech service"""
    
    # Personalities with voice disabled
    VOICE_DISABLED_PERSONALITIES = [
        "student_tutor",  # Text-only as per requirements
    ]
    
    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY
        self.model = settings.DEEPGRAM_MODEL
        self.encoding = settings.DEEPGRAM_ENCODING
        self.sample_rate = settings.DEEPGRAM_SAMPLE_RATE
        self.cost_per_char = settings.VOICE_COST_PER_CHAR
        
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not configured in environment variables")
    
    def is_voice_enabled(self, personality: str) -> bool:
        """Check if voice is enabled for a personality"""
        return personality not in self.VOICE_DISABLED_PERSONALITIES
    
    def get_voice_model(self, personality: str, gender: str = "female") -> str:
        """Get voice model for personality and gender"""
        return DeepgramVoiceModel.get_voice_model(personality, gender)
    
    async def stream_tts(
        self,
        text: str,
        personality: str,
        gender: str = "female",
        user_id: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream TTS audio from Deepgram via WebSocket
        
        Args:
            text: Text to convert to speech
            personality: Personality mode
            gender: Voice gender preference ('male' or 'female')
            user_id: User ID for usage tracking
            
        Yields:
            Audio chunks as bytes
        """
        voice_model = self.get_voice_model(personality, gender)
        
        # Calculate cost
        character_count = len(text)
        cost = character_count * self.cost_per_char
        
        # WebSocket URL for Deepgram TTS
        url = f"wss://api.deepgram.com/v1/speak?model={voice_model}&encoding={self.encoding}&sample_rate={self.sample_rate}"
        
        # Create WebSocket connection
        extra_headers = {
            "Authorization": f"Token {self.api_key}"
        }
        
        async with websockets.connect(url, extra_headers=extra_headers) as websocket:
            # Send text for synthesis
            message = {
                "type": "Speak",
                "text": text
            }
            await websocket.send(json.dumps(message))
            
            # Send Flush to trigger audio generation
            await websocket.send(json.dumps({"type": "Flush"}))
            
            # Receive audio chunks
            total_bytes = 0
            while True:
                try:
                    message = await websocket.recv()
                    
                    if isinstance(message, bytes):
                        # Audio data
                        total_bytes += len(message)
                        yield message
                    
                    elif isinstance(message, str):
                        # Metadata or control message
                        data = json.loads(message)
                        
                        if data.get("type") == "SpeakStarted":
                            continue
                        
                        elif data.get("type") == "SpeakEnd":
                            # Stream complete
                            break
                        
                        elif data.get("type") == "Metadata":
                            # Extract duration if available
                            metadata = data.get("metadata", {})
                            duration = metadata.get("duration_seconds", 0)
                            
                            # Track usage
                            if user_id:
                                await self._track_usage(
                                    user_id=user_id,
                                    personality=personality,
                                    voice_gender=gender,
                                    character_count=character_count,
                                    cost=cost,
                                    duration_seconds=duration
                                )
                            break
                        
                except websockets.exceptions.ConnectionClosed:
                    break
            
            # Send Close message
            await websocket.send(json.dumps({"type": "Close"}))
    
    async def _track_usage(
        self,
        user_id: str,
        personality: str,
        voice_gender: str,
        character_count: int,
        cost: float,
        duration_seconds: float
    ):
        """Track TTS usage in database"""
        try:
            db = next(get_db())
            
            voice_usage = VoiceUsage(
                user_id=user_id,
                personality_mode=personality,
                voice_gender=voice_gender,
                character_count=character_count,
                cost=cost,
                duration_seconds=duration_seconds,
                date=datetime.utcnow()
            )
            
            db.add(voice_usage)
            db.commit()
            
        except Exception as e:
            # Log error but don't break TTS stream
            print(f"Error tracking voice usage: {e}")
        finally:
            db.close()
    
    def calculate_daily_cost(self, usage_records: list[VoiceUsage]) -> float:
        """Calculate total cost from usage records"""
        return sum(record.cost for record in usage_records)
    
    def get_daily_character_count(self, usage_records: list[VoiceUsage]) -> int:
        """Get total character count from usage records"""
        return sum(record.character_count for record in usage_records)


# Singleton instance
deepgram_tts = DeepgramTTS()