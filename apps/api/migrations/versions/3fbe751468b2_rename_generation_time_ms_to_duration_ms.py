"""rename generation_time_ms to duration_ms

Revision ID: 3fbe751468b2
Revises: 805b44dd1bb0
Create Date: 2026-03-16 10:02:18.548892

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '3fbe751468b2'
down_revision: Union[str, Sequence[str], None] = '805b44dd1bb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('batches', 'generation_time_ms', new_column_name='duration_ms')
    op.drop_column('videos', 'generation_time_ms')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('batches', 'duration_ms', new_column_name='generation_time_ms')
    op.add_column('videos', op.Column('generation_time_ms', op.Integer(), nullable=False, server_default='0'))
