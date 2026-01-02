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
    op.add_column('conversations', 
        sa.Column('depth', sa.Float(), nullable=False, server_default='0.0')
    )
    op.add_column('conversations',
        sa.Column('last_depth_update', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.add_column('conversations',
        sa.Column('depth_enabled', sa.Boolean(), nullable=False, server_default='true')
    )
    
    # Add turn score columns to messages table (for analytics/debugging)
    op.add_column('messages',
        sa.Column('turn_score', sa.Float(), nullable=True)
    )
    op.add_column('messages',
        sa.Column('scoring_source', sa.String(20), nullable=True)
    )


def downgrade():
    # Remove depth tracking columns from conversations
    op.drop_column('conversations', 'depth')
    op.drop_column('conversations', 'last_depth_update')
    op.drop_column('conversations', 'depth_enabled')
    
    # Remove turn score columns from messages
    op.drop_column('messages', 'turn_score')
    op.drop_column('messages', 'scoring_source')