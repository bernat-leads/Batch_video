from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from api.settings import settings

# FastAPI engine — connection pool with pre-ping
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# Celery engine — NullPool so each task gets a fresh connection
# (avoids event-loop mismatch with asyncpg)
_celery_engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    future=True,
    poolclass=NullPool,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session (FastAPI routes)."""
    async with AsyncSession(engine) as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database. Tables are created via Alembic migrations."""
    async with engine.begin():
        pass


async def save(session: AsyncSession, db_object: object) -> None:
    """Save a database object to the session and commit changes."""
    session.add(db_object)
    await session.commit()
    await session.refresh(db_object)


@asynccontextmanager
async def async_session_factory() -> AsyncGenerator[AsyncSession, None]:
    """Create a standalone async session for Celery tasks.

    Uses NullPool engine and expire_on_commit=False so attributes
    remain accessible after commit without lazy reloads.
    """
    async with AsyncSession(_celery_engine, expire_on_commit=False) as session:
        try:
            yield session
        finally:
            await session.close()


SessionDep = Annotated[AsyncSession, Depends(get_db)]
