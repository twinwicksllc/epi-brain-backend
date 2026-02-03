"""Sync user table columns with the latest model

Revision ID: 2026_02_04_0001
Revises: 2026_02_03_0005
Create Date: 2026-02-04 00:00:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '2026_02_04_0001'
down_revision = '2026_02_03_0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ensure every User column from the latest model exists in the database."""
    op.execute("CREATE TYPE IF NOT EXISTS plantier AS ENUM ('free', 'premium', 'enterprise')")

    statements = [
        # subscription identifiers
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS tier VARCHAR(50) NOT NULL DEFAULT 'free'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255)",

        # Commercial MVP fields
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_tier plantier NOT NULL DEFAULT 'free'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS paddle_subscription_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS paddle_customer_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_senior BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_military BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_firstresponder BOOLEAN NOT NULL DEFAULT false",

        # Preferences
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS voice_preference VARCHAR(50) NOT NULL DEFAULT 'none'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS primary_mode VARCHAR(50) NOT NULL DEFAULT 'personal_friend'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS silo_id VARCHAR(50)",

        # Usage tracking
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS message_count VARCHAR(255) NOT NULL DEFAULT '0'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_message_reset TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()",

        # Voice limits
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS voice_limit INTEGER",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS voice_used INTEGER NOT NULL DEFAULT 0",

        # Admin/referral metadata
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin VARCHAR(10) NOT NULL DEFAULT 'false'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code VARCHAR(20)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by UUID",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_credits VARCHAR(255) NOT NULL DEFAULT '0'",

        # Memory & NEBP
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS global_memory JSON NOT NULL DEFAULT '{}'::json",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS nebp_phase VARCHAR(20) NOT NULL DEFAULT 'discovery'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS nebp_clarity_metrics JSON NOT NULL DEFAULT '{}'::json",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscribed_personalities JSON NOT NULL DEFAULT '[\"personal_friend\",\"discovery_mode\"]'::json",

        # Accountability & tone controls
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS accountability_style VARCHAR(50) NOT NULL DEFAULT 'adaptive'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS sentiment_override_enabled BOOLEAN NOT NULL DEFAULT true",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS depth_sensitivity_enabled BOOLEAN NOT NULL DEFAULT true",

        # Timestamp auditing
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE",
    ]

    for statement in statements:
        op.execute(statement)

    index_statements = [
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_paddle_subscription_id ON users (paddle_subscription_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_paddle_customer_id ON users (paddle_customer_id)",
    ]

    for statement in index_statements:
        op.execute(statement)


def downgrade() -> None:
    """Revert the schema to the previous revision by dropping the additions."""
    for statement in [
        "DROP INDEX IF EXISTS ix_users_paddle_customer_id",
        "DROP INDEX IF EXISTS ix_users_paddle_subscription_id",
        "ALTER TABLE users DROP COLUMN IF EXISTS last_login",
        "ALTER TABLE users DROP COLUMN IF EXISTS updated_at",
        "ALTER TABLE users DROP COLUMN IF EXISTS created_at",
        "ALTER TABLE users DROP COLUMN IF EXISTS depth_sensitivity_enabled",
        "ALTER TABLE users DROP COLUMN IF EXISTS sentiment_override_enabled",
        "ALTER TABLE users DROP COLUMN IF EXISTS accountability_style",
        "ALTER TABLE users DROP COLUMN IF EXISTS subscribed_personalities",
        "ALTER TABLE users DROP COLUMN IF EXISTS nebp_clarity_metrics",
        "ALTER TABLE users DROP COLUMN IF EXISTS nebp_phase",
        "ALTER TABLE users DROP COLUMN IF EXISTS global_memory",
        "ALTER TABLE users DROP COLUMN IF EXISTS referral_credits",
        "ALTER TABLE users DROP COLUMN IF EXISTS referred_by",
        "ALTER TABLE users DROP COLUMN IF EXISTS referral_code",
        "ALTER TABLE users DROP COLUMN IF EXISTS is_admin",
        "ALTER TABLE users DROP COLUMN IF EXISTS voice_used",
        "ALTER TABLE users DROP COLUMN IF EXISTS voice_limit",
        "ALTER TABLE users DROP COLUMN IF EXISTS last_message_reset",
        "ALTER TABLE users DROP COLUMN IF EXISTS message_count",
        "ALTER TABLE users DROP COLUMN IF EXISTS silo_id",
        "ALTER TABLE users DROP COLUMN IF EXISTS primary_mode",
        "ALTER TABLE users DROP COLUMN IF EXISTS voice_preference",
        "ALTER TABLE users DROP COLUMN IF EXISTS is_firstresponder",
        "ALTER TABLE users DROP COLUMN IF EXISTS is_military",
        "ALTER TABLE users DROP COLUMN IF EXISTS is_senior",
        "ALTER TABLE users DROP COLUMN IF EXISTS paddle_customer_id",
        "ALTER TABLE users DROP COLUMN IF EXISTS paddle_subscription_id",
        "ALTER TABLE users DROP COLUMN IF EXISTS plan_tier",
        "ALTER TABLE users DROP COLUMN IF EXISTS stripe_subscription_id",
        "ALTER TABLE users DROP COLUMN IF EXISTS stripe_customer_id",
        "ALTER TABLE users DROP COLUMN IF EXISTS tier",
        "DROP TYPE IF EXISTS plantier",
    ]:
        op.execute(statement)
