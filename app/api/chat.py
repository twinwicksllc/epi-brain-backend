"""
Chat API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.conversation import ConversationResponse, ConversationCreate, ConversationWithMessages
from app.schemas.message import ChatRequest, ChatResponse, MessageResponse
from app.core.dependencies import get_current_active_user, check_message_limit
from app.core.exceptions import ConversationNotFound, UnauthorizedAccess, MessageLimitExceeded
from app.services.claude import ClaudeService

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send a message and get AI response
    
    Args:
        chat_request: Chat request with message and optional conversation_id
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AI response with message details
    """
    # Check message limit
    if not check_message_limit(current_user, db):
        raise MessageLimitExceeded()
    
    # Get or create conversation
    if chat_request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == chat_request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise ConversationNotFound()
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=current_user.id,
            mode=chat_request.mode,
            title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message
        )
        db.add(conversation)
        db.flush()
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=chat_request.message
    )
    db.add(user_message)
    db.flush()
    
    # Get AI response
    start_time = datetime.utcnow()
    
    try:
        claude_service = ClaudeService()
        ai_response = await claude_service.get_response(
            message=chat_request.message,
            mode=chat_request.mode,
            conversation_history=conversation.messages
        )
        
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Save AI message
        ai_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=ai_response["content"],
            tokens_used=str(ai_response.get("tokens_used", 0)),
            response_time_ms=str(response_time_ms)
        )
        db.add(ai_message)
        
        # Update user message count
        current_user.message_count = str(int(current_user.message_count) + 1)
        
        db.commit()
        db.refresh(ai_message)
        
        return ChatResponse(
            message_id=ai_message.id,
            conversation_id=conversation.id,
            content=ai_message.content,
            mode=conversation.mode,
            created_at=ai_message.created_at,
            tokens_used=int(ai_message.tokens_used) if ai_message.tokens_used else None,
            response_time_ms=response_time_ms
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error getting AI response: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """
    Get user's conversations
    
    Args:
        current_user: Current authenticated user
        db: Database session
        skip: Number of conversations to skip
        limit: Maximum number of conversations to return
        
    Returns:
        List of user's conversations
    """
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(
        Conversation.updated_at.desc()
    ).offset(skip).limit(limit).all()
    
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation with messages
    
    Args:
        conversation_id: Conversation UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Conversation with messages
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise ConversationNotFound()
    
    if conversation.user_id != current_user.id:
        raise UnauthorizedAccess()
    
    return conversation


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation
    
    Args:
        conversation_data: Conversation creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created conversation
    """
    conversation = Conversation(
        user_id=current_user.id,
        mode=conversation_data.mode,
        title=conversation_data.title
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation
    
    Args:
        conversation_id: Conversation UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise ConversationNotFound()
    
    if conversation.user_id != current_user.id:
        raise UnauthorizedAccess()
    
    db.delete(conversation)
    db.commit()
    
    return {"message": "Conversation deleted successfully"}