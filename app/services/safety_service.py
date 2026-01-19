"""
Safety Service for Psychology Expert Mode

Implements safety layers including:
- High-risk keyword detection
- Crisis resource responses
- Professional help recommendations
- Disclaimer system
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SafetyService:
    """Service for handling safety concerns in Psychology Expert mode"""
    
    # High-risk keywords organized by category
    HIGH_RISK_KEYWORDS = {
        "suicide": [
            "suicide", "suicidal", "kill myself", "end my life", "want to die",
            "better off dead", "no reason to live", "take my own life",
            "end it all", "not worth living"
        ],
        "self_harm": [
            "cut myself", "hurt myself", "self harm", "self-harm", "cutting",
            "burning myself", "self injury", "self-injury"
        ],
        "violence": [
            "kill someone", "hurt someone", "murder", "violent thoughts",
            "harm others", "attack someone"
        ],
        "abuse": [
            "being abused", "domestic violence", "sexual abuse", "physical abuse",
            "emotional abuse", "abusive relationship"
        ],
        "severe_crisis": [
            "emergency", "crisis", "can't go on", "losing control",
            "breaking down", "can't cope anymore"
        ]
    }
    
    # Crisis resources by country/region
    CRISIS_RESOURCES = {
        "US": {
            "name": "National Suicide Prevention Lifeline",
            "phone": "988",
            "text": "Text HOME to 741741",
            "url": "https://988lifeline.org/"
        },
        "UK": {
            "name": "Samaritans",
            "phone": "116 123",
            "url": "https://www.samaritans.org/"
        },
        "CA": {
            "name": "Canada Suicide Prevention Service",
            "phone": "1-833-456-4566",
            "text": "Text 45645",
            "url": "https://www.crisisservicescanada.ca/"
        },
        "AU": {
            "name": "Lifeline Australia",
            "phone": "13 11 14",
            "url": "https://www.lifeline.org.au/"
        },
        "INTERNATIONAL": {
            "name": "International Association for Suicide Prevention",
            "url": "https://www.iasp.info/resources/Crisis_Centres/"
        }
    }
    
    # Professional help recommendations
    PROFESSIONAL_HELP_TYPES = {
        "psychiatrist": "A medical doctor who can diagnose mental health conditions and prescribe medication",
        "psychologist": "A mental health professional who provides therapy and psychological testing",
        "therapist": "A licensed mental health professional who provides counseling and therapy",
        "counselor": "A trained professional who provides guidance and support for specific issues",
        "crisis_center": "Immediate support for mental health emergencies",
        "support_group": "Peer support groups for specific mental health conditions"
    }
    
    def __init__(self):
        """Initialize the safety service"""
        self.compiled_patterns = self._compile_keyword_patterns()
    
    def _compile_keyword_patterns(self) -> Dict[str, List[re.Pattern]]:
        """
        Compile regex patterns for high-risk keywords
        
        Returns:
            Dictionary of compiled regex patterns by category
        """
        patterns = {}
        for category, keywords in self.HIGH_RISK_KEYWORDS.items():
            patterns[category] = [
                re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                for keyword in keywords
            ]
        return patterns
    
    def detect_high_risk_content(self, text: str) -> Tuple[bool, List[str], str]:
        """
        Detect high-risk content in user message
        
        Args:
            text: User message text
            
        Returns:
            Tuple of (is_high_risk, detected_categories, severity_level)
        """
        detected_categories = []
        
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    detected_categories.append(category)
                    break
        
        is_high_risk = len(detected_categories) > 0
        
        # Determine severity level
        severity = "none"
        if "suicide" in detected_categories or "violence" in detected_categories:
            severity = "critical"
        elif "self_harm" in detected_categories or "severe_crisis" in detected_categories:
            severity = "high"
        elif "abuse" in detected_categories:
            severity = "moderate"
        
        if is_high_risk:
            logger.warning(f"High-risk content detected: categories={detected_categories}, severity={severity}")
        
        return is_high_risk, detected_categories, severity
    
    def get_crisis_response(self, categories: List[str], region: str = "US") -> str:
        """
        Generate appropriate crisis response based on detected categories
        
        Args:
            categories: List of detected risk categories
            region: User's region/country code
            
        Returns:
            Crisis response message with resources
        """
        # Get crisis resources for region
        resources = self.CRISIS_RESOURCES.get(region, self.CRISIS_RESOURCES["US"])
        
        response = "I'm very concerned about what you're sharing. Your safety is the top priority.\n\n"
        
        if "suicide" in categories:
            response += "**If you're having thoughts of suicide, please reach out for immediate help:**\n\n"
        elif "self_harm" in categories:
            response += "**If you're thinking about harming yourself, please get immediate support:**\n\n"
        elif "violence" in categories:
            response += "**If you're having thoughts of harming others, please seek immediate help:**\n\n"
        elif "abuse" in categories:
            response += "**If you're experiencing abuse, please reach out for support:**\n\n"
        else:
            response += "**If you're in crisis, please reach out for immediate support:**\n\n"
        
        # Add crisis resources
        response += f"**{resources['name']}**\n"
        if "phone" in resources:
            response += f"📞 Call: {resources['phone']}\n"
        if "text" in resources:
            response += f"💬 {resources['text']}\n"
        if "url" in resources:
            response += f"🌐 Visit: {resources['url']}\n"
        
        response += "\n**Emergency Services:**\n"
        response += "🚨 If you're in immediate danger, call 911 (US) or your local emergency number\n\n"
        
        response += "I'm an AI assistant and cannot provide emergency support. "
        response += "Please reach out to a trained professional who can help you right now.\n\n"
        response += "You don't have to face this alone. Help is available 24/7."
        
        return response
    
    def get_professional_help_recommendation(self, issue_type: str = "general") -> str:
        """
        Generate professional help recommendation
        
        Args:
            issue_type: Type of issue (e.g., 'depression', 'anxiety', 'trauma')
            
        Returns:
            Professional help recommendation message
        """
        response = "**Consider Seeking Professional Help:**\n\n"
        response += "While I can provide general information and support, a licensed mental health professional can offer:\n\n"
        
        response += "• **Personalized Assessment:** Comprehensive evaluation of your specific situation\n"
        response += "• **Evidence-Based Treatment:** Proven therapeutic approaches tailored to your needs\n"
        response += "• **Ongoing Support:** Regular sessions to track progress and adjust treatment\n"
        response += "• **Medication Management:** If appropriate, psychiatric evaluation and medication\n"
        response += "• **Crisis Intervention:** Immediate support during mental health emergencies\n\n"
        
        response += "**Types of Mental Health Professionals:**\n\n"
        for prof_type, description in self.PROFESSIONAL_HELP_TYPES.items():
            response += f"• **{prof_type.replace('_', ' ').title()}:** {description}\n"
        
        response += "\n**How to Find Help:**\n\n"
        response += "• Ask your primary care doctor for a referral\n"
        response += "• Contact your insurance provider for in-network providers\n"
        response += "• Use online directories like Psychology Today (psychologytoday.com)\n"
        response += "• Check with your employer's Employee Assistance Program (EAP)\n"
        response += "• Contact local community mental health centers\n"
        
        return response
    
    def get_disclaimer(self, mode: str = "psychology_expert") -> str:
        """
        Get appropriate disclaimer for Psychology Expert mode
        
        Args:
            mode: AI mode (default: psychology_expert)
            
        Returns:
            Disclaimer message
        """
        if mode == "psychology_expert":
            return (
                "**Important Disclaimer:**\n\n"
                "I'm an AI assistant trained to provide general information about mental health and CBT techniques. "
                "I am NOT a licensed therapist, psychologist, or psychiatrist. "
                "I cannot diagnose mental health conditions, prescribe medication, or provide emergency crisis support.\n\n"
                "**What I Can Do:**\n"
                "• Share general information about mental health topics\n"
                "• Guide you through CBT exercises and techniques\n"
                "• Help you track thoughts, emotions, and behaviors\n"
                "• Provide psychoeducation about mental health\n"
                "• Suggest coping strategies and self-help resources\n\n"
                "**What I Cannot Do:**\n"
                "• Diagnose mental health conditions\n"
                "• Prescribe medication or treatment plans\n"
                "• Provide emergency crisis intervention\n"
                "• Replace professional mental health care\n"
                "• Offer legal or medical advice\n\n"
                "If you're experiencing a mental health crisis or need professional support, "
                "please reach out to a licensed mental health professional or crisis service."
            )
        return ""
    
    def should_show_disclaimer(self, conversation_depth: int) -> bool:
        """
        Determine if disclaimer should be shown based on conversation depth
        
        Args:
            conversation_depth: Number of messages in conversation
            
        Returns:
            True if disclaimer should be shown
        """
        # Show disclaimer at start of conversation and periodically
        return conversation_depth == 0 or conversation_depth % 20 == 0
    
    def get_safety_prompt_addition(self, detected_categories: List[str] = None) -> str:
        """
        Get additional safety instructions to add to system prompt
        
        Args:
            detected_categories: List of detected risk categories (if any)
            
        Returns:
            Safety instructions for system prompt
        """
        prompt = "\n\n**CRITICAL SAFETY PROTOCOLS:**\n\n"
        
        if detected_categories:
            prompt += "⚠️ HIGH-RISK CONTENT DETECTED ⚠️\n\n"
            prompt += "The user's message contains indicators of potential crisis or harm. You MUST:\n\n"
            prompt += "1. **Prioritize Safety:** Express immediate concern for their wellbeing\n"
            prompt += "2. **Provide Crisis Resources:** Share appropriate crisis hotlines and resources\n"
            prompt += "3. **Encourage Professional Help:** Strongly recommend contacting a mental health professional or emergency services\n"
            prompt += "4. **Avoid Minimizing:** Do not downplay their concerns or suggest they'll 'feel better soon'\n"
            prompt += "5. **Stay Supportive:** Be empathetic but clear that professional help is needed\n"
            prompt += "6. **Do Not Attempt Treatment:** Do not try to 'fix' the crisis - refer to professionals\n\n"
        else:
            prompt += "Always maintain these safety guidelines:\n\n"
            prompt += "1. **Monitor for Crisis Indicators:** Watch for signs of suicidal ideation, self-harm, or violence\n"
            prompt += "2. **Provide Disclaimers:** Remind users you're not a replacement for professional care\n"
            prompt += "3. **Encourage Professional Help:** When appropriate, suggest seeking licensed mental health support\n"
            prompt += "4. **Stay Within Scope:** Provide psychoeducation and CBT techniques, not diagnosis or treatment\n"
            prompt += "5. **Be Supportive:** Offer empathy and validation while maintaining appropriate boundaries\n\n"
        
        prompt += "**Remember:** You are an AI assistant, not a therapist. Your role is to provide information, "
        prompt += "support, and guidance - not to replace professional mental health care."
        
        return prompt
    
    def log_safety_event(self, user_id: str, categories: List[str], severity: str, message_preview: str):
        """
        Log safety event for monitoring and review
        
        Args:
            user_id: User ID
            categories: Detected risk categories
            severity: Severity level
            message_preview: Preview of user message (first 100 chars)
        """
        logger.warning(
            f"SAFETY EVENT - User: {user_id}, Categories: {categories}, "
            f"Severity: {severity}, Preview: {message_preview[:100]}"
        )