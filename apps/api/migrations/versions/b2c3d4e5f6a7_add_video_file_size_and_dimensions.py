"""add video file_size_bytes, width, height columns

Revision ID: b2c3d4e5f6a7
Revises: 07cfd31b6aab
Create Date: 2026-03-14 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = '07cfd31b6aab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('videos', sa.Column('file_size_bytes', sa.Integer(), server_default='0', nullable=False))
    op.add_column('videos', sa.Column('width', sa.Integer(), server_default='1080', nullable=False))
    op.add_column('videos', sa.Column('height', sa.Integer(), server_default='1920', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('videos', 'height')
    op.drop_column('videos', 'width')
    op.drop_column('videos', 'file_size_bytes')
