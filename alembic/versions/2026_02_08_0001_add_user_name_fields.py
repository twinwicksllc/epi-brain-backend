"""Add first_name and full_name to users table

Revision ID: 2026_02_08_0001
Revises: 2026_02_04_0001
Create Date: 2026-02-08 00:00:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '2026_02_08_0001'
down_revision = '2026_02_04_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add first_name and full_name columns to users table."""
    try:
        op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100)")
        op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255)")
    except Exception as e:
        # Column already exists, continue
        pass


def downgrade() -> None:
    """Remove first_name and full_name columns from users table."""
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS first_name")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS full_name")
