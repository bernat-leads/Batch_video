"""Pydantic schemas for AppSettings."""

from pydantic import BaseModel


class AppSettingsRead(BaseModel):
    """Schema for reading app settings."""

    master_prompt: str
    retention_days: int
    default_script_column: str
    default_voice_column: str
    default_style_column: str
    default_top_text_column: str

    model_config = {"from_attributes": True}


class AppSettingsUpdate(BaseModel):
    """Schema for updating app settings."""

    master_prompt: str | None = None
    retention_days: int | None = None
    default_script_column: str | None = None
    default_voice_column: str | None = None
    default_style_column: str | None = None
    default_top_text_column: str | None = None
