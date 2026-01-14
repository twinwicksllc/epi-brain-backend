"""
Memory API Endpoints

Provides REST API for managing user memory:
- GET /api/v1/memory/global - Get user's global memory
- PUT /api/v1/memory/global - Update global memory field
- PUT /api/v1/memory/personality - Update personality-specific context
- GET /api/v1/memory/session/{conversation_id} - Get session memory
- POST /api/v1/memory/consolidate/{conversation_id} - Consolidate session to global
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.memory_service import MemoryService
from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


class UpdateMemoryRequest(BaseModel):
    """Request to update a memory field"""
    category: str
    key: str
    value: Any


class UpdatePersonalityContextRequest(BaseModel):
    """Request to update personality-specific context"""
    personality: str
    context: Dict[str, Any]


@router.get("/global")
async def get_global_memory(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's global memory
    
    Returns the complete global memory structure including:
    - user_profile
    - communication_preferences
    - personality_contexts
    - behavioral_patterns
    """
    try:
        memory_service = MemoryService(db)
        return memory_service.get_global_memory(str(current_user.id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get global memory: {str(e)}")


@router.put("/global")
async def update_global_memory(
    request: UpdateMemoryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific field in user's global memory
    
    Example request:
    ```json
    {
        "category": "communication_preferences",
        "key": "style",
        "value": "concise"
    }
    ```
    """
    try:
        memory_service = MemoryService(db)
        return memory_service.update_global_memory(
            user_id=str(current_user.id),
            category=request.category,
            key=request.key,
            value=request.value
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update global memory: {str(e)}")


@router.put("/personality")
async def update_personality_context(
    request: UpdatePersonalityContextRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update personality-specific context
    
    Example request:
    ```json
    {
        "personality": "weight_loss_coach",
        "context": {
            "diet_type": "vegetarian",
            "goal_weight": 170,
            "workout_preference": "morning"
        }
    }
    ```
    """
    try:
        memory_service = MemoryService(db)
        return memory_service.update_personality_context(
            user_id=str(current_user.id),
            personality=request.personality,
            context=request.context
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update personality context: {str(e)}")


@router.get("/personality/{personality}")
async def get_personality_context(
    personality: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get context for a specific personality
    
    Returns the personality-specific context or empty dict if none exists
    """
    try:
        memory_service = MemoryService(db)
        return memory_service.get_personality_context(
            user_id=str(current_user.id),
            personality=personality
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personality context: {str(e)}")


@router.get("/session/{conversation_id}")
async def get_session_memory(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get conversation's session memory
    
    Returns the session memory for the specified conversation
    """
    try:
        memory_service = MemoryService(db)
        return memory_service.get_session_memory(conversation_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session memory: {str(e)}")


@router.post("/consolidate/{conversation_id}")
async def consolidate_memory(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Consolidate session memory into global memory
    
    This merges temporary session preferences into permanent global memory,
    following consolidation rules (durable info promoted, temporary discarded)
    """
    try:
        memory_service = MemoryService(db)
        return memory_service.consolidate_session_to_global(
            user_id=str(current_user.id),
            conversation_id=conversation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to consolidate memory: {str(e)}")


@router.get("/render/{conversation_id}")
async def render_memory_for_conversation(
    conversation_id: str,
    personality: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Render memory as markdown for AI prompt injection
    
    This is primarily for debugging - the chat API uses this internally
    """
    try:
        memory_service = MemoryService(db)
        rendered = memory_service.render_memory_for_prompt(
            user_id=str(current_user.id),
            conversation_id=conversation_id,
            personality=personality
        )
        return {"rendered_memory": rendered}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render memory: {str(e)}")