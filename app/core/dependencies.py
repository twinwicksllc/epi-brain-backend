"""
FastAPI Dependencies
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.schemas.user import TokenData

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract token from credentials
    token = credentials.credentials
    
    # Verify and decode token
    payload = verify_token(token, token_type="access")
    
    if payload is None:
        raise credentials_exception
    
    # Extract user_id from payload
    user_id: Optional[str] = payload.get("sub")
    
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user
    Can be extended to check if user is active/verified
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Current active user
    """
    # Add additional checks here if needed (e.g., is_active, is_verified)
    return current_user


async def require_pro_tier(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to require Pro tier or higher
    
    Args:
        current_user: Current user
        
    Returns:
        Current user if Pro or Enterprise tier
        
    Raises:
        HTTPException: If user is not Pro or Enterprise tier
    """
    if not (current_user.is_pro_tier or current_user.is_enterprise_tier):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires Pro or Enterprise tier"
        )
    
    return current_user


async def require_enterprise_tier(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to require Enterprise tier
    
    Args:
        current_user: Current user
        
    Returns:
        Current user if Enterprise tier
        
    Raises:
        HTTPException: If user is not Enterprise tier
    """
    if not current_user.is_enterprise_tier:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires Enterprise tier"
        )
    
    return current_user


def check_message_limit(user: User, db: Session) -> bool:
    """
    Check if user has exceeded their message limit
    
    Args:
        user: User object
        db: Database session
        
    Returns:
        True if user can send messages, False otherwise
    """
    # Pro and Enterprise users have unlimited messages
    if user.has_unlimited_messages:
        return True
    
    # Check free tier message limit
    from app.config import settings
    
    message_count = int(user.message_count)
    
    if message_count >= settings.FREE_TIER_MESSAGE_LIMIT:
        return False
    
    return True