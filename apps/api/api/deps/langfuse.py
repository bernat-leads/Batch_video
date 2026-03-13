"""Langfuse client and callback handler for tracing.

Uses Langfuse SDK v3.  Prompts are local Python constants (not fetched from Langfuse).

Tracing architecture:
    All LangChain call sites use ``langfuse_trace()`` as a context manager.
    It sets up Langfuse attributes (user/session/metadata) and yields a
    ready-to-use LangChain ``config`` dict with the callback handler.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from functools import lru_cache
from typing import Annotated, Generator

from fastapi import Depends
from langfuse import Langfuse, propagate_attributes
from langfuse.langchain import CallbackHandler

from api.settings import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Langfuse client (singleton)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_langfuse_client() -> Langfuse:
    """Return a cached Langfuse client built from application settings."""
    return Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        base_url=settings.LANGFUSE_BASE_URL,
        environment=settings.ENVIRONMENT,
        release=settings.ENVIRONMENT,
    )


LangfuseDep = Annotated[Langfuse, Depends(get_langfuse_client)]

# ---------------------------------------------------------------------------
# LangChain tracing context
# ---------------------------------------------------------------------------


@contextmanager
def langfuse_trace(
    *,
    user_id: str = "",
    session_id: str = "",
    **metadata: object,
) -> Generator[dict, None, None]:
    """Establish Langfuse trace context and yield a LangChain config dict.

    Combines ``propagate_attributes()`` (user/session/metadata) with a
    ``CallbackHandler``.  The yielded dict is ready to pass as ``config=``
    to any LangChain ``ainvoke()`` / ``invoke()`` call.

    Usage::

        with langfuse_trace(user_id="u-1", session_id="s-1") as config:
            await chain.ainvoke(input, config=config)
    """
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        metadata=metadata,
    ):
        yield {
            "callbacks": [CallbackHandler()],
            "tags": [settings.ENVIRONMENT],
        }
