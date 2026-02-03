"""
Assistant Tools API
Internal messaging, notes, and utility tools for Pocket EPI MVP
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.user_note import UserNote
from app.core.dependencies import get_current_active_user
from app.services.email_service import EmailService
from app.services.user_note_service import UserNoteService

router = APIRouter()


# Pydantic Schemas
class InternalMessageRequest(BaseModel):
    """Request to send internal message"""
    recipient_name: str = Field(..., description="Team member name (tom, darrick, etc.)")
    subject: str = Field(..., description="Message subject")
    message: str = Field(..., description="Message content")
    include_user_context: bool = Field(default=True, description="Include sender's email in message")


class InternalMessageResponse(BaseModel):
    """Response from internal message"""
    success: bool
    message: str
    recipient: Optional[str] = None
    error: Optional[str] = None


class CreateNoteRequest(BaseModel):
    """Request to create a note"""
    content: str = Field(..., description="Note content")
    note_type: str = Field(default="quick_note", description="Type: quick_note, draft, reflection, thought")
    title: Optional[str] = Field(None, description="Optional title")
    conversation_id: Optional[str] = Field(None, description="Link to conversation")
    personality_mode: Optional[str] = Field(None, description="AI personality context")
    tags: Optional[str] = Field(None, description="Comma-separated tags")


class UpdateNoteRequest(BaseModel):
    """Request to update a note"""
    content: Optional[str] = Field(None, description="New content")
    title: Optional[str] = Field(None, description="New title")
    tags: Optional[str] = Field(None, description="New tags")


class NoteResponse(BaseModel):
    """Response with note data"""
    id: str
    user_id: str
    note_type: str
    title: Optional[str]
    content: str
    conversation_id: Optional[str]
    personality_mode: Optional[str]
    tags: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TranslationRequest(BaseModel):
    """Request for translation"""
    text: str = Field(..., description="Text to translate")
    target_language: str = Field(default="spanish", description="Target language")
    context: Optional[str] = Field(None, description="Context for better translation")


class PolishRequest(BaseModel):
    """Request for text polishing/proofreading"""
    text: str = Field(..., description="Text to polish")
    mode: str = Field(default="email", description="Mode: email, formal, casual, professional")
    context: Optional[str] = Field(None, description="Context for better polishing")


# Internal Messaging Endpoints
@router.post("/internal-message", response_model=InternalMessageResponse)
async def send_internal_message(
    request: InternalMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send internal message to team member
    
    Allows EPI to send thoughts/notes to specific people (Tom, Darrick, etc.)
    Maps names to email addresses from environment variables.
    """
    try:
        email_service = EmailService()
        
        # Add user context if requested
        sender_context = current_user.email if request.include_user_context else None
        
        result = email_service.send_internal_message(
            recipient_name=request.recipient_name,
            subject=request.subject,
            message=request.message,
            sender_context=sender_context
        )
        
        if result["success"]:
            return InternalMessageResponse(
                success=True,
                message=f"Message sent to {request.recipient_name}",
                recipient=result.get("recipient")
            )
        else:
            return InternalMessageResponse(
                success=False,
                message=f"Failed to send message: {result.get('error')}",
                error=result.get("error")
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/internal-message/available-recipients")
async def get_available_recipients(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available internal message recipients"""
    email_service = EmailService()
    return {
        "recipients": list(email_service.TEAM_MEMBERS.keys()),
        "note": "Use these names in the 'recipient_name' field"
    }


# User Notes Endpoints
@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    request: CreateNoteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new note/draft/reflection
    
    Allows users to save Quick Notes, Drafts, or Reflections.
    EPI can act as a 'thinking partner' who remembers ideas.
    """
    try:
        note_service = UserNoteService(db)
        
        note = note_service.create_note(
            user_id=str(current_user.id),
            content=request.content,
            note_type=request.note_type,
            title=request.title,
            conversation_id=request.conversation_id,
            personality_mode=request.personality_mode,
            tags=request.tags
        )
        
        return NoteResponse.from_orm(note)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create note: {str(e)}"
        )


@router.get("/notes", response_model=List[NoteResponse])
async def get_notes(
    note_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's notes with optional filtering"""
    try:
        note_service = UserNoteService(db)
        notes = note_service.get_user_notes(
            user_id=str(current_user.id),
            note_type=note_type,
            limit=limit,
            offset=offset
        )
        
        return [NoteResponse.from_orm(note) for note in notes]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notes: {str(e)}"
        )


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific note by ID"""
    try:
        note_service = UserNoteService(db)
        note = note_service.get_note_by_id(note_id, str(current_user.id))
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        return NoteResponse.from_orm(note)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve note: {str(e)}"
        )


@router.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    request: UpdateNoteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing note"""
    try:
        note_service = UserNoteService(db)
        note = note_service.update_note(
            note_id=note_id,
            user_id=str(current_user.id),
            content=request.content,
            title=request.title,
            tags=request.tags
        )
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        return NoteResponse.from_orm(note)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update note: {str(e)}"
        )


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a note"""
    try:
        note_service = UserNoteService(db)
        deleted = note_service.delete_note(note_id, str(current_user.id))
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete note: {str(e)}"
        )


@router.get("/notes/search/{search_term}", response_model=List[NoteResponse])
async def search_notes(
    search_term: str,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search notes by content or title"""
    try:
        note_service = UserNoteService(db)
        notes = note_service.search_notes(
            user_id=str(current_user.id),
            search_term=search_term,
            limit=limit
        )
        
        return [NoteResponse.from_orm(note) for note in notes]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search notes: {str(e)}"
        )


@router.get("/notes-summary")
async def get_notes_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get summary statistics for user's notes"""
    try:
        note_service = UserNoteService(db)
        summary = note_service.get_notes_summary(str(current_user.id))
        
        return summary
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notes summary: {str(e)}"
        )


# Translation & Polish Tools
@router.post("/translate")
async def translate_text(
    request: TranslationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Translate text to target language (high-quality Spanish translation)
    
    Note: This endpoint returns instructions for the AI to perform translation.
    In production, integrate with dedicated translation service or LLM.
    """
    return {
        "instruction": "translate",
        "text": request.text,
        "target_language": request.target_language,
        "context": request.context,
        "prompt": f"""Please provide a high-quality translation of the following text to {request.target_language}.
Context: {request.context or 'General translation'}

Text to translate:
{request.text}

Provide natural, fluent translation that captures the original meaning and tone."""
    }


@router.post("/polish")
async def polish_text(
    request: PolishRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Polish/proofread text for specific mode (email drafting, formal, etc.)
    
    Note: This endpoint returns instructions for the AI to perform polishing.
    In production, integrate with dedicated proofreading service or LLM.
    """
    mode_prompts = {
        "email": "professional email format with clear structure",
        "formal": "formal business communication",
        "casual": "friendly, approachable tone",
        "professional": "polished professional writing"
    }
    
    mode_instruction = mode_prompts.get(request.mode, "general polishing")
    
    return {
        "instruction": "polish",
        "text": request.text,
        "mode": request.mode,
        "context": request.context,
        "prompt": f"""Please proofread and polish the following text for {mode_instruction}.
Context: {request.context or 'General polishing'}

Original text:
{request.text}

Provide:
1. Polished version
2. Key improvements made
3. Grammar/style suggestions"""
    }
