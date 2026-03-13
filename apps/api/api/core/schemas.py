"""Shared schemas — pagination, error responses, and common types."""

import math
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, page_size: int
    ) -> "PageResponse[T]":
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0,
        )


class ErrorResponse(BaseModel):
    """Standard error response returned by the global exception handler."""

    status: Literal["error"] = "error"
    message: str
    detail: Any | None = None
