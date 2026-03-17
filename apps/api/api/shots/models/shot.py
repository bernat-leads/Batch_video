"""Shot SQLAlchemy model."""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.models import BaseModel
from api.core.schemas import AICost


class Shot(BaseModel):
    __tablename__ = "shots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    effect_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    @property
    def cost(self) -> AICost:
        """AI cost for this shot's image generation."""
        return AICost(cost_usd=self.cost_usd)

    video: Mapped["Video"] = relationship(back_populates="shots")  # noqa: F821
