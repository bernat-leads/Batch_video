"""replace_flat_cost_fields_with_per_stage_ai_cost_columns

Revision ID: 7bcb6049e1fa
Revises: 29dc417ed63d
Create Date: 2026-03-16 19:14:59.085101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bcb6049e1fa'
down_revision: Union[str, Sequence[str], None] = '29dc417ed63d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- Videos: add per-stage columns with server_default ---
    op.add_column('videos', sa.Column('tts_cost_usd', sa.Float(), nullable=False, server_default='0'))
    op.add_column('videos', sa.Column('tts_token_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('videos', sa.Column('segmentation_cost_usd', sa.Float(), nullable=False, server_default='0'))
    op.add_column('videos', sa.Column('segmentation_token_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('videos', sa.Column('image_generation_cost_usd', sa.Float(), nullable=False, server_default='0'))
    op.add_column('videos', sa.Column('image_generation_token_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('videos', sa.Column('total_token_count', sa.Integer(), nullable=False, server_default='0'))

    # Migrate existing data: tokens_used → segmentation_token_count + total_token_count
    op.execute("UPDATE videos SET segmentation_token_count = tokens_used, total_token_count = tokens_used")

    op.drop_column('videos', 'tokens_used')
    op.drop_column('videos', 'avg_cost_per_shot_usd')

    # --- Batches: add per-stage columns with server_default ---
    op.add_column('batches', sa.Column('tts_cost_usd', sa.Float(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('tts_token_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('segmentation_cost_usd', sa.Float(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('segmentation_token_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('image_generation_cost_usd', sa.Float(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('image_generation_token_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('total_token_count', sa.Integer(), nullable=False, server_default='0'))

    # Migrate existing data: tokens_used → segmentation_token_count + total_token_count
    op.execute("UPDATE batches SET segmentation_token_count = tokens_used, total_token_count = tokens_used")

    op.drop_column('batches', 'tokens_used')
    op.drop_column('batches', 'avg_cost_per_video_usd')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('videos', sa.Column('tokens_used', sa.INTEGER(), autoincrement=False, nullable=False, server_default='0'))
    op.add_column('videos', sa.Column('avg_cost_per_shot_usd', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False, server_default='0'))
    op.execute("UPDATE videos SET tokens_used = segmentation_token_count")
    op.drop_column('videos', 'total_token_count')
    op.drop_column('videos', 'image_generation_token_count')
    op.drop_column('videos', 'image_generation_cost_usd')
    op.drop_column('videos', 'segmentation_token_count')
    op.drop_column('videos', 'segmentation_cost_usd')
    op.drop_column('videos', 'tts_token_count')
    op.drop_column('videos', 'tts_cost_usd')
    op.add_column('batches', sa.Column('avg_cost_per_video_usd', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False, server_default='0'))
    op.add_column('batches', sa.Column('tokens_used', sa.INTEGER(), autoincrement=False, nullable=False, server_default='0'))
    op.execute("UPDATE batches SET tokens_used = segmentation_token_count")
    op.drop_column('batches', 'total_token_count')
    op.drop_column('batches', 'image_generation_token_count')
    op.drop_column('batches', 'image_generation_cost_usd')
    op.drop_column('batches', 'segmentation_token_count')
    op.drop_column('batches', 'segmentation_cost_usd')
    op.drop_column('batches', 'tts_token_count')
    op.drop_column('batches', 'tts_cost_usd')
