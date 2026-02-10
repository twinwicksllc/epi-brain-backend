"""
Groq API Service — Neural-Electronic Brain Pipeline (NEBP)

Implements a 4-layer pipeline:
  Layer 1: Neural Input (STT)    — whisper-large-v3-turbo @ 400 RPM
  Layer 2: Buffer (Pre-Processing) — llama-3.1-8b-instant (stutter clean + intent fmt)
  Layer 3: Reasoning Core        — llama-3.3-70b-versatile / openai/gpt-oss-120b
  Layer 4: Safety Gateway        — llama-guard-4-12b (content moderation)
"""

from groq import Groq
from typing import List, Dict, Optional, AsyncGenerator
import logging

from app.config import settings
from app.models.message import Message
from app.prompts.discovery_mode import get_discovery_prompt

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────
# Layer 2: Buffer / Pre-Processing prompt
# ────────────────────────────────────────────────────────────────
import re

NEBP_BUFFER_SYSTEM_PROMPT = """You are a transcript pre-processor inside an AI
pipeline. Your ONLY job is to take a raw voice transcript and return a single
cleaned sentence (or short paragraph) that:
1. Removes stutters, filler words (um, uh, like, you know), and false starts.
2. Fixes obvious mis-transcriptions when context makes the intent clear.
3. Preserves the user's original meaning and tone — do NOT add, remove, or
   editorialize any intent.
4. CRITICAL: If the text is already clear and contains NO stutters, fillers, or
   false starts, return the input EXACTLY as provided without changing a single
   character.
5. Returns ONLY the cleaned text. No commentary, no labels, no markdown."""

# Stutter pattern detection for conditional bypass
STUTTER_PATTERNS = [
    r'\b(um|uh|er|ah|hmm|like|you know|basically|literally|honestly|right|so)\b',
    r'\b(\w+)\s+\1\b',  # Repeated words
    r'\w+\s+\.\.\.',  # Trailing ellipsis
    r'\b(yeah|yep|nope|kinda|sorta|gonna|wanna|gotta)\b',  # Informal/unstable speech
]

def _has_stutter_patterns(text: str) -> bool:
    """Detect if text contains characteristic stutter/filler patterns."""
    text_lower = text.lower()
    for pattern in STUTTER_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


class GroqService:
    """Service for interacting with Groq API — full NEBP pipeline"""
    
    def __init__(self):
        """Initialize Groq client with NEBP layer references"""
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        # NEBP layer models (read from config for env-var override)
        self.stt_model = settings.NEBP_STT_MODEL          # Layer 1
        self.buffer_model = settings.NEBP_BUFFER_MODEL     # Layer 2
        self.reasoning_model = settings.NEBP_REASONING_MODEL  # Layer 3
        self.safety_model = settings.NEBP_SAFETY_MODEL     # Layer 4

    # ────────────────────────────────────────────────────────────────
    # Layer 2: Buffer / Pre-Processing
    # ────────────────────────────────────────────────────────────────
    async def _buffer_preprocess(self, raw_text: str, is_voice: bool = False) -> str:
        """NEBP Layer 2 — clean stutters and format intent via a fast small model.

        Only executes if:
        - is_voice=True (explicitly marked as voice input), OR
        - Text contains characteristic stutter/filler patterns

        If the buffer is disabled or the call fails, returns the original text so
        the pipeline is never blocked.

        Args:
            raw_text: Input text to clean
            is_voice: True if input came from voice/STT, False if text input
        """
        if not settings.NEBP_BUFFER_ENABLED:
            return raw_text

        # Conditional bypass: only process if voice OR stutter patterns detected
        has_stutters = _has_stutter_patterns(raw_text)
        should_process = is_voice or has_stutters

        if not should_process:
            logger.info(f"[NEBP L2-Buffer] bypass (not voice, no stutter patterns) - {len(raw_text)} chars passed through")
            return raw_text

        try:
            response = self.client.chat.completions.create(
                model=self.buffer_model,
                messages=[
                    {"role": "system", "content": NEBP_BUFFER_SYSTEM_PROMPT},
                    {"role": "user", "content": raw_text},
                ],
                temperature=0.0,
                max_tokens=settings.NEBP_BUFFER_MAX_TOKENS,
                stream=False,
            )
            cleaned = response.choices[0].message.content.strip()
            if cleaned:
                logger.info(f"[NEBP L2-Buffer] processed ({len(raw_text)}->{len(cleaned)} chars, is_voice={is_voice}, has_stutters={has_stutters})")
                return cleaned
            return raw_text
        except Exception as e:
            logger.warning(f"[NEBP L2-Buffer] pre-processing failed, using raw text: {e}")
            return raw_text

    # ────────────────────────────────────────────────────────────────
    # Layer 4: Safety Gateway
    # ────────────────────────────────────────────────────────────────
    async def _safety_gate(self, ai_response: str, user_message: str = "") -> Dict:
        """NEBP Layer 4 — run llama-guard on the AI response before returning.

        Returns a dict with:
          - safe (bool): True if content passed moderation
          - flagged_categories (list[str]): any categories flagged
          - original_response (str): original AI text
          - response (str): the text to actually return (replaced if unsafe)
        """
        result = {
            "safe": True,
            "flagged_categories": [],
            "original_response": ai_response,
            "response": ai_response,
        }

        if not settings.NEBP_SAFETY_ENABLED:
            return result

        try:
            guard_response = self.client.chat.completions.create(
                model=self.safety_model,
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": ai_response},
                ],
                temperature=0.0,
                max_tokens=128,
                stream=False,
            )
            verdict = guard_response.choices[0].message.content.strip().lower()
            logger.info(f"[NEBP L4-Safety] verdict: {verdict}")

            # llama-guard returns 'safe' or 'unsafe\n<categories>'
            if verdict.startswith("unsafe"):
                lines = verdict.split("\n")
                categories = [l.strip() for l in lines[1:] if l.strip()] if len(lines) > 1 else ["unspecified"]
                result["safe"] = False
                result["flagged_categories"] = categories
                result["response"] = (
                    "I want to make sure I’m being helpful and safe. "
                    "Let me rephrase my response in a more appropriate way. "
                    "Could you tell me more about what you’re looking for so I can assist you better?"
                )
                logger.warning(f"[NEBP L4-Safety] BLOCKED response, categories={categories}")
        except Exception as e:
            # Safety gate must never block the pipeline — log and pass through
            logger.warning(f"[NEBP L4-Safety] guard check failed, passing through: {e}")

        return result

    # ────────────────────────────────────────────────────────────────
    # Layer 1: Neural Input (STT)  — exposed for voice endpoint
    # ────────────────────────────────────────────────────────────────
    async def transcribe_audio(self, audio_file, language: str = "en") -> str:
        """NEBP Layer 1 — Speech-to-text using whisper-large-v3-turbo on Groq.

        Args:
            audio_file: file-like object (e.g. UploadFile.file)
            language: ISO-639-1 language code

        Returns:
            Raw transcript text (feed into Layer 2 buffer next).
        """
        try:
            transcription = self.client.audio.transcriptions.create(
                model=self.stt_model,
                file=audio_file,
                language=language,
                response_format="text",
            )
            logger.info(f"[NEBP L1-STT] transcribed {len(transcription)} chars using {self.stt_model}")
            return transcription
        except Exception as e:
            logger.error(f"[NEBP L1-STT] transcription failed: {e}")
            raise

    # ────────────────────────────────────────────────────────────────
    # Model selection  (Layer 3 mapping)
    # ────────────────────────────────────────────────────────────────
    def _select_model(self, mode: str, user_tier: Optional[str] = None) -> str:
        """Select Layer 3 reasoning model based on user tier and personality mode.

        Falls back to settings.GROQ_MODEL when no specific mapping found.
        CRITICAL: OpenAI-hosted models on Groq use the openai/ prefix.
        """
        tier = (user_tier or "").lower()
        # Free tier
        if tier == "free":
            return settings.GROQ_MODEL_MAP_FREE.get(mode, settings.GROQ_MODEL_FREE_DEFAULT or settings.GROQ_MODEL)

        # Paid/pro/enterprise tiers
        if tier in ("pro", "enterprise", "paid", "premium"):
            return settings.GROQ_MODEL_MAP_PAID.get(mode, settings.GROQ_MODEL_PAID_DEFAULT or settings.GROQ_MODEL)

        # Default fallback
        return settings.GROQ_MODEL
    
    def _get_system_prompt(self, mode: str, silo_id: Optional[str] = None) -> str:
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
            "discovery_mode": get_discovery_prompt(silo_id)
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
        conversation_depth: Optional[float] = None,
        silo_id: Optional[str] = None
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
            # ── NEBP Layer 2: Buffer pre-processing ──────────────
            processed_message = await self._buffer_preprocess(message)

            # Format conversation history
            messages = []
            
            # Add system prompt as first message (with memory context if available)
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
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Add conversation history
            if conversation_history:
                messages.extend(self._format_conversation_history(conversation_history))
            
            # Add current (buffer-cleaned) message
            messages.append({
                "role": "user",
                "content": processed_message
            })
            
            # ── NEBP Layer 3: Reasoning Core ─────────────────────
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
            
            logger.info(f"[NEBP L3-Reasoning] Mode: {mode}, Model: {model}, Tokens: {tokens_used}")

            # ── NEBP Layer 4: Safety Gateway ─────────────────────
            safety_result = await self._safety_gate(content, user_message=processed_message)
            final_content = safety_result["response"]

            return {
                "content": final_content,
                "tokens_used": tokens_used,
                "model": model,
                "nebp_buffer_applied": (processed_message != message),
                "nebp_safety_passed": safety_result["safe"],
                "nebp_safety_categories": safety_result["flagged_categories"],
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
        conversation_depth: Optional[float] = None,
        silo_id: Optional[str] = None
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
            # ── NEBP Layer 2: Buffer pre-processing ──────────────
            processed_message = await self._buffer_preprocess(message)

            # Format conversation history
            messages = []
            
            # Add system prompt as first message
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
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Add conversation history
            if conversation_history:
                messages.extend(self._format_conversation_history(conversation_history))
            
            # Add current (buffer-cleaned) message
            messages.append({
                "role": "user",
                "content": processed_message
            })
            
            # ── NEBP Layer 3: Reasoning Core ─────────────────────
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
            
            # Collect full response for safety gate while streaming chunks
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    yield chunk.choices[0].delta.content
            
            logger.info(f"[NEBP L3-Reasoning] streaming done - Mode: {mode}, Model: {model}")

            # ── NEBP Layer 4: Safety Gateway (post-stream audit) ─
            # For streaming we run the safety gate AFTER all chunks are yielded.
            # If unsafe, yield a corrective follow-up message.
            safety_result = await self._safety_gate(full_response, user_message=processed_message)
            if not safety_result["safe"]:
                logger.warning(f"[NEBP L4-Safety] streaming response flagged, appending correction")
                yield f"\n\n---\n{safety_result['response']}"
            
        except Exception as e:
            logger.error(f"Groq streaming API error: {e}")
            raise Exception(f"Groq streaming API error: {str(e)}")