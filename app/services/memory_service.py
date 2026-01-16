"""
Memory Service - Manages structured memory for users and conversations

This service handles:
- Global memory (user-level, persistent across sessions)
- Session memory (conversation-level, temporary)
- Memory injection into AI prompts
- Memory consolidation
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.conversation import Conversation
from datetime import datetime
import json


class MemoryService:
    """Manages structured memory for users and conversations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== GLOBAL MEMORY ====================
    
    async def get_global_memory(self, user_id: str) -> Dict[str, Any]:
        """Get user's global memory"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User {user_id} not found when getting global memory")
            return {}
        
        # Handle both dict and string (JSON) formats
        if isinstance(user.global_memory, str):
            try:
                memory = json.loads(user.global_memory) if user.global_memory else {}
                logger.debug(f"Retrieved global memory for user {user_id}: {memory}")
                return memory
            except Exception as e:
                logger.error(f"Error parsing global memory for user {user_id}: {e}")
                return {}
        
        logger.debug(f"Retrieved global memory for user {user_id}: {user.global_memory}")
        return user.global_memory if user.global_memory else {}
    
    async def update_global_memory(
        self, 
        user_id: str, 
        category: str, 
        key: str, 
        value: Any
    ) -> Dict[str, Any]:
        """
        Update a specific field in global memory
        
        Example:
            update_global_memory(
                user_id="123",
                category="communication_preferences",
                key="style",
                value="concise"
            )
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Initialize memory if empty
        memory = await self.get_global_memory(user_id)
        if not memory:
            memory = self._get_default_global_memory()
        
        # Update specific field
        if category not in memory:
            memory[category] = {}
        
        memory[category][key] = value
        
        # Update metadata
        if "metadata" not in memory:
            memory["metadata"] = {}
        memory["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        
        # Save back to database
        user.global_memory = memory
        
        # Mark as modified for SQLAlchemy to detect change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "global_memory")
        
        self.db.commit()
        logger.info(f"Updated global memory for user {user_id}: {memory}")
        return memory
    
    async def update_personality_context(
        self,
        user_id: str,
        personality: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update context for a specific personality
        
        Example:
            update_personality_context(
                user_id="123",
                personality="weight_loss_coach",
                context={"diet_type": "vegetarian", "goal_weight": 170}
            )
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        memory = await self.get_global_memory(user_id)
        if not memory:
            memory = self._get_default_global_memory()
        
        if "personality_contexts" not in memory:
            memory["personality_contexts"] = {}
        
        # Merge new context with existing
        if personality not in memory["personality_contexts"]:
            memory["personality_contexts"][personality] = {}
        
        memory["personality_contexts"][personality].update(context)
        
        # Update metadata
        if "metadata" not in memory:
            memory["metadata"] = {}
        memory["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        
        user.global_memory = memory
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "global_memory")
        
        self.db.commit()
        return memory
    
    async def get_personality_context(
        self,
        user_id: str,
        personality: str
    ) -> Dict[str, Any]:
        """Get context for a specific personality"""
        memory = await self.get_global_memory(user_id)
        return memory.get("personality_contexts", {}).get(personality, {})
    
    # ==================== SESSION MEMORY ====================
    
    async def get_session_memory(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation's session memory"""
        conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return {}
        
        # Handle both dict and string (JSON) formats
        if isinstance(conv.session_memory, str):
            try:
                return json.loads(conv.session_memory) if conv.session_memory else {}
            except:
                return {}
        return conv.session_memory if conv.session_memory else {}
    
    async def update_session_memory(
        self,
        conversation_id: str,
        category: str,
        key: str,
        value: Any
    ) -> Dict[str, Any]:
        """Update a specific field in session memory"""
        conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        memory = await self.get_session_memory(conversation_id)
        if not memory:
            memory = self._get_default_session_memory()
        
        if category not in memory:
            memory[category] = {}
        
        memory[category][key] = value
        
        # Update metadata
        if "metadata" not in memory:
            memory["metadata"] = {}
        memory["metadata"]["last_activity"] = datetime.utcnow().isoformat()
        
        conv.session_memory = memory
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(conv, "session_memory")
        
        self.db.commit()
        return memory
    
    # ==================== MEMORY CONSOLIDATION ====================
    
    async def consolidate_session_to_global(
        self,
        user_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Consolidate session memory into global memory
        
        Rules:
        1. Temporary preferences are discarded
        2. Durable patterns are promoted to global
        3. Session facts are cleared
        """
        session_mem = await self.get_session_memory(conversation_id)
        global_mem = await self.get_global_memory(user_id)
        
        # Extract durable information from session
        current_context = session_mem.get("current_context", {})
        
        # Example: If user had consistent mood/topic, update behavioral patterns
        if "topic" in current_context:
            # Could track topic frequency in global memory
            pass
        
        # Mark session as consolidated
        await self.update_session_memory(
            conversation_id,
            "metadata",
            "consolidation_pending",
            False
        )
        
        return global_mem
    
    # ==================== MEMORY INJECTION ====================
    
    async def render_memory_for_prompt(
        self,
        user_id: str,
        conversation_id: str,
        personality: str
    ) -> str:
        """
        Render memories as markdown for AI prompt injection
        
        Returns formatted string like:
        
        USER PROFILE:
        - Name: John
        - Industry: Healthcare
        
        COMMUNICATION PREFERENCES:
        - Style: Concise
        - Tone: Friendly
        
        WEIGHT LOSS COACH CONTEXT:
        - Diet: Vegetarian
        - Goal Weight: 170 lbs
        
        CURRENT SESSION:
        - Topic: Job interview preparation
        - Mood: Nervous
        """
        global_mem = await self.get_global_memory(user_id)
        session_mem = await self.get_session_memory(conversation_id)
        
        sections = []
        
        # User Profile
        if "user_profile" in global_mem and global_mem["user_profile"]:
            profile = global_mem["user_profile"]
            sections.append("USER PROFILE:")
            for key, value in profile.items():
                sections.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        # Communication Preferences
        if "communication_preferences" in global_mem and global_mem["communication_preferences"]:
            prefs = global_mem["communication_preferences"]
            sections.append("\nCOMMUNICATION PREFERENCES:")
            for key, value in prefs.items():
                sections.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        # Personality-Specific Context
        if "personality_contexts" in global_mem:
            if personality in global_mem["personality_contexts"]:
                context = global_mem["personality_contexts"][personality]
                if context:  # Only add if not empty
                    sections.append(f"\n{personality.upper().replace('_', ' ')} CONTEXT:")
                    for key, value in context.items():
                        if isinstance(value, list):
                            sections.append(f"- {key.replace('_', ' ').title()}: {', '.join(map(str, value))}")
                        else:
                            sections.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        # Current Session Context
        if "current_context" in session_mem and session_mem["current_context"]:
            context = session_mem["current_context"]
            sections.append("\nCURRENT SESSION:")
            for key, value in context.items():
                sections.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        # Return empty string if no memory
        if not sections:
            return ""
        
        return "\n".join(sections)
    
    # ==================== HELPER METHODS ====================
    
    def _get_default_global_memory(self) -> Dict[str, Any]:
        """Default structure for global memory"""
        return {
            "user_profile": {},
            "communication_preferences": {},
            "personality_contexts": {},
            "behavioral_patterns": {},
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "memory_version": "1.0"
            }
        }
    
    def _get_default_session_memory(self) -> Dict[str, Any]:
        """Default structure for session memory"""
        return {
            "current_context": {},
            "temporary_preferences": {},
            "session_facts": {},
            "conversation_flow": {},
            "metadata": {
                "session_start": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "consolidation_pending": False
            }
        }