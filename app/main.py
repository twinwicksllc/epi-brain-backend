"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text

from app.core.logger import logger

from app.config import settings
from app.database import engine, Base
from app.api import auth, chat, users, modes, admin, voice, memory
# Phase 4 imports
try:
    from app.api import thought_records, behavioral_activation, exposure_hierarchy
    PHASE_4_API_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Phase 4 API endpoints not available: {e}")
    PHASE_4_API_AVAILABLE = False

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

# Always use explicit allowed origins - no environment-dependent logic
allowed_origins = [
    "https://epibraingenius.com",
    "https://www.epibraingenius.com",
    "https://api.epibraingenius.com",
    "https://improved-broccoli-4qqj59q7gjx276p4.github.dev",  # Codespace for testing
]

# Allow CORS_ORIGINS env var to override if explicitly set
if settings.CORS_ORIGINS and settings.CORS_ORIGINS != "*":
    allowed_origins = settings.cors_origins_list
    logger.info(f"🌐 CORS: Using environment variable override: {allowed_origins}")

allow_credentials_value = True
logger.info(f"🌐 CORS Configuration:")
logger.info(f"   Environment: {settings.ENVIRONMENT}")
logger.info(f"   Production detected: {is_production}")
logger.info(f"   Allowed origins: {allowed_origins}")

# Add CORS middleware BEFORE all others - this is critical
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials_value,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)

# Add explicit CORS response middleware (runs AFTER app logic but BEFORE response sent)
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    """Add explicit CORS headers to every response"""
    origin = request.headers.get("origin")
    method = request.method
    
    # List of allowed origins
    allowed_origins_list = [
        "https://epibraingenius.com",
        "https://www.epibraingenius.com",
        "https://api.epibraingenius.com",
        "https://improved-broccoli-4qqj59q7gjx276p4.github.dev",
    ]
    
    # Log incoming request for debugging
    logger.info(f"📍 CORS Request: origin={origin}, method={method}, path={request.url.path}")
    
    # Handle preflight OPTIONS requests
    if method == "OPTIONS":
        logger.info(f"📋 OPTIONS preflight request from origin: {origin}")
        
        # For OPTIONS requests, return immediately with headers
        if origin and origin in allowed_origins_list:
            logger.info(f"✅ Allowing preflight from whitelisted origin: {origin}")
            return JSONResponse(
                content={},
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
                    "Access-Control-Allow-Headers": request.headers.get("access-control-request-headers", "*"),
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "3600",
                }
            )
        else:
            logger.warning(f"❌ Rejecting preflight from unauthorized origin: {origin}")
            return JSONResponse(
                content={"detail": "Origin not allowed"},
                status_code=403
            )
    
    # Get response from application
    response = await call_next(request)
    
    # Add CORS headers to actual response
    if origin and origin in allowed_origins_list:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        logger.debug(f"✅ Added CORS headers for {origin} on {method} {request.url.path}")
    else:
        logger.warning(f"❌ No CORS headers added for {origin} on {method} {request.url.path}")
    
    return response
    
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
app.include_router(memory.router)

# Accountability Layer routers - Phase 2B
from app.api import goals, habits, check_ins, paddle, assistant_tools
app.include_router(goals.router, prefix=f"{settings.API_V1_PREFIX}/goals", tags=["Goals"])
app.include_router(habits.router, prefix=f"{settings.API_V1_PREFIX}/habits", tags=["Habits"])
app.include_router(check_ins.router, prefix=f"{settings.API_V1_PREFIX}/check-ins", tags=["Check-ins"])

# Commercial MVP - Paddle Integration
app.include_router(paddle.router, prefix=f"{settings.API_V1_PREFIX}", tags=["Paddle"])

# Pocket EPI MVP - Assistant Tools
app.include_router(assistant_tools.router, prefix=f"{settings.API_V1_PREFIX}/assistant-tools", tags=["Assistant Tools"])

# Phase 4: CBT API endpoints
if PHASE_4_API_AVAILABLE:
    app.include_router(thought_records.router, prefix=f"{settings.API_V1_PREFIX}/thought-records", tags=["Thought Records"])
    app.include_router(behavioral_activation.router, prefix=f"{settings.API_V1_PREFIX}/behavioral-activation", tags=["Behavioral Activation"])
    app.include_router(exposure_hierarchy.router, prefix=f"{settings.API_V1_PREFIX}/exposure-hierarchy", tags=["Exposure Hierarchy"])


# Global Validation Error Handler - Exposes field-level validation errors to logs
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed logging"""
    # Log all validation errors with field names and reasons
    error_details = []
    for error in exc.errors():
        field = '.'.join(str(x) for x in error['loc'][1:]) if len(error['loc']) > 1 else str(error['loc'][0])
        error_details.append({
            'field': field,
            'type': error['type'],
            'message': error['msg'],
            'context': error.get('ctx', {})
        })
    
    logger.error(f"Validation Error Details: {error_details}")
    logger.error(f"Request path: {request.url.path}")
    logger.error(f"Request method: {request.method}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "message": "Validation failed - check logs for field names"
        }
    )


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
    
    # Start rate limiter cleanup task
    import asyncio
    from app.core.rate_limiter import clean_expired_entries
    
    async def rate_limiter_cleanup_task():
        """Periodic cleanup of expired rate limit entries"""
        while True:
            await asyncio.sleep(3600)  # Run every hour
            try:
                clean_expired_entries()
            except Exception as e:
                logger.error(f"Error in rate limiter cleanup: {e}")
    
    # Start cleanup task in background
    asyncio.create_task(rate_limiter_cleanup_task())
    logger.info("✅ Started rate limiter cleanup task")
    
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