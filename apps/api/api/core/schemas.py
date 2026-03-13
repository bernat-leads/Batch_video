"""Shared schemas — task responses and common types."""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel


class Locale(StrEnum):
    EN = "en"
    LT = "lt"
    RU = "ru"


# Task Response Schemas
class TaskResponseBase(BaseModel):
    """Base schema for task responses."""

    status: Literal["success", "error", "created", "exists", "failed"] | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response returned by the global exception handler."""

    status: Literal["error"] = "error"
    message: str
    detail: Any | None = None
