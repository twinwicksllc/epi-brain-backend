"""
Deepgram Text-to-Speech (TTS) Service using WebSocket API.

Provides streaming TTS with Deepgram Aura models.
"""
import asyncio
import json
import logging
from typing import Optional
import websockets
from app.config import settings

logger = logging.getLogger(__name__)

# Voice model mappings for personality modes
VOICE_MODELS = {
    "personal_friend": {
        "male": "aura-arcas-en",
        "female": "aura-asteria-en"
    },
    "sales_agent": {
        "male": "aura-luna-en",  # Persuasive, confident
        "female": "aura-asteria-en"
    },
    "student_tutor": {
        "male": "aura-arcas-en",
        "female": "aura-asteria-en"
    },
    "kids_learning": {
        "male": "orca-v2",  # More playful
        "female": "aura-luna-en"
    },
    "christian_companion": {
        "male": "aura-orion-en",  # Deep, warm
        "female": "aura-asteria-en"
    },
    "customer_service": {
        "male": "aura-arcas-en",
        "female": "aura-luna-en"
    },
    "psychology_expert": {
        "male": "aura-orion-en",
        "female": "athena"  # Professional, calm
    },
    "business_mentor": {
        "male": "zeus",  # Deep, authoritative
        "female": "athena"
    },
    "weight_loss_coach": {
        "male": "arcas",
        "female": "luna"
    }
}


class DeepgramService:
    """Service for Deepgram TTS using WebSocket API."""
    
    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY
        # Use stable Aura-1 models for reliability
        self.base_url = "wss://api.deepgram.com/v1/speak"
        
    def get_voice_model(self, personality_mode: str, gender: str = "male") -> str:
        """Get the voice model for a given personality mode and gender."""
        if personality_mode not in VOICE_MODELS:
            logger.warning(f"Unknown personality mode: {personality_mode}, using default")
            return VOICE_MODELS["personal_friend"][gender]
        
        return VOICE_MODELS[personality_mode].get(gender, VOICE_MODELS[personality_mode]["male"])
    
    async def stream_tts(
        self,
        text: str,
        personality_mode: str = "personal_friend",
        gender: str = "male",
        sample_rate: int = 24000
    ) -> bytes:
        """
        Stream TTS audio using WebSocket API.
        
        Args:
            text: Text to convert to speech
            personality_mode: Personality mode for voice selection
            gender: Voice gender (male/female)
            sample_rate: Audio sample rate (default 24000)
            
        Returns:
            Raw audio bytes (PCM16 format)
        """
        voice_model = self.get_voice_model(personality_mode, gender)
        
        # Build WebSocket URL with parameters
        url = f"{self.base_url}?model={voice_model}&encoding=linear16&sample_rate={sample_rate}"
        
        headers = {
            "Authorization": f"Token {self.api_key}"
        }
        
        audio_buffer = []
        
        try:
            logger.info(f"Connecting to Deepgram WebSocket: {url}")
            
            async with websockets.connect(url, extra_headers=headers) as websocket:
                # Send the Speak message
                speak_message = {
                    "type": "Speak",
                    "text": text
                }
                
                logger.info(f"Sending Speak message for text: {text[:50]}...")
                await websocket.send(json.dumps(speak_message))
                
                # Wait for audio chunks
                # Set a timeout to avoid hanging forever
                timeout = 30  # 30 seconds total timeout
                
                try:
                    # Set timeout for each message
                    async for message in websocket:
                        # Check overall timeout
                        if timeout <= 0:
                            logger.warning("Timeout reached, stopping audio reception")
                            break
                        # Handle binary messages (audio data)
                        if isinstance(message, bytes):
                            audio_size = len(message)
                            audio_buffer.append(message)
                            logger.info(f"Received {audio_size} bytes of audio data (total: {sum(len(a) for a in audio_buffer)} bytes)")
                        
                        # Handle text messages (metadata, events)
                        elif isinstance(message, str):
                            try:
                                data = json.loads(message)
                                msg_type = data.get("type", "")
                                
                                if msg_type == "Metadata":
                                    logger.info(f"Received Metadata: {data}")
                                elif msg_type == "Flushed":
                                    logger.info("Received Flushed event - audio generation complete")
                                    break  # Stop receiving, audio is done
                                elif msg_type == "Warning":
                                    logger.warning(f"Deepgram warning: {data}")
                                elif msg_type == "Error":
                                    logger.error(f"Deepgram error: {data}")
                                    break
                                else:
                                    logger.info(f"Received message type: {msg_type}")
                            except json.JSONDecodeError:
                                logger.warning(f"Could not parse JSON message: {message}")
                
                except asyncio.TimeoutError:
                    logger.warning(f"WebSocket timeout after {timeout} seconds")
                
                # Don't send Close - let WebSocket context manager handle it
                logger.info(f"Audio streaming complete. Total audio bytes: {sum(len(a) for a in audio_buffer)}")
                
                # Combine all audio chunks
                if audio_buffer:
                    combined_audio = b"".join(audio_buffer)
                    logger.info(f"Combined audio size: {len(combined_audio)} bytes")
                    return combined_audio
                else:
                    logger.warning("No audio data received from Deepgram")
                    return b""
                    
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error streaming TTS: {e}")
            raise


# Singleton instance
deepgram_service = DeepgramService()