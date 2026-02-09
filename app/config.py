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
    
    # ─── NEBP (Neural-Electronic Brain Pipeline) Layer Configuration ───
    # Layer 1: Neural Input (STT) — Whisper large-v3-turbo, 400 RPM
    NEBP_STT_MODEL: str = os.getenv("NEBP_STT_MODEL", "whisper-large-v3-turbo")
    NEBP_STT_RPM: int = int(os.getenv("NEBP_STT_RPM", "400"))
    
    # Layer 2: Buffer / Pre-Processing — fast stutter-clean + intent formatting
    NEBP_BUFFER_MODEL: str = os.getenv("NEBP_BUFFER_MODEL", "llama-3.1-8b-instant")
    NEBP_BUFFER_ENABLED: bool = os.getenv("NEBP_BUFFER_ENABLED", "True").lower() == "true"
    NEBP_BUFFER_MAX_TOKENS: int = int(os.getenv("NEBP_BUFFER_MAX_TOKENS", "512"))
    
    # Layer 3: Reasoning Core — primary logic model
    NEBP_REASONING_MODEL: str = os.getenv("NEBP_REASONING_MODEL", "llama-3.3-70b-versatile")
    NEBP_REASONING_FALLBACK_MODEL: str = os.getenv("NEBP_REASONING_FALLBACK_MODEL", "openai/gpt-oss-120b")
    
    # Layer 4: Safety Gateway — ultra-fast content moderation
    NEBP_SAFETY_MODEL: str = os.getenv("NEBP_SAFETY_MODEL", "llama-guard-4-12b")
    NEBP_SAFETY_ENABLED: bool = os.getenv("NEBP_SAFETY_ENABLED", "True").lower() == "true"
    
    # Groq Model Selection (Tier-based)
    # CRITICAL: OpenAI-hosted models on Groq MUST use the 'openai/' prefix
    GROQ_MODEL_FREE_DEFAULT: str = "openai/gpt-oss-120b"
    GROQ_MODEL_PAID_DEFAULT: str = "llama-3.3-70b-versatile"
    
    # Free Tier Model Mappings (openai/ prefix applied to gpt-oss models)
    GROQ_MODEL_MAP_FREE: dict = {
        "psychology_expert": "groq/compound-mini",
        "personal_friend": "openai/gpt-oss-120b",
        "christian_companion": "openai/gpt-oss-120b",
        "student_tutor": "openai/gpt-oss-120b",
        "sales_agent": "openai/gpt-oss-120b",
        "customer_service": "openai/gpt-oss-120b",
        "business_mentor": "openai/gpt-oss-120b",
        "weight_loss_coach": "openai/gpt-oss-120b",
        "kids_learning": "llama-3.1-8b-instant",
        "discovery_mode": "openai/gpt-oss-120b",
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
        "customer_service": "openai/gpt-oss-120b",
        "kids_learning": "llama-3.1-8b-instant",
        "discovery_mode": "llama-3.3-70b-versatile",
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

    # Master API Key (Mobile MVP REST endpoint)
    BOSS_API_KEY: str = os.getenv("BOSS_API_KEY", "")
    
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
    VOICE_PREMIUM_LIMIT: int = 999999  # Unlimited for premium (Commercial MVP)
    VOICE_ENTERPRISE_LIMIT: int = 999999  # Unlimited for enterprise (Commercial MVP)
    
    # Paddle Integration (Commercial MVP)
    PADDLE_VENDOR_ID: str = os.getenv("PADDLE_VENDOR_ID", "")
    PADDLE_API_KEY: str = os.getenv("PADDLE_API_KEY", "")
    PADDLE_WEBHOOK_SECRET: str = os.getenv("PADDLE_WEBHOOK_SECRET", "")
    PADDLE_PLAN_ID_PREMIUM: str = os.getenv("PADDLE_PLAN_ID_PREMIUM", "")
    PADDLE_PLAN_ID_ENTERPRISE: str = os.getenv("PADDLE_PLAN_ID_ENTERPRISE", "")
    PADDLE_ENVIRONMENT: str = os.getenv("PADDLE_ENVIRONMENT", "sandbox")
    
    # Email Configuration (Pocket EPI MVP - Internal Messaging)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "EPI Assistant")
    
    # Internal Team Email Addresses (Pocket EPI MVP)
    EMAIL_TOM: str = os.getenv("EMAIL_TOM", "")
    EMAIL_DARRICK: str = os.getenv("EMAIL_DARRICK", "")
    EMAIL_TWINWICKS: str = os.getenv("EMAIL_TWINWICKS", "")
    
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