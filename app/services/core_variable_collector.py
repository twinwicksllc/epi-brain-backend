"""
Core Variable Collection Service - Phase 2
Guides AI in collecting core variables from users naturally
"""

from typing import List, Dict, Optional
from app.config.memory_config import (
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
        - Always ask within first 5 messages if missing required variables
        - Don't ask if conversation is deep (user is engaged in serious topic)
        - Don't ask if we've asked in last 3 messages
        - Don't ask if completion > 80%
        """
        status = await self.assess_completion_status(user_id)
        
        # If already mostly complete, don't ask
        if status["completion_percentage"] >= 80:
            return False
        
        # Don't interrupt deep conversations
        if conversation_depth > 0.6:
            return False
        
        # Ask in early conversations if missing required variables
        if message_count <= 5 and status["missing_variables"]:
            return True
        
        # If very incomplete (< 30%), ask within first 10 messages
        if status["completion_percentage"] < 30 and message_count <= 10:
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
        """
        personality_prompts = {
            "personal_friend": {
                "greeting": "Hey! 👋 I'd love to get to know you better so I can be more helpful.",
                "closing": "Feel free to answer whatever you're comfortable with!"
            },
            "sales_agent": {
                "greeting": "To ensure I provide the best service for you, I'd like to understand a bit more about your needs.",
                "closing": "These details will help me tailor my approach for you."
            },
            "student_tutor": {
                "greeting": "To make our learning sessions as effective as possible, I'd like to understand your preferences.",
                "closing": "This will help me create a personalized learning experience for you!"
            },
            "kids_learning": {
                "greeting": "Hi there! Let's make this super fun! Can you tell me a few things so I can help you better?",
                "closing": "You're doing great! 💪"
            },
            "christian_companion": {
                "greeting": "I'm blessed to have this conversation with you. To better support you in your faith journey, I'd love to know a bit more about you.",
                "closing": "Thank you for sharing with me."
            },
            "customer_service": {
                "greeting": "To provide you with the best possible assistance, I'd like to understand your preferences.",
                "closing": "This will help me serve you better."
            },
            "psychology_expert": {
                "greeting": "Creating a comfortable and effective therapeutic experience starts with understanding your preferences.",
                "closing": "This information will help me tailor our sessions to your needs."
            },
            "business_mentor": {
                "greeting": "To provide the most relevant and strategic guidance for your business, I'd like to understand your situation better.",
                "closing": "This context will help me give you more targeted advice."
            },
            "weight_loss_coach": {
                "greeting": "To create the most effective personalized fitness plan for you, I'd love to learn a bit more about you.",
                "closing": "This information will help me design the perfect program for you!"
            }
        }
        
        # Get personality-specific prompts
        persona = personality_prompts.get(personality, personality_prompts["personal_friend"])
        
        # Select 2-3 most important questions (don't overwhelm)
        num_questions = min(len(questions), 3)
        selected_questions = questions[:num_questions]
        
        # Build the prompt
        if message_count == 0:
            # First message - more comprehensive
            prompt = f"{persona['greeting']}\n\n"
            for question in selected_questions:
                prompt += f"• {question}\n"
            prompt += f"\n{persona['closing']}"
        else:
            # Subsequent messages - more conversational
            prompt = f"{persona['greeting']}\n\n"
            for i, question in enumerate(selected_questions, 1):
                prompt += f"{i}. {question}\n"
            prompt += f"\n{persona['closing']}"
        
        return prompt
    
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