"""Core routes - root and health check."""

import logging

from fastapi import APIRouter
from sqlalchemy import text

from api.deps.db import SessionDep
from api.deps.redis import AsyncRedisDep

logger = logging.getLogger(__name__)

router = APIRouter(tags=["core"])


@router.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "FastAPI backend is running!", "version": "0.1.0"}


@router.get("/health")
async def health_check(db: SessionDep, redis: AsyncRedisDep) -> dict[str, str]:
    """Health check endpoint — verifies DB and Redis connectivity."""
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check: DB unreachable")
        return {"status": "unhealthy", "db": "down"}

    try:
        await redis.ping()
    except Exception:
        logger.exception("Health check: Redis unreachable")
        return {"status": "unhealthy", "redis": "down"}

    return {"status": "healthy"}
