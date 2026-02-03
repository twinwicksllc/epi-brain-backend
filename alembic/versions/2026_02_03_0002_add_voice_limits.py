"""Add voice_limit and voice_used tracking to users

Revision ID: 2026_02_03_0002
Revises: 2026_02_03_0001
Create Date: 2026-02-03 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_02_03_0002'
down_revision = '2026_02_03_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('voice_limit', sa.Integer(), nullable=True)  # null = unlimited (for admin/pro)
    )
    op.add_column(
        'users',
        sa.Column('voice_used', sa.Integer(), nullable=False, server_default='0')  # Voice messages used today
    )


def downgrade() -> None:
    op.drop_column('users', 'voice_used')
    op.drop_column('users', 'voice_limit')
