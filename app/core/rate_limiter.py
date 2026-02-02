"""
IP-based Rate Limiter for Discovery Mode
Limits unauthenticated sessions to 5 messages per hour per IP
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# In-memory storage for rate limiting (IP -> (message_count, window_start))
# In production, use Redis for distributed rate limiting
_rate_limit_storage: Dict[str, Tuple[int, datetime]] = {}

# Discovery context storage (IP -> captured_name, captured_intent, message_history)
_discovery_context_storage: Dict[str, Dict[str, any]] = {}

# Configuration
MAX_MESSAGES_PER_HOUR = 5
RATE_LIMIT_WINDOW_HOURS = 1


def check_rate_limit(ip_address: str) -> Tuple[bool, int]:
    """
    Check if an IP address has exceeded the rate limit.
    
    Args:
        ip_address: The IP address to check
        
    Returns:
        Tuple of (is_allowed, remaining_messages)
        - is_allowed: True if the request should be allowed
        - remaining_messages: Number of messages remaining in the current window
    """
    now = datetime.utcnow()
    
    # Get current rate limit data for this IP
    if ip_address in _rate_limit_storage:
        count, window_start = _rate_limit_storage[ip_address]
        
        # Check if we're still in the same time window
        window_end = window_start + timedelta(hours=RATE_LIMIT_WINDOW_HOURS)
        
        if now < window_end:
            # Still in the same window
            if count >= MAX_MESSAGES_PER_HOUR:
                # Rate limit exceeded
                remaining = 0
                logger.warning(f"Rate limit exceeded for IP {ip_address}: {count}/{MAX_MESSAGES_PER_HOUR} messages")
                return False, remaining
            else:
                # Increment count
                _rate_limit_storage[ip_address] = (count + 1, window_start)
                remaining = MAX_MESSAGES_PER_HOUR - (count + 1)
                logger.debug(f"Rate limit check for IP {ip_address}: {count + 1}/{MAX_MESSAGES_PER_HOUR} messages")
                return True, remaining
        else:
            # Window expired, start new window
            _rate_limit_storage[ip_address] = (1, now)
            # Reset discovery context when window expires
            if ip_address in _discovery_context_storage:
                del _discovery_context_storage[ip_address]
                logger.debug(f"Discovery context reset for IP {ip_address}")
            remaining = MAX_MESSAGES_PER_HOUR - 1
            logger.debug(f"Rate limit window reset for IP {ip_address}")
            return True, remaining
    else:
        # First request from this IP
        _rate_limit_storage[ip_address] = (1, now)
        remaining = MAX_MESSAGES_PER_HOUR - 1
        logger.debug(f"First request from IP {ip_address}")
        return True, remaining


def get_discovery_context(ip_address: str) -> Dict[str, any]:
    """
    Get discovery context for an IP address.
    
    Args:
        ip_address: The IP address to check
        
    Returns:
        Dictionary with captured_name, captured_intent, and message_history
    """
    return _discovery_context_storage.get(ip_address, {
        "captured_name": None,
        "captured_intent": None,
        "message_history": [],
        "non_engagement_strikes": 0,
        "honest_attempt_strikes": 0,
        "repetition_count": 0
    })


def update_discovery_context(ip_address: str, metadata: Dict[str, Optional[str]], user_message: str):
    """
    Update discovery context for an IP address.
    
    Args:
        ip_address: The IP address
        metadata: Captured name and intent
        user_message: Current user message
    """
    if ip_address not in _discovery_context_storage:
        _discovery_context_storage[ip_address] = {
            "captured_name": None,
            "captured_intent": None,
            "message_history": [],
            "non_engagement_strikes": 0,
            "honest_attempt_strikes": 0,
            "repetition_count": 0
        }
    
    context = _discovery_context_storage[ip_address]
    
    # Update captured fields if present
    if metadata.get("captured_name"):
        context["captured_name"] = metadata["captured_name"]
    
    if metadata.get("captured_intent"):
        context["captured_intent"] = metadata["captured_intent"]
    
    # Add message to history (keep last 5 messages)
    context["message_history"].append(user_message)
    if len(context["message_history"]) > 5:
        context["message_history"] = context["message_history"][-5:]
    
    logger.debug(f"Updated discovery context for IP {ip_address}: "
                 f"name={context['captured_name']}, intent={context['captured_intent']}")


def clean_expired_entries():
    """
    Clean up expired entries from the rate limit storage.
    Should be called periodically (e.g., via a background task).
    """
    now = datetime.utcnow()
    expired_ips = []
    
    for ip_address, (count, window_start) in _rate_limit_storage.items():
        window_end = window_start + timedelta(hours=RATE_LIMIT_WINDOW_HOURS)
        if now >= window_end:
            expired_ips.append(ip_address)
    
    for ip_address in expired_ips:
        del _rate_limit_storage[ip_address]
        # Also clean up discovery context
        if ip_address in _discovery_context_storage:
            del _discovery_context_storage[ip_address]
        logger.debug(f"Cleaned up expired rate limit entry for IP {ip_address}")
    
    if expired_ips:
        logger.info(f"Cleaned up {len(expired_ips)} expired rate limit entries")


def get_rate_limit_info(ip_address: str) -> Dict[str, any]:
    """
    Get rate limit information for an IP address.
    
    Args:
        ip_address: The IP address to check
        
    Returns:
        Dictionary with rate limit info
    """
    now = datetime.utcnow()
    
    if ip_address in _rate_limit_storage:
        count, window_start = _rate_limit_storage[ip_address]
        window_end = window_start + timedelta(hours=RATE_LIMIT_WINDOW_HOURS)
        
        if now < window_end:
            remaining = MAX_MESSAGES_PER_HOUR - count
            seconds_until_reset = int((window_end - now).total_seconds())
            return {
                "messages_used": count,
                "messages_remaining": remaining,
                "limit": MAX_MESSAGES_PER_HOUR,
                "window_hours": RATE_LIMIT_WINDOW_HOURS,
                "seconds_until_reset": seconds_until_reset,
                "reset_at": window_end.isoformat()
            }
    
    return {
        "messages_used": 0,
        "messages_remaining": MAX_MESSAGES_PER_HOUR,
        "limit": MAX_MESSAGES_PER_HOUR,
        "window_hours": RATE_LIMIT_WINDOW_HOURS,
        "seconds_until_reset": RATE_LIMIT_WINDOW_HOURS * 3600,
        "reset_at": (now + timedelta(hours=RATE_LIMIT_WINDOW_HOURS)).isoformat()
    }
