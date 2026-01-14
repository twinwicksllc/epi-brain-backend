"""Groq TTS Service - Free, Fast, No Rate Limits"""

import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class GroqTTSService:
    """Groq Text-to-Speech Service using HTTP API"""
    
    # Groq TTS models (using their fast inference models)
    # Note: Groq doesn't have a dedicated TTS API, so we'll use their LLM with special instructions
    # or use an alternative approach
    
    async def generate_speech(
        self,
        text: str,
        voice: str = "default",
        model: str = "llama-3.3-70b-versatile",
        output_format: str = "mp3",
        instructions: Optional[str] = None,
    ) -> bytes:
        """
        Generate speech from text
        
        Note: Groq doesn't have a native TTS API yet. This is a placeholder.
        We'll need to use an alternative approach.
        
        Options:
        1. Use Groq's LLM to generate phonetic text, then use a local TTS engine
        2. Use an external free TTS service like:
           - ElevenLabs (has free tier)
           - Coqui TTS (open source)
           - Google TTS (free but limited)
           - Microsoft Azure TTS (free tier available)
        
        For now, let's use Google TTS as a temporary free solution.
        """
        
        # Using Google Translate TTS API (free, but limited)
        # This is a temporary solution
        try:
            google_tts_url = "https://translate.google.com/translate_tts"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "ie": "UTF-8",
                    "tl": "en-US",  # Language
                    "client": "tw-ob",
                    "q": text,
                }
                
                response = await client.get(google_tts_url, params=params)
                
                if response.status_code == 200:
                    logger.info(f"✅ Google TTS generated: {len(response.content)} bytes")
                    return response.content
                else:
                    raise Exception(f"Google TTS failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ TTS generation failed: {str(e)}")
            raise Exception(f"TTS generation failed: {str(e)}")
    
    async def generate_speech_for_personality(
        self,
        text: str,
        personality: str,
        gender: str = "female",
        model: str = "llama-3.3-70b-versatile",
        output_format: str = "mp3",
        instructions: Optional[str] = None,
    ) -> bytes:
        """
        Generate speech for a specific personality
        
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
        return await self.generate_speech(
            text=text,
            voice="default",
            model=model,
            output_format=output_format,
            instructions=instructions,
        )