"""change video model_costs from json to jsonb

Revision ID: e0f6a8b9d1c3
Revises: d9e5f7b8c0a2
Create Date: 2026-03-19 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e0f6a8b9d1c3'
down_revision: Union[str, Sequence[str], None] = 'd9e5f7b8c0a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change model_costs from json to jsonb."""
    op.alter_column(
        'videos',
        'model_costs',
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        postgresql_using='model_costs::jsonb',
    )


def downgrade() -> None:
    """Change model_costs back from jsonb to json."""
    op.alter_column(
        'videos',
        'model_costs',
        type_=postgresql.JSON(astext_type=sa.Text()),
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using='model_costs::json',
    )
