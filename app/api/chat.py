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
from app.services.depth_scorer import DepthScorer
from app.services.depth_engine import ConversationDepthEngine
from app.config import settings
import logging

# Phase 2 imports - wrapped in try/except for safety
try:
    from app.services.core_variable_collector import CoreVariableCollector
    from app.services.active_memory_extractor import ActiveMemoryExtractor
    from app.services.privacy_controls import PrivacyControls
    from app.services.memory_prompt_enhancer import MemoryPromptEnhancer
    from app.services.response_parser import ResponseParser
    PHASE_2_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Phase 2 memory services not available: {e}")
    PHASE_2_AVAILABLE = False

# Phase 2A imports - semantic memory (wrapped in try/except for safety)
try:
    from app.services.semantic_memory_service import SemanticMemoryService
    import openai
    PHASE_2A_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Phase 2A semantic memory service not available: {e}")
    PHASE_2A_AVAILABLE = False

# Phase 2B imports - goal management (wrapped in try/except for safety)
try:
    from app.services.goal_service import GoalService
    from app.services.habit_service import HabitService
    from app.services.check_in_service import CheckInService
    PHASE_2B_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Phase 2B goal management services not available: {e}")
    PHASE_2B_AVAILABLE = False

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
    
    # Get AI response
    start_time = datetime.utcnow()
    
    try:
        # MEMORY INJECTION: Load and inject user memory into AI context
        memory_service = MemoryService(db)
        memory_context = await memory_service.render_memory_for_prompt(
            user_id=str(current_user.id),
            conversation_id=str(conversation.id),
            personality=chat_request.mode
        )
        if memory_context:
            logger.info(f"Injecting memory context for user {current_user.id}:\n{memory_context}")
        else:
            logger.debug(f"No memory context available for user {current_user.id}")
        
        # PHASE 2A: SEMANTIC MEMORY RETRIEVAL
        semantic_memory_context = ""
        if PHASE_2A_AVAILABLE and settings.SEMANTIC_MEMORY_ENABLED:
            try:
                # Initialize OpenAI client for embeddings
                openai_client = None
                if settings.OPENAI_API_KEY:
                    openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                else:
                    logger.warning("OPENAI_API_KEY not set, semantic memory retrieval disabled")
                
                if openai_client:
                    semantic_memory_service = SemanticMemoryService(db, openai_client)
                    
                    # Retrieve relevant semantic memories
                    relevant_memories = await semantic_memory_service.retrieve_relevant_memories(
                        user_id=str(current_user.id),
                        mode=chat_request.mode,
                        current_input=chat_request.message,
                        max_memories=settings.SEMANTIC_MEMORY_MAX_MEMORIES,
                        min_importance=settings.SEMANTIC_MEMORY_MIN_IMPORTANCE / 10.0
                    )
                    
                    if relevant_memories:
                        semantic_memory_context = semantic_memory_service.format_memories_for_prompt(relevant_memories)
                        logger.info(f"Retrieved {len(relevant_memories)} semantic memories for user {current_user.id}, mode {chat_request.mode}")
                    else:
                        logger.debug(f"No semantic memories found for user {current_user.id}, mode {chat_request.mode}")
            except Exception as e:
                logger.error(f"Error retrieving semantic memories: {e}", exc_info=True)
                # Don't fail the request if semantic memory retrieval fails
        
        # Combine memory contexts (existing + semantic)
        combined_memory_context = memory_context
        if semantic_memory_context:
            if combined_memory_context:
                combined_memory_context = f"{combined_memory_context}\n\n{semantic_memory_context}"
            else:
                combined_memory_context = semantic_memory_context
        
        # PHASE 2B: GOAL CONTEXT RETRIEVAL
        goal_context = ""
        if PHASE_2B_AVAILABLE and settings.MEMORY_ENABLED:
            try:
                goal_service = GoalService(db)
                habit_service = HabitService(db)
                
                # Retrieve active goals
                active_goals = goal_service.get_user_goals(
                    user_id=str(current_user.id),
                    status="in_progress"
                )
                
                # Retrieve due habits
                due_habits = habit_service.get_due_habits(
                    user_id=str(current_user.id)
                )
                
                # Format goal context for AI
                if active_goals or due_habits:
                    goal_context_parts = []
                    
                    if active_goals:
                        goal_context_parts.append("Active Goals:")
                        for goal in active_goals:
                            goal_info = f"- {goal.title}"
                            if goal.specific_description:
                                goal_info += f": {goal.specific_description}"
                            if goal.current_streak_days > 0:
                                goal_info += f" (Streak: {goal.current_streak_days} days)"
                            goal_context_parts.append(goal_info)
                    
                    if due_habits:
                        goal_context_parts.append("\nHabits Due Today:")
                        for habit in due_habits:
                            habit_info = f"- {habit.name}"
                            if habit.current_streak > 0:
                                habit_info += f" (Streak: {habit.current_streak} days)"
                            goal_context_parts.append(habit_info)
                    
                    goal_context = "\n".join(goal_context_parts)
                    logger.info(f"Retrieved {len(active_goals)} active goals and {len(due_habits)} due habits for user {current_user.id}")
                else:
                    logger.debug(f"No active goals or due habits for user {current_user.id}")
            except Exception as e:
                logger.error(f"Error retrieving goal context: {e}", exc_info=True)
                # Don't fail the request if goal retrieval fails
        
        # Combine all contexts (memory + semantic + goals)
        if goal_context:
            if combined_memory_context:
                combined_memory_context = f"{combined_memory_context}\n\n{goal_context}"
            else:
                combined_memory_context = goal_context
        
        # PHASE 2: Parse user message for core variable information
        if PHASE_2_AVAILABLE and settings.MEMORY_ENABLED:
            try:
                response_parser = ResponseParser(memory_service)
                extracted = await response_parser.parse_and_extract(
                    user_id=str(current_user.id),
                    user_message=chat_request.message,
                    conversation_id=str(conversation.id)
                )
                if extracted:
                    logger.info(f"Extracted core variables from user message: {extracted}")
            except Exception as e:
                logger.error(f"Error parsing user response: {e}", exc_info=True)
        
        # PHASE 2: Core Variable Collection (if enabled)
        collection_prompt = None
        if PHASE_2_AVAILABLE and settings.MEMORY_ENABLED and settings.MEMORY_CORE_COLLECTION_ENABLED:
            try:
                core_collector = CoreVariableCollector(memory_service)
                # Count messages BEFORE flush to avoid issues
                message_count = db.query(Message).filter(
                    Message.conversation_id == conversation.id
                ).count()
                
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
            except Exception as e:
                logger.error(f"Phase 2 core collection error: {e}", exc_info=True)
                # Don't fail the request if Phase 2 has issues
        
        # PHASE 2B: ACCOUNTABILITY PROMPTS
        accountability_prompt = None
        if PHASE_2B_AVAILABLE and settings.MEMORY_ENABLED:
            try:
                goal_service = GoalService(db)
                check_in_service = CheckInService(db)
                
                # Check if user has overdue check-ins
                overdue_items = check_in_service.get_overdue_items(
                    user_id=str(current_user.id)
                )
                
                if overdue_items:
                    # Generate accountability prompt for overdue items
                    overdue_goals = [item for item in overdue_items if item['type'] == 'goal']
                    
                    if overdue_goals:
                        # Get user's accountability style (default to 'grace' if not set)
                        accountability_style = getattr(current_user, 'accountability_style', 'grace')
                        
                        # Generate prompt based on accountability style
                        if accountability_style == 'tactical':
                            accountability_prompt = (
                                f"\n\n[Accountability Check] You have {len(overdue_goals)} goal(s) that need attention. "
                                "Let's get back on track. What's holding you back?"
                            )
                        elif accountability_style == 'grace':
                            accountability_prompt = (
                                f"\n\n[Gentle Reminder] I noticed you have {len(overdue_goals)} goal(s) that could use some attention. "
                                "No pressure - want to talk about how things are going?"
                            )
                        elif accountability_style == 'analyst':
                            accountability_prompt = (
                                f"\n\n[Progress Analysis] Data shows {len(overdue_goals)} goal(s) are behind schedule. "
                                "Let's analyze what's working and what needs adjustment."
                            )
                        else:  # adaptive
                            # Use conversation depth to determine tone
                            if new_depth and new_depth > 0.5:
                                # High depth - use grace approach
                                accountability_prompt = (
                                    f"\n\n[Check-in] I see you have {len(overdue_goals)} goal(s) that might need attention. "
                                    "How are you feeling about your progress?"
                                )
                            else:
                                # Low depth - use tactical approach
                                accountability_prompt = (
                                    f"\n\n[Quick Check] {len(overdue_goals)} goal(s) need updates. "
                                    "Ready to share your progress?"
                                )
                        
                        if accountability_prompt:
                            logger.info(f"Generated accountability prompt for user {current_user.id} ({accountability_style} style)")
                
            except Exception as e:
                logger.error(f"Phase 2B accountability prompt error: {e}", exc_info=True)
                # Don't fail the request if accountability prompt generation fails
        
        # Choose AI service based on configuration
        use_groq = getattr(settings, 'USE_GROQ', True)  # Default to Groq if not set
        if use_groq:
            ai_service = GroqService()
        else:
            ai_service = ClaudeService()
        
        # Get AI response with combined memory context (existing + semantic)
        # Exclude the last message (current user message) from history to avoid duplicate
        conversation_history = conversation.messages[:-1] if conversation.messages else []
        ai_response = await ai_service.get_response(
            message=chat_request.message,
            mode=chat_request.mode,
            conversation_history=conversation_history,
            user_tier=current_user.tier.value if hasattr(current_user, "tier") else None,
            memory_context=combined_memory_context  # Pass combined memory context to AI service
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
        
        # PHASE 2: Active Memory Extraction (if enabled)
        if PHASE_2_AVAILABLE and settings.MEMORY_ENABLED and settings.MEMORY_AUTO_EXTRACTION_ENABLED:
            try:
                active_extractor = ActiveMemoryExtractor(memory_service, GroqService())
                # Count messages BEFORE flush to avoid issues
                message_count = db.query(Message).filter(
                    Message.conversation_id == conversation.id
                ).count()
                
                should_extract = await active_extractor.should_extract_from_conversation(
                    user_id=str(current_user.id),
                    message_count=message_count,
                    conversation_depth=new_depth if new_depth else 0.0
                )
                
                if should_extract:
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
                logger.error(f"Phase 2 active extraction error: {e}", exc_info=True)
                # Don't fail the request if Phase 2 has issues
        
        # PHASE 2A: SEMANTIC MEMORY EXTRACTION
        if PHASE_2A_AVAILABLE and settings.SEMANTIC_MEMORY_ENABLED:
            try:
                # Initialize OpenAI client for embeddings
                openai_client = None
                if settings.OPENAI_API_KEY:
                    openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                
                if openai_client:
                    semantic_memory_service = SemanticMemoryService(db, openai_client)
                    
                    # Extract semantic memories from conversation
                    # Only extract if we have enough messages (minimum threshold)
                    message_count = db.query(Message).filter(
                        Message.conversation_id == conversation.id
                    ).count()
                    
                    # Extract every N messages (configurable)
                    extraction_interval = settings.MEMORY_EXTRACTION_INTERVAL
                    if message_count >= settings.MEMORY_MIN_MESSAGES_FOR_EXTRACTION and message_count % extraction_interval == 0:
                        extracted_memories = await semantic_memory_service.extract_memories_from_conversation(
                            conversation=conversation,
                            max_memories=5
                        )
                        
                        if extracted_memories:
                            logger.info(
                                f"Extracted {len(extracted_memories)} semantic memories "
                                f"from conversation {conversation.id} (mode: {chat_request.mode})"
                            )
                        else:
                            logger.debug(
                                f"No semantic memories extracted from conversation {conversation.id} "
                                f"(mode: {chat_request.mode})"
                            )
            except Exception as e:
                logger.error(f"Phase 2A semantic memory extraction error: {e}", exc_info=True)
                # Don't fail the request if semantic memory extraction fails
        
        # PHASE 2B: GOAL EXTRACTION AND UPDATES
        if PHASE_2B_AVAILABLE and settings.MEMORY_ENABLED:
            try:
                goal_service = GoalService(db)
                habit_service = HabitService(db)
                
                # Check if user message mentions goals or progress
                user_message_lower = chat_request.message.lower()
                
                # Keywords that indicate goal-related content
                goal_keywords = ['goal', 'progress', 'achieved', 'completed', 'milestone', 'target']
                habit_keywords = ['habit', 'routine', 'daily', 'completed', 'did', 'finished']
                
                # Check for goal mentions
                if any(keyword in user_message_lower for keyword in goal_keywords):
                    # Get user's active goals
                    active_goals = goal_service.get_user_goals(
                        user_id=str(current_user.id),
                        status="in_progress"
                    )
                    
                    # Simple extraction: look for progress indicators
                    if active_goals and ('progress' in user_message_lower or 'update' in user_message_lower):
                        # For now, log that we detected a potential goal update
                        # In future, use AI to extract specific progress details
                        logger.info(
                            f"Detected potential goal update in conversation {conversation.id}. "
                            f"User has {len(active_goals)} active goals."
                        )
                
                # Check for habit completion mentions
                if any(keyword in user_message_lower for keyword in habit_keywords):
                    # Get user's active habits
                    active_habits = habit_service.get_user_habits(
                        user_id=str(current_user.id),
                        status="active"
                    )
                    
                    # Simple extraction: look for completion indicators
                    if active_habits and ('completed' in user_message_lower or 'did' in user_message_lower or 'finished' in user_message_lower):
                        # For now, log that we detected a potential habit completion
                        # In future, use AI to extract specific habit completions
                        logger.info(
                            f"Detected potential habit completion in conversation {conversation.id}. "
                            f"User has {len(active_habits)} active habits."
                        )
                
            except Exception as e:
                logger.error(f"Phase 2B goal extraction error: {e}", exc_info=True)
                # Don't fail the request if goal extraction fails
        
        db.commit()
        db.refresh(ai_message)
        
        # PHASE 2: Enhance response with collection prompt if needed
        # PHASE 2B: Add accountability prompt if needed
        final_content = ai_message.content
        
        # Add collection prompt (Phase 2)
        if collection_prompt and PHASE_2_AVAILABLE:
            try:
                final_content = f"{final_content}\n\n{collection_prompt}"
            except Exception as e:
                logger.error(f"Phase 2 prompt enhancement error: {e}", exc_info=True)
        
        # Add accountability prompt (Phase 2B)
        if accountability_prompt and PHASE_2B_AVAILABLE:
            try:
                final_content = f"{final_content}\n\n{accountability_prompt}"
            except Exception as e:
                logger.error(f"Phase 2B accountability prompt enhancement error: {e}", exc_info=True)
        
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
