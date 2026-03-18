"""Redis client dependencies."""

from typing import Annotated

import redis
import redis.asyncio as aioredis
from fastapi import Depends

from api.settings import settings

# Sync pool for non-async usage (e.g. sync Celery tasks)
sync_pool = redis.ConnectionPool.from_url(settings.CELERY_BROKER_URL)

# Shared async pool for FastAPI (single event loop, safe to reuse)
async_pool = aioredis.ConnectionPool.from_url(settings.CELERY_BROKER_URL)


async def get_async_redis():
    """Get an async Redis client from the shared pool (FastAPI only)."""
    client = aioredis.Redis(connection_pool=async_pool)
    try:
        yield client
    finally:
        await client.aclose()


def get_sync_redis() -> redis.Redis:
    """Get a sync Redis client from the shared pool (for Celery worker threads)."""
    return redis.Redis(connection_pool=sync_pool)


def create_async_redis() -> aioredis.Redis:
    """Create a standalone async Redis client for Celery tasks.

    Does NOT use the shared pool — each call gets its own connection
    bound to the current event loop, avoiding 'event loop is closed' errors.
    Caller is responsible for calling `await client.aclose()`.
    """
    return aioredis.from_url(settings.CELERY_BROKER_URL)


async def shutdown_redis() -> None:
    """Close Redis connection pools during app shutdown."""
    await async_pool.aclose()
    sync_pool.disconnect()


AsyncRedisDep = Annotated[aioredis.Redis, Depends(get_async_redis)]
