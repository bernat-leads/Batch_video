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


class AICost(BaseModel):
    """Reusable cost + token count for a pipeline stage or aggregate."""

    token_count: int = 0
    cost_usd: float = 0.0

    @classmethod
    def from_chain_result(
        cls,
        result: dict,
        input_cost_per_token: float = 0.0,
        output_cost_per_token: float = 0.0,
    ) -> "AICost":
        """Create AICost from a LangChain chain result with usage metadata."""
        usage = result.get("raw", result).usage_metadata or {}
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        total_tokens = input_tokens + output_tokens
        cost = (
            input_tokens * input_cost_per_token + output_tokens * output_cost_per_token
        )
        return cls(token_count=total_tokens, cost_usd=cost)


class ErrorResponse(BaseModel):
    """Standard error response returned by the global exception handler."""

    status: Literal["error"] = "error"
    message: str
    detail: Any | None = None
