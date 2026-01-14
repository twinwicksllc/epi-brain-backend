"""
Memory Configuration - Phase 2
Defines core variables, active memory variables, and privacy-sensitive variables
"""

from typing import Dict, List, Literal
from pydantic import BaseModel, Field

class VariableConfig(BaseModel):
    """Configuration for a memory variable"""
    collection_method: Literal["core", "active", "privacy"] = Field(
        ...,
        description="How this variable should be collected"
    )
    prompt_template: str = Field(
        default="",
        description="Template for asking user about this variable"
    )
    required: bool = Field(
        default=False,
        description="Whether this variable is required for basic functionality"
    )
    personality_specific: bool = Field(
        default=False,
        description="Whether this is specific to certain personality modes"
    )
    applicable_personalities: List[str] = Field(
        default_factory=list,
        description="Which personality modes this applies to"
    )

# Core Variables - Actively Collected with Guidance
CORE_VARIABLES = {
    # User Profile
    "user_profile.name": VariableConfig(
        collection_method="core",
        prompt_template="What name should I call you?",
        required=True
    ),
    "user_profile.preferred_name": VariableConfig(
        collection_method="core",
        prompt_template="Is there a nickname or preferred name you'd like me to use?",
        required=False
    ),
    "user_profile.location": VariableConfig(
        collection_method="core",
        prompt_template="What city or area are you located in?",
        required=True
    ),
    "user_profile.timezone": VariableConfig(
        collection_method="core",
        prompt_template="What timezone are you in? (e.g., EST, PST, GMT)",
        required=True
    ),
    "user_profile.language_preference": VariableConfig(
        collection_method="core",
        prompt_template="What language would you prefer to communicate in?",
        required=True,
        default="English"
    ),
    
    # Communication Preferences
    "communication_preferences.preferred_tone": VariableConfig(
        collection_method="core",
        prompt_template="Do you prefer a more formal or casual conversation style?",
        required=True
    ),
    "communication_preferences.communication_style": VariableConfig(
        collection_method="core",
        prompt_template="Would you like detailed explanations or more concise responses?",
        required=True
    ),
    "communication_preferences.response_length_preference": VariableConfig(
        collection_method="core",
        prompt_template="Do you prefer short, medium, or long responses?",
        required=True
    ),
}

# Active Memory Variables - Automatically Extracted from Conversations
ACTIVE_MEMORY_VARIABLES = {
    # User Profile (Auto-extract)
    "user_profile.interests": VariableConfig(
        collection_method="active",
        personality_specific=False
    ),
    "user_profile.life_events": VariableConfig(
        collection_method="active",
        personality_specific=False
    ),
    "user_profile.relationships_mentioned": VariableConfig(
        collection_method="active",
        personality_specific=False
    ),
    
    # Behavioral Patterns (Auto-extract)
    "behavioral_patterns.preferred_topics": VariableConfig(
        collection_method="active",
        personality_specific=False
    ),
    "behavioral_patterns.conversation_depth_preference": VariableConfig(
        collection_method="active",
        personality_specific=False
    ),
    "behavioral_patterns.engagement_patterns": VariableConfig(
        collection_method="active",
        personality_specific=False
    ),
    
    # Personality-Specific Active Memory (Auto-extract)
    "personality_contexts.personal_friend.emotional_state": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["personal_friend"]
    ),
    "personality_contexts.personal_friend.recent_activities": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["personal_friend"]
    ),
    "personality_contexts.personal_friend.concerns": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["personal_friend"]
    ),
    
    "personality_contexts.weight_loss_coach.fitness_goals": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["weight_loss_coach"]
    ),
    "personality_contexts.weight_loss_coach.dietary_restrictions": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["weight_loss_coach"]
    ),
    "personality_contexts.weight_loss_coach.exercise_preferences": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["weight_loss_coach"]
    ),
    "personality_contexts.weight_loss_coach.progress_tracking": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["weight_loss_coach"]
    ),
    
    "personality_contexts.business_mentor.industry": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["business_mentor"]
    ),
    "personality_contexts.business_mentor.company_stage": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["business_mentor"]
    ),
    "personality_contexts.business_mentor.business_goals": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["business_mentor"]
    ),
    "personality_contexts.business_mentor.challenges": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["business_mentor"]
    ),
    "personality_contexts.business_mentor.expertise_areas": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["business_mentor"]
    ),
    
    "personality_contexts.student_tutor.learning_goals": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["student_tutor"]
    ),
    "personality_contexts.student_tutor.subjects": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["student_tutor"]
    ),
    "personality_contexts.student_tutor.learning_style": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["student_tutor"]
    ),
    
    "personality_contexts.kids_learning.interests": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["kids_learning"]
    ),
    "personality_contexts.kids_learning.learning_level": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["kids_learning"]
    ),
    
    "personality_contexts.christian_companion.faith_journey": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["christian_companion"]
    ),
    "personality_contexts.christian_companion.prayer_requests": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["christian_companion"]
    ),
    
    "personality_contexts.customer_service.interaction_history": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["customer_service"]
    ),
    "personality_contexts.customer_service.common_issues": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["customer_service"]
    ),
    
    "personality_contexts.psychology_expert.emotional_patterns": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["psychology_expert"]
    ),
    "personality_contexts.psychology_expert.therapy_goals": VariableConfig(
        collection_method="active",
        personality_specific=True,
        applicable_personalities=["psychology_expert"]
    ),
}

# Privacy-Sensitive Variables - Never Auto-Extract, Require Permission
PRIVACY_SENSITIVE_VARIABLES = {
    # Personal Information
    "user_profile.birth_date": VariableConfig(
        collection_method="privacy",
        prompt_template="Would you like to share your birthday? I can use it to remember special occasions."
    ),
    "user_profile.phone_number": VariableConfig(
        collection_method="privacy",
        prompt_template="Would you like to share your phone number? This is optional and will only be used for account-related communications."
    ),
    "user_profile.address": VariableConfig(
        collection_method="privacy",
        prompt_template="Would you like to share your address? This is completely optional."
    ),
    
    # Health Information (Weight Loss Coach)
    "personality_contexts.weight_loss_coach.current_weight": VariableConfig(
        collection_method="privacy",
        prompt_template="To help track your progress, would you like to share your current weight? This information will be kept private and used only for your fitness journey.",
        personality_specific=True,
        applicable_personalities=["weight_loss_coach"]
    ),
    "personality_contexts.weight_loss_coach.target_weight": VariableConfig(
        collection_method="privacy",
        prompt_template="What's your target weight? This is optional and will help me create a personalized plan.",
        personality_specific=True,
        applicable_personalities=["weight_loss_coach"]
    ),
    "personality_contexts.weight_loss_coach.health_conditions": VariableConfig(
        collection_method="privacy",
        prompt_template="Are there any health conditions or medical restrictions I should know about to provide safe advice? This information will be kept confidential.",
        personality_specific=True,
        applicable_personalities=["weight_loss_coach"]
    ),
    
    # Financial Information (Business Mentor)
    "personality_contexts.business_mentor.revenue": VariableConfig(
        collection_method="privacy",
        prompt_template="Would you like to share your current revenue? This is completely optional and will help me provide more targeted business advice.",
        personality_specific=True,
        applicable_personalities=["business_mentor"]
    ),
    "personality_contexts.business_mentor.company_name": VariableConfig(
        collection_method="privacy",
        prompt_template="What's your company name? This is optional and will help me provide more personalized advice.",
        personality_specific=True,
        applicable_personalities=["business_mentor"]
    ),
    "personality_contexts.business_mentor.financial_goals": VariableConfig(
        collection_method="privacy",
        prompt_template="What are your financial goals? This is optional and will help me create a tailored strategy.",
        personality_specific=True,
        applicable_personalities=["business_mentor"]
    ),
}

def get_variable_config(variable_path: str) -> VariableConfig:
    """Get configuration for a specific variable"""
    if variable_path in CORE_VARIABLES:
        return CORE_VARIABLES[variable_path]
    elif variable_path in ACTIVE_MEMORY_VARIABLES:
        return ACTIVE_MEMORY_VARIABLES[variable_path]
    elif variable_path in PRIVACY_SENSITIVE_VARIABLES:
        return PRIVACY_SENSITIVE_VARIABLES[variable_path]
    else:
        return VariableConfig(collection_method="active")

def get_core_variables() -> Dict[str, VariableConfig]:
    """Get all core variables"""
    return CORE_VARIABLES

def get_active_variables(personality: str = None) -> Dict[str, VariableConfig]:
    """Get active memory variables, optionally filtered by personality"""
    if personality:
        return {
            path: config for path, config in ACTIVE_MEMORY_VARIABLES.items()
            if not config.personality_specific or personality in config.applicable_personalities
        }
    return ACTIVE_MEMORY_VARIABLES

def get_privacy_variables(personality: str = None) -> Dict[str, VariableConfig]:
    """Get privacy-sensitive variables, optionally filtered by personality"""
    if personality:
        return {
            path: config for path, config in PRIVACY_SENSITIVE_VARIABLES.items()
            if not config.personality_specific or personality in config.applicable_personalities
        }
    return PRIVACY_SENSITIVE_VARIABLES

def get_missing_core_variables(global_memory: dict) -> List[str]:
    """Get list of core variables that are missing or empty"""
    missing = []
    for path, config in CORE_VARIABLES.items():
        if config.required:
            parts = path.split('.')
            value = global_memory
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    missing.append(path)
                    break
            else:
                if not value or value == "":
                    missing.append(path)
    return missing

def get_collection_questions_for_missing(missing_variables: List[str]) -> List[str]:
    """Generate natural questions for missing core variables"""
    questions = []
    for var_path in missing_variables:
        config = CORE_VARIABLES.get(var_path)
        if config and config.prompt_template:
            questions.append(config.prompt_template)
    return questions