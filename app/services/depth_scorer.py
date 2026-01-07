"""
Hybrid depth scoring service using heuristics + LLM
"""

from typing import Dict, Optional
import re
import logging
from app.services.groq_service import GroqService
from app.config import settings

logger = logging.getLogger(__name__)


class DepthScorer:
    """Scores conversation turns for emotional/introspective depth"""
    
    def __init__(self):
        self.groq = GroqService()
        
        # Heuristic patterns for first-person reflection
        self.first_person_patterns = [
            r'\bI feel\b', r'\bI think\b', r'\bI believe\b',
            r'\bI\'m\b', r'\bI am\b', r'\bmy\b', r'\bme\b',
            r'\bI\'ve\b', r'\bI have\b', r'\bI\'d\b', r'\bI would\b'
        ]
        
        # Emotion vocabulary
        self.emotion_words = [
            'anxious', 'worried', 'scared', 'afraid', 'sad', 'depressed',
            'lonely', 'hurt', 'pain', 'struggle', 'difficult', 'hard',
            'confused', 'lost', 'overwhelmed', 'stressed', 'frustrated',
            'grateful', 'thankful', 'blessed', 'hopeful', 'peaceful',
            'vulnerable', 'open', 'honest', 'real', 'authentic',
            'empty', 'numb', 'broken', 'healing', 'growing'
        ]
        
        # Introspective/existential language
        self.introspective_words = [
            'why', 'meaning', 'purpose', 'identity', 'who am i',
            'what if', 'wondering', 'questioning', 'soul', 'heart',
            'journey', 'growth', 'change', 'transform', 'heal',
            'understand', 'realize', 'discover', 'learn', 'reflect'
        ]
    
    async def score_turn(
        self,
        user_message: str,
        assistant_message: Optional[str] = None,
        user_tier: Optional[str] = None
    ) -> Dict:
        """
        Score a conversation turn for depth
        
        Args:
            user_message: The user's message to score
            assistant_message: Optional assistant response (not currently used)
            
        Returns:
            {
                'score': float (0.0-1.0),
                'source': 'heuristic' | 'llm',
                'heuristic_score': float,
                'llm_score': float | None
            }
        """
        # Skip very short messages
        if len(user_message) < settings.DEPTH_MIN_MESSAGE_LENGTH:
            logger.debug(f"Message too short ({len(user_message)} chars), skipping depth scoring")
            return {
                'score': 0.0,
                'source': 'heuristic',
                'heuristic_score': 0.0,
                'llm_score': None
            }
        
        # Calculate heuristic score
        heuristic_score = self._heuristic_score(user_message)
        logger.debug(f"Heuristic score: {heuristic_score:.2f}")
        
        # Decide if we need LLM refinement
        use_llm = (
            heuristic_score > settings.DEPTH_LLM_THRESHOLD or
            len(user_message) > 120
        )
        
        if use_llm:
            logger.info(f"Using LLM scorer (heuristic={heuristic_score:.2f}, length={len(user_message)})")
            llm_score = await self._llm_score(user_message, user_tier=user_tier)
            final_score = 0.6 * heuristic_score + 0.4 * llm_score
            source = 'llm'
            logger.info(f"LLM score: {llm_score:.2f}, Final: {final_score:.2f}")
        else:
            llm_score = None
            final_score = heuristic_score
            source = 'heuristic'
            logger.debug(f"Using heuristic only: {final_score:.2f}")
        
        return {
            'score': max(0.0, min(1.0, final_score)),
            'source': source,
            'heuristic_score': heuristic_score,
            'llm_score': llm_score
        }
    
    def _heuristic_score(self, message: str) -> float:
        """
        Calculate heuristic depth score based on pattern matching
        
        Args:
            message: User message to score
            
        Returns:
            Score from 0.0 to 1.0
        """
        message_lower = message.lower()
        score = 0.0
        
        # 1. First-person reflection density (0-0.3)
        first_person_count = sum(
            len(re.findall(pattern, message_lower, re.IGNORECASE))
            for pattern in self.first_person_patterns
        )
        first_person_score = min(0.3, first_person_count * 0.05)
        score += first_person_score
        
        # 2. Emotion vocabulary (0-0.3)
        emotion_count = sum(
            1 for word in self.emotion_words
            if word in message_lower
        )
        emotion_score = min(0.3, emotion_count * 0.1)
        score += emotion_score
        
        # 3. Introspective language (0-0.3)
        introspective_count = sum(
            1 for word in self.introspective_words
            if word in message_lower
        )
        introspective_score = min(0.3, introspective_count * 0.1)
        score += introspective_score
        
        # 4. Question depth (0-0.1)
        deep_questions = ['why', 'how do i', 'what should i', 'how can i']
        if any(q in message_lower for q in deep_questions):
            score += 0.1
        
        logger.debug(
            f"Heuristic breakdown - First-person: {first_person_score:.2f}, "
            f"Emotion: {emotion_score:.2f}, Introspective: {introspective_score:.2f}"
        )
        
        return min(1.0, score)
    
    async def _llm_score(self, message: str, user_tier: Optional[str] = None) -> float:
        """
        Use LLM to score message depth
        
        Args:
            message: User message to score
            
        Returns:
            Score from 0.0 to 1.0
        """
        prompt = f"""Rate the emotional or introspective depth of the following user message.
0.0 = casual or transactional
1.0 = deeply introspective or vulnerable

User message:
"{message}"

Respond with only a number between 0.0 and 1.0."""

        try:
            response = await self.groq.get_response(
                message=prompt,
                mode="personal_friend",  # Use any mode, doesn't matter for scoring
                conversation_history=[],
                user_tier=user_tier
            )
            
            # Extract number from response
            content = response['content'].strip()
            
            # Try to extract just the number
            # Handle responses like "0.75" or "The depth is 0.75"
            import re
            number_match = re.search(r'(\d+\.?\d*)', content)
            if number_match:
                score = float(number_match.group(1))
            else:
                score = float(content)
            
            # Clamp to valid range
            score = max(0.0, min(1.0, score))
            logger.info(f"LLM scored message as {score:.2f}")
            return score
            
        except Exception as e:
            # Fail closed - return conservative score
            logger.error(f"LLM scoring failed: {e}, using fallback score 0.5")
            return 0.5