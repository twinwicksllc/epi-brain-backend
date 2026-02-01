"""
Discovery Mode Extraction Service
Implements LLM-first validation and contextual understanding for name and intent capture.
Replaces simple regex matching with AI-driven extraction and engagement assessment.
"""

import json
import logging
from typing import Dict, Optional, Tuple
from groq import Groq

logger = logging.getLogger(__name__)


class DiscoveryExtractionService:
    """
    Service for LLM-first name and intent validation in Discovery Mode.
    
    Features:
    - Contextual name validation (not just length checks)
    - Engagement quality assessment (honest vs. not trying)
    - Correction detection and handling
    - Dynamic persona-driven responses
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Initialize the extraction service.
        
        Args:
            groq_api_key: API key for Groq. If None, will attempt to use environment variable.
        """
        import os
        key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY not provided and not in environment")
        self.client = Groq(api_key=key)
    
    async def validate_and_extract_name(
        self,
        user_input: str,
        previous_name: Optional[str] = None,
        conversation_history: Optional[list] = None
    ) -> Dict[str, any]:
        """
        Validate if user input is a plausible name using LLM-first approach.
        
        Args:
            user_input: User's response
            previous_name: Previously captured name (if user correcting)
            conversation_history: List of previous messages for context
            
        Returns:
            Dictionary with:
            - is_name: bool - whether input is plausible name
            - name_value: Optional[str] - extracted name if valid
            - is_correction: bool - whether user is correcting previous name
            - contextual_response: str - how to respond (if not a name)
            - confidence: float - confidence score (0.0-1.0)
        """
        prompt = self._build_name_validation_prompt(user_input, previous_name)
        
        try:
            response = self.client.messages.create(
                model="mixtral-8x7b-32768",  # Using Groq's fast model
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse LLM response
            parsed = self._parse_name_validation_response(result_text, user_input)
            return parsed
            
        except Exception as e:
            logger.error(f"Error in name validation: {e}")
            # Fallback: basic validation
            return self._fallback_name_validation(user_input, previous_name)
    
    async def validate_and_extract_intent(
        self,
        user_input: str,
        captured_name: Optional[str] = None,
        conversation_history: Optional[list] = None
    ) -> Dict[str, any]:
        """
        Validate and extract intent using LLM.
        
        Args:
            user_input: User's response
            captured_name: Name already captured (for context)
            conversation_history: Previous messages
            
        Returns:
            Dictionary with:
            - is_intent: bool - whether valid intent detected
            - intent_value: Optional[str] - extracted intent
            - contextual_response: str - how to respond
            - confidence: float - confidence score (0.0-1.0)
        """
        prompt = self._build_intent_validation_prompt(user_input, captured_name)
        
        try:
            response = self.client.messages.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            parsed = self._parse_intent_validation_response(result_text, user_input)
            return parsed
            
        except Exception as e:
            logger.error(f"Error in intent validation: {e}")
            return self._fallback_intent_validation(user_input)
    
    async def assess_engagement_quality(
        self,
        user_input: str,
        conversation_turn: int = 1,
        previous_inputs: Optional[list] = None
    ) -> Dict[str, any]:
        """
        Assess whether user is genuinely engaged or clearly not trying.
        
        Args:
            user_input: Current user message
            conversation_turn: Which turn of conversation (1, 2, 3...)
            previous_inputs: List of previous user inputs
            
        Returns:
            Dictionary with:
            - is_engaged: bool - user is genuinely trying
            - is_honest_attempt: bool - user is honestly trying but struggling
            - is_non_engagement: bool - user is clearly not trying
            - strike_weight: int - weight of this non-engagement (1-3)
                - 1 = minor (user is trying but being playful)
                - 2 = moderate (user seems dismissive but could recover)
                - 3 = severe (user is clearly wasting time)
            - recommendation: str - how to respond
        """
        prompt = self._build_engagement_assessment_prompt(
            user_input,
            conversation_turn,
            previous_inputs
        )
        
        try:
            response = self.client.messages.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,  # Lower temp for more consistent assessment
                max_tokens=400
            )
            
            result_text = response.choices[0].message.content.strip()
            parsed = self._parse_engagement_response(result_text)
            return parsed
            
        except Exception as e:
            logger.error(f"Error in engagement assessment: {e}")
            return self._fallback_engagement_assessment(user_input)
    
    def _build_name_validation_prompt(
        self,
        user_input: str,
        previous_name: Optional[str] = None
    ) -> str:
        """Build prompt for name validation."""
        correction_context = ""
        if previous_name:
            correction_context = f"\nPreviously captured name was: '{previous_name}'\nDetermine if user is correcting this."
        
        return f"""You are an expert at understanding human communication. 
Your task: Determine if the user's input is a plausible name.

User input: "{user_input}"{correction_context}

Analyze this input and respond with a JSON object:
{{
  "is_name": <true if plausible name, false if greeting/nonsense/sentence>,
  "extracted_name": "<the name if is_name is true, otherwise null>",
  "is_correction": <true if correcting previous name>,
  "input_type": "<one of: name | greeting | nonsense | sentence | playful_nonsense>",
  "confidence": <0.0 to 1.0>,
  "contextual_response": "<how to respond if NOT a name - warm, conversational, no length validation mentioned>"
}}

Examples of contextual responses:
- For "Skinna marinka...": "That's a catchy tune! But I'd love to know what to actually call you. What's your name?"
- For "Hey there": "Hey! Great to connect. What's your name?"
- For "ABC": "Got it - those are your initials. What's your full first name I can use?"

DO NOT focus on length. Focus on: Is this person actually giving me their name?"""
    
    def _build_intent_validation_prompt(
        self,
        user_input: str,
        captured_name: Optional[str] = None
    ) -> str:
        """Build prompt for intent validation."""
        name_context = f" (Name: {captured_name})" if captured_name else ""
        
        return f"""You are an expert at understanding human needs and intentions.
Your task: Determine if the user's input reveals their intent/reason for seeking help.

User input: "{user_input}"{name_context}

Respond with a JSON object:
{{
  "is_intent": <true if valid intent detected>,
  "extracted_intent": "<specific reason they're here, or null>",
  "intent_category": "<one of: emotional_health | productivity | relationships | health_fitness | learning | career | other>",
  "confidence": <0.0 to 1.0>,
  "contextual_response": "<how to respond if NOT a clear intent - warm follow-up>"
}}

A valid intent is when the user indicates WHY they're here:
- "I need help with anxiety"
- "I want to improve my confidence"
- "I'm struggling with stress management"

An invalid intent is:
- Generic responses that don't indicate need: "I don't know" "Maybe?" "Whatever"
- Deflections: "Ask me later" "Not sure yet"
- Nonsense: "Purple elephants" "The moon is round"

Be conversational in contextual_response - no templates."""
    
    def _build_engagement_assessment_prompt(
        self,
        user_input: str,
        conversation_turn: int = 1,
        previous_inputs: Optional[list] = None
    ) -> str:
        """Build prompt for engagement quality assessment."""
        history_context = ""
        if previous_inputs:
            history_context = "\n\nPrevious user inputs in this conversation:\n"
            for i, inp in enumerate(previous_inputs[-3:], 1):  # Last 3 inputs
                history_context += f"{i}. \"{inp}\"\n"
        
        return f"""You are an expert at assessing genuine user engagement vs. time-wasting behavior.
Your task: Determine if this user is honestly trying, playfully engaging, or clearly not trying.

Context: Conversation turn #{conversation_turn}
Current user input: "{user_input}"{history_context}

Respond with a JSON object:
{{
  "is_engaged": <true if user is making genuine attempt>,
  "is_honest_attempt": <true if struggling but genuinely trying>,
  "is_non_engagement": <true if clearly wasting time>,
  "strike_weight": <1-3: 1=minor/playful, 2=dismissive but recoverable, 3=severe/clear time-wasting>,
  "engagement_pattern": "<one of: genuine | playful | dismissive | clearly_not_trying | spam>",
  "recommendation": "<specific instruction for the AI on how to respond>"
}}

Guidance:
- "Skinna marinka..." on turn 1 = playful (weight: 1, honest_attempt: true)
- "lol" "idk" "whatever" = dismissive (weight: 2, honest_attempt: false)
- Completely random strings or clear spam = not trying (weight: 3)
- But if they tried in previous turns and now playing = weight: 1
- Consistent nonsense after 2+ turns = weight: 3

DO NOT be rigid. Context matters. A joke on turn 1 might be fine, 
but the same pattern on turn 3 suggests they're not engaging."""
    
    def _parse_name_validation_response(
        self,
        response_text: str,
        user_input: str
    ) -> Dict[str, any]:
        """Parse name validation LLM response."""
        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                
                return {
                    "is_name": data.get("is_name", False),
                    "name_value": data.get("extracted_name"),
                    "is_correction": data.get("is_correction", False),
                    "input_type": data.get("input_type", "unknown"),
                    "contextual_response": data.get("contextual_response", "What's your name?"),
                    "confidence": float(data.get("confidence", 0.5))
                }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse name validation response: {e}")
        
        return self._fallback_name_validation(user_input)
    
    def _parse_intent_validation_response(
        self,
        response_text: str,
        user_input: str
    ) -> Dict[str, any]:
        """Parse intent validation LLM response."""
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                
                return {
                    "is_intent": data.get("is_intent", False),
                    "intent_value": data.get("extracted_intent"),
                    "intent_category": data.get("intent_category", "other"),
                    "contextual_response": data.get("contextual_response", "Tell me more."),
                    "confidence": float(data.get("confidence", 0.5))
                }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse intent validation response: {e}")
        
        return self._fallback_intent_validation(user_input)
    
    def _parse_engagement_response(
        self,
        response_text: str
    ) -> Dict[str, any]:
        """Parse engagement assessment LLM response."""
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                
                return {
                    "is_engaged": data.get("is_engaged", True),
                    "is_honest_attempt": data.get("is_honest_attempt", True),
                    "is_non_engagement": data.get("is_non_engagement", False),
                    "strike_weight": int(data.get("strike_weight", 1)),
                    "engagement_pattern": data.get("engagement_pattern", "unknown"),
                    "recommendation": data.get("recommendation", "Continue normally.")
                }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse engagement response: {e}")
        
        return self._fallback_engagement_assessment("")
    
    def _fallback_name_validation(
        self,
        user_input: str,
        previous_name: Optional[str] = None
    ) -> Dict[str, any]:
        """Fallback name validation using heuristics."""
        # Very basic heuristics for fallback
        is_name = (
            len(user_input.split()) <= 4 and
            len(user_input) <= 40 and
            user_input[0].isupper() and
            not any(word in user_input.lower() for word in ["help", "need", "want", "struggling"])
        )
        
        return {
            "is_name": is_name,
            "name_value": user_input if is_name else None,
            "is_correction": previous_name is not None and user_input != previous_name,
            "input_type": "unknown",
            "contextual_response": "What's your name?" if not is_name else "",
            "confidence": 0.5
        }
    
    def _fallback_intent_validation(
        self,
        user_input: str
    ) -> Dict[str, any]:
        """Fallback intent validation using heuristics."""
        intent_keywords = ["help", "need", "want", "struggling", "working on", "interested in", "dealing"]
        has_intent = any(kw in user_input.lower() for kw in intent_keywords)
        
        return {
            "is_intent": has_intent,
            "intent_value": user_input if has_intent and len(user_input) > 10 else None,
            "intent_category": "other",
            "contextual_response": "Tell me more about what brought you here.",
            "confidence": 0.5
        }
    
    def _fallback_engagement_assessment(
        self,
        user_input: str
    ) -> Dict[str, any]:
        """Fallback engagement assessment."""
        # Very basic: check for nonsense
        is_nonsense = len(user_input) < 3 or user_input.lower() in ["lol", "idk", "whatever", "bye"]
        
        return {
            "is_engaged": not is_nonsense,
            "is_honest_attempt": not is_nonsense,
            "is_non_engagement": is_nonsense,
            "strike_weight": 3 if is_nonsense else 1,
            "engagement_pattern": "clearly_not_trying" if is_nonsense else "unknown",
            "recommendation": "Please take a moment..." if is_nonsense else "Continue normally."
        }
