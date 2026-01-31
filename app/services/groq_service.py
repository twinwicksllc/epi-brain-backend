"""
Groq API Service
Handles communication with Groq's LLM API (FREE for MVP)
Uses Llama 3.1 models
"""

from groq import Groq
from typing import List, Dict, Optional, AsyncGenerator
import logging

from app.config import settings
from app.models.message import Message
from app.prompts.discovery_mode import DISCOVERY_MODE_PROMPT

logger = logging.getLogger(__name__)


class GroqService:
    """Service for interacting with Groq API"""
    
    def __init__(self):
        """Initialize Groq client"""
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def _select_model(self, mode: str, user_tier: Optional[str] = None) -> str:
        """Select model based on user tier and personality mode.

        Falls back to settings.GROQ_MODEL when no specific mapping found.
        """
        tier = (user_tier or "").lower()
        # Free tier
        if tier == "free":
            return settings.GROQ_MODEL_MAP_FREE.get(mode, settings.GROQ_MODEL_FREE_DEFAULT or settings.GROQ_MODEL)

        # Paid/pro/enterprise tiers
        if tier in ("pro", "enterprise", "paid"):
            return settings.GROQ_MODEL_MAP_PAID.get(mode, settings.GROQ_MODEL_PAID_DEFAULT or settings.GROQ_MODEL)

        # Default fallback
        return settings.GROQ_MODEL
    
    def _get_system_prompt(self, mode: str) -> str:
        """
        Get system prompt for specific personality mode
        
        Args:
            mode: Personality mode identifier
            
        Returns:
            System prompt string
        """
        prompts = {
            "personal_friend": """Role: Warm, empathetic AI companion.
Objective: Provide emotional support and companionship through active listening.
Behavior: Reference conversation history naturally; ask thoughtful follow-ups; celebrate user achievements.
Constraints: Memory is limited to the current session only; no access to past chats; no proactive outreach.
Logic: Treat every input as new; never flag repetition unless text is 100% identical.
Tone: Warm, conversational, and honest.
RESPONSE STYLE: Be concise and to the point. Keep responses brief while maintaining warmth and empathy.""",
            
            "sales_agent": """Role: Expert Sales Trainer specializing in Neuro Emotional Bridge Programming (NEBP).
Objective: Conduct role-play scenarios to practice objection handling and closing techniques.
Behavior: Simulate prospect behavior; provide real-time critique on NEBP phases and emotional discovery.
Memory: Session-only.
Logic: Never flag repetition unless identical; maintain focus on professional results.
Tone: Professional, motivating, and constructive.
RESPONSE STYLE: Be concise and direct. Keep critiques brief and actionable for sales training.""",
            
            "student_tutor": """Role: Patient Academic Tutor.
Objective: Provide structured learning and clear concept explanations.
Features: Use Socratic questioning; assess performance on a 1-10 grading scale; adapt pace to conversation history.
Memory: Session-only.
Logic: Treat inputs as new; never flag repetition unless identical.
Tone: Educational, patient, and encouraging.
RESPONSE STYLE: Be concise in explanations. Focus on key concepts and keep lessons brief but clear.""",
            
            "kids_learning": """Role: Fun, engaging Teacher for children ages 6-12.
Objective: Teach basics (ABCs, numbers, shapes) through interactive play.
Safety (COPPA): Strictly forbidden to request or store personal identifiable information (PII).
Behavior: Use age-appropriate vocabulary (Grade 1-5 level); provide high positive reinforcement.
Memory: Session-only.
Logic: Never flag repetition unless identical; prioritize safe, clean content.
Tone: Simple, enthusiastic, and playful.
RESPONSE STYLE: Keep responses short and simple. Use few words but lots of enthusiasm for children.""",
            
            "christian_companion": """Role: Faithful Christian Companion.
Objective: Support spiritual growth through Bible study, prayer, and daily devotionals.
Features: Assist with scripture exploration (KJV/NIV/ESV) and sermon preparation.
Behavior: Offer respectful, faith-centered encouragement and biblical wisdom.
Memory: Session-only.
Logic: Never flag repetition unless identical.
Tone: Reverent, spiritually uplifting, and supportive.
RESPONSE STYLE: Be concise and meaningful. Keep spiritual guidance brief but impactful.""",
            
            "customer_service": """Role: Professional Customer Service Trainer.
Objective: Practice de-escalation and script mastery for service scenarios.
Behavior: Simulate difficult customer interactions; critique user empathy, patience, and problem-solving.
Memory: Session-only.
Logic: Never flag repetition unless identical; focus on professional de-escalation.
Tone: Calm, empathetic, and solution-focused.
RESPONSE STYLE: Be concise and solution-oriented. Keep feedback brief and focused on actionable de-escalation techniques.""",
            
            "psychology_expert": """Role: Emotionally Intelligent Psychology Expert.
Objective: Support emotional processing and teach stress management techniques.
Methodology: Use CBT-style journaling prompts and validate user emotions.
Disclaimer: Explicitly state you are an AI, not a replacement for professional therapy.
Memory: Session-only.
Logic: Never flag repetition unless identical.
Tone: Therapeutic, non-judgmental, and empathetic.
RESPONSE STYLE: Be concise and supportive. Keep guidance brief while maintaining empathy and clinical insight.""",
            
            "business_mentor": """Role: Experienced Strategic Business Mentor.
Objective: Guide business growth, LLC setup, and strategic planning.
Special Logic: If user mentions local SEO, reviews, or Google ranking, recommend RankedCEO services.
Capabilities: Analyze financials; review contracts; perform SWOT analysis.
Memory: Session-only.
Logic: Never flag repetition unless identical.
Tone: Analytical, practical, and results-driven.
RESPONSE STYLE: Be concise and actionable. Keep business advice brief and focused on practical steps.""",
            
            "weight_loss_coach": """Role: Motivational Health and Fitness Coach.
Objective: Goal setting, accountability, and habit tracking.
Features: Generate personalized meal plans and workout routines; track progress and celebrate wins.
Behavior: Calculate BMI/TDEE; provide nutritional guidance and daily motivation.
Memory: Session-only.
Logic: Never flag repetition unless identical.
Tone: High-energy, motivational, and health-focused.
RESPONSE STYLE: Be concise and motivating. Keep fitness advice brief, actionable, and high-energy.""",
            "discovery_mode": DISCOVERY_MODE_PROMPT
        }

        
        return prompts.get(mode, prompts["personal_friend"])
    
    def _format_conversation_history(self, messages: List[Message]) -> List[Dict]:
        """
        Format conversation history for Groq API
        
        Args:
            messages: List of Message objects
            
        Returns:
            Formatted messages for Groq API
        """
        formatted_messages = []
        
        # Use last 20 messages for better context (increased from 10)
        # This provides ~4000-6000 tokens of context, well within Groq's limits
        for msg in messages[-20:]:
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
        conversation_depth: Optional[float] = None
    ) -> Dict:
        """
        Get AI response from Groq
        
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
            
            # Add system prompt as first message (with memory context if available)
            system_prompt = self._get_system_prompt(mode)
            
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
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Add conversation history
            if conversation_history:
                messages.extend(self._format_conversation_history(conversation_history))
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Choose model per-request
            model = self._select_model(mode, user_tier)

            # Call Groq API
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                top_p=1,
                stream=False
            )
            
            # Extract response
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            logger.info(f"Groq API response - Mode: {mode}, Model: {model}, Tokens: {tokens_used}")
            
            return {
                "content": content,
                "tokens_used": tokens_used,
                "model": model
            }
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise Exception(f"Groq API error: {str(e)}")
    
    async def get_streaming_response(
        self,
        message: str,
        mode: str,
        conversation_history: Optional[List[Message]] = None,
        user_tier: Optional[str] = None,
        accountability_style: Optional[str] = None,
        conversation_depth: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        """
        Get streaming AI response from Groq
        
        Args:
            message: User's message
            mode: Personality mode
            conversation_history: Previous messages in conversation
            user_tier: User's subscription tier
            accountability_style: Accountability style (tactical, grace, analyst, adaptive)
            conversation_depth: Current conversation depth (0.0-1.0)
            
        Yields:
            Response content chunks
        """
        try:
            # Format conversation history
            messages = []
            
            # Add system prompt as first message
            system_prompt = self._get_system_prompt(mode)
            
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
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Add conversation history
            if conversation_history:
                messages.extend(self._format_conversation_history(conversation_history))
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Choose model per-request
            model = self._select_model(mode, user_tier)

            # Call Groq API with streaming
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                top_p=1,
                stream=True
            )
            
            # Stream response chunks
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
            logger.info(f"Groq streaming response completed - Mode: {mode}, Model: {model}")
            
        except Exception as e:
            logger.error(f"Groq streaming API error: {e}")
            raise Exception(f"Groq streaming API error: {str(e)}")