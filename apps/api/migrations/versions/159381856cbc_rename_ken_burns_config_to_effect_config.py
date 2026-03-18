"""rename_ken_burns_config_to_effect_config

Revision ID: 159381856cbc
Revises: 7bcb6049e1fa
Create Date: 2026-03-17 16:15:17.389889

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '159381856cbc'
down_revision: Union[str, Sequence[str], None] = '7bcb6049e1fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('shots', 'ken_burns_config', new_column_name='effect_config')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('shots', 'effect_config', new_column_name='ken_burns_config')
