"""rename_video_status_pending_to_processing_completed_to_finished

Revision ID: d688fb97c3bf
Revises: 6681ae86ec51
Create Date: 2026-03-16 16:19:40.850363

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd688fb97c3bf'
down_revision: Union[str, Sequence[str], None] = '6681ae86ec51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename video status values: pending->processing, completed->finished."""
    op.execute("UPDATE videos SET status = 'processing' WHERE status = 'pending'")
    op.execute("UPDATE videos SET status = 'finished' WHERE status = 'completed'")


def downgrade() -> None:
    """Revert video status values."""
    op.execute("UPDATE videos SET status = 'pending' WHERE status = 'processing'")
    op.execute("UPDATE videos SET status = 'completed' WHERE status = 'finished'")
