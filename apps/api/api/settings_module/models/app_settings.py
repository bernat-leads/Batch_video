"""AppSettings database model."""

import uuid

from sqlalchemy import Integer, Text
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
