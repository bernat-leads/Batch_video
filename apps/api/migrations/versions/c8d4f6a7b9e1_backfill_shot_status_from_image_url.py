"""backfill shot status from image_url

Revision ID: c8d4f6a7b9e1
Revises: b7c3e4f5a6d8
Create Date: 2026-03-19 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c8d4f6a7b9e1'
down_revision: Union[str, Sequence[str], None] = 'b7c3e4f5a6d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Set status='generated' for shots that already have an image_url."""
    op.execute(
        "UPDATE shots SET status = 'generated' WHERE image_url IS NOT NULL"
    )


def downgrade() -> None:
    """Reset all statuses back to pending."""
    op.execute(
        "UPDATE shots SET status = 'pending' WHERE status = 'generated'"
    )
