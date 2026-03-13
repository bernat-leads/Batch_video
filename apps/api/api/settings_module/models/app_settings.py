"""AppSettings database model."""

import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.core.models import BaseModel


class AppSettings(BaseModel):
    """Singleton app settings."""

    __tablename__ = "app_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    master_prompt: Mapped[str] = mapped_column(Text, default="")
    retention_days: Mapped[int] = mapped_column(Integer, default=7)
    default_script_column: Mapped[str] = mapped_column(
        String(100), default="script_text"
    )
    default_voice_column: Mapped[str] = mapped_column(
        String(100), default="voice_id"
    )
    default_style_column: Mapped[str] = mapped_column(
        String(100), default="style"
    )
    default_top_text_column: Mapped[str] = mapped_column(
        String(100), default="top_text"
    )
