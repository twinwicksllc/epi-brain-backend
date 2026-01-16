"""
Active Memory Extraction Service - Phase 2
Automatically extracts relevant information from conversations
"""

from typing import List, Dict, Optional, Any
import json
import re
from datetime import datetime
from app.memory_config import get_active_variables, get_variable_config
from app.services.memory_service import MemoryService
from app.models.message import Message
from app.services.groq_service import GroqService
import logging

logger = logging.getLogger(__name__)

class ActiveMemoryExtractor:
    """Service for automatically extracting memory from conversations"""
    
    def __init__(self, memory_service: MemoryService, ai_service: GroqService):
        self.memory_service = memory_service
        self.ai_service = ai_service
    
    async def extract_from_conversation(
        self,
        user_id: str,
        conversation_id: str,
        personality: str,
        recent_messages: List[Message],
        max_extraction_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze conversation and extract memory-worthy information
        """
        if not recent_messages:
            return {"extracted": [], "errors": []}
        
        # Get active variables for this personality
        active_variables = get_active_variables(personality)
        
        # Prepare conversation context
        conversation_context = self._prepare_conversation_context(recent_messages)
        
        # Generate extraction prompt
        extraction_prompt = self._generate_extraction_prompt(
            conversation_context,
            personality,
            active_variables
        )
        
        try:
            # Use AI to extract information
            extraction_result = await self._ai_extract(extraction_prompt)
            
            # Process and validate extractions
            processed = self._process_extraction_result(extraction_result, active_variables)
            
            # Update memory with extracted information
            updated = await self._update_memory_with_extraction(
                user_id,
                conversation_id,
                processed["extracted_data"]
            )
            
            return {
                "success": True,
                "extracted": processed["extracted_data"],
                "updated_count": updated,
                "confidence": processed["confidence"],
                "errors": processed["errors"]
            }
            
        except Exception as e:
            logger.error(f"Extraction error for user {user_id}: {str(e)}")
            return {
                "success": False,
                "extracted": [],
                "errors": [str(e)]
            }
    
    def _prepare_conversation_context(self, messages: List[Message]) -> str:
        """Format messages for AI analysis"""
        context_parts = []
        for msg in messages[-10:]:  # Last 10 messages max
            role = "User" if msg.role == "user" else "Assistant"
            context_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def _generate_extraction_prompt(
        self,
        conversation: str,
        personality: str,
        active_variables: Dict
    ) -> str:
        """Generate prompt for AI to extract information"""
        
        # Build list of variable descriptions
        variable_descriptions = []
        for var_path, config in active_variables.items():
            category = var_path.split('.')[0]
            if category == "user_profile":
                var_desc = f"- User profile information (interests, life events, relationships)"
            elif category == "behavioral_patterns":
                var_desc = f"- Behavioral patterns (topics, conversation style, engagement)"
            elif category == "personality_contexts":
                context_type = var_path.split('.')[2]
                var_desc = f"- Personality-specific context: {context_type}"
            else:
                var_desc = f"- {var_path}"
            
            variable_descriptions.append(var_desc)
        
        prompt = f"""You are analyzing a conversation to extract information for memory storage.

Personality Mode: {personality}

Conversation:
{conversation}

Your task: Extract relevant information from this conversation that should be remembered for future conversations.

Look for:
{chr(10).join(variable_descriptions)}

Rules:
1. ONLY extract information that is explicitly mentioned or clearly implied
2. Do NOT guess or infer information that isn't stated
3. Focus on preferences, facts, goals, and patterns
4. Ignore temporary or one-time mentions (e.g., "I have a headache today")
5. Return ONLY a valid JSON object with the extracted information

Example output format:
{{
  "user_profile": {{
    "interests": ["hiking", "reading", "technology"],
    "recent_activities": ["planned a hiking trip"]
  }},
  "personality_contexts": {{
    "weight_loss_coach": {{
      "fitness_goals": ["lose 20 pounds by summer"],
      "exercise_preferences": ["hiking", "swimming"]
    }}
  }},
  "behavioral_patterns": {{
    "preferred_topics": ["fitness", "outdoor activities"],
    "conversation_depth_preference": "deep"
  }}
}}

Extract the relevant information from the conversation above and return it as a JSON object."""

        return prompt
    
    async def _ai_extract(self, prompt: str) -> str:
        """Use AI to extract information"""
        # Use a smaller, faster model for extraction
        try:
            response = await self.ai_service.get_response(
                message=prompt,
                mode="system",  # Use system mode for extraction
                memory_context=None
            )
            return response.get("content", "")
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}")
            raise
    
    def _process_extraction_result(
        self,
        result: str,
        active_variables: Dict
    ) -> Dict[str, Any]:
        """Process and validate AI extraction result"""
        try:
            # Try to parse JSON
            extracted_data = json.loads(result)
            
            # Validate against active variables
            valid_extractions = {}
            errors = []
            confidence = 0.8
            
            for category, data in extracted_data.items():
                if category in ["user_profile", "behavioral_patterns", "personality_contexts"]:
                    valid_extractions[category] = data
                else:
                    errors.append(f"Unknown category: {category}")
            
            return {
                "extracted_data": valid_extractions,
                "confidence": confidence,
                "errors": errors
            }
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse extraction result as JSON: {result}")
            # Try to extract using regex as fallback
            return self._fallback_extraction(result, active_variables)
    
    def _fallback_extraction(
        self,
        text: str,
        active_variables: Dict
    ) -> Dict[str, Any]:
        """Fallback extraction using regex patterns"""
        extracted = {
            "user_profile": {
                "interests": [],
                "life_events": []
            }
        }
        
        # Simple pattern matching for interests
        interest_patterns = [
            r"I love\s+([\w\s]+)",
            r"I enjoy\s+([\w\s]+)",
            r"I'm interested in\s+([\w\s]+)",
            r"My hobbies include\s+([\w\s]+)"
        ]
        
        for pattern in interest_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                interest = match.strip()
                if interest and interest not in extracted["user_profile"]["interests"]:
                    extracted["user_profile"]["interests"].append(interest)
        
        return {
            "extracted_data": extracted,
            "confidence": 0.5,
            "errors": ["Used fallback extraction (lower confidence)"]
        }
    
    async def _update_memory_with_extraction(
        self,
        user_id: str,
        conversation_id: str,
        extracted_data: Dict[str, Any]
    ) -> int:
        """Update memory with extracted information"""
        updated_count = 0
        
        for category, data in extracted_data.items():
            try:
                if category == "user_profile":
                    # Update global memory
                    for key, value in data.items():
                        await self.memory_service.update_global_memory(
                            user_id=user_id,
                            category=category,
                            key=key,
                            value=value
                        )
                        updated_count += 1
                
                elif category == "behavioral_patterns":
                    # Update global memory
                    for key, value in data.items():
                        await self.memory_service.update_global_memory(
                            user_id=user_id,
                            category=category,
                            key=key,
                            value=value
                        )
                        updated_count += 1
                
                elif category == "personality_contexts":
                    # Update personality-specific context
                    for personality, context in data.items():
                        for key, value in context.items():
                            await self.memory_service.update_personality_context(
                                user_id=user_id,
                                personality=personality,
                                context=context
                            )
                            updated_count += 1
                
            except Exception as e:
                logger.error(f"Error updating memory for {category}: {str(e)}")
        
        return updated_count
    
    async def should_extract_from_conversation(
        self,
        user_id: str,
        message_count: int,
        conversation_depth: float = 0.0
    ) -> bool:
        """
        Determine if we should extract memory from this conversation
        Rules:
        - Extract after every 2 messages (more frequent for better memory)
        - Extract if conversation depth > 0.3 (meaningful conversation)
        - Always extract in early conversations to catch important info
        """
        if message_count < 1:
            return False
        
        # Extract every 2 messages (changed from 5 for better memory capture)
        if message_count % 2 == 0:
            return True
        
        # Extract if conversation becomes deep
        if conversation_depth > 0.5 and message_count >= 2:
            return True
        
        return False