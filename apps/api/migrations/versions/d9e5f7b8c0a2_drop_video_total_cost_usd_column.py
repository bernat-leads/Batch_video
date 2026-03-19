"""drop video total_cost_usd column (now computed from model_costs JSON)

Revision ID: d9e5f7b8c0a2
Revises: c8d4f6a7b9e1
Create Date: 2026-03-19 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd9e5f7b8c0a2'
down_revision: Union[str, Sequence[str], None] = 'c8d4f6a7b9e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop total_cost_usd — now computed live from model_costs JSON."""
    op.drop_column('videos', 'total_cost_usd')


def downgrade() -> None:
    """Restore total_cost_usd and backfill from model_costs."""
    op.add_column('videos', sa.Column('total_cost_usd', sa.FLOAT(), nullable=False, server_default='0.0'))
    # Backfill from model_costs JSON
    op.execute("""
        UPDATE videos SET total_cost_usd = COALESCE(
            (SELECT SUM((value->>'cost_usd')::float) FROM jsonb_each(model_costs)),
            0.0
        )
    """)
