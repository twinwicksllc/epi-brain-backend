"""
OpenAI TTS Service - Text to Speech using OpenAI's HTTP API

Simple, reliable, and cost-effective TTS implementation using OpenAI's gpt-4o-mini-tts model.
"""

import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class OpenAITTSService:
    """OpenAI Text-to-Speech Service using HTTP API"""
    
    # Available OpenAI voices (13 total, using best 6 for personality mapping)
    VOICES = {
        # Female voices
        "coral": {"gender": "female", "description": "Warm and friendly"},
        "nova": {"gender": "female", "description": "Energetic and engaging"},
        "shimmer": {"gender": "female", "description": "Calm and soothing"},
        "fable": {"gender": "female", "description": "Storyteller style"},
        
        # Male voices  
        "alloy": {"gender": "male", "description": "Natural and balanced"},
        "echo": {"gender": "male", "description": "Deep and authoritative"},
        "onyx": {"gender": "male", "description": "Confident and professional"},
        "sage": {"gender": "male", "description": "Wise and thoughtful"},
        
        # High quality voices (recommended)
        "marin": {"gender": "female", "description": "Highest quality female"},
        "cedar": {"gender": "male", "description": "Highest quality male"},
        
        # Additional voices
        "ash": {"gender": "male", "description": "Soft and gentle"},
        "ballad": {"gender": "male", "description": "Melodic and expressive"},
        "verse": {"gender": "female", "description": "Poetic and articulate"},
    }
    
    # Voice mappings for EPI Brain personalities
    PERSONALITY_VOICES = {
        "personal_friend": {
            "male": "alloy",  # Natural and friendly
            "female": "coral",  # Warm and engaging
        },
        "sales_agent": {
            "male": "echo",  # Authoritative and confident
            "female": "nova",  # Energetic and persuasive
        },
        "student_tutor": {
            "male": "sage",  # Wise and educational
            "female": "shimmer",  # Calm and patient
        },
        "kids_learning": {
            "male": "ballad",  # Expressive and fun
            "female": "fable",  # Storyteller style
        },
        "christian_companion": {
            "male": "cedar",  # Highest quality, warm
            "female": "marin",  # Highest quality, gentle
        },
        "customer_service": {
            "male": "alloy",  # Natural and balanced
            "female": "coral",  # Warm and professional
        },
        "psychology_expert": {
            "male": "sage",  # Wise and thoughtful
            "female": "shimmer",  # Calm and empathetic
        },
        "business_mentor": {
            "male": "echo",  # Authoritative and professional
            "female": "nova",  # Confident and engaging
        },
        "weight_loss_coach": {
            "male": "ash",  # Gentle and encouraging
            "female": "coral",  # Warm and supportive
        },
    }
    
    def __init__(self):
        """Initialize OpenAI TTS service"""
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not configured - TTS will not work")
    
    def get_voice_for_personality(self, personality: str, gender: str = "female") -> str:
        """
        Get the appropriate OpenAI voice for a personality and gender
        
        Args:
            personality: The AI personality mode
            gender: "male" or "female"
            
        Returns:
            OpenAI voice name
        """
        personality_voices = self.PERSONALITY_VOICES.get(personality, {})
        voice = personality_voices.get(gender, "coral")  # Default to coral
        
        logger.info(f"Selected voice '{voice}' for personality '{personality}' ({gender})")
        return voice
    
    async def generate_speech(
        self,
        text: str,
        voice: str = "coral",
        model: str = "gpt-4o-mini-tts",
        output_format: str = "mp3",
        instructions: Optional[str] = None,
    ) -> bytes:
        """
        Generate speech from text using OpenAI's TTS API
        
        Args:
            text: Text to convert to speech
            voice: OpenAI voice to use
            model: TTS model (gpt-4o-mini-tts, tts-1, tts-1-hd)
            output_format: Audio format (mp3, wav, opus, aac, flac, pcm)
            instructions: Optional instructions for voice style
            
        Returns:
            Audio data as bytes
            
        Raises:
            Exception: If TTS generation fails
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        if not text or len(text.strip()) == 0:
            raise ValueError("Text cannot be empty")
        
        # Build request payload
        payload = {
            "model": model,
            "voice": voice,
            "input": text.strip(),
            "response_format": output_format,
        }
        
        if instructions:
            payload["instructions"] = instructions
        
        logger.info(f"Generating TTS: {len(text)} chars, voice={voice}, model={model}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/audio/speech",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"OpenAI TTS API error: {response.status_code} - {error_text}")
                    raise Exception(f"TTS generation failed: {response.status_code}")
                
                audio_data = response.content
                logger.info(f"TTS generated successfully: {len(audio_data)} bytes ({output_format})")
                
                return audio_data
                
        except httpx.TimeoutException:
            logger.error("OpenAI TTS API timeout")
            raise Exception("TTS generation timed out")
        except Exception as e:
            logger.error(f"OpenAI TTS API error: {str(e)}")
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
        voice = self.get_voice_for_personality(personality, gender)
        return await self.generate_speech(
            text=text,
            voice=voice,
            model=model,
            output_format=output_format,
            instructions=instructions,
        )
    
    def get_available_voices(self) -> dict:
        """
        Get information about all available voices
        
        Returns:
            Dictionary of voice information
        """
        return self.VOICES
    
    def get_voice_info(self, voice: str) -> dict:
        """
        Get information about a specific voice
        
        Args:
            voice: Voice name
            
        Returns:
            Voice information dictionary
        """
        return self.VOICES.get(voice, {"gender": "unknown", "description": "Unknown voice"})