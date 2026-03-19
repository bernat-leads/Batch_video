"""Batch SQLAlchemy model."""

import uuid

from sqlalchemy import JSON, String, Text, case, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from api.core.models import BaseModel
from api.videos.models.video import Video


class Batch(BaseModel):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    column_mapping: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    videos: Mapped[list[Video]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# Computed column properties — live stats derived from videos via subqueries.
# ---------------------------------------------------------------------------


def _video_count(status: str | None = None):
    """Build a correlated subquery counting videos for a batch."""
    stmt = select(func.count()).where(Video.batch_id == Batch.id).correlate(Batch)
    if status:
        stmt = stmt.where(Video.status == status)
    return stmt.scalar_subquery()


Batch.total_videos = column_property(_video_count(), deferred=False)
Batch.completed_count = column_property(_video_count("finished"), deferred=False)
Batch.failed_count = column_property(_video_count("failed"), deferred=False)
Batch.pending_count = column_property(_video_count("processing"), deferred=False)

Batch.duration_ms = column_property(
    select(func.coalesce(func.sum(Video.duration_ms), 0))
    .where(Video.batch_id == Batch.id)
    .correlate(Batch)
    .scalar_subquery(),
    deferred=False,
)

Batch.total_cost_usd = column_property(
    select(func.coalesce(func.sum(Video.total_cost_usd), 0.0))
    .where(Video.batch_id == Batch.id)
    .correlate(Batch)
    .scalar_subquery(),
    deferred=False,
)

Batch.status = column_property(
    case(
        (_video_count() == 0, "failed"),
        (_video_count("processing") > 0, "processing"),
        (_video_count("failed") == _video_count(), "failed"),
        else_="completed",
    ),
    deferred=False,
)
