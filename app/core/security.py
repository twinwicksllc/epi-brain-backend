"""
Security utilities for authentication and password hashing
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from uuid import UUID

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    # Check if it's a SHA256 hash (fallback)
    if hashed_password.startswith('sha256$'):
        hash_part = hashed_password.split('$', 1)[1]
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hash_part
    elif hashed_password.startswith('sha256') and len(hashed_password) == 70:
        hash_part = hashed_password[6:]  # Remove 'sha256' prefix
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hash_part
    elif len(hashed_password) == 64 and all(c in '0123456789abcdef' for c in hashed_password.lower()):
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    
    # bcrypt has a 72 byte limit, truncate if necessary
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except:
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    # bcrypt has a 72 byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    
    try:
        return pwd_context.hash(password)
    except Exception as e:
        # Fallback to a simple hash if bcrypt fails
        import hashlib
        return f"sha256${hashlib.sha256(password.encode()).hexdigest()}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Data to encode in token (typically user_id and email)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token
    
    Args:
        data: Data to encode in token (typically user_id and email)
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify a JWT token and check its type
    
    Args:
        token: JWT token to verify
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded token payload or None if invalid
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    if payload.get("type") != token_type:
        return None
    
    return payload


def generate_referral_code(user_id: UUID) -> str:
    """
    Generate a unique referral code for a user
    
    Args:
        user_id: User's UUID
        
    Returns:
        Referral code string
    """
    import hashlib
    
    # Create a hash of the user_id
    hash_object = hashlib.sha256(str(user_id).encode())
    hash_hex = hash_object.hexdigest()
    
    # Take first 8 characters and make uppercase
    referral_code = hash_hex[:8].upper()
    
    return f"EPI{referral_code}"
def verify_admin_key(admin_key: str = None) -> bool:
    """
    Verify admin API key
    
    This security function extracts the admin_key from query parameters.
    Usage: add to endpoint as: admin_key: str = Security(verify_admin_key)
    
    Frontend should call: GET /api/v1/admin/usage?admin_key=YOUR_ADMIN_KEY
    
    Args:
        admin_key: Admin API key to verify (extracted from query parameters)
    
    Returns:
        True if admin key is valid, raises HTTPException otherwise
    
    Raises:
        HTTPException: If admin key is missing or invalid
    """
    from fastapi import HTTPException
    from app.config import settings
    
    if not admin_key:
        raise HTTPException(
            status_code=401, 
            detail="Admin API key required. Pass as query parameter: ?admin_key=YOUR_KEY"
        )
    
    if not settings.ADMIN_API_KEY:
        raise HTTPException(status_code=500, detail="Admin API key not configured on server")
    
    if admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin API key")
    
    return True

