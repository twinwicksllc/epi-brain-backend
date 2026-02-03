"""
User Note Service
Manage user notes, drafts, reflections, and thoughts
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
import logging

from app.models.user_note import UserNote

logger = logging.getLogger(__name__)


class UserNoteService:
    """Service for managing user notes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_note(
        self,
        user_id: str,
        content: str,
        note_type: str = "quick_note",
        title: Optional[str] = None,
        conversation_id: Optional[str] = None,
        personality_mode: Optional[str] = None,
        tags: Optional[str] = None
    ) -> UserNote:
        """
        Create a new note for a user
        
        Args:
            user_id: User ID
            content: Note content
            note_type: Type (quick_note, draft, reflection, thought)
            title: Optional title
            conversation_id: Optional conversation link
            personality_mode: AI personality that created this
            tags: Comma-separated tags
        
        Returns:
            Created UserNote
        """
        try:
            note = UserNote(
                user_id=user_id,
                note_type=note_type,
                title=title,
                content=content,
                conversation_id=conversation_id,
                personality_mode=personality_mode,
                tags=tags
            )
            
            self.db.add(note)
            self.db.commit()
            self.db.refresh(note)
            
            logger.info(f"Created {note_type} for user {user_id}: {title or 'Untitled'}")
            
            return note
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create note for user {user_id}: {str(e)}")
            raise
    
    def get_user_notes(
        self,
        user_id: str,
        note_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[UserNote]:
        """
        Get notes for a user
        
        Args:
            user_id: User ID
            note_type: Optional filter by type
            limit: Max notes to return
            offset: Pagination offset
        
        Returns:
            List of UserNote objects
        """
        query = self.db.query(UserNote).filter(UserNote.user_id == user_id)
        
        if note_type:
            query = query.filter(UserNote.note_type == note_type)
        
        query = query.order_by(desc(UserNote.created_at))
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def get_note_by_id(self, note_id: str, user_id: str) -> Optional[UserNote]:
        """
        Get a specific note by ID (with user verification)
        
        Args:
            note_id: Note ID
            user_id: User ID (for authorization)
        
        Returns:
            UserNote if found and belongs to user, None otherwise
        """
        return self.db.query(UserNote).filter(
            UserNote.id == note_id,
            UserNote.user_id == user_id
        ).first()
    
    def update_note(
        self,
        note_id: str,
        user_id: str,
        content: Optional[str] = None,
        title: Optional[str] = None,
        tags: Optional[str] = None
    ) -> Optional[UserNote]:
        """
        Update an existing note
        
        Args:
            note_id: Note ID
            user_id: User ID (for authorization)
            content: New content
            title: New title
            tags: New tags
        
        Returns:
            Updated UserNote or None if not found
        """
        note = self.get_note_by_id(note_id, user_id)
        
        if not note:
            return None
        
        try:
            if content is not None:
                note.content = content
            if title is not None:
                note.title = title
            if tags is not None:
                note.tags = tags
            
            note.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(note)
            
            logger.info(f"Updated note {note_id} for user {user_id}")
            
            return note
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update note {note_id}: {str(e)}")
            raise
    
    def delete_note(self, note_id: str, user_id: str) -> bool:
        """
        Delete a note
        
        Args:
            note_id: Note ID
            user_id: User ID (for authorization)
        
        Returns:
            True if deleted, False if not found
        """
        note = self.get_note_by_id(note_id, user_id)
        
        if not note:
            return False
        
        try:
            self.db.delete(note)
            self.db.commit()
            
            logger.info(f"Deleted note {note_id} for user {user_id}")
            
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete note {note_id}: {str(e)}")
            raise
    
    def search_notes(
        self,
        user_id: str,
        search_term: str,
        limit: int = 20
    ) -> List[UserNote]:
        """
        Search notes by content or title
        
        Args:
            user_id: User ID
            search_term: Search term
            limit: Max results
        
        Returns:
            List of matching UserNote objects
        """
        search_pattern = f"%{search_term}%"
        
        return self.db.query(UserNote).filter(
            UserNote.user_id == user_id
        ).filter(
            (UserNote.content.ilike(search_pattern)) |
            (UserNote.title.ilike(search_pattern))
        ).order_by(desc(UserNote.created_at)).limit(limit).all()
    
    def get_notes_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for user's notes
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with note statistics
        """
        from sqlalchemy import func
        
        # Count by type
        type_counts = self.db.query(
            UserNote.note_type,
            func.count(UserNote.id).label('count')
        ).filter(
            UserNote.user_id == user_id
        ).group_by(UserNote.note_type).all()
        
        # Recent notes
        recent_notes = self.get_user_notes(user_id, limit=5)
        
        return {
            "total_notes": sum(count for _, count in type_counts),
            "by_type": {note_type: count for note_type, count in type_counts},
            "recent_notes": [
                {
                    "id": str(note.id),
                    "type": note.note_type,
                    "title": note.title,
                    "preview": note.content[:100] + "..." if len(note.content) > 100 else note.content,
                    "created_at": note.created_at.isoformat()
                }
                for note in recent_notes
            ]
        }
