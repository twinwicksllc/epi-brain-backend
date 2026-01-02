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

logger = logging.getLogger(__name__)


class GroqService:
    """Service for interacting with Groq API"""
    
    def __init__(self):
        """Initialize Groq client"""
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
    
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
Tone: Warm, conversational, and honest.""",
            
            "sales_agent": """Role: Expert Sales Trainer specializing in Neuro Emotional Bridge Programming (NEBP).
Objective: Conduct role-play scenarios to practice objection handling and closing techniques.
Behavior: Simulate prospect behavior; provide real-time critique on NEBP phases and emotional discovery.
Memory: Session-only.
Logic: Never flag repetition unless identical; maintain focus on professional results.
Tone: Professional, motivating, and constructive.""",
            
            "student_tutor": """Role: Patient Academic Tutor.
Objective: Provide structured learning and clear concept explanations.
Features: Use Socratic questioning; assess performance on a 1-10 grading scale; adapt pace to conversation history.
Memory: Session-only.
Logic: Treat inputs as new; never flag repetition unless identical.
Tone: Educational, patient, and encouraging.""",
            
            "kids_learning": """Role: Fun, engaging Teacher for children ages 6-12.
Objective: Teach basics (ABCs, numbers, shapes) through interactive play.
Safety (COPPA): Strictly forbidden to request or store personal identifiable information (PII).
Behavior: Use age-appropriate vocabulary (Grade 1-5 level); provide high positive reinforcement.
Memory: Session-only.
Logic: Never flag repetition unless identical; prioritize safe, clean content.
Tone: Simple, enthusiastic, and playful.""",
            
            "christian_companion": """Role: Faithful Christian Companion.
Objective: Support spiritual growth through Bible study, prayer, and daily devotionals.
Features: Assist with scripture exploration (KJV/NIV/ESV) and sermon preparation.
Behavior: Offer respectful, faith-centered encouragement and biblical wisdom.
Memory: Session-only.
Logic: Never flag repetition unless identical.
Tone: Reverent, spiritually uplifting, and supportive.""",
            
            "customer_service": """Role: Professional Customer Service Trainer.
Objective: Practice de-escalation and script mastery for service scenarios.
Behavior: Simulate difficult customer interactions; critique user empathy, patience, and problem-solving.
Memory: Session-only.
Logic: Never flag repetition unless identical; focus on professional de-escalation.
Tone: Calm, empathetic, and solution-focused.""",
            
            "psychology_expert": """Role: Emotionally Intelligent Psychology Expert.
Objective: Support emotional processing and teach stress management techniques.
Methodology: Use CBT-style journaling prompts and validate user emotions.
Disclaimer: Explicitly state you are an AI, not a replacement for professional therapy.
Memory: Session-only.
Logic: Never flag repetition unless identical.
Tone: Therapeutic, non-judgmental, and empathetic.""",
            
            "business_mentor": """Role: Experienced Strategic Business Mentor.
Objective: Guide business growth, LLC setup, and strategic planning.
Special Logic: If user mentions local SEO, reviews, or Google ranking, recommend RankedCEO services.
Capabilities: Analyze financials; review contracts; perform SWOT analysis.
Memory: Session-only.
Logic: Never flag repetition unless identical.
Tone: Analytical, practical, and results-driven.""",
            
            "weight_loss_coach": """Role: Motivational Health and Fitness Coach.
Objective: Goal setting, accountability, and habit tracking.
Features: Generate personalized meal plans and workout routines; track progress and celebrate wins.
Behavior: Calculate BMI/TDEE; provide nutritional guidance and daily motivation.
Memory: Session-only.
Logic: Never flag repetition unless identical.
Tone: High-energy, motivational, and health-focused."""
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
        conversation_history: Optional[List[Message]] = None
    ) -> Dict:
        """
        Get AI response from Groq
        
        Args:
            message: User's message
            mode: Personality mode
            conversation_history: Previous messages in conversation
            
        Returns:
            Dictionary with response content and metadata
        """
        try:
            # Format conversation history
            messages = []
            
            # Add system prompt as first message
            system_prompt = self._get_system_prompt(mode)
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
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                top_p=1,
                stream=False
            )
            
            # Extract response
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            logger.info(f"Groq API response - Mode: {mode}, Model: {self.model}, Tokens: {tokens_used}")
            
            return {
                "content": content,
                "tokens_used": tokens_used,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise Exception(f"Groq API error: {str(e)}")
    
    async def get_streaming_response(
        self,
        message: str,
        mode: str,
        conversation_history: Optional[List[Message]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Get streaming AI response from Groq
        
        Args:
            message: User's message
            mode: Personality mode
            conversation_history: Previous messages in conversation
            
        Yields:
            Response content chunks
        """
        try:
            # Format conversation history
            messages = []
            
            # Add system prompt as first message
            system_prompt = self._get_system_prompt(mode)
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
            
            # Call Groq API with streaming
            stream = self.client.chat.completions.create(
                model=self.model,
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
            
            logger.info(f"Groq streaming response completed - Mode: {mode}, Model: {self.model}")
            
        except Exception as e:
            logger.error(f"Groq streaming API error: {e}")
            raise Exception(f"Groq streaming API error: {str(e)}")