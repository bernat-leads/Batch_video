"""Video SQLAlchemy model."""

import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.models import BaseModel


class Video(BaseModel):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    script_text: Mapped[str] = mapped_column(Text, nullable=False)
    voice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    style: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    current_stage: Mapped[str] = mapped_column(
        String(30), nullable=False, default="queued"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    shots: Mapped[list["Shot"]] = relationship(  # noqa: F821
        back_populates="video",
        cascade="all, delete-orphan",
        order_by="Shot.order",
    )
