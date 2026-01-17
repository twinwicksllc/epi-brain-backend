"""
Application Configuration
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "EPI Brain"
    VERSION: str = "0.1.0"
    
    # Aliases for FastAPI
    APP_NAME: str = "EPI Brain"
    APP_VERSION: str = "0.1.0"
    
    # Memory System Settings (Phase 2)
    MEMORY_ENABLED: bool = True
    MEMORY_AUTO_EXTRACTION_ENABLED: bool = True
    MEMORY_EXTRACTION_INTERVAL: int = 2  # Extract every N messages (reduced from 5)
    MEMORY_MIN_MESSAGES_FOR_EXTRACTION: int = 1  # Reduced from 3
    MEMORY_CORE_COLLECTION_ENABLED: bool = True
    MEMORY_PRIVACY_CONSENT_ENABLED: bool = True
    
    # Semantic Memory Settings (Phase 2A)
    SEMANTIC_MEMORY_ENABLED: bool = True
    SEMANTIC_MEMORY_MODEL: str = "text-embedding-3-small"  # OpenAI embedding model
    SEMANTIC_MEMORY_DIMENSION: int = 1536  # Dimension for text-embedding-3-small
    SEMANTIC_MEMORY_SIMILARITY_THRESHOLD: float = 0.75  # Minimum similarity score
    SEMANTIC_MEMORY_MAX_MEMORIES: int = 10  # Max memories to retrieve per query
    SEMANTIC_MEMORY_MIN_IMPORTANCE: int = 3  # Minimum importance score (1-10)
    SEMANTIC_MEMORY_AUTO_EXPIRE_DAYS: int = 90  # Default expiration in days
    SEMANTIC_MEMORY_CONSOLIDATE_THRESHOLD: int = 5  # Consolidate similar memories
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./epi_brain.db")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Groq AI
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    USE_GROQ: bool = True  # Use Groq by default (set to False to use Claude)
    
    # Groq Model Selection (Tier-based)
    GROQ_MODEL_FREE_DEFAULT: str = "gpt-oss-20b"
    GROQ_MODEL_PAID_DEFAULT: str = "llama-3.3-70b-versatile"
    
    # Free Tier Model Mappings
    GROQ_MODEL_MAP_FREE: dict = {
        "psychology_expert": "groq/compound-mini",
        "personal_friend": "gpt-oss-20b",
        "christian_companion": "gpt-oss-20b",
        "student_tutor": "gpt-oss-20b",
        "sales_agent": "gpt-oss-20b",
        "customer_service": "gpt-oss-20b",
        "business_mentor": "gpt-oss-20b",
        "weight_loss_coach": "gpt-oss-20b",
        "kids_learning": "llama-3.1-8b-instant",
    }
    
    # Paid Tier Model Mappings
    GROQ_MODEL_MAP_PAID: dict = {
        "psychology_expert": "llama-3.3-70b-versatile",
        "personal_friend": "llama-3.3-70b-versatile",
        "christian_companion": "llama-3.3-70b-versatile",
        "student_tutor": "llama-3.3-70b-versatile",
        "sales_agent": "llama-3.3-70b-versatile",
        "business_mentor": "llama-3.3-70b-versatile",
        "weight_loss_coach": "llama-3.3-70b-versatile",
        "customer_service": "gpt-oss-20b",
        "kids_learning": "llama-3.1-8b-instant",
    }
    
    # OpenAI (for TTS)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # ElevenLabs (optional)
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    
    # Anthropic/Claude (optional)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")  # Alias for ANTHROPIC_API_KEY
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = 4096
    
    # Stripe (optional)
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    
    # Admin API
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "")
    
    # Depth Tracking
    DEPTH_ENABLED: bool = True
    DEPTH_UP_ALPHA: float = 0.80
    DEPTH_DOWN_ALPHA: float = 0.15
    DEPTH_MIN_MESSAGE_LENGTH: int = 20
    DEPTH_LLM_THRESHOLD: float = 0.3
    DEPTH_DECAY_RATE: float = 0.002
    DEPTH_TRACKED_MODES: list = [
        "personal_friend", 
        "weight_loss_coach", 
        "christian_companion", 
        "psychology_expert", 
        "business_mentor"
    ]
    
    # Voice TTS Settings
    VOICE_ENABLED: bool = True  # Global voice feature toggle
    VOICE_TTS_ENABLED: bool = True
    VOICE_TTS_MODEL: str = "eleven_multilingual_v2"
    VOICE_TTS_FORMAT: str = "mp3"
    
    # Message Limits
    FREE_TIER_MESSAGE_LIMIT: int = 100  # Daily message limit for free tier
    
    # Voice Limits
    FREE_TIER_VOICE_LIMIT: int = 10
    VOICE_FREE_LIMIT: int = 10
    VOICE_PRO_LIMIT: int = 50  # PRO users get 50 messages per day
    VOICE_ADMIN_LIMIT: int = 999999  # Admin unlimited access
    VOICE_ALERT_THRESHOLD: float = 0.8  # Alert when 80% of limit reached
    
    # CORS Origins List
    @property
    def cors_origins_list(self) -> list:
        """Parse CORS origins into a list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()