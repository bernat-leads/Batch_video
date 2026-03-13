"""Tavily async client for web search."""

from __future__ import annotations

import logging
from functools import lru_cache

from tavily import AsyncTavilyClient

from api.settings import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_tavily_client() -> AsyncTavilyClient:
    """Return a cached async Tavily client built from application settings."""
    return AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
