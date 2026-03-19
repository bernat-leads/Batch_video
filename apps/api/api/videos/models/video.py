"""Video SQLAlchemy model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text, func, select, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from api.core.models import BaseModel
from api.core.schemas import AICost
from api.parser import ParsedRow
from api.videos.enums import VideoStage, VideoStatus

if TYPE_CHECKING:
    from api.shots.models.shot import Shot


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
    voice_id: Mapped[str] = mapped_column(String(255), nullable=False)
    style: Mapped[str | None] = mapped_column(String(255), nullable=True)
    top_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VideoStatus] = mapped_column(
        String(20), nullable=False, default=VideoStatus.processing, index=True
    )
    current_stage: Mapped[VideoStage] = mapped_column(
        String(30), nullable=False, default=VideoStage.queued, index=True
    )
    audio_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Per-model costs: {model_name: {token_count: int, cost_usd: float}}
    model_costs: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # total_cost_usd computed live from model_costs JSON — see column_property below

    @classmethod
    def from_parsed_row(cls, row: ParsedRow, batch_id: uuid.UUID) -> Video:
        """Create a Video from a parsed spreadsheet row."""
        return cls(
            batch_id=batch_id,
            script_text=row.data["script_text"],
            voice_id=row.data.get("voice_id") or None,
            style=row.data.get("style") or None,
            top_text=row.data.get("top_text") or None,
            file_name=row.data.get("file_name") or None,
            status=VideoStatus.processing if row.is_valid else VideoStatus.failed,
            current_stage=VideoStage.queued,
            error_message=row.error_message,
        )

    @property
    def s3_prefix(self) -> str:
        """S3 key prefix for all video assets."""
        return f"videos/{self.id}"

    @property
    def audio_s3_key(self) -> str:
        """S3 key for the TTS audio file."""
        return f"{self.s3_prefix}/audio"

    @property
    def word_timestamps_s3_key(self) -> str:
        """S3 key for persisted word-level timestamps."""
        return f"{self.s3_prefix}/word_timestamps.json"

    @property
    def output_s3_key(self) -> str:
        """S3 key for the final rendered video."""
        return f"{self.s3_prefix}/output.mp4"

    def shot_s3_key(self, order: int) -> str:
        """S3 key for a shot image by order number."""
        return f"{self.s3_prefix}/shots/{order:03d}.png"

    @staticmethod
    def build_shot_s3_key(video_id: uuid.UUID, order: int) -> str:
        """S3 key for a shot image by video ID and order number."""
        return f"videos/{video_id}/shots/{order:03d}.png"

    @staticmethod
    def shots_cost(shots: list[Shot]) -> AICost:
        """Calculate combined AI cost across all shots."""
        return AICost(cost_usd=sum(shot.cost_usd for shot in shots))

    def record_model_cost(
        self, model: str, cost_usd: float, token_count: int = 0
    ) -> None:
        """Add or update a model's cost entry. Reassigns dict for SQLAlchemy dirty tracking."""
        costs = dict(self.model_costs or {})
        existing = costs.get(model, {"token_count": 0, "cost_usd": 0.0})
        costs[model] = {
            "token_count": existing["token_count"] + token_count,
            "cost_usd": existing["cost_usd"] + cost_usd,
        }
        self.model_costs = costs

    batch: Mapped[Batch | None] = relationship(back_populates="videos")  # noqa: F821
    shots: Mapped[list[Shot]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
        order_by="Shot.order",
    )


# ---------------------------------------------------------------------------
# Computed column property — total_cost_usd derived from model_costs JSON.
# Uses PostgreSQL jsonb_each to sum cost_usd from all model entries.
# ---------------------------------------------------------------------------
Video.total_cost_usd = column_property(
    func.coalesce(
        select(func.sum(text("(value->>'cost_usd')::float")))
        .select_from(func.jsonb_each(Video.__table__.c.model_costs))
        .correlate(Video)
        .scalar_subquery(),
        0.0,
    ),
    deferred=False,
)
