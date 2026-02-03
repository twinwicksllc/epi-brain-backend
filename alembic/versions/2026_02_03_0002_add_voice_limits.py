"""Add voice_limit and voice_used tracking to users

Revision ID: c9b2d3e4f5g6
Revises: b8a1c2d3e4f5
Create Date: 2026-02-03 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9b2d3e4f5g6'
down_revision = 'b8a1c2d3e4f5'
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
