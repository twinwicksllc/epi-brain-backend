"""Add user_notes table for Pocket EPI MVP

Revision ID: 2026_02_03_0004
Revises: 2026_02_03_0003
Create Date: 2026-02-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2026_02_03_0004'
down_revision = '2026_02_03_0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_notes table for quick notes, drafts, and reflections
    op.create_table(
        'user_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('note_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('personality_mode', sa.String(50), nullable=True),
        sa.Column('tags', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for user_notes table
    op.create_index('ix_user_notes_user_id', 'user_notes', ['user_id'])
    op.create_index('ix_user_notes_note_type', 'user_notes', ['note_type'])
    op.create_index('ix_user_notes_conversation_id', 'user_notes', ['conversation_id'])
    op.create_index('ix_user_notes_created_at', 'user_notes', ['created_at'])
    
    # Create composite indexes for common query patterns
    op.create_index('ix_user_notes_user_type', 'user_notes', ['user_id', 'note_type'])
    op.create_index('ix_user_notes_user_created', 'user_notes', ['user_id', 'created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_user_notes_user_created', table_name='user_notes')
    op.drop_index('ix_user_notes_user_type', table_name='user_notes')
    op.drop_index('ix_user_notes_created_at', table_name='user_notes')
    op.drop_index('ix_user_notes_conversation_id', table_name='user_notes')
    op.drop_index('ix_user_notes_note_type', table_name='user_notes')
    op.drop_index('ix_user_notes_user_id', table_name='user_notes')
    
    # Drop table
    op.drop_table('user_notes')
