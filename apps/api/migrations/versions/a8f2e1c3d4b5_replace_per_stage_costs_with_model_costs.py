"""replace per-stage cost columns with model_costs json

Revision ID: a8f2e1c3d4b5
Revises: 3dd36cf742e2
Create Date: 2026-03-18 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8f2e1c3d4b5'
down_revision: Union[str, Sequence[str], None] = '3dd36cf742e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add model_costs JSON column
    op.add_column('videos', sa.Column('model_costs', sa.JSON(), server_default='{}', nullable=False))
    op.add_column('batches', sa.Column('model_costs', sa.JSON(), server_default='{}', nullable=False))

    # 2. Migrate existing per-stage data into model_costs
    op.execute("""
        UPDATE videos SET model_costs = jsonb_build_object(
            'eleven_multilingual_v2', jsonb_build_object(
                'token_count', tts_token_count, 'cost_usd', tts_cost_usd
            ),
            'claude-sonnet-4-20250514', jsonb_build_object(
                'token_count', segmentation_token_count, 'cost_usd', segmentation_cost_usd
            ),
            'imagen-4.0-fast-generate-001', jsonb_build_object(
                'token_count', image_generation_token_count, 'cost_usd', image_generation_cost_usd
            )
        )
        WHERE tts_cost_usd > 0 OR segmentation_cost_usd > 0 OR image_generation_cost_usd > 0
    """)
    op.execute("""
        UPDATE batches SET model_costs = jsonb_build_object(
            'eleven_multilingual_v2', jsonb_build_object(
                'token_count', tts_token_count, 'cost_usd', tts_cost_usd
            ),
            'claude-sonnet-4-20250514', jsonb_build_object(
                'token_count', segmentation_token_count, 'cost_usd', segmentation_cost_usd
            ),
            'imagen-4.0-fast-generate-001', jsonb_build_object(
                'token_count', image_generation_token_count, 'cost_usd', image_generation_cost_usd
            )
        )
        WHERE tts_cost_usd > 0 OR segmentation_cost_usd > 0 OR image_generation_cost_usd > 0
    """)

    # 3. Drop old per-stage columns + total_token_count (units differ per model)
    op.drop_column('videos', 'tts_cost_usd')
    op.drop_column('videos', 'tts_token_count')
    op.drop_column('videos', 'segmentation_cost_usd')
    op.drop_column('videos', 'segmentation_token_count')
    op.drop_column('videos', 'image_generation_cost_usd')
    op.drop_column('videos', 'image_generation_token_count')
    op.drop_column('videos', 'total_token_count')

    op.drop_column('batches', 'tts_cost_usd')
    op.drop_column('batches', 'tts_token_count')
    op.drop_column('batches', 'segmentation_cost_usd')
    op.drop_column('batches', 'segmentation_token_count')
    op.drop_column('batches', 'image_generation_cost_usd')
    op.drop_column('batches', 'image_generation_token_count')
    op.drop_column('batches', 'total_token_count')


def downgrade() -> None:
    # Re-add per-stage columns + total_token_count
    for table in ('videos', 'batches'):
        op.add_column(table, sa.Column('total_token_count', sa.Integer(), server_default='0', nullable=False))
        op.add_column(table, sa.Column('tts_cost_usd', sa.Float(), server_default='0', nullable=False))
        op.add_column(table, sa.Column('tts_token_count', sa.Integer(), server_default='0', nullable=False))
        op.add_column(table, sa.Column('segmentation_cost_usd', sa.Float(), server_default='0', nullable=False))
        op.add_column(table, sa.Column('segmentation_token_count', sa.Integer(), server_default='0', nullable=False))
        op.add_column(table, sa.Column('image_generation_cost_usd', sa.Float(), server_default='0', nullable=False))
        op.add_column(table, sa.Column('image_generation_token_count', sa.Integer(), server_default='0', nullable=False))

    # Migrate data back from JSON
    for table in ('videos', 'batches'):
        op.execute(f"""
            UPDATE {table} SET
                tts_cost_usd = COALESCE((model_costs->'eleven_multilingual_v2'->>'cost_usd')::float, 0),
                tts_token_count = COALESCE((model_costs->'eleven_multilingual_v2'->>'token_count')::int, 0),
                segmentation_cost_usd = COALESCE((model_costs->'claude-sonnet-4-20250514'->>'cost_usd')::float, 0),
                segmentation_token_count = COALESCE((model_costs->'claude-sonnet-4-20250514'->>'token_count')::int, 0),
                image_generation_cost_usd = COALESCE((model_costs->'imagen-4.0-fast-generate-001'->>'cost_usd')::float, 0),
                image_generation_token_count = COALESCE((model_costs->'imagen-4.0-fast-generate-001'->>'token_count')::int, 0)
        """)

    op.drop_column('videos', 'model_costs')
    op.drop_column('batches', 'model_costs')
