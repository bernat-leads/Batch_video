"""Batch SQLAlchemy model."""

import uuid

from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.batches.enums import BatchStatus
from api.core.models import BaseModel
from api.core.schemas import AICost


class Batch(BaseModel):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=BatchStatus.processing.value
    )
    total_videos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processing_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Per-stage totals
    tts_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tts_token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    segmentation_cost_usd: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    segmentation_token_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    image_generation_cost_usd: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    image_generation_token_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    column_mapping: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def tts(self) -> AICost:
        return AICost(token_count=self.tts_token_count, cost_usd=self.tts_cost_usd)

    @property
    def segmentation(self) -> AICost:
        return AICost(
            token_count=self.segmentation_token_count,
            cost_usd=self.segmentation_cost_usd,
        )

    @property
    def image_generation(self) -> AICost:
        return AICost(
            token_count=self.image_generation_token_count,
            cost_usd=self.image_generation_cost_usd,
        )

    @property
    def total(self) -> AICost:
        return AICost(token_count=self.total_token_count, cost_usd=self.total_cost_usd)

    videos: Mapped[list["Video"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )

    def derive_status(self) -> BatchStatus:
        """Derive batch status from video counts."""
        if self.total_videos == 0:
            return BatchStatus.failed
        if self.pending_count > 0:
            return BatchStatus.processing
        if self.failed_count == self.total_videos:
            return BatchStatus.failed
        return BatchStatus.completed
