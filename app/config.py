"""
Application Configuration
Manages environment variables and application settings
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "EPI Brain API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = ""
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0
    
    # Redis
    REDIS_URL: str = ""
    REDIS_MAX_CONNECTIONS: int = 50
    
    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AI Provider Selection
    USE_GROQ: bool = True  # Set to False to use Claude instead
    
    # Groq API (FREE for MVP)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # or "llama-3.1-8b-instant" for faster responses
    
    # Claude API (for production)
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = 4096
    
    # ElevenLabs
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID_MALE: Optional[str] = None
    ELEVENLABS_VOICE_ID_FEMALE: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: Optional[str] = None
    STRIPE_PRICE_ID_ENTERPRISE: Optional[str] = None
    
    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # SendGrid
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: Optional[str] = None
    
    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: str = "https://epibraingenius.com,https://www.epibraingenius.com"  # Production CORS origins
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    DATADOG_API_KEY: Optional[str] = None
    
    # Feature Flags
    ENABLE_VOICE_FEATURES: bool = True
    ENABLE_NEURAL_LEARNING: bool = True
    ENABLE_REFERRAL_SYSTEM: bool = True
    
    # Tier Limits
    FREE_TIER_MESSAGE_LIMIT: int = 9999  # Increased for development
    FREE_TIER_HISTORY_DAYS: int = 7
    PRO_TIER_PRICE: float = 19.99
    ENTERPRISE_TIER_MIN_USERS: int = 100
    
    # Depth Feature Configuration
    DEPTH_ENABLED: bool = True
    DEPTH_TRACKED_MODES: list = [
        "personal_friend",
        "weight_loss_coach",
        "christian_companion",
        "psychology_expert",
        "business_mentor"
    ]
    
    # Depth Engine Parameters
    DEPTH_UP_ALPHA: float = 0.80      # Speed going deeper
    DEPTH_DOWN_ALPHA: float = 0.15    # Speed coming back up
    DEPTH_DECAY_RATE: float = 0.002   # Per second decay
    
    # Scoring Parameters
    DEPTH_LLM_THRESHOLD: float = 0.6  # When to use LLM
    DEPTH_MIN_MESSAGE_LENGTH: int = 20  # Ignore very short messages
    DEPTH_RAPID_MESSAGE_WINDOW: int = 5  # Seconds to batch rapid messages
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Uses lru_cache to avoid reading .env file multiple times
    """
    return Settings()


# Global settings instance
settings = get_settings()