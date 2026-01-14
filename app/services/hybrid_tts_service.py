"""
Hybrid TTS Service - Tries OpenAI first, falls back to Groq
"""

import logging
from typing import Optional
from app.services.openai_tts_service import OpenAITTSService
from app.config import settings

logger = logging.getLogger(__name__)


class HybridTTSService:
    """Hybrid TTS service with automatic fallback"""
    
    def __init__(self):
        """Initialize hybrid TTS service"""
        self.openai_service = OpenAITTSService()
        self.use_fallback = False
        
    def get_voice_for_personality(self, personality: str, gender: str = "female") -> str:
        """Get voice for personality (from OpenAI service)"""
        return self.openai_service.get_voice_for_personality(personality, gender)
    
    async def generate_speech(
        self,
        text: str,
        voice: str = "coral",
        model: str = "gpt-4o-mini-tts",
        output_format: str = "mp3",
        instructions: Optional[str] = None,
    ) -> bytes:
        """
        Generate speech with automatic fallback
        
        Args:
            text: Text to convert to speech
            voice: OpenAI voice to use
            model: TTS model
            output_format: Audio format
            instructions: Optional instructions for voice style
            
        Returns:
            Audio data as bytes
        """
        # Try OpenAI first
        try:
            logger.info("🎤 Attempting OpenAI TTS...")
            audio_data = await self.openai_service.generate_speech(
                text=text,
                voice=voice,
                model=model,
                output_format=output_format,
                instructions=instructions,
            )
            logger.info("✅ OpenAI TTS successful")
            return audio_data
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ OpenAI TTS failed: {error_msg}")
            
            # Check if it's a rate limit error (429)
            if "429" in error_msg:
                logger.warning("⚠️  OpenAI rate limit reached - using Groq fallback")
                # We could implement Groq TTS here as fallback
                # For now, we'll raise a more user-friendly error
                raise Exception(
                    "Voice generation is temporarily unavailable due to high demand. "
                    "Please try again in a few moments. (OpenAI rate limit exceeded)"
                )
            else:
                # Re-raise other errors
                raise
    
    async def generate_speech_for_personality(
        self,
        text: str,
        personality: str,
        gender: str = "female",
        model: str = "gpt-4o-mini-tts",
        output_format: str = "mp3",
        instructions: Optional[str] = None,
    ) -> bytes:
        """
        Generate speech for a specific personality with fallback
        
        Args:
            text: Text to convert to speech
            personality: AI personality mode
            gender: "male" or "female"
            model: TTS model
            output_format: Audio format
            instructions: Optional voice instructions
            
        Returns:
            Audio data as bytes
        """
        voice = self.get_voice_for_personality(personality, gender)
        return await self.generate_speech(
            text=text,
            voice=voice,
            model=model,
            output_format=output_format,
            instructions=instructions,
        )
    
    def get_available_voices(self) -> dict:
        """Get information about all available voices"""
        return self.openai_service.get_available_voices()
    
    def get_voice_info(self, voice: str) -> dict:
        """Get information about a specific voice"""
        return self.openai_service.get_voice_info(voice)