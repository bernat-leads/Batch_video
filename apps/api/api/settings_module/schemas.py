"""Pydantic schemas for AppSettings."""

from pydantic import BaseModel


class AppSettingsRead(BaseModel):
    """Schema for reading app settings."""

    master_prompt: str
    retention_days: int
    column_defaults: dict[str, str]

    model_config = {"from_attributes": True}


class AppSettingsUpdate(BaseModel):
    """Schema for updating app settings."""

    master_prompt: str | None = None
    retention_days: int | None = None
    column_defaults: dict[str, str] | None = None
