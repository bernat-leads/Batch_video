"""add batch stat count columns

Revision ID: ca7e952f3c09
Revises: e9e1bdbfcdd2
Create Date: 2026-03-14 12:34:07.612696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca7e952f3c09'
down_revision: Union[str, Sequence[str], None] = 'e9e1bdbfcdd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('batches', sa.Column('completed_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('processing_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('pending_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('batches', 'pending_count')
    op.drop_column('batches', 'processing_count')
    op.drop_column('batches', 'failed_count')
    op.drop_column('batches', 'completed_count')
