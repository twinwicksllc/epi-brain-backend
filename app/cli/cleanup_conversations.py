"""CLI command for cleaning up old conversations"""

import click
from sqlalchemy.orm import Session
from datetime import datetime
import sys

from app.database import get_db
from app.services.conversation_cleanup import ConversationCleanupService


@click.group()
def cleanup():
    """Conversation cleanup commands"""
    pass


@cleanup.command()
@click.option('--days', default=30, help='Number of days threshold (default: 30)')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
@click.option('--batch-size', default=100, help='Batch size for deletion (default: 100)')
def old(days: int, dry_run: bool, batch_size: int):
    """Clean up conversations older than specified days"""
    click.echo(f"Starting conversation cleanup (threshold: {days} days)")
    click.echo(f"Dry run: {dry_run}")
    click.echo(f"Batch size: {batch_size}")
    click.echo("-" * 50)
    
    db = next(get_db())
    cleanup_service = ConversationCleanupService(days_threshold=days)
    
    try:
        # First, count what we have
        count = cleanup_service.count_old_conversations(db)
        click.echo(f"Found {count} conversations older than {days} days")
        
        if count == 0:
            click.echo("Nothing to clean up!")
            return
        
        if not dry_run:
            click.confirm(f"\nDelete {count} conversations and their messages?", abort=True)
        
        # Perform cleanup
        stats = cleanup_service.cleanup_old_conversations(
            db,
            batch_size=batch_size,
            dry_run=dry_run
        )
        
        # Display results
        click.echo("-" * 50)
        click.echo("Cleanup Summary:")
        click.echo(f"  Conversations deleted: {stats['total_deleted']}")
        click.echo(f"  Messages deleted: {stats['total_messages_deleted']}")
        click.echo(f"  Batches processed: {stats['batches_processed']}")
        click.echo(f"  Cutoff date: {stats['cutoff_date']}")
        
        if dry_run:
            click.echo("\nThis was a DRY RUN - no changes were made.")
        else:
            click.echo("\n✓ Cleanup completed successfully!")
    
    except Exception as e:
        click.echo(f"\n✗ Error during cleanup: {str(e)}", err=True)
        sys.exit(1)
    finally:
        db.close()


@cleanup.command()
@click.option('--days', default=30, help='Number of days threshold (default: 30)')
def count(days: int):
    """Count conversations older than specified days"""
    db = next(get_db())
    cleanup_service = ConversationCleanupService(days_threshold=days)
    
    try:
        count = cleanup_service.count_old_conversations(db)
        cutoff_date = cleanup_service.get_cutoff_date()
        
        click.echo(f"Conversations older than {days} days (before {cutoff_date}): {count}")
        
        if count > 0:
            click.echo(f"\nRun 'cleanup old --days {days}' to delete these conversations.")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        db.close()


@cleanup.command()
@click.option('--user-id', required=True, help='User ID to clean up for')
@click.option('--days', default=30, help='Number of days threshold (default: 30)')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
def user(user_id: str, days: int, dry_run: bool):
    """Clean up old conversations for a specific user"""
    click.echo(f"Cleaning up conversations for user: {user_id}")
    click.echo(f"Threshold: {days} days")
    click.echo(f"Dry run: {dry_run}")
    
    db = next(get_db())
    cleanup_service = ConversationCleanupService(days_threshold=days)
    
    try:
        stats = cleanup_service.cleanup_conversations_for_user(
            db,
            user_id=user_id,
            dry_run=dry_run
        )
        
        click.echo("-" * 50)
        click.echo(f"Conversations found: {stats['total_deleted']}")
        click.echo(f"Messages found: {stats['total_messages_deleted']}")
        click.echo(f"Cutoff date: {stats['cutoff_date']}")
        
        if not dry_run:
            click.echo("\n✓ Cleanup completed successfully!")
        else:
            click.echo("\nThis was a DRY RUN - no changes were made.")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    cleanup()