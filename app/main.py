"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import logging

from app.config import settings
from app.database import engine, Base
from app.api import auth, chat, users, modes, admin, voice

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="EPI Brain - AI-powered conversational platform with 9 distinct personality modes",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS based on environment
# Check if we're in production (Render environment or explicitly set)
is_production = (
    settings.ENVIRONMENT == "production" or 
    "RENDER" in str(settings.ENVIRONMENT).upper() or
    "render" in str(settings.DATABASE_URL).lower()
)

if is_production:
    # Production: Only allow specific frontend domains
    allowed_origins = [
        "https://epibraingenius.com",
        "https://www.epibraingenius.com",
    ]
    # Explicitly allow common headers including Authorization
    allowed_headers = [
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "Origin",
        "Referer",
        "User-Agent",
    ]
    print(f"🌐 CORS: Production mode detected - allowing origins: {allowed_origins}")
else:
    # Development: Allow all origins for testing
    allowed_origins = ["*"]
    print(f"🔧 CORS: Development mode - allowing all origins")
    allowed_headers = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=allowed_headers,
    expose_headers=["*"],
)

# Add debug middleware to check CORS headers
@app.middleware("http")
async def debug_cors(request: Request, call_next):
    response = await call_next(request)
    
    # Add debug headers
    response.headers["X-Debug-CORS-Origin"] = str(request.headers.get("origin"))
    response.headers["X-Debug-CORS-Method"] = str(request.headers.get("access-control-request-method"))
    response.headers["X-Debug-Environment"] = str(settings.ENVIRONMENT)
    
    return response


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to EPI Brain API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "operational"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION
    }


# Include API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(chat.router, prefix=f"{settings.API_V1_PREFIX}/chat", tags=["Chat"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
app.include_router(modes.router, prefix=f"{settings.API_V1_PREFIX}/modes", tags=["Modes"])
app.include_router(admin.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["Admin"])
app.include_router(voice.router, prefix=f"{settings.API_V1_PREFIX}/voice")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Run database migrations
    try:
        with engine.connect() as conn:
            # Check if is_admin column exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'is_admin'
            """))
            column_exists = result.fetchone()[0] > 0
            
            if not column_exists:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN is_admin VARCHAR(10) NOT NULL DEFAULT 'false'
                """))
                conn.commit()
                logger.info("✅ Migration completed: Added is_admin column")
            else:
                logger.info("ℹ️  is_admin column already exists")
    except Exception as e:
        logger.warning(f"⚠️  Migration error: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info(f"Shutting down {settings.APP_NAME}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )