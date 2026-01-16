"""
Core Variable Collection Service - Phase 2
Guides AI in collecting core variables from users naturally
"""

from typing import List, Dict, Optional
from app.memory_config import (
    get_variable_config,
    get_core_variables,
    get_missing_core_variables,
    get_collection_questions_for_missing
)
from app.services.memory_service import MemoryService
import logging

logger = logging.getLogger(__name__)

class CoreVariableCollector:
    """Service for collecting core variables from users"""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
    
    async def assess_completion_status(self, user_id: str) -> Dict:
        """
        Assess how complete the user's core variables are
        Returns completion percentage and missing variables
        """
        global_memory = await self.memory_service.get_global_memory(user_id)
        missing_variables = get_missing_core_variables(global_memory)
        
        total_core_vars = len([v for v in get_core_variables().values() if v.required])
        completed_vars = total_core_vars - len(missing_variables)
        completion_percentage = (completed_vars / total_core_vars * 100) if total_core_vars > 0 else 100
        
        return {
            "completion_percentage": round(completion_percentage, 2),
            "completed_variables": completed_vars,
            "total_required_variables": total_core_vars,
            "missing_variables": missing_variables,
            "is_complete": len(missing_variables) == 0
        }
    
    async def should_ask_for_core_variables(
        self, 
        user_id: str,
        message_count: int,
        conversation_depth: float = 0.0
    ) -> bool:
        """
        Determine if we should ask for core variables
        Rules:
        - Only ask on message 2 or 3 if missing critical variables (name)
        - Don't ask if conversation is deep (user is engaged in serious topic)
        - Don't ask if completion > 50% (we have the basics)
        - Be very conservative to avoid feeling transactional
        """
        status = await self.assess_completion_status(user_id)
        
        # If we have at least 50% of info, don't ask
        if status["completion_percentage"] >= 50:
            return False
        
        # Don't interrupt deep conversations
        if conversation_depth > 0.5:
            return False
        
        # Only ask on message 2 or 3, and only if we're missing name
        if message_count in [2, 3]:
            # Check if name is missing
            missing_name = "user_profile.name" in status["missing_variables"]
            if missing_name:
                return True
        
        return False
    
    async def generate_collection_prompt(
        self, 
        user_id: str,
        personality: str,
        message_count: int = 0
    ) -> Optional[str]:
        """
        Generate a natural prompt to collect missing core variables
        Returns None if we shouldn't ask
        """
        status = await self.assess_completion_status(user_id)
        
        if not status["missing_variables"]:
            return None
        
        # Get missing variables and their questions
        missing_questions = get_collection_questions_for_missing(status["missing_variables"])
        
        if not missing_questions:
            return None
        
        # Generate personality-appropriate collection prompt
        prompt = self._generate_personality_prompt(
            personality,
            missing_questions,
            message_count
        )
        
        return prompt
    
    def _generate_personality_prompt(
        self,
        personality: str,
        questions: List[str],
        message_count: int
    ) -> str:
        """
        Generate a personality-appropriate prompt for collecting variables
        Keep it natural and conversational, not like a form
        """
        personality_prompts = {
            "personal_friend": {
                "casual": "By the way, what should I call you?"
            },
            "sales_agent": {
                "casual": "Quick question - what name should I use for you?"
            },
            "student_tutor": {
                "casual": "Before we continue, what should I call you?"
            },
            "kids_learning": {
                "casual": "Hey, what's your name?"
            },
            "christian_companion": {
                "casual": "I'd love to know your name so I can address you properly."
            },
            "customer_service": {
                "casual": "May I have your name for our conversation?"
            },
            "psychology_expert": {
                "casual": "What would you like me to call you?"
            },
            "business_mentor": {
                "casual": "What should I call you?"
            },
            "weight_loss_coach": {
                "casual": "What's your name?"
            }
        }
        
        # Get personality-specific prompt
        persona = personality_prompts.get(personality, personality_prompts["personal_friend"])
        
        # Just ask for name in a natural way
        # Don't ask multiple questions at once - it's overwhelming
        return persona["casual"]
    
    async def mark_as_collected(self, user_id: str, variable_path: str, value: any):
        """
        Mark a core variable as collected and store its value
        """
        parts = variable_path.split('.')
        category = parts[0]
        
        # Build nested structure
        if len(parts) == 2:
            key = parts[1]
            await self.memory_service.update_global_memory(
                user_id=user_id,
                category=category,
                key=key,
                value=value
            )
        elif len(parts) == 3:
            key = parts[1]
            subkey = parts[2]
            await self.memory_service.update_global_memory(
                user_id=user_id,
                category=category,
                key=key,
                value={subkey: value}
            )
        elif len(parts) == 4:
            key = parts[1]
            subkey = parts[2]
            subsubkey = parts[3]
            await self.memory_service.update_global_memory(
                user_id=user_id,
                category=category,
                key=key,
                value={subkey: {subsubkey: value}}
            )
        
        logger.info(f"Core variable collected: {variable_path} = {value} for user {user_id}")
    
    async def get_next_priority_variable(self, user_id: str) -> Optional[str]:
        """
        Get the next highest-priority variable to collect
        Priority: name > preferred_name > location > timezone > communication preferences
        """
        status = await self.assess_completion_status(user_id)
        
        priority_order = [
            "user_profile.name",
            "user_profile.preferred_name",
            "user_profile.location",
            "user_profile.timezone",
            "communication_preferences.preferred_tone",
            "communication_preferences.communication_style",
            "communication_preferences.response_length_preference"
        ]
        
        for var_path in priority_order:
            if var_path in status["missing_variables"]:
                return var_path
        
        return None