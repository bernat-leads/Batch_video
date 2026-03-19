"""AppSettings database model."""

import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.core.models import BaseModel

DEFAULT_COLUMN_DEFAULTS: dict[str, str] = {
    "script_text": "script_text",
    "voice_id": "voice_id",
    "style": "style",
    "top_text": "top_text",
    "file_name": "file_name",
}


class AppSettings(BaseModel):
    """Singleton app settings."""

    __tablename__ = "app_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    master_prompt: Mapped[str] = mapped_column(Text, default="")
    retention_days: Mapped[int] = mapped_column(Integer, default=7)
    column_defaults: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=lambda: dict(DEFAULT_COLUMN_DEFAULTS)
    )
