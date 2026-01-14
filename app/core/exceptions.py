"""
Custom Exception Classes
"""

from fastapi import HTTPException, status


class MessageLimitExceeded(HTTPException):
    """Exception raised when user exceeds message limit"""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Message limit exceeded. Please upgrade to Pro tier for unlimited messages."
        )


class InvalidCredentials(HTTPException):
    """Exception raised for invalid login credentials"""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )


class UserAlreadyExists(HTTPException):
    """Exception raised when user already exists"""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )


class ConversationNotFound(HTTPException):
    """Exception raised when conversation is not found"""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )


class UnauthorizedAccess(HTTPException):
    """Exception raised for unauthorized access to resources"""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )


class InvalidMode(HTTPException):
    """Exception raised for invalid personality mode"""
    
    def __init__(self, mode: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid personality mode: {mode}"
        )


class ClaudeAPIError(HTTPException):
    """Exception raised for Claude API errors"""
    
    def __init__(self, detail: str = "Error communicating with AI service"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )