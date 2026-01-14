"""
ElevenLabs TTS Service - Free Tier Available (10,000 chars/month)
High quality voices, generous free tier, no rate limits.
"""

import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class ElevenLabsTTSService:
    """ElevenLabs Text-to-Speech Service"""
    
    # High quality voices with ElevenLabs voice IDs
    # These are the pre-made voices available to all users
    VOICES = {
        # Main voices (User's preference)
        "FGY2WhTYpPnrIDTdsKH5": {"name": "Laura", "gender": "female", "description": "Main female voice - Warm and friendly"},
        "nPczCjzI2devNBz1zQrb": {"name": "Brian", "gender": "male", "description": "Main male voice - Natural and balanced"},
        
        # Backup female voices
        "21m00Tcm4TlvDq8ikWAM": {"name": "Rachel", "gender": "female", "description": "Warm and friendly"},
        "AZnzlk1XvdvUeBnXmlld": {"name": "Domi", "gender": "female", "description": "Energetic and engaging"},
        "EXAVITQu4vr4xnSDxMaL": {"name": "Bella", "gender": "female", "description": "Calm and soothing"},
        "XB0fDUnXU5powFXDhCwa": {"name": "Charlotte", "gender": "female", "description": "Professional and clear"},
        
        # Backup male voices
        "pNInz6obpgDQGcFmaJgB": {"name": "Adam", "gender": "male", "description": "Natural and balanced"},
        "ErXwobaYiN019PkySvjV": {"name": "Antoni", "gender": "male", "description": "Deep and authoritative"},
        "TxGEqnHWrfWFTfGW9XjX": {"name": "Josh", "gender": "male", "description": "Confident and professional"},
        "IKne3meq5aSn9XLyUdCD": {"name": "Charlie", "gender": "male", "description": "Wise and thoughtful"},
    }
    
    # Voice mappings for EPI Brain personalities (using voice IDs)
    PERSONALITY_VOICES = {
        "personal_friend": {
            "male": "nPczCjzI2devNBz1zQrb",  # Brian - Natural and friendly
            "female": "FGY2WhTYpPnrIDTdsKH5",  # Laura - Warm and engaging
        },
        "sales_agent": {
            "male": "nPczCjzI2devNBz1zQrb",  # Brian - Confident and professional
            "female": "FGY2WhTYpPnrIDTdsKH5",  # Laura - Persuasive and engaging
        },
        "student_tutor": {
            "male": "nPczCjzI2devNBz1zQrb",  # Brian - Educational and clear
            "female": "FGY2WhTYpPnrIDTdsKH5",  # Laura - Patient and supportive
        },
        "kids_learning": {
            "male": "TxGEqnHWrfWFTfGW9XjX",  # Josh - Expressive and fun
            "female": "EXAVITQu4vr4xnSDxMaL",  # Bella - Cheerful and clear
        },
        "christian_companion": {
            "male": "nPczCjzI2devNBz1zQrb",  # Brian - Wise and warm
            "female": "FGY2WhTYpPnrIDTdsKH5",  # Laura - Gentle and supportive
        },
        "customer_service": {
            "male": "nPczCjzI2devNBz1zQrb",  # Brian - Professional and helpful
            "female": "FGY2WhTYpPnrIDTdsKH5",  # Laura - Warm and professional
        },
        "psychology_expert": {
            "male": "IKne3meq5aSn9XLyUdCD",  # Charlie - Wise and thoughtful
            "female": "EXAVITQu4vr4xnSDxMaL",  # Bella - Calm and empathetic
        },
        "business_mentor": {
            "male": "ErXwobaYiN019PkySvjV",  # Antoni - Authoritative and professional
            "female": "AZnzlk1XvdvUeBnXmlld",  # Domi - Confident and engaging
        },
        "weight_loss_coach": {
            "male": "TxGEqnHWrfWFTfGW9XjX",  # Josh - Encouraging and supportive
            "female": "FGY2WhTYpPnrIDTdsKH5",  # Laura - Warm and motivating
        },
    }
    
    def __init__(self):
        """Initialize ElevenLabs TTS service"""
        self.api_key = settings.ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not configured - TTS will not work")
    
    def get_voice_for_personality(self, personality: str, gender: str = "female") -> str:
        """
        Get the appropriate ElevenLabs voice ID for a personality and gender
        
        Args:
            personality: The AI personality mode
            gender: "male" or "female"
            
        Returns:
            ElevenLabs voice ID
        """
        personality_voices = self.PERSONALITY_VOICES.get(personality, {})
        voice_id = personality_voices.get(gender, "FGY2WhTYpPnrIDTdsKH5")  # Default to Laura
        
        voice_name = self.VOICES.get(voice_id, {}).get("name", "Unknown")
        logger.info(f"Selected voice '{voice_name}' (ID: {voice_id}) for personality '{personality}' ({gender})")
        return voice_id
    
    async def generate_speech(
        self,
        text: str,
        voice: str = "FGY2WhTYpPnrIDTdsKH5",
        model: str = "eleven_multilingual_v2",
        output_format: str = "mp3_44100_128",
        instructions: Optional[str] = None,
    ) -> bytes:
        """
        Generate speech from text using ElevenLabs TTS API
        
        Args:
            text: Text to convert to speech
            voice: ElevenLabs voice to use
            model: TTS model (eleven_multilingual_v2, eleven_monolingual_v1)
            output_format: Audio format (mp3, pcm_mulaw, etc.)
            instructions: Optional instructions for voice style
            
        Returns:
            Audio data as bytes
            
        Raises:
            Exception: If TTS generation fails
        """
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not configured")
        
        if not text or len(text.strip()) == 0:
            raise ValueError("Text cannot be empty")
        
        logger.info(f"Generating TTS: {len(text)} chars, voice={voice}, model={model}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Voice parameter is already a voice ID
                voice_id = voice
                
                # Generate speech
                url = f"{self.base_url}/text-to-speech/{voice_id}"
                
                payload = {
                    "text": text.strip(),
                    "model_id": model,
                    "output_format": output_format,
                }
                
                # ElevenLabs voice settings
                voice_settings = {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                }
                
                if instructions:
                    voice_settings["style"] = instructions
                
                payload["voice_settings"] = voice_settings
                
                response = await client.post(
                    url,
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json",
                        "Accept": "audio/mpeg",
                    },
                    json=payload,
                )
                
                if response.status_code == 401:
                    raise Exception("Invalid ElevenLabs API key")
                elif response.status_code == 429:
                    raise Exception("ElevenLabs rate limit exceeded. Free tier: 10,000 chars/month")
                elif response.status_code == 400:
                    error_text = response.text
                    logger.error(f"ElevenLabs TTS API error 400: {error_text}")
                    logger.error(f"Request payload: {payload}")
                    raise Exception(f"TTS generation failed: 400 - {error_text}")
                elif response.status_code != 200:
                    error_text = response.text
                    logger.error(f"ElevenLabs TTS API error: {response.status_code} - {error_text}")
                    raise Exception(f"TTS generation failed: {response.status_code}")
                
                audio_data = response.content
                logger.info(f"TTS generated successfully: {len(audio_data)} bytes ({output_format})")
                
                return audio_data
                
        except httpx.TimeoutException:
            logger.error("ElevenLabs TTS API timeout")
            raise Exception("TTS generation timed out")
        except Exception as e:
            logger.error(f"ElevenLabs TTS API error: {str(e)}")
            raise
    
    
    
    async def generate_speech_for_personality(
        self,
        text: str,
        personality: str,
        gender: str = "female",
        model: str = "eleven_multilingual_v2",
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