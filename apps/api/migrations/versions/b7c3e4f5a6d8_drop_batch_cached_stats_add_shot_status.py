"""drop batch cached stats columns, add shot status and error_message

Revision ID: b7c3e4f5a6d8
Revises: 239f9a65d33f
Create Date: 2026-03-19 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7c3e4f5a6d8'
down_revision: Union[str, Sequence[str], None] = '239f9a65d33f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop cached stats columns from batches (now computed live from videos)
    op.drop_column('batches', 'status')
    op.drop_column('batches', 'total_videos')
    op.drop_column('batches', 'completed_count')
    op.drop_column('batches', 'failed_count')
    op.drop_column('batches', 'processing_count')
    op.drop_column('batches', 'pending_count')
    op.drop_column('batches', 'duration_ms')
    op.drop_column('batches', 'model_costs')
    op.drop_column('batches', 'total_cost_usd')

    # Add status and error_message to shots
    op.add_column('shots', sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'))
    op.add_column('shots', sa.Column('error_message', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove shot status columns
    op.drop_column('shots', 'error_message')
    op.drop_column('shots', 'status')

    # Restore cached stats columns on batches
    op.add_column('batches', sa.Column('status', sa.VARCHAR(length=30), nullable=False, server_default='processing'))
    op.add_column('batches', sa.Column('total_videos', sa.INTEGER(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('completed_count', sa.INTEGER(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('failed_count', sa.INTEGER(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('processing_count', sa.INTEGER(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('pending_count', sa.INTEGER(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('duration_ms', sa.INTEGER(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('model_costs', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'))
    op.add_column('batches', sa.Column('total_cost_usd', sa.FLOAT(), nullable=False, server_default='0.0'))
