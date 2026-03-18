"""Celery application configuration, async task decorator, and task context."""

import json
from collections.abc import AsyncGenerator, Callable, Coroutine
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from asgiref.sync import async_to_sync
from celery import Celery, Task
from kombu.serialization import register
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps.db import async_session_factory
from api.deps.redis import create_async_redis
from api.deps.storage import s3_client
from api.events.service import EventService
from api.settings import settings
from api.storage import StorageService

_P = ParamSpec("_P")
_R = TypeVar("_R")


# ---------------------------------------------------------------------------
# Pydantic-aware JSON serializer for Celery
# ---------------------------------------------------------------------------


class _PydanticEncoder(json.JSONEncoder):
    """JSON encoder that serializes Pydantic models via model_dump."""

    def default(self, o: object) -> Any:
        if isinstance(o, BaseModel):
            return o.model_dump(mode="json")
        return super().default(o)


def _pydantic_dumps(obj: Any) -> str:
    return json.dumps(obj, cls=_PydanticEncoder)


def _pydantic_loads(data: str) -> Any:
    return json.loads(data)


register(
    "pydantic_json",
    _pydantic_dumps,
    _pydantic_loads,
    content_type="application/x-pydantic+json",
    content_encoding="utf-8",
)


# ---------------------------------------------------------------------------
# Celery app
# ---------------------------------------------------------------------------

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["api.deps.tasks", "api.batches.tasks", "api.videos.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json", "pydantic_json"],
    result_serializer="pydantic_json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    result_expires=3600,
    beat_schedule={
        "cleanup-expired-videos": {
            "task": "api.deps.tasks.cleanup_expired_videos",
            "schedule": 86400,  # daily
        },
        "recover-stale-videos": {
            "task": "api.deps.tasks.recover_stale_videos",
            "schedule": 300,  # every 5 minutes
        },
    },
)


# ---------------------------------------------------------------------------
# Async task decorator
# ---------------------------------------------------------------------------


def async_task(app: Celery, *args: Any, **kwargs: Any):
    """Decorator to register async functions as Celery tasks via asgiref."""

    def _decorator(func: Callable[_P, Coroutine[Any, Any, _R]]) -> Task:
        sync_call = async_to_sync(func)

        @app.task(*args, **kwargs)
        @wraps(func)
        def _decorated(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            return sync_call(*args, **kwargs)

        return _decorated

    return _decorator


# ---------------------------------------------------------------------------
# Task context (DI for Celery tasks)
# ---------------------------------------------------------------------------


class TaskContext(BaseModel):
    """Shared resources for Celery task execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session: AsyncSession
    storage: StorageService
    events: EventService


@asynccontextmanager
async def task_context() -> AsyncGenerator[TaskContext, None]:
    """Provide DB session, storage, and events for a Celery task.

    Usage:
        async with task_context() as ctx:
            # ctx.session, ctx.storage, ctx.events
    """
    redis_client = create_async_redis()
    try:
        async with async_session_factory() as session:
            yield TaskContext(
                session=session,
                storage=StorageService(s3_client),
                events=EventService(redis_client),
            )
    finally:
        await redis_client.aclose()


# ---------------------------------------------------------------------------
# Worker entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """Run Celery worker."""
    celery_app.worker_main(
        argv=[
            "worker",
            "--loglevel=info",
            "--concurrency=10",
            "--pool=threads",
            "--events",
        ]
    )


if __name__ == "__main__":
    main()
