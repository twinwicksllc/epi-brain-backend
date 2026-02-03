"""Add silo_id and NEBP tracking fields to users

Revision ID: 2026_02_03_0001
Revises: 79010fc92133
Create Date: 2026-02-03 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_02_03_0001'
down_revision = '79010fc92133'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('silo_id', sa.String(length=50), nullable=True))
    op.add_column(
        'users',
        sa.Column('nebp_phase', sa.String(length=20), nullable=False, server_default='discovery')
    )
    op.add_column(
        'users',
        sa.Column('nebp_clarity_metrics', sa.JSON(), nullable=False, server_default='{}')
    )


def downgrade() -> None:
    op.drop_column('users', 'nebp_clarity_metrics')
    op.drop_column('users', 'nebp_phase')
    op.drop_column('users', 'silo_id')
