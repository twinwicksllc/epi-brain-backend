"""
Response Parser Service - Phase 2 Enhancement
Parses user responses to extract core variable information
"""

import re
import logging
from typing import Dict, Any, Optional, List
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)

class ResponseParser:
    """Service for parsing user responses and extracting information"""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
    
    async def parse_and_extract(
        self,
        user_id: str,
        user_message: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Parse user message and extract core variable information
        
        Args:
            user_id: User ID
            user_message: The user's message
            conversation_id: Conversation ID
            
        Returns:
            Dictionary with extracted information
        """
        extracted = {}
        
        logger.debug(f"Parsing message for user {user_id}: {user_message[:100]}...")
        
        # Extract name
        name = self._extract_name(user_message)
        if name:
            await self.memory_service.update_global_memory(
                user_id=user_id,
                category="user_profile",
                key="name",
                value=name
            )
            extracted["name"] = name
            logger.info(f"Extracted name: {name} for user {user_id}")
        
        # Extract location
        location = self._extract_location(user_message)
        if location:
            await self.memory_service.update_global_memory(
                user_id=user_id,
                category="user_profile",
                key="location",
                value=location
            )
            extracted["location"] = location
            logger.info(f"Extracted location: {location} for user {user_id}")
        
        # Extract timezone
        timezone = self._extract_timezone(user_message)
        if timezone:
            await self.memory_service.update_global_memory(
                user_id=user_id,
                category="user_profile",
                key="timezone",
                value=timezone
            )
            extracted["timezone"] = timezone
            logger.info(f"Extracted timezone: {timezone} for user {user_id}")
        
        # Extract communication preferences
        tone = self._extract_preferred_tone(user_message)
        if tone:
            await self.memory_service.update_global_memory(
                user_id=user_id,
                category="communication_preferences",
                key="preferred_tone",
                value=tone
            )
            extracted["preferred_tone"] = tone
            logger.info(f"Extracted tone preference: {tone} for user {user_id}")
        
        if extracted:
            logger.info(f"Total extracted for user {user_id}: {extracted}")
        else:
            logger.debug(f"No information extracted from message for user {user_id}")
        
        return extracted
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name from user message"""
        # Patterns for name extraction (more specific to avoid false positives)
        patterns = [
            r"my name is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"call me\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]
        
        # Words that should never be extracted as names
        invalid_names = {
            "test", "testing", "hello", "hi", "hey", "in", "at", "on", "by",
            "from", "to", "with", "for", "and", "or", "but", "the", "a", "an",
            "cst", "est", "pst", "mst", "gmt", "utc", "yes", "no", "ok", "okay"
        }
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Validate the extracted name
                if (name and 
                    len(name) > 1 and 
                    len(name) < 50 and  # Reasonable name length
                    name.lower() not in invalid_names and
                    not any(char.isdigit() for char in name)):  # No numbers
                    return name.title()
        
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from user message"""
        # Patterns for location extraction
        patterns = [
            r"(?:i'm|i am|live in|from|located in)\s+(?:[\w\s]+,\s*([A-Z]{2})|([\w\s]+))",
            r"(?:in|at)\s+([A-Z][a-z]+\s+(?:County|City|State|Province|Region))",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Return the last capture group that matched
                for group in reversed(match.groups()):
                    if group and len(group) > 2:
                        return group.strip().title()
        
        return None
    
    def _extract_timezone(self, text: str) -> Optional[str]:
        """Extract timezone from user message"""
        # Common timezone abbreviations
        timezone_pattern = r"(?:timezone|time zone)\s*(?:is|:)?\s*([A-Z]{3,4})"
        match = re.search(timezone_pattern, text, re.IGNORECASE)
        
        if match:
            tz = match.group(1).upper()
            if tz in ["EST", "EDT", "CST", "CDT", "MST", "MDT", "PST", "PDT", "GMT", "UTC"]:
                return tz
        
        return None
    
    def _extract_preferred_tone(self, text: str) -> Optional[str]:
        """Extract preferred communication tone from user message"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["formal", "professional", "serious"]):
            return "formal"
        elif any(word in text_lower for word in ["casual", "informal", "chill", "relaxed"]):
            return "casual"
        elif any(word in text_lower for word in ["friendly", "warm", "nice"]):
            return "friendly"
        
        return None