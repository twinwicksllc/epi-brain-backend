"""Conversation Cleanup Service

This service handles the automatic cleanup of old conversations
that are older than a specified number of days.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, delete
import logging

from app.models.conversation import Conversation
from app.models.message import Message

logger = logging.getLogger(__name__)


class ConversationCleanupService:
    """Service for cleaning up old conversations"""
    
    def __init__(self, days_threshold: int = 30):
        """
        Initialize the cleanup service
        
        Args:
            days_threshold: Number of days after which conversations are considered old
        """
        self.days_threshold = days_threshold
    
    def get_cutoff_date(self) -> datetime:
        """
        Get the cutoff date for old conversations
        
        Returns:
            datetime: The cutoff date (current time minus threshold days)
        """
        return datetime.utcnow() - timedelta(days=self.days_threshold)
    
    def count_old_conversations(self, db: Session) -> int:
        """
        Count the number of conversations older than the threshold
        
        Args:
            db: Database session
            
        Returns:
            int: Number of old conversations
        """
        cutoff_date = self.get_cutoff_date()
        
        count = db.query(Conversation).filter(
            Conversation.updated_at < cutoff_date
        ).count()
        
        logger.info(f"Found {count} conversations older than {self.days_threshold} days")
        return count
    
    def get_old_conversations(self, db: Session, limit: int = 100) -> list[Conversation]:
        """
        Get conversations older than the threshold
        
        Args:
            db: Database session
            limit: Maximum number of conversations to return
            
        Returns:
            List of old conversations
        """
        cutoff_date = self.get_cutoff_date()
        
        conversations = db.query(Conversation).filter(
            Conversation.updated_at < cutoff_date
        ).limit(limit).all()
        
        return conversations
    
    def cleanup_old_conversations(
        self, 
        db: Session, 
        batch_size: int = 100,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Delete conversations older than the threshold
        
        Args:
            db: Database session
            batch_size: Number of conversations to delete in each batch
            dry_run: If True, only count what would be deleted without actually deleting
            
        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = self.get_cutoff_date()
        stats = {
            "total_deleted": 0,
            "total_messages_deleted": 0,
            "batches_processed": 0,
            "cutoff_date": cutoff_date.isoformat(),
            "dry_run": dry_run
        }
        
        logger.info(f"Starting cleanup of conversations older than {cutoff_date.isoformat()}")
        logger.info(f"Dry run: {dry_run}")
        
        while True:
            # Get a batch of old conversations
            old_conversations = db.query(Conversation).filter(
                Conversation.updated_at < cutoff_date
            ).limit(batch_size).all()
            
            if not old_conversations:
                break
            
            # Count messages in this batch
            batch_messages = sum(conv.message_count for conv in old_conversations)
            
            if dry_run:
                logger.info(f"Would delete {len(old_conversations)} conversations with {batch_messages} messages")
                stats["total_deleted"] += len(old_conversations)
                stats["total_messages_deleted"] += batch_messages
                stats["batches_processed"] += 1
                
                # In dry run, we break after first batch to avoid too much output
                break
            else:
                # Delete conversations (cascade will handle messages)
                conversation_ids = [conv.id for conv in old_conversations]
                
                # First delete messages manually to ensure proper cascade
                db.query(Message).filter(
                    Message.conversation_id.in_(conversation_ids)
                ).delete(synchronize_session=False)
                
                # Then delete conversations
                db.query(Conversation).filter(
                    Conversation.id.in_(conversation_ids)
                ).delete(synchronize_session=False)
                
                db.commit()
                
                stats["total_deleted"] += len(old_conversations)
                stats["total_messages_deleted"] += batch_messages
                stats["batches_processed"] += 1
                
                logger.info(
                    f"Deleted batch {stats['batches_processed']}: "
                    f"{len(old_conversations)} conversations, {batch_messages} messages"
                )
        
        logger.info(
            f"Cleanup complete. Total: {stats['total_deleted']} conversations, "
            f"{stats['total_messages_deleted']} messages in {stats['batches_processed']} batches"
        )
        
        return stats
    
    def cleanup_conversations_for_user(
        self,
        db: Session,
        user_id: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Delete old conversations for a specific user
        
        Args:
            db: Database session
            user_id: ID of the user to clean up conversations for
            dry_run: If True, only count what would be deleted
            
        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = self.get_cutoff_date()
        
        old_conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.updated_at < cutoff_date
        ).all()
        
        stats = {
            "user_id": user_id,
            "total_deleted": len(old_conversations),
            "total_messages_deleted": sum(conv.message_count for conv in old_conversations),
            "cutoff_date": cutoff_date.isoformat(),
            "dry_run": dry_run
        }
        
        if dry_run:
            logger.info(
                f"Would delete {len(old_conversations)} conversations for user {user_id} "
                f"({stats['total_messages_deleted']} messages)"
            )
        else:
            if old_conversations:
                conversation_ids = [conv.id for conv in old_conversations]
                
                # Delete messages first
                db.query(Message).filter(
                    Message.conversation_id.in_(conversation_ids)
                ).delete(synchronize_session=False)
                
                # Delete conversations
                db.query(Conversation).filter(
                    Conversation.id.in_(conversation_ids)
                ).delete(synchronize_session=False)
                
                db.commit()
                
                logger.info(
                    f"Deleted {len(old_conversations)} conversations for user {user_id} "
                    f"({stats['total_messages_deleted']} messages)"
                )
        
        return stats