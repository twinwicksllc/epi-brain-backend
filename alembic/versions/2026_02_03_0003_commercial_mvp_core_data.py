"""Add Commercial MVP core data fields

Revision ID: 2026_02_03_0003
Revises: 2026_02_03_0002
Create Date: 2026-02-03 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '2026_02_03_0003'
down_revision = '2026_02_03_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create PlanTier enum type
    op.execute("CREATE TYPE plantier AS ENUM ('free', 'premium', 'enterprise')")
    
    # Add new columns to users table for Commercial MVP
    op.add_column('users', sa.Column('plan_tier', sa.Enum('free', 'premium', 'enterprise', name='plantier'), nullable=False, server_default='free'))
    op.add_column('users', sa.Column('paddle_subscription_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('paddle_customer_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('is_senior', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('is_military', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('is_firstresponder', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create unique indexes for Paddle fields
    op.create_index('ix_users_paddle_subscription_id', 'users', ['paddle_subscription_id'], unique=True)
    op.create_index('ix_users_paddle_customer_id', 'users', ['paddle_customer_id'], unique=True)
    
    # Create usage_logs table for token tracking and analytics
    op.create_table(
        'usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_tier', sa.String(50), nullable=False),
        sa.Column('is_enterprise_account', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enterprise_account_id', sa.String(255), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('personality_mode', sa.String(50), nullable=False),
        sa.Column('tokens_input', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tokens_output', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tokens_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('token_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('llm_model', sa.String(100), nullable=False),
        sa.Column('llm_provider', sa.String(50), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('chat_metadata', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for usage_logs table for better query performance
    op.create_index('ix_usage_logs_user_id', 'usage_logs', ['user_id'])
    op.create_index('ix_usage_logs_plan_tier', 'usage_logs', ['plan_tier'])
    op.create_index('ix_usage_logs_is_enterprise_account', 'usage_logs', ['is_enterprise_account'])
    op.create_index('ix_usage_logs_enterprise_account_id', 'usage_logs', ['enterprise_account_id'])
    op.create_index('ix_usage_logs_conversation_id', 'usage_logs', ['conversation_id'])
    op.create_index('ix_usage_logs_personality_mode', 'usage_logs', ['personality_mode'])
    op.create_index('ix_usage_logs_llm_model', 'usage_logs', ['llm_model'])
    op.create_index('ix_usage_logs_created_at', 'usage_logs', ['created_at'])


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index('ix_usage_logs_created_at', table_name='usage_logs')
    op.drop_index('ix_usage_logs_llm_model', table_name='usage_logs')
    op.drop_index('ix_usage_logs_personality_mode', table_name='usage_logs')
    op.drop_index('ix_usage_logs_conversation_id', table_name='usage_logs')
    op.drop_index('ix_usage_logs_enterprise_account_id', table_name='usage_logs')
    op.drop_index('ix_usage_logs_is_enterprise_account', table_name='usage_logs')
    op.drop_index('ix_usage_logs_plan_tier', table_name='usage_logs')
    op.drop_index('ix_usage_logs_user_id', table_name='usage_logs')
    
    # Drop usage_logs table
    op.drop_table('usage_logs')
    
    # Drop user column indexes
    op.drop_index('ix_users_paddle_customer_id', table_name='users')
    op.drop_index('ix_users_paddle_subscription_id', table_name='users')
    
    # Drop user columns
    op.drop_column('users', 'is_firstresponder')
    op.drop_column('users', 'is_military')
    op.drop_column('users', 'is_senior')
    op.drop_column('users', 'paddle_customer_id')
    op.drop_column('users', 'paddle_subscription_id')
    op.drop_column('users', 'plan_tier')
    
    # Drop enum type
    op.execute("DROP TYPE plantier")
