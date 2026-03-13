"""Video SQLAlchemy model."""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.models import BaseModel
from api.videos.enums import VideoStage, VideoStatus


class Video(BaseModel):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batches.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    script_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    voice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    style: Mapped[str | None] = mapped_column(String(255), nullable=True)
    top_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VideoStatus] = mapped_column(
        String(20), nullable=False, default=VideoStatus.pending, index=True
    )
    current_stage: Mapped[VideoStage] = mapped_column(
        String(30), nullable=False, default=VideoStage.queued
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_cost_per_shot_usd: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=1080)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=1920)

    batch: Mapped["Batch | None"] = relationship(back_populates="videos")  # noqa: F821
    shots: Mapped[list["Shot"]] = relationship(  # noqa: F821
        back_populates="video",
        cascade="all, delete-orphan",
        order_by="Shot.order",
    )
