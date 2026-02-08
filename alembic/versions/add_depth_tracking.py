"""Add depth tracking to conversations and messages

Revision ID: 001_add_depth_tracking
Revises: 
Create Date: 2026-01-02 02:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '001_add_depth_tracking'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add depth tracking columns to conversations table
    # Use execute with IF NOT EXISTS to handle idempotency
    try:
        op.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS depth FLOAT NOT NULL DEFAULT 0.0")
        op.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS last_depth_update TIMESTAMP NOT NULL DEFAULT now()")
        op.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS depth_enabled BOOLEAN NOT NULL DEFAULT true")
    except:
        # Columns might already exist, continue
        pass
    
    # Add turn score columns to messages table (for analytics/debugging)
    try:
        op.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS turn_score FLOAT")
        op.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS scoring_source VARCHAR(20)")
    except:
        # Columns might already exist, continue
        pass


def downgrade():
    # Remove depth tracking columns from conversations
    op.drop_column('conversations', 'depth')
    op.drop_column('conversations', 'last_depth_update')
    op.drop_column('conversations', 'depth_enabled')
    
    # Remove turn score columns from messages
    op.drop_column('messages', 'turn_score')
    op.drop_column('messages', 'scoring_source')