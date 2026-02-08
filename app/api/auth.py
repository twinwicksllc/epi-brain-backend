"""
Authentication API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_referral_code
)
from app.core.exceptions import InvalidCredentials, UserAlreadyExists

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user object
        
    Raises:
        UserAlreadyExists: If user with email already exists
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    
    if existing_user:
        raise UserAlreadyExists()
    
    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        full_name=user_data.full_name,
        voice_preference=user_data.voice_preference,
        silo_id=user_data.silo_id,
    )
    
    # Generate referral code
    db.add(new_user)
    db.flush()  # Flush to get the user ID
    
    new_user.referral_code = generate_referral_code(new_user.id)
    
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return JWT tokens
    
    Args:
        credentials: User login credentials
        db: Database session
        
    Returns:
        Access and refresh tokens
        
    Raises:
        InvalidCredentials: If email or password is incorrect
    """
    try:
        logger.info(f"🔐 Login attempt for email: {credentials.email}")
        
        # Get user by email
        user = db.query(User).filter(User.email == credentials.email).first()
        
        if not user:
            logger.warning(f"❌ Login failed - user not found: {credentials.email}")
            raise InvalidCredentials()
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            logger.warning(f"❌ Login failed - invalid password for: {credentials.email}")
            raise InvalidCredentials()
        
        # Update last login
        try:
            user.last_login = datetime.utcnow()
            db.commit()
            logger.debug(f"✓ Updated last_login for {credentials.email}")
        except Exception as e:
            logger.warning(f"⚠️  Could not update last_login: {e}")
            db.rollback()
        
        # Create tokens
        try:
            token_data = {"sub": str(user.id), "email": user.email}
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)
            logger.info(f"✅ Tokens created for {credentials.email}")
        except Exception as e:
            logger.error(f"❌ Token creation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create authentication tokens"
            )
        
        # Serialize user object for response
        try:
            logger.debug(f"🔍 Serializing user object for {credentials.email}")
            logger.debug(f"🔍 User fields: id={user.id}, tier={user.tier}, plan_tier={user.plan_tier}, voice_preference={user.voice_preference}")
            user_response = UserResponse.model_validate(user)
            logger.info(f"✅ Login successful for {credentials.email}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": user_response
            }
        except Exception as e:
            logger.error(f"❌ User serialization failed: {e}", exc_info=True)
            logger.error(f"❌ User object dict: {user.__dict__}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to serialize user data: {str(e)}"
            )
    
    except InvalidCredentials:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token
    
    Args:
        refresh_token: Refresh token
        db: Database session
        
    Returns:
        New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    token_data = {"sub": str(user.id), "email": user.email}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout():
    """
    Logout user (client should delete tokens)
    
    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}