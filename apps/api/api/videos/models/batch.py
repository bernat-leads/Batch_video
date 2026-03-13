"""Batch SQLAlchemy model."""

import uuid

from sqlalchemy import Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.models import BaseModel


class Batch(BaseModel):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_videos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_cost_per_video_usd: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    videos: Mapped[list["Video"]] = relationship(  # noqa: F821
        back_populates="batch",
        cascade="all, delete-orphan",
    )
