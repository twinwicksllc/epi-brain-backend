"""Add subscription tracking to User model

Revision ID: 002_add_subscription_tracking
Revises: 001_add_depth_tracking
Create Date: 2026-01-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_subscription_tracking'
down_revision = '001_add_depth_tracking'
branch_labels = None
depends_on = None


def upgrade():
    # Add subscribed_personalities column to users table
    op.add_column('users',
        sa.Column('subscribed_personalities', sa.JSON(), nullable=False, server_default='["personal_friend"]')
    )


def downgrade():
    # Remove subscribed_personalities column from users table
    op.drop_column('users', 'subscribed_personalities')
