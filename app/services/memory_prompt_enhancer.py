"""Memory Prompt Enhancer - Phase 2
Integrates memory system instructions into AI system prompts
"""

from typing import Dict, Optional
from app.memory_config import (
    get_core_variables,
    get_active_variables,
    get_privacy_variables
)
import logging

logger = logging.getLogger(__name__)

class MemoryPromptEnhancer:
    """Enhances system prompts with memory-related instructions"""
    
    def __init__(self):
        pass
    
    def enhance_system_prompt(
        self,
        original_prompt: str,
        personality: str,
        memory_context: str,
        core_collection_enabled: bool = True,
        auto_extraction_enabled: bool = True
    ) -> str:
        """
        Enhance the original system prompt with memory instructions
        """
        # Build memory instructions
        memory_instructions = self._build_memory_instructions(
            personality,
            memory_context,
            core_collection_enabled,
            auto_extraction_enabled
        )
        
        # Combine with original prompt
        enhanced_prompt = f"""{original_prompt}

{memory_instructions}

Use this information to provide personalized responses. Reference stored details naturally in conversation."""
        
        return enhanced_prompt
    
    def _build_memory_instructions(
        self,
        personality: str,
        memory_context: str,
        core_collection_enabled: bool,
        auto_extraction_enabled: bool
    ) -> str:
        """Build memory-related instructions for the AI"""
        
        instructions = ["<memory_system>"]
        
        # Memory context injection
        if memory_context:
            instructions.append("You have access to the user's stored memory:")
            instructions.append(f"{memory_context}")
            instructions.append("")
            instructions.append("Use this memory to:")
            instructions.append("• Remember user preferences and tailor responses accordingly")
            instructions.append("• Reference past conversations naturally without explicitly stating 'I remember'")
            instructions.append("• Build on previous discussions and context")
            instructions.append("")
        
        # Core variable collection instructions
        if core_collection_enabled:
            core_vars = get_core_variables()
            core_instructions = self._get_core_collection_instructions(personality)
            instructions.extend(core_instructions)
        
        # Auto-extraction instructions
        if auto_extraction_enabled:
            active_vars = get_active_variables(personality)
            extraction_instructions = self._get_extraction_instructions(personality)
            instructions.extend(extraction_instructions)
        
        instructions.append("</memory_system>")
        
        return "\n".join(instructions)
    
    def _get_core_collection_instructions(self, personality: str) -> list:
        """Get instructions for collecting core variables"""
        
        base_instructions = [
            "",
            "<core_variable_collection>",
            "You should naturally collect the following core information from users:",
            "",
            "Essential Information:",
            "• Name (what to call the user)",
            "• Location (city/area and timezone)",
            "• Communication preferences (formal/casual, detailed/concise, response length)",
            "",
            "How to collect:",
            "• Ask naturally within the first few messages",
            "• Don't overwhelm with too many questions at once",
            "• Weave questions into conversation naturally",
            "• Respect user comfort level - if they seem hesitant, back off",
            "",
        ]
        
        personality_specific = {
            "personal_friend": [
                "As a friend, make this feel like getting to know each other.",
                "Example: 'Hey! What name should I call you? And where are you located?'"
            ],
            "sales_agent": [
                "As a sales trainer, frame this as understanding their needs for better training.",
                "Example: 'To tailor the training to your situation, what name should I use and where are you based?'"
            ],
            "weight_loss_coach": [
                "As a fitness coach, explain why you need this info for personalization.",
                "Example: 'To create the best plan for you, what's your name and where are you located? This helps with scheduling and recommendations.'"
            ],
            "business_mentor": [
                "As a business mentor, position this as understanding their context.",
                "Example: 'To provide relevant guidance, what name should I use and what area are you in?'"
            ],
            "student_tutor": [
                "As a tutor, frame this as creating a better learning experience.",
                "Example: 'To personalize our sessions, what name should I use? And what timezone are you in for scheduling?'"
            ],
        }
        
        if personality in personality_specific:
            base_instructions.extend(personality_specific[personality])
        
        base_instructions.append("</core_variable_collection>")
        
        return base_instructions
    
    def _get_extraction_instructions(self, personality: str) -> list:
        """Get instructions for automatic memory extraction"""
        
        base_instructions = [
            "",
            "<active_memory_extraction>",
            "You should automatically extract and remember relevant information from conversations:",
            "",
            "What to extract:",
            "• Interests, hobbies, and activities mentioned",
            "• Goals, targets, and objectives",
            "• Preferences (exercise types, learning styles, etc.)",
            "• Important life events or circumstances",
            "• Behavioral patterns and communication style",
            "",
            "What NOT to extract:",
            "• Temporary states (e.g., 'I have a headache today')",
            "• Privacy-sensitive information without consent",
            "• Financial details (revenue, income) - ask permission first",
            "• Health details (weight, conditions) - ask permission first",
            "• Personal contact information - ask permission first",
            "",
            "How to handle privacy-sensitive information:",
            "• If user mentions financial/health/personal details, ask: 'Would you like me to remember this for future conversations?'",
            "• Only store with explicit permission",
            "• Explain why you're asking and how it will be used",
            "",
        ]
        
        personality_specific = {
            "weight_loss_coach": [
                "For fitness coaching, extract: fitness goals, exercise preferences, dietary restrictions.",
                "Ask permission before storing: current weight, target weight, health conditions.",
            ],
            "business_mentor": [
                "For business mentoring, extract: industry, company stage, business goals, challenges.",
                "Ask permission before storing: revenue, company name, financial details.",
            ],
            "psychology_expert": [
                "For psychology support, extract: emotional patterns, therapy goals, coping strategies.",
                "Be extra cautious with personal information - always ask permission.",
            ],
        }
        
        if personality in personality_specific:
            base_instructions.extend(personality_specific[personality])
        
        base_instructions.append("</active_memory_extraction>")
        
        return base_instructions
    
    def enhance_for_core_collection(
        self,
        original_response: str,
        missing_variables: list,
        personality: str
    ) -> str:
        """
        Enhance an AI response to include questions about missing core variables
        """
        if not missing_variables:
            return original_response
        
        # Generate natural questions for missing variables
        questions = self._generate_questions_for_variables(missing_variables, personality)
        
        if not questions:
            return original_response
        
        # Append questions to response
        collection_prompt = self._generate_collection_prompt(questions, personality)
        
        enhanced_response = f"{original_response}\n\n{collection_prompt}"
        
        return enhanced_response
    
    def _generate_questions_for_variables(self, variables: list, personality: str) -> list:
        """Generate natural questions for specific variables"""
        
        question_templates = {
            "user_profile.name": "What name should I call you?",
            "user_profile.preferred_name": "Is there a nickname you'd prefer?",
            "user_profile.location": "What city or area are you located in?",
            "user_profile.timezone": "What timezone are you in?",
            "communication_preferences.preferred_tone": "Do you prefer formal or casual conversations?",
            "communication_preferences.communication_style": "Would you like detailed or concise explanations?",
            "communication_preferences.response_length_preference": "Do you prefer short, medium, or long responses?",
        }
        
        questions = []
        for var_path in variables:
            if var_path in question_templates:
                questions.append(question_templates[var_path])
        
        return questions[:3]  # Max 3 questions at once
    
    def _generate_collection_prompt(self, questions: list, personality: str) -> str:
        """Generate a prompt for collecting missing variables"""
        
        personality_prompts = {
            "personal_friend": "To get to know you better:",
            "sales_agent": "To tailor my training to your needs:",
            "weight_loss_coach": "To create the perfect plan for you:",
            "business_mentor": "To provide relevant guidance:",
            "student_tutor": "To personalize our sessions:",
            "kids_learning": "Let's get started!",
            "christian_companion": "To better support you:",
            "customer_service": "To assist you better:",
            "psychology_expert": "To create a comfortable experience:",
        }
        
        intro = personality_prompts.get(personality, "To help me better assist you:")
        
        prompt = f"{intro}\n"
        for i, question in enumerate(questions, 1):
            prompt += f"{i}. {question}\n"
        
        return prompt