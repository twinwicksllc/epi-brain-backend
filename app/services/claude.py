"""
Claude API Service
Handles communication with Anthropic's Claude API
"""

import anthropic
from typing import List, Dict, Optional
import logging

from app.config import settings
from app.models.message import Message
from app.prompts.discovery_mode import get_discovery_prompt

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for interacting with Claude API"""
    
    def __init__(self):
        """Initialize Claude client"""
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
    
    def _get_system_prompt(self, mode: str, silo_id: Optional[str] = None) -> str:
        """
        Get system prompt for specific personality mode
        
        Args:
            mode: Personality mode identifier
            
        Returns:
            System prompt string
        """
        prompts = {
            "personal_friend": """You are a warm, empathetic personal friend. Your role is to:
- Provide emotional support and companionship
- Listen without judgment
- Remember previous conversations and user preferences
- Ask thoughtful follow-up questions
- Celebrate user achievements
- Be available 24/7 for daily check-ins
- Create genuine emotional connections

Tone: Warm, friendly, supportive, and conversational.""",
            
            "sales_agent": """You are an expert sales trainer specializing in NEBP (Neuro Emotional Bridge Programming). Your role is to:
- Role-play customer conversations
- Teach NEBP methodology
- Practice objection handling
- Provide real-time feedback on sales approaches
- Help improve closing techniques
- Analyze sales scenarios

Tone: Professional, constructive, motivating, and results-oriented.""",
            
            "student_tutor": """You are a patient, knowledgeable tutor. Your role is to:
- Provide structured learning experiences
- Grade performance on a 1-10 scale
- Track learning progress
- Explain concepts clearly
- Adapt to student's learning pace
- Provide encouragement and constructive feedback

Tone: Patient, educational, encouraging, and clear.""",
            
            "kids_learning": """You are a fun, engaging teacher for young children. Your role is to:
- Teach ABCs, numbers, colors, and shapes
- Make learning fun and interactive
- Use simple, age-appropriate language
- Provide positive reinforcement
- Keep content safe and educational
- Encourage curiosity and exploration

Tone: Enthusiastic, simple, encouraging, and playful.""",
            
            "christian_companion": """You are a faithful Christian companion. Your role is to:
- Provide prayer support and guidance
- Help with Bible study and scripture exploration
- Assist with sermon preparation
- Offer daily devotionals
- Support spiritual growth
- Provide faith-based encouragement

Tone: Respectful, faith-centered, encouraging, and spiritually uplifting.""",
            
            "customer_service": """You are a professional customer service trainer. Your role is to:
- Practice difficult customer scenarios
- Teach de-escalation techniques
- Improve professional communication
- Handle technical support situations
- Provide feedback on customer interactions
- Build empathy and patience

Tone: Professional, calm, empathetic, and solution-focused.""",
            
            "psychology_expert": """You are an emotionally intelligent psychology expert. Your role is to:
- Practice deep listening and empathy
- Support emotional processing
- Teach stress management techniques
- Guide personal growth
- Validate emotions
- Provide coping strategies

Tone: Therapeutic, non-judgmental, empathetic, and supportive.
Note: You are not a replacement for professional therapy.""",
            
            "business_mentor": """You are an experienced business mentor. Your role is to:
- Guide business growth and strategy
- Provide LLC/Corp setup guidance
- Analyze business financials
- Review contracts and agreements
- Offer marketing strategies
- Connect to RankedCEO services when relevant

Tone: Strategic, analytical, practical, and results-driven.""",
            
            "weight_loss_coach": """You are a motivational weight loss coach. Your role is to:
            - Set realistic health goals
            - Create personalized meal plans
            - Design workout routines
            - Provide daily accountability
            - Track progress and celebrate wins
            - Offer nutritional guidance
            - Maintain motivation

            Tone: Motivational, supportive, health-focused, and encouraging.""",
            "discovery_mode": get_discovery_prompt(silo_id)
        }
        
        return prompts.get(mode, prompts["personal_friend"])
    
    def _format_conversation_history(self, messages: List[Message]) -> List[Dict]:
        """
        Format conversation history for Claude API
        
        Args:
            messages: List of Message objects
            
        Returns:
            Formatted messages for Claude API
        """
        formatted_messages = []
        
        for msg in messages[-10:]:  # Last 10 messages for context
            if msg.role.value in ["user", "assistant"]:
                formatted_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        return formatted_messages
    
    async def get_response(
        self,
        message: str,
        mode: str,
        conversation_history: Optional[List[Message]] = None,
        user_tier: Optional[str] = None,
        memory_context: Optional[str] = None,
        accountability_style: Optional[str] = None,
        conversation_depth: Optional[float] = None,
        silo_id: Optional[str] = None
    ) -> Dict:
        """
        Get AI response from Claude
        
        Args:
            message: User's message
            mode: Personality mode
            conversation_history: Previous messages in conversation
            user_tier: User's subscription tier
            memory_context: User's memory context (injected into system prompt)
            accountability_style: Accountability style (tactical, grace, analyst, adaptive)
            conversation_depth: Current conversation depth (0.0-1.0)
            
        Returns:
            Dictionary with response content and metadata
        """
        try:
            # Format conversation history
            messages = []
            if conversation_history:
                messages = self._format_conversation_history(conversation_history)
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Get system prompt
            system_prompt = self._get_system_prompt(mode, silo_id=silo_id)
            
            # Inject accountability style into system prompt (Phase 3)
            if accountability_style:
                try:
                    from app.prompts.accountability_styles import get_accountability_prompt
                    accountability_prompt = get_accountability_prompt(accountability_style, conversation_depth)
                    system_prompt = f"""{system_prompt}

<accountability_style>
{accountability_prompt}
</accountability_style>

Apply the accountability style above when providing support and guidance. Maintain consistency with this style throughout the conversation."""
                except Exception as e:
                    logger.error(f"Error loading accountability style: {e}")
            
            # Inject memory context into system prompt
            if memory_context:
                system_prompt = f"""{system_prompt}

<user_memory>
{memory_context}
</user_memory>

Use the user memory above to personalize your responses. Apply preferences naturally without explicitly mentioning them unless relevant to the conversation."""
            
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages
            )
            
            # Extract response
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            logger.info(f"Claude API response - Mode: {mode}, Tokens: {tokens_used}")
            
            return {
                "content": content,
                "tokens_used": tokens_used,
                "model": self.model
            }
            
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise Exception(f"Claude API error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in Claude service: {e}")
            raise Exception(f"Error getting AI response: {str(e)}")