"""
Personality Router Service

Handles dynamic selection and adaptation of accountability styles based on:
- User preferences
- Conversation depth
- User emotional state
- Context signals
"""

from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PersonalityRouter:
    """
    Routes to appropriate accountability style based on context
    """
    
    # Depth thresholds for adaptive routing
    HIGH_DEPTH_THRESHOLD = 0.5
    LOW_DEPTH_THRESHOLD = 0.3
    
    # Valid accountability styles
    VALID_STYLES = ['tactical', 'grace', 'analyst', 'adaptive']
    
    def __init__(self):
        """Initialize the personality router"""
        self.default_style = 'grace'  # Safe default
    
    def determine_style(
        self,
        user_preference: Optional[str] = None,
        conversation_depth: Optional[float] = None,
        user_state: Optional[str] = None,
        context_signals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Determine the appropriate accountability style based on context
        
        Args:
            user_preference: User's preferred accountability style
            conversation_depth: Current conversation depth (0.0-1.0)
            user_state: User's emotional state ('distressed', 'energized', 'neutral', etc.)
            context_signals: Additional context signals (goal status, recent activity, etc.)
            
        Returns:
            Dict with 'style', 'reason', and 'confidence' keys
        """
        # Validate user preference
        if user_preference and user_preference not in self.VALID_STYLES:
            logger.warning(f"Invalid user preference: {user_preference}, using default")
            user_preference = self.default_style
        
        # Priority 1: User's emotional state (override everything)
        if user_state:
            state_style = self._route_by_state(user_state)
            if state_style:
                return {
                    'style': state_style,
                    'reason': f'User state: {user_state}',
                    'confidence': 0.95,
                    'depth': conversation_depth
                }
        
        # Priority 2: Adaptive routing based on depth
        if user_preference == 'adaptive' and conversation_depth is not None:
            adaptive_style = self._route_by_depth(conversation_depth)
            return {
                'style': adaptive_style,
                'reason': f'Adaptive routing based on depth: {conversation_depth:.2f}',
                'confidence': 0.85,
                'depth': conversation_depth
            }
        
        # Priority 3: User preference (if not adaptive)
        if user_preference and user_preference != 'adaptive':
            # Still apply depth modulation for intensity
            intensity = self._calculate_intensity(conversation_depth) if conversation_depth else 1.0
            return {
                'style': user_preference,
                'reason': 'User preference',
                'confidence': 0.90,
                'depth': conversation_depth,
                'intensity': intensity
            }
        
        # Priority 4: Context signals
        if context_signals:
            context_style = self._route_by_context(context_signals)
            if context_style:
                return {
                    'style': context_style,
                    'reason': 'Context signals',
                    'confidence': 0.70,
                    'depth': conversation_depth
                }
        
        # Default: Use grace style (safest)
        return {
            'style': self.default_style,
            'reason': 'Default (no preference set)',
            'confidence': 0.60,
            'depth': conversation_depth
        }
    
    def _route_by_state(self, user_state: str) -> Optional[str]:
        """
        Route based on user's emotional state
        
        Args:
            user_state: User's emotional state
            
        Returns:
            Appropriate style or None
        """
        state_lower = user_state.lower()
        
        # Distressed, anxious, overwhelmed -> Grace
        if any(word in state_lower for word in ['distress', 'anxious', 'overwhelm', 'sad', 'depressed', 'struggling']):
            return 'grace'
        
        # Energized, motivated, excited -> Tactical
        if any(word in state_lower for word in ['energized', 'motivated', 'excited', 'pumped', 'ready']):
            return 'tactical'
        
        # Analytical, curious, questioning -> Analyst
        if any(word in state_lower for word in ['analytical', 'curious', 'wondering', 'thinking', 'analyzing']):
            return 'analyst'
        
        return None
    
    def _route_by_depth(self, depth: float) -> str:
        """
        Route based on conversation depth
        
        Args:
            depth: Conversation depth (0.0-1.0)
            
        Returns:
            Appropriate style
        """
        if depth > self.HIGH_DEPTH_THRESHOLD:
            # High depth - use grace for emotional safety
            return 'grace'
        elif depth < self.LOW_DEPTH_THRESHOLD:
            # Low depth - use tactical for efficiency
            return 'tactical'
        else:
            # Medium depth - use analyst for balanced approach
            return 'analyst'
    
    def _route_by_context(self, context_signals: Dict[str, Any]) -> Optional[str]:
        """
        Route based on context signals
        
        Args:
            context_signals: Dictionary of context signals
            
        Returns:
            Appropriate style or None
        """
        # Check for overdue goals (suggests need for accountability)
        if context_signals.get('overdue_goals', 0) > 2:
            return 'tactical'
        
        # Check for recent struggles (suggests need for support)
        if context_signals.get('recent_struggles', False):
            return 'grace'
        
        # Check for data-focused queries
        if context_signals.get('data_query', False):
            return 'analyst'
        
        return None
    
    def _calculate_intensity(self, depth: Optional[float]) -> float:
        """
        Calculate intensity modifier based on depth
        
        Args:
            depth: Conversation depth (0.0-1.0)
            
        Returns:
            Intensity modifier (0.5-1.0)
        """
        if depth is None:
            return 1.0
        
        # High depth -> lower intensity (be gentler)
        # Low depth -> higher intensity (be more direct)
        if depth > self.HIGH_DEPTH_THRESHOLD:
            return 0.6  # Gentle
        elif depth < self.LOW_DEPTH_THRESHOLD:
            return 1.0  # Full intensity
        else:
            return 0.8  # Moderate
    
    def get_style_instructions(
        self,
        style: str,
        depth: Optional[float] = None,
        intensity: Optional[float] = None
    ) -> str:
        """
        Get additional instructions for style application
        
        Args:
            style: The accountability style
            depth: Conversation depth
            intensity: Intensity modifier
            
        Returns:
            Additional instructions string
        """
        instructions = []
        
        # Add depth context
        if depth is not None:
            if depth > self.HIGH_DEPTH_THRESHOLD:
                instructions.append("The user is in a deep, vulnerable conversation. Prioritize emotional safety and support.")
            elif depth < self.LOW_DEPTH_THRESHOLD:
                instructions.append("This is a quick, transactional conversation. Be efficient and to the point.")
            else:
                instructions.append("This is a balanced conversation. Maintain your core style while being responsive.")
        
        # Add intensity modulation
        if intensity is not None and intensity < 1.0:
            if style == 'tactical':
                instructions.append(f"Moderate your directness (intensity: {intensity:.1f}). Be firm but gentler than usual.")
            elif style == 'analyst':
                instructions.append(f"Balance logic with empathy (intensity: {intensity:.1f}). Don't be overly clinical.")
        
        return "\n".join(instructions) if instructions else ""
    
    def should_switch_style(
        self,
        current_style: str,
        new_context: Dict[str, Any]
    ) -> bool:
        """
        Determine if style should be switched mid-conversation
        
        Args:
            current_style: Current accountability style
            new_context: New context information
            
        Returns:
            True if style should switch, False otherwise
        """
        # Only switch for critical state changes
        user_state = new_context.get('user_state')
        if user_state:
            state_lower = user_state.lower()
            
            # Switch to grace if user becomes distressed
            if current_style != 'grace' and any(word in state_lower for word in ['distress', 'anxious', 'overwhelm']):
                logger.info(f"Switching from {current_style} to grace due to user distress")
                return True
        
        # Generally maintain consistency within a conversation
        return False
    
    def log_routing_decision(
        self,
        user_id: str,
        decision: Dict[str, Any],
        conversation_id: Optional[str] = None
    ):
        """
        Log the routing decision for analytics
        
        Args:
            user_id: User ID
            decision: Routing decision dictionary
            conversation_id: Optional conversation ID
        """
        logger.info(
            f"Personality routing for user {user_id}: "
            f"style={decision['style']}, "
            f"reason={decision['reason']}, "
            f"confidence={decision['confidence']:.2f}, "
            f"depth={decision.get('depth', 'N/A')}, "
            f"conversation={conversation_id or 'N/A'}"
        )


# Singleton instance
_router_instance = None

def get_personality_router() -> PersonalityRouter:
    """Get or create the personality router singleton"""
    global _router_instance
    if _router_instance is None:
        _router_instance = PersonalityRouter()
    return _router_instance