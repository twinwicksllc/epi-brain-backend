"""
Chat API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, AsyncGenerator
from uuid import UUID
from datetime import datetime
import json

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.conversation import ConversationResponse, ConversationCreate, ConversationWithMessages
from app.schemas.message import ChatRequest, ChatResponse, MessageResponse
from app.core.dependencies import get_current_active_user, check_message_limit
from app.core.exceptions import ConversationNotFound, UnauthorizedAccess, MessageLimitExceeded
from app.services.claude import ClaudeService
from app.services.groq_service import GroqService
from app.services.memory_service import MemoryService
from app.services.core_variable_collector import CoreVariableCollector
from app.services.active_memory_extractor import ActiveMemoryExtractor
from app.services.privacy_controls import PrivacyControls
from app.services.memory_prompt_enhancer import MemoryPromptEnhancer
from app.services.depth_scorer import DepthScorer
from app.services.depth_engine import ConversationDepthEngine
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize depth scorer
depth_scorer = DepthScorer()
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize depth scorer
depth_scorer = DepthScorer()


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
    
    # Check if depth tracking is enabled for this mode
    depth_enabled = (
        settings.DEPTH_ENABLED and
        conversation.depth_enabled and
        chat_request.mode in settings.DEPTH_TRACKED_MODES
    )
    
    # Score the turn if depth tracking is enabled
    turn_score = None
    new_depth = None
    if depth_enabled:
        try:
            logger.info(f"Scoring depth for conversation {conversation.id}, mode {chat_request.mode}")
            scoring_result = await depth_scorer.score_turn(
                user_message=chat_request.message,
                user_tier=current_user.tier.value if hasattr(current_user, "tier") else None
            )
            turn_score = scoring_result['score']
            
            # Update conversation depth
            engine = ConversationDepthEngine(
                initial_depth=conversation.depth,
                last_updated_at=conversation.last_depth_update
            )
            new_depth = engine.update(turn_score)
            
            conversation.depth = new_depth
            conversation.last_depth_update = datetime.utcnow()
            
            # Save turn score to message (for analytics)
            user_message.turn_score = turn_score
            user_message.scoring_source = scoring_result['source']
            
            logger.info(
                f"Depth updated: {conversation.depth:.2f} "
                f"(turn_score={turn_score:.2f}, source={scoring_result['source']})"
            )
        except Exception as e:
            logger.error(f"Error scoring depth: {e}", exc_info=True)
            # Don't fail the request if depth scoring fails
    
    # Initialize Phase 2 memory services
    memory_service = MemoryService(db)
    core_collector = CoreVariableCollector(memory_service)
    active_extractor = ActiveMemoryExtractor(memory_service, GroqService())
    privacy_controls = PrivacyControls(memory_service)
    prompt_enhancer = MemoryPromptEnhancer()
    
    # Get message count for this conversation
    message_count = len(conversation.messages)
    
    # PHASE 2: Core Variable Collection
    # Check if we should ask for core variables
    collection_prompt = None
    if settings.MEMORY_CORE_COLLECTION_ENABLED:
        should_collect = await core_collector.should_ask_for_core_variables(
            user_id=str(current_user.id),
            message_count=message_count,
            conversation_depth=new_depth if new_depth else 0.0
        )
        
        if should_collect:
            collection_prompt = await core_collector.generate_collection_prompt(
                user_id=str(current_user.id),
                personality=chat_request.mode,
                message_count=message_count
            )
            if collection_prompt:
                logger.info(f"Generated core variable collection prompt for user {current_user.id}")
    
    # Get AI response
    start_time = datetime.utcnow()
    
    try:
        # MEMORY INJECTION: Load and inject user memory into AI context
        memory_context = memory_service.render_memory_for_prompt(
            user_id=str(current_user.id),
            conversation_id=str(conversation.id),
            personality=chat_request.mode
        )
        
        # Choose AI service based on configuration
        use_groq = getattr(settings, 'USE_GROQ', True)  # Default to Groq if not set
        if use_groq:
            ai_service = GroqService()
        else:
            ai_service = ClaudeService()
        
        # Get AI response with memory context
        # Exclude the last message (current user message) from history to avoid duplicate
        conversation_history = conversation.messages[:-1] if conversation.messages else []
        ai_response = await ai_service.get_response(
            message=chat_request.message,
            mode=chat_request.mode,
            conversation_history=conversation_history,
            user_tier=current_user.tier.value if hasattr(current_user, "tier") else None,
            memory_context=memory_context  # Pass memory context to AI service
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
        
        # PHASE 2: Active Memory Extraction
        # Extract relevant information from conversation
        if settings.MEMORY_AUTO_EXTRACTION_ENABLED:
            should_extract = await active_extractor.should_extract_from_conversation(
                user_id=str(current_user.id),
                message_count=message_count,
                conversation_depth=new_depth if new_depth else 0.0
            )
            
            if should_extract:
                try:
                    # Get recent messages for extraction
                    recent_messages = conversation.messages[-10:] if len(conversation.messages) >= 10 else conversation.messages
                    
                    extraction_result = await active_extractor.extract_from_conversation(
                        user_id=str(current_user.id),
                        conversation_id=str(conversation.id),
                        personality=chat_request.mode,
                        recent_messages=recent_messages
                    )
                    
                    if extraction_result["success"]:
                        logger.info(
                            f"Extracted {len(extraction_result['extracted'])} items "
                            f"from conversation {conversation.id}"
                        )
                except Exception as e:
                    logger.error(f"Memory extraction failed: {e}", exc_info=True)
                    # Don't fail the request if extraction fails
        
        # PHASE 2: Privacy Detection
        # Detect privacy-sensitive information in user's message
        if settings.MEMORY_PRIVACY_CONSENT_ENABLED:
            detected_privacy = await privacy_controls.detect_privacy_sensitive_content(
                text=chat_request.message,
                personality=chat_request.mode
            )
            
            if detected_privacy:
                logger.info(f"Detected privacy-sensitive content in conversation {conversation.id}")
                # Privacy prompt would be generated here for frontend to display
        
        db.commit()
        db.refresh(ai_message)
        
        # PHASE 2: Enhance response with core variable collection if needed
        final_content = ai_message.content
        if collection_prompt:
            final_content = prompt_enhancer.enhance_for_core_collection(
                original_response=ai_message.content,
                missing_variables=[],  # Already handled by collection_prompt
                personality=chat_request.mode
            )
            if collection_prompt:
                final_content = f"{ai_message.content}\n\n{collection_prompt}"
        
        return ChatResponse(
            message_id=ai_message.id,
            conversation_id=conversation.id,
            content=final_content,
            mode=conversation.mode,
            created_at=ai_message.created_at,
            tokens_used=int(ai_message.tokens_used) if ai_message.tokens_used else None,
            response_time_ms=response_time_ms,
            depth=new_depth if depth_enabled else None
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
            List of user's conversations ordered by last update
    """
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()

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
    try:
        logger.info(f"Getting conversation {conversation_id} for user {current_user.id}")
        
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found for user {current_user.id}")
            raise ConversationNotFound()
        
        if conversation.user_id != current_user.id:
            logger.warning(f"User {current_user.id} attempted to access conversation {conversation_id} owned by {conversation.user_id}")
            raise UnauthorizedAccess()
        
        logger.info(f"Successfully retrieved conversation {conversation_id}")
        return conversation
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


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


@router.post("/stream")
async def stream_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send a message and get streaming AI response
    
    Args:
        chat_request: Chat request with message and optional conversation_id
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Streaming AI response
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
    
    # Check if depth tracking is enabled for this mode
    depth_enabled = (
        settings.DEPTH_ENABLED and
        conversation.depth_enabled and
        chat_request.mode in settings.DEPTH_TRACKED_MODES
    )
    
    # Score the turn if depth tracking is enabled
    new_depth = None
    if depth_enabled:
        try:
            logger.info(f"Scoring depth for streaming conversation {conversation.id}")
            scoring_result = await depth_scorer.score_turn(
                user_message=chat_request.message,
                user_tier=current_user.tier.value if hasattr(current_user, "tier") else None
            )
            turn_score = scoring_result['score']
            
            # Update conversation depth
            engine = ConversationDepthEngine(
                initial_depth=conversation.depth,
                last_updated_at=conversation.last_depth_update
            )
            new_depth = engine.update(turn_score)
            
            conversation.depth = new_depth
            conversation.last_depth_update = datetime.utcnow()
            
            # Save turn score to message
            user_message.turn_score = turn_score
            user_message.scoring_source = scoring_result['source']
            
            logger.info(f"Depth updated in streaming: {new_depth:.2f}")
        except Exception as e:
            logger.error(f"Error scoring depth in streaming: {e}", exc_info=True)
    
    db.commit()
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate SSE stream"""
        start_time = datetime.utcnow()
        full_response = ""

        try:
            # Choose AI service based on configuration
            use_groq = getattr(settings, 'USE_GROQ', True)  # Default to Groq if not set
            if use_groq:
                ai_service = GroqService()
            else:
                ai_service = ClaudeService()

            # Get streaming response (select model based on user tier)
            # Exclude the last message (current user message) from history to avoid duplicate
            conversation_history = conversation.messages[:-1] if conversation.messages else []
            response = await ai_service.get_streaming_response(
                message=chat_request.message,
                mode=chat_request.mode,
                conversation_history=conversation_history,
                user_tier=current_user.tier.value if hasattr(current_user, "tier") else None
            )
            async for chunk in response:
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            # Send done signal
            yield f"data: [DONE]\n\n"

            # Save AI message to database
            response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            ai_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=full_response,
                tokens_used="0",  # Groq doesn't provide token count in streaming
                response_time_ms=str(response_time_ms)
            )
            db.add(ai_message)

            # Update user message count
            current_user.message_count = str(int(current_user.message_count) + 1)

            db.commit()

        except Exception as e:
            db.rollback()
            error_msg = f"Error getting AI response: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/conversations/{conversation_id}/depth")
async def get_conversation_depth(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current depth for a conversation
    
    Args:
        conversation_id: Conversation ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Current depth value with metadata
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise ConversationNotFound()
    
    # Check if depth tracking is enabled
    if not conversation.depth_enabled or conversation.mode not in settings.DEPTH_TRACKED_MODES:
        return {
            "depth": None,
            "enabled": False,
            "mode": conversation.mode
        }
    
    # Get depth with decay applied
    engine = ConversationDepthEngine(
        initial_depth=conversation.depth,
        last_updated_at=conversation.last_depth_update
    )
    current_depth = engine.get_depth()
    
    return {
        "depth": current_depth,
        "enabled": True,
        "mode": conversation.mode,
        "last_updated": conversation.last_depth_update.isoformat()
    }


@router.post("/conversations/{conversation_id}/depth/disable")
async def disable_depth_tracking(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Disable depth tracking for a conversation
    
    Args:
        conversation_id: Conversation ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise ConversationNotFound()
    
    conversation.depth_enabled = False
    conversation.depth = 0.0  # Reset depth when disabled
    db.commit()
    
    logger.info(f"Depth tracking disabled for conversation {conversation_id}")
    
    return {
        "message": "Depth tracking disabled",
        "conversation_id": str(conversation_id)
    }


@router.post("/conversations/{conversation_id}/depth/enable")
async def enable_depth_tracking(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Enable depth tracking for a conversation
    
    Args:
        conversation_id: Conversation ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise ConversationNotFound()
    
    # Check if mode supports depth tracking
    if conversation.mode not in settings.DEPTH_TRACKED_MODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Depth tracking not available for mode '{conversation.mode}'"
        )
    
    conversation.depth_enabled = True
    db.commit()
    
    logger.info(f"Depth tracking enabled for conversation {conversation_id}")
    
    return {
        "message": "Depth tracking enabled",
        "conversation_id": str(conversation_id)
    }


# ============================================
# PHASE 2: Memory Management Endpoints
# ============================================

@router.get("/memory/completion-status")
async def get_memory_completion_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get completion status of core memory variables
    """
    memory_service = MemoryService(db)
    core_collector = CoreVariableCollector(memory_service)
    
    status = await core_collector.assess_completion_status(user_id=str(current_user.id))
    
    return {
        "user_id": str(current_user.id),
        "completion_percentage": status["completion_percentage"],
        "completed_variables": status["completed_variables"],
        "total_required_variables": status["total_required_variables"],
        "missing_variables": status["missing_variables"],
        "is_complete": status["is_complete"]
    }


@router.get("/memory/next-priority-variable")
async def get_next_priority_variable(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the next highest-priority core variable to collect
    """
    memory_service = MemoryService(db)
    core_collector = CoreVariableCollector(memory_service)
    
    next_var = await core_collector.get_next_priority_variable(user_id=str(current_user.id))
    
    return {
        "next_variable": next_var,
        "prompt": next_var if next_var else None
    }


@router.post("/memory/extract")
async def trigger_memory_extraction(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger memory extraction from a conversation
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise ConversationNotFound()
    
    memory_service = MemoryService(db)
    active_extractor = ActiveMemoryExtractor(memory_service, GroqService())
    
    # Get recent messages
    recent_messages = conversation.messages[-10:] if len(conversation.messages) >= 10 else conversation.messages
    
    extraction_result = await active_extractor.extract_from_conversation(
        user_id=str(current_user.id),
        conversation_id=str(conversation.id),
        personality=conversation.mode,
        recent_messages=recent_messages
    )
    
    return {
        "success": extraction_result["success"],
        "extracted_count": len(extraction_result["extracted"]),
        "extracted_data": extraction_result["extracted"],
        "errors": extraction_result["errors"]
    }


@router.post("/memory/privacy-consent")
async def handle_privacy_consent(
    variable_path: str,
    value: str,
    consent: bool,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Handle user consent for storing privacy-sensitive information
    """
    memory_service = MemoryService(db)
    privacy_controls = PrivacyControls(memory_service)
    
    result = await privacy_controls.store_with_permission(
        user_id=str(current_user.id),
        variable_path=variable_path,
        value=value,
        user_consent=consent
    )
    
    return result


@router.get("/memory/privacy-settings")
async def get_privacy_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's privacy settings
    """
    memory_service = MemoryService(db)
    privacy_controls = PrivacyControls(memory_service)
    
    settings = await privacy_controls.get_user_privacy_settings(user_id=str(current_user.id))
    
    return {
        "user_id": str(current_user.id),
        "privacy_settings": settings
    }


@router.put("/memory/privacy-settings")
async def update_privacy_settings(
    settings_update: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user's privacy settings
    """
    memory_service = MemoryService(db)
    privacy_controls = PrivacyControls(memory_service)
    
    result = await privacy_controls.update_privacy_settings(
        user_id=str(current_user.id),
        settings=settings_update
    )
    
    return result
