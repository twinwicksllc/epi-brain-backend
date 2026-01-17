"""
Semantic Memory Service

Handles extraction, storage, and retrieval of semantic memories
for cross-conversation context awareness.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.semantic_memory import SemanticMemory, is_semantic_memory_enabled
from app.models.conversation import Conversation
from app.models.message import Message

logger = logging.getLogger(__name__)

# Memory extraction prompts for different modes
MEMORY_EXTRACTION_PROMPTS = {
    'personal_friend': """
Extract important personal details, preferences, relationships, and life events from this conversation.
Focus on: names, birthdays, important dates, personal goals, preferences, family members, friends.
""",
    'christian_companion': """
Extract spiritual journey information, prayer requests, faith questions, and biblical topics discussed.
Focus on: spiritual goals, prayer needs, favorite scriptures, faith milestones, church involvement.
""",
    'psychology_expert': """
Extract therapy-relevant information, patterns, triggers, and progress in mental health topics.
Focus on: coping strategies, patterns identified, triggers, progress made, therapy goals.
""",
    'business_mentor': """
Extract business goals, challenges, wins, team dynamics, and strategic insights.
Focus on: business objectives, milestones, team members, challenges faced, successes achieved.
""",
    'weight_loss_coach': """
Extract diet preferences, exercise habits, challenges, and weight loss milestones.
Focus on: food preferences, exercise routine, challenges faced, progress made, health goals.
""",
    'kids_learning': """
Extract child's interests, school activities, achievements, and learning preferences.
Focus on: favorite subjects, hobbies, school activities, achievements, learning style.
""",
}


class SemanticMemoryService:
    """Service for managing semantic memories across conversations"""
    
    def __init__(self, db: Session, openai_client=None):
        """
        Initialize the semantic memory service
        
        Args:
            db: SQLAlchemy database session
            openai_client: OpenAI client for embedding generation (optional)
        """
        self.db = db
        self.openai_client = openai_client
        
        # Default memory expiration (90 days)
        self.default_expiration_days = 90
        
    async def extract_memories_from_conversation(
        self, 
        conversation: Conversation,
        max_memories: int = 5
    ) -> List[SemanticMemory]:
        """
        Extract important memories from a conversation
        
        Args:
            conversation: The conversation to extract memories from
            max_memories: Maximum number of memories to extract
            
        Returns:
            List of extracted SemanticMemory objects
        """
        # Check if semantic memory is enabled for this mode
        if not is_semantic_memory_enabled(conversation.mode):
            logger.info(f"Semantic memory not enabled for mode: {conversation.mode}")
            return []
        
        # Get all messages from the conversation
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at).all()
        
        if not messages:
            logger.info(f"No messages found for conversation {conversation.id}")
            return []
        
        # Build conversation text for analysis
        conversation_text = self._build_conversation_text(messages)
        
        # Extract memories using AI (synchronous for now, will be async)
        memories_data = await self._extract_memories_with_ai(
            conversation_text=conversation_text,
            mode=conversation.mode,
            user_id=conversation.user_id,
            conversation_id=conversation.id,
            max_memories=max_memories
        )
        
        # Create and save memories
        saved_memories = []
        for memory_data in memories_data:
            memory = SemanticMemory(
                user_id=conversation.user_id,
                mode=conversation.mode,
                embedding=memory_data['embedding'],
                content=memory_data['content'],
                importance_score=memory_data.get('importance_score', 0.5),
                category=memory_data.get('category', 'general'),
                source_conversation_id=conversation.id,
                source_message_id=memory_data.get('source_message_id'),
                expires_at=datetime.utcnow() + timedelta(days=self.default_expiration_days),
                tags=json.dumps(memory_data.get('tags', [])),
                is_sensitive=str(memory_data.get('is_sensitive', False)).lower()
            )
            
            self.db.add(memory)
            saved_memories.append(memory)
        
        # Commit all memories at once
        try:
            self.db.commit()
            logger.info(f"Extracted {len(saved_memories)} memories from conversation {conversation.id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving memories: {e}")
            return []
        
        return saved_memories
    
    async def retrieve_relevant_memories(
        self,
        user_id: str,
        mode: str,
        current_input: str,
        max_memories: int = 5,
        min_importance: float = 0.3
    ) -> List[SemanticMemory]:
        """
        Retrieve semantically relevant memories for context
        
        Args:
            user_id: The user's ID
            mode: The current AI mode
            current_input: The current user input for similarity search
            max_memories: Maximum number of memories to return
            min_importance: Minimum importance score threshold
            
        Returns:
            List of relevant SemanticMemory objects
        """
        # Check if semantic memory is enabled for this mode
        if not is_semantic_memory_enabled(mode):
            return []
        
        if not self.openai_client:
            logger.warning("OpenAI client not available for semantic search")
            return []
        
        # Generate embedding for current input
        try:
            embedding_response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=current_input
            )
            query_embedding = embedding_response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding for search: {e}")
            return []
        
        # Query for relevant memories
        # Note: This is a simplified query that doesn't use pgvector similarity
        # In production with pgvector, we would use vector cosine similarity
        try:
            # Get memories for this user and mode that aren't expired
            memories = self.db.query(SemanticMemory).filter(
                and_(
                    SemanticMemory.user_id == user_id,
                    SemanticMemory.mode == mode,
                    SemanticMemory.importance_score >= min_importance,
                    or_(
                        SemanticMemory.expires_at.is_(None),
                        SemanticMemory.expires_at > datetime.utcnow()
                    )
                )
            ).order_by(
                desc(SemanticMemory.importance_score),
                desc(SemanticMemory.access_count)
            ).limit(max_memories * 2).all()
            
            # Record access for retrieved memories
            for memory in memories:
                memory.record_access()
            
            self.db.commit()
            
            # Return top memories (simplified - in production would use vector similarity)
            return memories[:max_memories]
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    def format_memories_for_prompt(self, memories: List[SemanticMemory]) -> str:
        """
        Format retrieved memories for inclusion in AI prompts
        
        Args:
            memories: List of SemanticMemory objects
            
        Returns:
            Formatted string for AI prompt
        """
        if not memories:
            return ""
        
        formatted = "Relevant Context from Previous Conversations:\n\n"
        
        for i, memory in enumerate(memories, 1):
            tags_str = ", ".join(memory.tags_list) if memory.tags_list else ""
            tags_suffix = f" ({tags_str})" if tags_str else ""
            formatted += f"{i}. {memory.content}{tags_suffix}\n"
        
        return formatted + "\n"
    
    def delete_memories_for_mode(self, user_id: str, mode: str) -> int:
        """
        Delete all memories for a specific mode
        
        Args:
            user_id: The user's ID
            mode: The mode to delete memories for
            
        Returns:
            Number of memories deleted
        """
        try:
            deleted = self.db.query(SemanticMemory).filter(
                and_(
                    SemanticMemory.user_id == user_id,
                    SemanticMemory.mode == mode
                )
            ).delete()
            
            self.db.commit()
            logger.info(f"Deleted {deleted} memories for user {user_id}, mode {mode}")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting memories: {e}")
            return 0
    
    def delete_expired_memories(self) -> int:
        """
        Delete all expired memories (cleanup job)
        
        Returns:
            Number of memories deleted
        """
        try:
            deleted = self.db.query(SemanticMemory).filter(
                SemanticMemory.expires_at < datetime.utcnow()
            ).delete()
            
            self.db.commit()
            logger.info(f"Deleted {deleted} expired memories")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting expired memories: {e}")
            return 0
    
    # Private helper methods
    
    def _build_conversation_text(self, messages: List[Message]) -> str:
        """Build a text representation of the conversation"""
        lines = []
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            lines.append(f"{role}: {msg.content}")
        return "\n\n".join(lines)
    
    async def _extract_memories_with_ai(
        self,
        conversation_text: str,
        mode: str,
        user_id: str,
        conversation_id: str,
        max_memories: int
    ) -> List[Dict[str, Any]]:
        """
        Use AI to extract memories from conversation text
        
        This is a placeholder - in production, this would call OpenAI/Claude API
        to intelligently extract memories with their importance scores.
        """
        # For now, return empty list
        # In production, implement this with AI API call
        logger.warning("AI-based memory extraction not yet implemented")
        return []