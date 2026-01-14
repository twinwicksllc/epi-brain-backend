"""
Conversation depth state manager with inertia and decay
"""

from datetime import datetime
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class ConversationDepthEngine:
    """
    Manages authoritative depth state for a conversation
    
    Implements:
    - Asymmetric inertia (faster going deeper, slower coming back up)
    - Temporal decay (depth decreases over time with inactivity)
    - Bounded depth (always between 0.0 and 1.0)
    """
    
    def __init__(self, initial_depth: float = 0.0, last_updated_at: datetime = None):
        """
        Initialize depth engine
        
        Args:
            initial_depth: Starting depth value (0.0-1.0)
            last_updated_at: When depth was last updated (defaults to now)
        """
        self.depth = max(0.0, min(1.0, initial_depth))
        self.last_updated_at = last_updated_at or datetime.utcnow()
        
        logger.debug(f"Initialized DepthEngine with depth={self.depth:.2f}")
    
    def update(self, turn_score: float) -> float:
        """
        Update depth based on new turn score
        
        Args:
            turn_score: Score from 0.0-1.0 representing this turn's depth
            
        Returns:
            New depth value after update
        """
        now = datetime.utcnow()
        elapsed_seconds = (now - self.last_updated_at).total_seconds()
        
        old_depth = self.depth
        
        # Apply temporal decay first
        decay_amount = settings.DEPTH_DECAY_RATE * elapsed_seconds
        self.depth = max(0.0, self.depth - decay_amount)
        
        if decay_amount > 0:
            logger.debug(f"Applied decay: {old_depth:.2f} -> {self.depth:.2f} ({elapsed_seconds:.1f}s elapsed)")
        
        # Asymmetric inertia - different speeds for going up vs down
        if turn_score > self.depth:
            # Going deeper - use faster alpha
            alpha = settings.DEPTH_UP_ALPHA
            direction = "deeper"
        else:
            # Coming back up - use slower alpha
            alpha = settings.DEPTH_DOWN_ALPHA
            direction = "lighter"
        
        # Update depth with inertia
        old_depth_before_update = self.depth
        self.depth += alpha * (turn_score - self.depth)
        
        # Clamp to valid range
        self.depth = max(0.0, min(1.0, self.depth))
        
        self.last_updated_at = now
        
        logger.info(
            f"Depth update: {old_depth_before_update:.2f} -> {self.depth:.2f} "
            f"(turn_score={turn_score:.2f}, direction={direction}, alpha={alpha})"
        )
        
        return self.depth
    
    def reset(self):
        """Reset depth to 0"""
        logger.info(f"Resetting depth from {self.depth:.2f} to 0.0")
        self.depth = 0.0
        self.last_updated_at = datetime.utcnow()
    
    def get_depth(self) -> float:
        """
        Get current depth with decay applied (without updating state)
        
        Returns:
            Current depth value with decay
        """
        now = datetime.utcnow()
        elapsed_seconds = (now - self.last_updated_at).total_seconds()
        
        # Apply decay without updating state
        decay_amount = settings.DEPTH_DECAY_RATE * elapsed_seconds
        decayed_depth = max(0.0, self.depth - decay_amount)
        
        return decayed_depth
    
    def get_state(self) -> dict:
        """
        Get complete engine state for debugging
        
        Returns:
            Dictionary with depth, last_updated, and decay info
        """
        now = datetime.utcnow()
        elapsed_seconds = (now - self.last_updated_at).total_seconds()
        current_depth = self.get_depth()
        
        return {
            'stored_depth': self.depth,
            'current_depth': current_depth,
            'last_updated_at': self.last_updated_at.isoformat(),
            'elapsed_seconds': elapsed_seconds,
            'decay_applied': self.depth - current_depth
        }