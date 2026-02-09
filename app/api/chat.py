"""
Chat API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, AsyncGenerator, Dict, Optional, Tuple
from uuid import UUID
from datetime import datetime
import json
import re

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.conversation import ConversationResponse, ConversationCreate, ConversationWithMessages
from app.schemas.message import ChatRequest, ChatResponse, MessageResponse
from app.core.dependencies import get_current_active_user, get_optional_user_from_auth_header, get_current_active_user_optional, check_message_limit
from app.core.exceptions import ConversationNotFound, UnauthorizedAccess, MessageLimitExceeded
from app.core.rate_limiter import check_rate_limit, get_rate_limit_info, get_discovery_context, update_discovery_context
from app.services.claude import ClaudeService
from app.services.groq_service import GroqService
from app.services.memory_service import MemoryService
from app.prompts.discovery_mode import DISCOVERY_MODE_ID
from app.services.depth_scorer import DepthScorer
from app.services.depth_engine import ConversationDepthEngine
from app.services.nebp_state_machine import NEBPStateMachine
from app.config import settings
import logging

# Initialize logger before any imports that might use it
logger = logging.getLogger(__name__)

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

# Phase 3 imports - personality router (wrapped in try/except for safety)
try:
    from app.services.personality_router import PersonalityRouter
    PHASE_3_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Phase 3 personality router not available: {e}")
    PHASE_3_AVAILABLE = False

# Phase 4 imports - CBT and safety (wrapped in try/except for safety)
try:
    from app.services.thought_record_service import ThoughtRecordService
    from app.services.behavioral_activation_service import BehavioralActivationService
    from app.services.exposure_hierarchy_service import ExposureHierarchyService
    from app.services.safety_service import SafetyService
    PHASE_4_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Phase 4 CBT and safety services not available: {e}")
    PHASE_4_AVAILABLE = False

# Discovery Mode extraction service (wrapped in try/except for safety)
try:
    from app.services.discovery_extraction_service import DiscoveryExtractionService
    DISCOVERY_EXTRACTION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Discovery extraction service not available: {e}")
    DISCOVERY_EXTRACTION_AVAILABLE = False

router = APIRouter()

# The homepage quick start always uses the core EPI Brain personality
HOMEPAGE_DEFAULT_PERSONALITY = "personal_friend"

# Initialize depth scorer
depth_scorer = DepthScorer()

MAX_DISCOVERY_METADATA_CHARS = 256

# Refined strike counter configuration
# - HONEST_ATTEMPT_STRIKES: More lenient for users genuinely trying (5 strikes allowed)
# - NON_ENGAGEMENT_STRIKES: Stricter for clear non-engagement (3 strikes triggers failsafe)
MAX_HONEST_ATTEMPT_STRIKES = 5  # User is trying but struggling
MAX_NON_ENGAGEMENT_STRIKES = 3   # User is clearly wasting time
DISCOVERY_FAILSAFE_MESSAGE = (
    "I'd love to help you with that! To unlock my full capabilities and move beyond "
    "our initial discovery, let's get your account set up first."
)

# Name validation constraints
MAX_NAME_LENGTH = 40
MAX_NAME_WORD_COUNT = 4

# Track engagement quality weights
STRIKE_WEIGHTS = {
    "honest_attempt": 1,      # Playful but genuine, or struggling
    "dismissive": 2,          # Dismissive but could recover
    "clear_non_engagement": 3 # Clearly wasting time or spam
}


def _resolve_user_tier(user: Optional[User]) -> Optional[str]:
    """
    Resolve the most accurate tier string for model selection.
    Prefers plan_tier (Commercial MVP) and falls back to legacy tier.
    """
    if not user:
        return None

    plan_tier = getattr(user, "plan_tier", None)
    if plan_tier:
        value = getattr(plan_tier, "value", None) or str(plan_tier)
        if value:
            return value.lower()

    legacy_tier = getattr(user, "tier", None)
    if legacy_tier:
        value = getattr(legacy_tier, "value", None) or str(legacy_tier)
        if value:
            return value.lower()

    return None

def _validate_extracted_name(name: str) -> bool:
    """
    Validate that extracted name meets reasonable constraints.
    Prevents 'greedy' extraction of full sentences as names.
    
    Args:
        name: Extracted name string
        
    Returns:
        True if valid, False if too long or too many words
    """
    if not name:
        return False
    
    # Check character length
    if len(name) > MAX_NAME_LENGTH:
        logger.debug(f"Name validation failed: length {len(name)} > {MAX_NAME_LENGTH}")
        return False
    
    # Check word count
    word_count = len(name.split())
    if word_count > MAX_NAME_WORD_COUNT:
        logger.debug(f"Name validation failed: {word_count} words > {MAX_NAME_WORD_COUNT}")
        return False
    
    return True

NAME_EXTRACTION_REGEX = re.compile(
    r"(?:my name is|i am called|call me|this is|name is|name's|i'm)\s+([\w'\-]+(?:\s+[\w'\-]+){0,3})(?:\s|[.,!?]|$)",
    re.IGNORECASE | re.UNICODE
)
INTENT_EXTRACTION_REGEX = re.compile(
    r"(?:here (?:to|for|because)|i'm here (?:to|for|because)|i came (?:to|for|because)|i'm looking (?:to|for)|i want (?:to|help with)|i need (?:to|help with)|looking for help with|need help with|want help with|hoping to|want to talk about|talk about|reaching out (?:to|because|for)|i've come to|struggling with|dealing with|working on|interested in)\s+(.+?)(?:[.!?]|$)",
    re.IGNORECASE
)

def _sanitize_discovery_value(value: str) -> str:
    """Keep discovery metadata compact so it stays within our limited disk budget."""
    trimmed = value.strip()
    if len(trimmed) <= MAX_DISCOVERY_METADATA_CHARS:
        return trimmed
    shortened = trimmed[:MAX_DISCOVERY_METADATA_CHARS - 3].rstrip()
    logger.debug("Truncating discovery metadata to %d chars", MAX_DISCOVERY_METADATA_CHARS)
    return f"{shortened}..."


def _detect_repetition(message: str, message_history: list) -> Tuple[bool, int]:
    """
    Detect if the user message is repetitive.
    
    Returns:
        Tuple of (is_repetitive, repetition_count)
    """
    if not message_history:
        return False, 0
    
    message_lower = message.strip().lower()
    
    # Check against recent messages
    recent_messages = message_history[-3:] if len(message_history) >= 3 else message_history
    
    repetition_count = 0
    for hist_msg in recent_messages:
        if hist_msg.lower().strip() == message_lower:
            repetition_count += 1
    
    # Also check for semantic similarity (same topic, similar wording)
    if repetition_count == 0 and len(recent_messages) >= 2:
        # Check if current message is very similar to previous messages
        words_current = set(message_lower.split())
        for hist_msg in recent_messages:
            words_hist = set(hist_msg.lower().split())
            if words_current and words_hist:
                # Calculate Jaccard similarity
                intersection = words_current & words_hist
                union = words_current | words_hist
                similarity = len(intersection) / len(union) if union else 0
                if similarity > 0.7:  # 70% similarity threshold
                    repetition_count += 1
    
    is_repetitive = repetition_count > 0
    return is_repetitive, repetition_count


def _capture_discovery_metadata(message: str) -> Dict[str, Optional[str]]:
    metadata = {"captured_name": None, "captured_intent": None, "invalid_name_format": False}

    name_match = NAME_EXTRACTION_REGEX.search(message)
    if name_match:
        extracted_name = name_match.group(1)
        if _validate_extracted_name(extracted_name):
            metadata["captured_name"] = _sanitize_discovery_value(extracted_name)
        else:
            # Mark as invalid but don't capture the name
            metadata["invalid_name_format"] = True
            logger.warning(f"Invalid name format detected: '{extracted_name}' (len={len(extracted_name)}, words={len(extracted_name.split())})")  

    intent_match = INTENT_EXTRACTION_REGEX.search(message)
    if intent_match:
        intent_text = intent_match.group(1).strip().rstrip(".!?")
        if intent_text:
            metadata["captured_intent"] = _sanitize_discovery_value(intent_text)

    return metadata


def _check_discovery_engagement(metadata: Dict[str, Optional[str]]) -> bool:
    """
    Check if user engaged with discovery prompt by providing name or intent.
    
    Args:
        metadata: Dictionary with captured_name and captured_intent
        
    Returns:
        True if user provided name or intent, False otherwise
    """
    return bool(metadata.get("captured_name") or metadata.get("captured_intent"))


def _get_non_engagement_count(conversation: Conversation) -> int:
    """Get the non-engagement strike count from conversation session memory."""
    if not conversation.session_memory:
        return 0
    return conversation.session_memory.get("non_engagement_strikes", 0)


def _get_honest_attempt_count(conversation: Conversation) -> int:
    """Get the honest attempt strike count (more lenient)."""
    if not conversation.session_memory:
        return 0
    return conversation.session_memory.get("honest_attempt_strikes", 0)


def _increment_strike_count(
    conversation: Conversation,
    db: Session,
    strike_weight: int = 1,
    is_honest_attempt: bool = False
) -> Tuple[int, int]:
    """
    Increment strike count based on engagement quality.
    
    Args:
        conversation: Conversation object
        db: Database session
        strike_weight: Weight of this strike (1-3)
        is_honest_attempt: True if user is genuinely trying
        
    Returns:
        Tuple of (total_non_engagement_strikes, total_honest_attempt_strikes)
    """
    if not conversation.session_memory:
        conversation.session_memory = {}
    
    if is_honest_attempt:
        # User is trying but struggling - use lenient counter
        current_count = conversation.session_memory.get("honest_attempt_strikes", 0)
        new_count = current_count + 1
        conversation.session_memory["honest_attempt_strikes"] = new_count
        logger.info(
            f"Honest attempt strike {new_count}/{MAX_HONEST_ATTEMPT_STRIKES} "
            f"(weight={strike_weight}) for conversation {conversation.id}"
        )
        db.flush()
        non_engagement_strikes = conversation.session_memory.get("non_engagement_strikes", 0)
        return non_engagement_strikes, new_count
    else:
        # User is not engaging - use strict counter
        current_count = conversation.session_memory.get("non_engagement_strikes", 0)
        new_count = current_count + strike_weight  # Weight can be 1-3
        conversation.session_memory["non_engagement_strikes"] = new_count
        logger.warning(
            f"Non-engagement strike +{strike_weight} (now {new_count}/{MAX_NON_ENGAGEMENT_STRIKES}) "
            f"for conversation {conversation.id}"
        )
        db.flush()
        honest_strikes = conversation.session_memory.get("honest_attempt_strikes", 0)
        return new_count, honest_strikes


def _should_trigger_failsafe(
    non_engagement_strikes: int,
    honest_attempt_strikes: int
) -> bool:
    """
    Determine if failsafe should trigger based on strike counts.
    
    Strategy:
    - Non-engagement strikes are weighted more heavily
    - Honest attempts get more chances
    """
    # Trigger if clear non-engagement threshold reached
    if non_engagement_strikes >= MAX_NON_ENGAGEMENT_STRIKES:
        return True
    
    # Don't trigger if user is genuinely trying
    return False


def _reset_strike_counts(conversation: Conversation, db: Session):
    """Reset strike counts when user shows engagement."""
    if conversation.session_memory:
        conversation.session_memory["non_engagement_strikes"] = 0
        conversation.session_memory["honest_attempt_strikes"] = 0
        db.flush()
        logger.info(f"Reset all strike counts for conversation {conversation.id}")


def _get_invalid_name_count(conversation: Conversation) -> int:
    """Get the invalid name count from conversation session memory."""
    if not conversation.session_memory:
        return 0
    return conversation.session_memory.get("invalid_name_count", 0)


def _increment_invalid_name_count(conversation: Conversation, db: Session) -> int:
    """Increment and return the invalid name count."""
    current_count = _get_invalid_name_count(conversation)
    new_count = current_count + 1
    
    if not conversation.session_memory:
        conversation.session_memory = {}
    
    conversation.session_memory["invalid_name_count"] = new_count
    db.flush()
    
    logger.warning(
        f"Invalid name format #{new_count} for conversation {conversation.id}"
    )
    
    return new_count


def _build_discovery_context(
    metadata: Dict[str, Optional[str]],
    trigger_signup_bridge: bool,
    invalid_name_format: bool = False,
    non_engagement_strikes: int = 0,
    is_honest_attempt: bool = False,
    repetition_count: int = 0,
    message_history: list = None
) -> Optional[str]:
    """
    Build context instructions for the LLM in Discovery Mode.
    
    This function provides the LLM with information about:
    - What data has been captured
    - Whether verification is needed
    - What to do if both pieces are captured
    - How to handle non-engagement
    - Current topic for context retention
    
    Args:
        metadata: Captured name and intent
        trigger_signup_bridge: Whether to show signup message
        invalid_name_format: Whether user provided sentence instead of name
        non_engagement_strikes: Current non-engagement strike count
        is_honest_attempt: Whether user is genuinely trying
        repetition_count: Number of repetitive inputs detected
        message_history: Recent messages from user
    """
    lines = []
    
    # CRITICAL: Inject current topic for context retention
    if metadata.get("captured_intent"):
        lines.append(f"\n📌 CURRENT TOPIC: {metadata['captured_intent']}")
        lines.append("→ ALWAYS remember this topic when user uses pronouns (it, this, that)")
        lines.append("→ Context retention is CRITICAL - do not forget the topic between turns")
    
    # Report captured data
    if metadata.get("captured_name"):
        lines.append(f"\n✓ Name Captured: {metadata['captured_name']}")
        lines.append("→ Next step: Verify the name, then ask about intent")
    
    if metadata.get("captured_intent"):
        lines.append(f"✓ Intent Captured: {metadata['captured_intent']}")
    
    # Handle repetition detection
    if repetition_count >= 2:
        lines.append(f"\n⚠️ REPETITION DETECTED (cycle {repetition_count})")
        lines.append("→ User is looping on the same topic")
        lines.append("→ PIVOT STRATEGY: Stop asking about feelings/opinions")
        lines.append(f"→ Say: 'I have some great strategies for {metadata.get('captured_intent', 'this topic')}, but to dive deeper, let's get your account set up.'")
        lines.append("→ Then trigger signup bridge immediately")
    
    # Handle invalid name format
    if invalid_name_format:
        lines.append(
            "\n⚠️ INVALID NAME FORMAT: User provided a sentence or long text, not a name.\n"
            "→ Action: Politely clarify without moving to intent question.\n"
            "→ Example: 'That sounds interesting, but I'd love to know what to actually call you. What's your name?'\n"
            "→ Do NOT ask about their intent until you have a proper name."
        )
    
    # Handle invalid name format
    if invalid_name_format:
        lines.append(
            "⚠️ INVALID NAME FORMAT: User provided a sentence or long text, not a name.\n"
            "→ Action: Politely clarify without moving to intent question.\n"
            "→ Example: 'That sounds interesting, but I'd love to know what to actually call you. What's your name?'\n"
            "→ Do NOT ask about their intent until you have a proper name."
        )
    
    # Handle signup bridge (both name and intent captured)
    if trigger_signup_bridge:
        from app.prompts.discovery_mode import DISCOVERY_MODE_SIGNUP_BRIDGE_TEMPLATE
        bridge_msg = DISCOVERY_MODE_SIGNUP_BRIDGE_TEMPLATE.format(
            name=metadata.get("captured_name", "there"),
            intent=metadata.get("captured_intent", "this")
        )
        lines.append(
            f"🎯 CRITICAL: Both name and intent captured!\n"
            f"→ Action: Deliver signup bridge message now (no more questions):\n\n{bridge_msg}"
        )
    
    # Handle non-engagement situation
    if non_engagement_strikes > 0:
        if is_honest_attempt:
            lines.append(
                f"ℹ️  User is genuinely trying but struggling ({non_engagement_strikes} honest attempt strikes).\n"
                f"→ Action: Be extra patient and supportive. They have room to recover."
            )
        else:
            if non_engagement_strikes >= MAX_NON_ENGAGEMENT_STRIKES:
                lines.append(
                    f"⛔ USER DISENGAGEMENT THRESHOLD REACHED ({non_engagement_strikes}/{MAX_NON_ENGAGEMENT_STRIKES} strikes).\n"
                    f"→ Action: Failsafe will be triggered. Stop using LLM calls. User should sign up for more."
                )
            else:
                remaining = MAX_NON_ENGAGEMENT_STRIKES - non_engagement_strikes
                lines.append(
                    f"⚠️  User not engaging ({non_engagement_strikes}/{MAX_NON_ENGAGEMENT_STRIKES} strikes).\n"
                    f"→ Action: {remaining} strike(s) remaining before failsafe triggers. Be direct but warm."
                )
    
    if not lines:
        return None

    return f"<discovery_context>\n" + "\n".join(lines) + "\n</discovery_context>"

    if not lines:
        return None

    return f"<discovery_context>\n" + "\n".join(lines) + "\n</discovery_context>"


@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Send a message and get AI response
    Supports both authenticated and unauthenticated users (for discovery mode)
    
    Args:
        chat_request: Chat request with message and optional conversation_id
        request: FastAPI request object (for IP rate limiting)
        db: Database session
        
    Returns:
        AI response with message details
    """
    # Get user from Authorization header (optional, None if not authenticated)
    auth_header = request.headers.get("authorization", "")
    current_user = get_optional_user_from_auth_header(auth_header, db) if auth_header else None
    
    mode = (chat_request.mode or "").strip()
    if not mode:
        mode = DISCOVERY_MODE_ID
    chat_request.mode = mode
    # Accept both "discovery" and "discovery_mode" for discovery mode
    discovery_mode_requested = mode == DISCOVERY_MODE_ID or mode == "discovery"
    
    # GUEST FALLBACK: If unauthenticated and mode is not a recognized personality,
    # treat as discovery mode (helps when frontend sends "default" or other unknown values)
    if not current_user and not discovery_mode_requested:
        # List of known personalities that require authentication
        authenticated_personalities = [
            "therapist", "coach", "mentor", "personal_friend", 
            "motivator", "psychologist", "life_coach", "wellness_advisor", "psychology_expert"
        ]
        if mode.lower() not in authenticated_personalities:
            # Unknown mode for guest → treat as discovery mode
            logger.info(f"[DEBUG] Guest sent unknown mode '{mode}', defaulting to discovery_mode")
            mode = DISCOVERY_MODE_ID
            discovery_mode_requested = True
    
    # Debug logging
    logger.info(f"[DEBUG] POST /message - auth_header present: {bool(auth_header)}, current_user: {current_user}, mode: '{mode}', discovery_mode_requested: {discovery_mode_requested}")
    
    # Normalize mode to "discovery_mode" for AI services
    if mode == "discovery":
        mode = DISCOVERY_MODE_ID
    
    # Resolve silo_id from request metadata or stored user profile
    silo_id = None
    if chat_request.metadata and isinstance(chat_request.metadata, dict):
        silo_id = chat_request.metadata.get("silo_id")
    if not silo_id and current_user:
        silo_id = getattr(current_user, "silo_id", None)

    # Entry point tagging for homepage quick starts
    entry_point = (chat_request.entry_point or "").strip() or None
    if chat_request.is_homepage_session and not entry_point:
        entry_point = "homepage_quickstart"
    if entry_point:
        entry_point = entry_point[:100]

    # For discovery mode, check if user is authenticated
    # If not authenticated, skip user-specific checks
    if not discovery_mode_requested:
        # Require authentication for non-discovery modes
        if current_user is None:
            logger.warning(f"[DEBUG] Rejecting unauthenticated request for non-discovery mode: {mode}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for this mode"
            )
        
        # Check message limit for authenticated users
        if not check_message_limit(current_user, db):
            raise MessageLimitExceeded()

    # IP-based rate limiting for discovery mode (unauthenticated sessions)
    if discovery_mode_requested:
        # Get client IP from request
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if forwarded (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Apply rate limit
        is_allowed, remaining = check_rate_limit(client_ip)
        
        if not is_allowed:
            rate_info = get_rate_limit_info(client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "You've reached the maximum number of discovery messages. Please create a free account to continue.",
                    "limit": rate_info["limit"],
                    "window_hours": rate_info["window_hours"],
                    "seconds_until_reset": rate_info["seconds_until_reset"],
                    "reset_at": rate_info["reset_at"]
                }
            )
        
        # Log rate limit info
        logger.info(f"Discovery mode rate limit check for IP {client_ip}: {remaining} messages remaining")
        
        # Get stored discovery context for this IP
        stored_context = get_discovery_context(client_ip)
        logger.info(f"Retrieved stored discovery context for IP {client_ip}: {stored_context}")
        
        # Check if user hit the limit (3 messages for proactive gating)
        DISCOVERY_LIMIT_THRESHOLD = 3
        messages_used = get_rate_limit_info(client_ip).get("messages_used", 0)
        
        if messages_used >= DISCOVERY_LIMIT_THRESHOLD:
            logger.warning(f"User hit discovery limit at {messages_used} messages (threshold: {DISCOVERY_LIMIT_THRESHOLD})")
            # Return limit_reached response immediately
            return ChatResponse(
                message_id=None,
                conversation_id=None,
                content="I'd love to continue exploring this topic with you, but I've reached my limit for discovery mode messages. To continue our conversation about " + (stored_context.get("captured_intent") or "this topic") + ", please create a free account. It only takes a moment!",
                mode=mode,
                created_at=datetime.utcnow(),
                tokens_used=None,
                response_time_ms=None,
                depth=None,
                metadata={"limit_reached": "true", "messages_used": str(messages_used)},
                limit_reached=True
            )

    # Check personality access (discovery mode is always available)
    if not discovery_mode_requested and current_user:
        homepage_personality_access = (
            chat_request.is_homepage_session and mode == HOMEPAGE_DEFAULT_PERSONALITY
        )
        if not homepage_personality_access and mode not in current_user.subscribed_personalities:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not subscribed to this personality."
            )

    discovery_metadata = {"captured_name": None, "captured_intent": None}
    discovery_context_block = None
    discovery_failsafe_triggered = False
    
    if discovery_mode_requested:
        # Get current message metadata
        current_metadata = _capture_discovery_metadata(chat_request.message)
        
        # Merge with stored context (stored context takes precedence)
        if stored_context.get("captured_name"):
            discovery_metadata["captured_name"] = stored_context["captured_name"]
        if current_metadata.get("captured_name"):
            discovery_metadata["captured_name"] = current_metadata["captured_name"]
        
        if stored_context.get("captured_intent"):
            discovery_metadata["captured_intent"] = stored_context["captured_intent"]
        if current_metadata.get("captured_intent"):
            discovery_metadata["captured_intent"] = current_metadata["captured_intent"]
        
        # Update stored context with new information
        update_discovery_context(client_ip, discovery_metadata, chat_request.message)
        
        # Detect repetition
        is_repetitive, repetition_increment = _detect_repetition(
            chat_request.message, 
            stored_context.get("message_history", [])
        )
        
        if is_repetitive:
            stored_context["repetition_count"] += repetition_increment
            logger.warning(f"Repetition detected for IP {client_ip}: count={stored_context['repetition_count']}")
        else:
            # Reset repetition count if user provides new content
            stored_context["repetition_count"] = 0

    if current_user:
        # Persist silo_id on user profile if provided
        if silo_id and getattr(current_user, "silo_id", None) != silo_id:
            current_user.silo_id = silo_id
        # Update NEBP phase and clarity metrics
        nebp_metrics = NEBPStateMachine.update_state(
            current_user,
            chat_request.message,
            discovery_metadata if discovery_mode_requested else None,
            silo_id=silo_id
        )
        if nebp_metrics:
            db.flush()
    
    # Get or create conversation
    # For discovery mode without authentication, we won't persist conversations
    conversation = None
    if current_user:
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

    # Tag conversation entry point for dashboard analytics
    if conversation and entry_point:
        if not conversation.session_memory:
            conversation.session_memory = {}
        conversation.session_memory["entry_point"] = entry_point
        conversation.session_memory["is_homepage_session"] = chat_request.is_homepage_session
        db.flush()
    
    # DISCOVERY FAILSAFE: Check engagement and strike counter with refined logic
    discovery_failsafe_triggered = False
    non_engagement_strikes = 0
    honest_attempt_strikes = 0
    
    if discovery_mode_requested and conversation:
        user_engaged = _check_discovery_engagement(discovery_metadata)
        invalid_name_detected = discovery_metadata.get("invalid_name_format", False)
        non_engagement_strikes = _get_non_engagement_count(conversation)
        honest_attempt_strikes = _get_honest_attempt_count(conversation)
        
        if user_engaged:
            # User provided valid name or intent - reset strikes
            _reset_strike_counts(conversation, db)
            logger.info(f"User engagement detected, reset strike counts for conversation {conversation.id}")
        elif invalid_name_detected:
            # User provided invalid name format (sentence instead of name)
            invalid_name_count = _increment_invalid_name_count(conversation, db)
            
            # Second invalid name treated as non-engagement strike
            if invalid_name_count >= 2:
                non_engagement_strikes, honest_attempt_strikes = _increment_strike_count(
                    conversation,
                    db,
                    strike_weight=1,
                    is_honest_attempt=False
                )
                logger.warning(
                    f"Second invalid name detected, incremented non-engagement strikes to {non_engagement_strikes}"
                )
        else:
            # User ignored discovery prompt entirely
            # Assess whether this is honest attempt or clear non-engagement
            is_honest = (honest_attempt_strikes > 0) or (non_engagement_strikes == 0)
            strike_weight = 1 if is_honest else 2  # Be stricter if pattern of non-engagement
            
            non_engagement_strikes, honest_attempt_strikes = _increment_strike_count(
                conversation,
                db,
                strike_weight=strike_weight,
                is_honest_attempt=is_honest
            )
            logger.info(
                f"Non-engagement detected (honest={is_honest}, weight={strike_weight}), "
                f"strikes now: non_engagement={non_engagement_strikes}, honest_attempt={honest_attempt_strikes}"
            )
        
        # Check if failsafe should trigger
        discovery_failsafe_triggered = _should_trigger_failsafe(non_engagement_strikes, honest_attempt_strikes)
        
        if discovery_failsafe_triggered:
            logger.critical(
                f"Discovery failsafe triggered for conversation {conversation.id}: "
                f"non_engagement={non_engagement_strikes}/{MAX_NON_ENGAGEMENT_STRIKES}"
            )
        
        # Build context for LLM with strike info
        trigger_signup = bool(discovery_metadata["captured_name"] and discovery_metadata["captured_intent"])
        discovery_context_block = _build_discovery_context(
            discovery_metadata,
            trigger_signup,
            invalid_name_format=invalid_name_detected,
            non_engagement_strikes=non_engagement_strikes,
            is_honest_attempt=(honest_attempt_strikes > 0),
            repetition_count=stored_context.get("repetition_count", 0),
            message_history=stored_context.get("message_history", [])
        )
    elif discovery_mode_requested:
        # Discovery mode without conversation (unauthenticated)
        # Simplified context for unauthenticated users
        trigger_signup = bool(discovery_metadata["captured_name"] and discovery_metadata["captured_intent"])
        discovery_context_block = _build_discovery_context(
            discovery_metadata,
            trigger_signup,
            invalid_name_format=False,
            non_engagement_strikes=0,
            is_honest_attempt=True,
            repetition_count=stored_context.get("repetition_count", 0),
            message_history=stored_context.get("message_history", [])
        )
    
    # Save user message (only if authenticated)
    if conversation:
        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=chat_request.message
        )
        db.add(user_message)
        db.flush()
    
    # DISCOVERY FAILSAFE: Return hardcoded response if failsafe triggered
    if discovery_failsafe_triggered and conversation:
        # Create failsafe response message
        failsafe_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=DISCOVERY_FAILSAFE_MESSAGE,
            tokens_used="0",
            response_time_ms="0"
        )
        db.add(failsafe_message)
        db.commit()
        db.refresh(failsafe_message)
        
        # Return response with failsafe flag
        return ChatResponse(
            message_id=failsafe_message.id,
            conversation_id=conversation.id,
            content=DISCOVERY_FAILSAFE_MESSAGE,
            mode=conversation.mode,
            created_at=failsafe_message.created_at,
            tokens_used=0,
            response_time_ms=0,
            depth=None,
            metadata={
                "failsafe_triggered": "true",
                "non_engagement_strikes": str(non_engagement_strikes),
                "honest_attempt_strikes": str(honest_attempt_strikes)
            }
        )
    
    # PHASE 4: SAFETY CHECKS (Psychology Expert Mode)
    safety_context = ""
    is_high_risk = False
    if PHASE_4_AVAILABLE and chat_request.mode == "psychology_expert" and current_user and conversation:
        try:
            safety_service = SafetyService()
            
            # Detect high-risk content
            is_high_risk, risk_categories, severity = safety_service.detect_high_risk_content(
                chat_request.message
            )
            
            if is_high_risk:
                # Log safety event
                safety_service.log_safety_event(
                    user_id=str(current_user.id),
                    categories=risk_categories,
                    severity=severity,
                    message_preview=chat_request.message
                )
                
                # Add crisis response to context
                crisis_response = safety_service.get_crisis_response(
                    categories=risk_categories,
                    region="US"  # TODO: Get user's region from profile
                )
                
                # Add safety prompt additions
                safety_context = safety_service.get_safety_prompt_addition(risk_categories)
                safety_context += f"\n\n**CRISIS RESPONSE TO INCLUDE:**\n{crisis_response}"
                
                logger.warning(
                    f"High-risk content detected in conversation {conversation.id}: "
                    f"categories={risk_categories}, severity={severity}"
                )
            
            # Add disclaimer if needed
            message_count = db.query(Message).filter(
                Message.conversation_id == conversation.id
            ).count()
            
            if safety_service.should_show_disclaimer(message_count):
                disclaimer = safety_service.get_disclaimer("psychology_expert")
                safety_context += f"\n\n**INCLUDE THIS DISCLAIMER:**\n{disclaimer}"
                
        except Exception as e:
            logger.error(f"Error in safety checks: {e}", exc_info=True)
            # Don't fail the request if safety checks fail
    
    # Check if depth tracking is enabled for this mode
    depth_enabled = (
        settings.DEPTH_ENABLED and
        conversation and
        conversation.depth_enabled and
        chat_request.mode in settings.DEPTH_TRACKED_MODES
    )
    
    # Score the turn if depth tracking is enabled
    turn_score = None
    new_depth = None
    if depth_enabled and conversation and current_user:
        try:
            logger.info(f"Scoring depth for conversation {conversation.id}, mode {chat_request.mode}")
            scoring_result = await depth_scorer.score_turn(
                user_message=chat_request.message,
                user_tier=_resolve_user_tier(current_user)
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
        # MEMORY INJECTION: Load and inject user memory into AI context (only for authenticated users)
        memory_context = ""
        if current_user and conversation:
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
        if current_user and conversation and PHASE_2A_AVAILABLE and settings.SEMANTIC_MEMORY_ENABLED:
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
        if current_user and conversation and PHASE_2B_AVAILABLE and settings.MEMORY_ENABLED:
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
        # PHASE 4: Add safety context for Psychology Expert mode
        if safety_context:
            if combined_memory_context:
                combined_memory_context = f"{combined_memory_context}\n\n{safety_context}"
            else:
                combined_memory_context = safety_context

        if discovery_context_block:
            if combined_memory_context:
                combined_memory_context = f"{combined_memory_context}\n\n{discovery_context_block}"
            else:
                combined_memory_context = discovery_context_block

        
        # PHASE 2: Parse user message for core variable information
        if current_user and conversation and PHASE_2_AVAILABLE and settings.MEMORY_ENABLED:
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
        if current_user and conversation and PHASE_2_AVAILABLE and settings.MEMORY_ENABLED and settings.MEMORY_CORE_COLLECTION_ENABLED:
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
        if current_user and conversation and PHASE_2B_AVAILABLE and settings.MEMORY_ENABLED:
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
        
        # PHASE 3: PERSONALITY ROUTER - Determine accountability style
        accountability_style = None
        if current_user and conversation and PHASE_2B_AVAILABLE:
            try:
                from app.services.personality_router import get_personality_router
                
                router = get_personality_router()
                
                # Get user's accountability style preference
                user_preference = getattr(current_user, 'accountability_style', None)
                
                # Determine appropriate style based on context
                routing_decision = router.determine_style(
                    user_preference=user_preference,
                    conversation_depth=new_depth if new_depth else None,
                    user_state=None,  # Could be extracted from conversation in future
                    context_signals={
                        'overdue_goals': len(overdue_items) if 'overdue_items' in locals() else 0,
                        'active_goals': len(active_goals) if 'active_goals' in locals() else 0
                    }
                )
                
                accountability_style = routing_decision['style']
                
                # Log routing decision
                router.log_routing_decision(
                    user_id=str(current_user.id),
                    decision=routing_decision,
                    conversation_id=str(conversation.id)
                )
                
                logger.info(
                    f"Personality routing: style={accountability_style}, "
                    f"reason={routing_decision['reason']}, "
                    f"confidence={routing_decision['confidence']:.2f}"
                )
                
            except Exception as e:
                logger.error(f"Phase 3 personality routing error: {e}", exc_info=True)
                # Don't fail the request if personality routing fails
        
        # Choose AI service based on configuration
        use_groq = getattr(settings, 'USE_GROQ', True)  # Default to Groq if not set
        
        # Get AI response with combined memory context (existing + semantic)
        # Exclude the last message (current user message) from history to avoid duplicate
        conversation_history = conversation.messages[:-1] if conversation and conversation.messages else []
        
        # Check if API key is configured
        if not settings.GROQ_API_KEY:
            error_msg = "GROQ_API_KEY not configured. Please set GROQ_API_KEY environment variable."
            logger.critical(error_msg)
            raise Exception(error_msg)
        
        # Use Groq service only (no fallback for now to simplify debugging)
        logger.info("Using Groq service...")
        ai_service = GroqService()
        
        try:
            ai_response = await ai_service.get_response(
                message=chat_request.message,
                mode=chat_request.mode,
                conversation_history=conversation_history,
                user_tier=_resolve_user_tier(current_user),
                memory_context=combined_memory_context,  # Pass combined memory context to AI service
                accountability_style=accountability_style,  # Phase 3: Pass accountability style
                conversation_depth=new_depth if new_depth else None,  # Phase 3: Pass conversation depth
                silo_id=silo_id
            )
            logger.info("Successfully got response from Groq service")
        except Exception as e:
            logger.error(f"Groq service failed: {e}", exc_info=True)
            raise Exception(f"Groq service failed: {str(e)}")
        
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Save AI message and update user count only for authenticated users
        ai_message = None
        if current_user and conversation:
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
        
        # PHASE 2: Active Memory Extraction (if enabled) - only for authenticated users
        if current_user and conversation and PHASE_2_AVAILABLE and settings.MEMORY_ENABLED and settings.MEMORY_AUTO_EXTRACTION_ENABLED:
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
        
        # PHASE 2A: SEMANTIC MEMORY EXTRACTION - only for authenticated users
        if current_user and conversation and PHASE_2A_AVAILABLE and settings.SEMANTIC_MEMORY_ENABLED:
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
        
        # PHASE 2B: GOAL EXTRACTION AND UPDATES - only for authenticated users
        if current_user and conversation and PHASE_2B_AVAILABLE and settings.MEMORY_ENABLED:
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
        
        # Only commit to database if we saved messages (authenticated users)
        if current_user and conversation and ai_message:
            db.commit()
            db.refresh(ai_message)
        
        # PHASE 2: Enhance response with collection prompt if needed
        # PHASE 2B: Add accountability prompt if needed
        final_content = ai_response["content"]  # Use the AI response directly
        
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
        
        metadata_response = None
        if discovery_mode_requested:
            captured_fields = {k: v for k, v in discovery_metadata.items() if v}
            metadata_response = captured_fields if captured_fields else None

        if entry_point:
            metadata_response = metadata_response or {}
            metadata_response["entry_point"] = entry_point
        if chat_request.is_homepage_session:
            metadata_response = metadata_response or {}
            metadata_response["is_homepage_session"] = "true"

        # Return response - handle both authenticated and unauthenticated users
        if current_user and conversation and ai_message:
            # Authenticated user: return full response with database IDs
            return ChatResponse(
                message_id=ai_message.id,
                conversation_id=conversation.id,
                content=final_content,
                mode=conversation.mode,
                created_at=ai_message.created_at,
                tokens_used=int(ai_message.tokens_used) if ai_message.tokens_used else None,
                response_time_ms=response_time_ms,
                depth=new_depth if depth_enabled else None,
                metadata=metadata_response
            )
        else:
            # Unauthenticated discovery mode: return simplified response
            return ChatResponse(
                message_id=None,  # No message saved
                conversation_id=None,  # No conversation created
                content=final_content,
                mode=chat_request.mode,
                created_at=datetime.utcnow(),  # Use current time
                tokens_used=ai_response.get("tokens_used"),
                response_time_ms=response_time_ms,
                depth=new_depth if depth_enabled else None,
                metadata=metadata_response
            )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error getting AI response: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: Optional[User] = Depends(get_current_active_user_optional),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """
    Get user's conversations
    For authenticated users: returns their conversations
    For unauthenticated users: returns empty list
    
    Args:
        current_user: Current authenticated user (optional)
        db: Database session
        skip: Number of conversations to skip
        limit: Maximum number of conversations to return
        
        Returns:
            List of user's conversations ordered by last update
    """
    # If not authenticated, return empty list for guests
    if not current_user:
        return []
    
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()

    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    current_user: Optional[User] = Depends(get_current_active_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation with messages
    For authenticated users: can only access their own conversations
    For unauthenticated users (discovery mode): can access public discovery conversations
    
    Args:
        conversation_id: Conversation UUID
        current_user: Current authenticated user (optional)
        db: Database session
        
    Returns:
        Conversation with messages
    """
    try:
        # If authenticated, use standard auth check
        if current_user:
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
        else:
            # For guests (unauthenticated), return public discovery conversations
            # Guests can view conversations without a user_id (for discovery mode sessions)
            logger.info(f"Getting conversation {conversation_id} for guest (unauthenticated)")
            
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                (Conversation.user_id == None) | (Conversation.mode == DISCOVERY_MODE_ID)
            ).first()
            
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found or not accessible to guests")
                raise ConversationNotFound()
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
    
    # Check personality access
    if chat_request.mode not in current_user.subscribed_personalities:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not subscribed to this personality."
        )
    
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
                user_tier=_resolve_user_tier(current_user)
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
            # PHASE 3: PERSONALITY ROUTER - Determine accountability style
            accountability_style = None
            if PHASE_2B_AVAILABLE:
                try:
                    from app.services.personality_router import get_personality_router
                    
                    router = get_personality_router()
                    
                    # Get user's accountability style preference
                    user_preference = getattr(current_user, 'accountability_style', None)
                    
                    # Determine appropriate style based on context
                    routing_decision = router.determine_style(
                        user_preference=user_preference,
                        conversation_depth=new_depth if new_depth else None,
                        user_state=None
                    )
                    
                    accountability_style = routing_decision['style']
                    
                    logger.info(
                        f"Streaming personality routing: style={accountability_style}, "
                        f"reason={routing_decision['reason']}"
                    )
                    
                except Exception as e:
                    logger.error(f"Phase 3 personality routing error in streaming: {e}", exc_info=True)
            
            # Check if API key is configured
            if not settings.GROQ_API_KEY:
                error_msg = "GROQ_API_KEY not configured. Please set GROQ_API_KEY environment variable."
                logger.critical(error_msg)
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                return
            
            # Get streaming response (select model based on user tier)
            # Exclude the last message (current user message) from history to avoid duplicate
            conversation_history = conversation.messages[:-1] if conversation.messages else []
            
            # Use Groq service only (no fallback for now to simplify debugging)
            logger.info("Using Groq service for streaming...")
            ai_service = GroqService()
            
            try:
                response = await ai_service.get_streaming_response(
                    message=chat_request.message,
                    mode=chat_request.mode,
                    conversation_history=conversation_history,
                    user_tier=_resolve_user_tier(current_user),
                    accountability_style=accountability_style,  # Phase 3: Pass accountability style
                    conversation_depth=new_depth if new_depth else None,  # Phase 3: Pass conversation depth
                    silo_id=silo_id
                )
                logger.info("Successfully got streaming response from Groq service")
            except Exception as e:
                logger.error(f"Groq streaming service failed: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': f'Groq service failed: {str(e)}'})}\n\n"
                return
            
            # Stream the response
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
