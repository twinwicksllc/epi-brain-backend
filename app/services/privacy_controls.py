"""
Privacy Controls Service - Phase 2
Handles privacy-sensitive variables and user consent
"""

from typing import Dict, List, Optional
from app.memory_config import get_privacy_variables, get_variable_config
from app.services.memory_service import MemoryService
import logging

logger = logging.getLogger(__name__)

class PrivacyControls:
    """Service for managing privacy-sensitive memory variables"""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
    
    async def request_permission_for_variable(
        self,
        user_id: str,
        variable_path: str,
        value: any
    ) -> Dict[str, any]:
        """
        Generate a permission request for a privacy-sensitive variable
        """
        config = get_variable_config(variable_path)
        
        if config.collection_method != "privacy":
            return {
                "error": "Variable is not privacy-sensitive",
                "required_permission": False
            }
        
        # Generate permission request
        permission_request = {
            "variable_path": variable_path,
            "value": value,
            "prompt": config.prompt_template,
            "required_permission": True,
            "storage_policy": "This information will be stored in your personal memory profile and used to personalize future conversations.",
            "privacy_guarantee": "Your information will never be shared with third parties and will only be used for providing personalized assistance."
        }
        
        return permission_request
    
    async def store_with_permission(
        self,
        user_id: str,
        variable_path: str,
        value: any,
        user_consent: bool
    ) -> Dict[str, any]:
        """
        Store privacy-sensitive variable only with user consent
        """
        if not user_consent:
            logger.info(f"User declined to store {variable_path}")
            return {
                "success": False,
                "stored": False,
                "message": "Information not stored per user preference"
            }
        
        try:
            # Store the variable
            parts = variable_path.split('.')
            category = parts[0]
            
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
            
            logger.info(f"Privacy-sensitive variable stored with consent: {variable_path}")
            
            return {
                "success": True,
                "stored": True,
                "message": "Information stored successfully"
            }
            
        except Exception as e:
            logger.error(f"Error storing privacy variable {variable_path}: {str(e)}")
            return {
                "success": False,
                "stored": False,
                "error": str(e)
            }
    
    async def detect_privacy_sensitive_content(
        self,
        text: str,
        personality: str
    ) -> List[Dict[str, any]]:
        """
        Detect if text contains privacy-sensitive information that might need consent
        """
        privacy_variables = get_privacy_variables(personality)
        detected = []
        
        # Define patterns for sensitive information
        sensitive_patterns = {
            "financial": [
                r"\$\d+,\d+",
                r"\$\d+\.?\d*k?",
                r"revenue|income|salary|profit"
            ],
            "health": [
                r"\d+\s*(lbs|kg|pounds|kilograms)",
                r"medical condition|health issue|diagnosis",
                r"allerg(y|ies)"
            ],
            "personal": [
                r"\d{3}-\d{2}-\d{4}",  # SSN pattern
                r"\d{11,}",  # Long numbers (could be phone)
                r"address|street|city|state|zip"
            ]
        }
        
        import re
        for category, patterns in sensitive_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    detected.append({
                        "category": category,
                        "matches": matches,
                        "suggestion": "This may contain privacy-sensitive information. Consider asking for user consent before storing."
                    })
        
        return detected
    
    async def generate_privacy_prompt(
        self,
        user_id: str,
        detected_info: List[Dict[str, any]],
        personality: str
    ) -> Optional[str]:
        """
        Generate a natural prompt to request permission for storing sensitive information
        """
        if not detected_info:
            return None
        
        personality_prompts = {
            "personal_friend": "I noticed you mentioned some personal details. Would you like me to remember this for future conversations? I'll keep it private.",
            "sales_agent": "To better serve you, would you like me to remember some details about your situation? This is completely optional.",
            "student_tutor": "I noticed some information that could help me personalize your learning experience. Would you like me to save this?",
            "kids_learning": "Can I remember this fun fact about you? It'll help me give you better answers!",
            "christian_companion": "I'd like to remember this to better support you in your journey. Would that be okay?",
            "customer_service": "To provide you with better service in the future, would you like me to remember these details?",
            "psychology_expert": "To provide more effective support, I'd like to note some information. Would you be comfortable with me remembering this?",
            "business_mentor": "This information could help me provide more targeted advice. Would you like me to save it for our future discussions?",
            "weight_loss_coach": "This information would help me create a more personalized plan for you. Would you like me to remember it?"
        }
        
        base_prompt = personality_prompts.get(
            personality,
            personality_prompts["personal_friend"]
        )
        
        # Add specific context about detected information
        context = ""
        categories = list(set([d["category"] for d in detected_info]))
        
        if "financial" in categories:
            context += " This includes financial information."
        if "health" in categories:
            context += " This includes health-related information."
        if "personal" in categories:
            context += " This includes personal contact information."
        
        full_prompt = f"{base_prompt}{context}\n\n[Yes, remember it] [No, don't store it]"
        
        return full_prompt
    
    async def get_user_privacy_settings(self, user_id: str) -> Dict[str, any]:
        """
        Get user's privacy settings for memory storage
        """
        global_memory = await self.memory_service.get_global_memory(user_id)
        
        # Default privacy settings
        privacy_settings = global_memory.get("privacy_settings", {
            "allow_automatic_extraction": True,
            "allow_core_variable_collection": True,
            "consent_for_financial": False,
            "consent_for_health": False,
            "consent_for_personal": False
        })
        
        return privacy_settings
    
    async def update_privacy_settings(
        self,
        user_id: str,
        settings: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Update user's privacy settings
        """
        await self.memory_service.update_global_memory(
            user_id=user_id,
            category="privacy_settings",
            key="privacy_settings",
            value=settings
        )
        
        return {
            "success": True,
            "message": "Privacy settings updated"
        }