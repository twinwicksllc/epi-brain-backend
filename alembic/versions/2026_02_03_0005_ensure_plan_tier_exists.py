"""Add plan_tier and Commercial MVP fields to users table

Revision ID: 2026_02_03_0005
Revises: 2026_02_03_0004
Create Date: 2026-02-04 00:00:00.000000

This migration ensures all Commercial MVP fields exist in the users table.
If you've already run 2026_02_03_0003, this may fail on the enum creation,
which is fine - just skip it in that case.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2026_02_03_0005'
down_revision = '2026_02_03_0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if plan_tier column already exists
    # Create PlanTier enum type if it doesn't exist
    try:
        op.execute("CREATE TYPE plantier AS ENUM ('free', 'premium', 'enterprise')")
    except Exception:
        # Enum already exists, that's fine
        pass
    
    # Add plan_tier column if it doesn't exist
    try:
        op.add_column('users', sa.Column('plan_tier', sa.Enum('free', 'premium', 'enterprise', name='plantier'), nullable=False, server_default='free'))
    except Exception:
        # Column already exists, that's fine
        pass
    
    # Add Paddle fields if they don't exist
    try:
        op.add_column('users', sa.Column('paddle_subscription_id', sa.String(255), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('users', sa.Column('paddle_customer_id', sa.String(255), nullable=True))
    except Exception:
        pass
    
    # Add special discount fields if they don't exist
    try:
        op.add_column('users', sa.Column('is_senior', sa.Boolean(), nullable=False, server_default='false'))
    except Exception:
        pass
    
    try:
        op.add_column('users', sa.Column('is_military', sa.Boolean(), nullable=False, server_default='false'))
    except Exception:
        pass
    
    try:
        op.add_column('users', sa.Column('is_firstresponder', sa.Boolean(), nullable=False, server_default='false'))
    except Exception:
        pass
    
    # Create indexes if they don't exist
    try:
        op.create_index('ix_users_paddle_subscription_id', 'users', ['paddle_subscription_id'], unique=True)
    except Exception:
        pass
    
    try:
        op.create_index('ix_users_paddle_customer_id', 'users', ['paddle_customer_id'], unique=True)
    except Exception:
        pass


def downgrade() -> None:
    # Drop indexes
    try:
        op.drop_index('ix_users_paddle_customer_id', table_name='users')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_users_paddle_subscription_id', table_name='users')
    except Exception:
        pass
    
    # Drop columns
    try:
        op.drop_column('users', 'is_firstresponder')
    except Exception:
        pass
    
    try:
        op.drop_column('users', 'is_military')
    except Exception:
        pass
    
    try:
        op.drop_column('users', 'is_senior')
    except Exception:
        pass
    
    try:
        op.drop_column('users', 'paddle_customer_id')
    except Exception:
        pass
    
    try:
        op.drop_column('users', 'paddle_subscription_id')
    except Exception:
        pass
    
    try:
        op.drop_column('users', 'plan_tier')
    except Exception:
        pass
    
    # Drop enum type
    try:
        op.execute("DROP TYPE plantier")
    except Exception:
        pass
