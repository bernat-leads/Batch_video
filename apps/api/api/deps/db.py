from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from api.settings import settings

engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    future=True,
    poolclass=NullPool,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
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
    """Save a database object to the session and commit changes.

    Args:
        session (AsyncSession): The async database session.
        db_object (object): The database object to save.
    """
    session.add(db_object)
    await session.commit()
    await session.refresh(db_object)


SessionDep = Annotated[AsyncSession, Depends(get_db)]


@asynccontextmanager
async def async_session_factory() -> AsyncGenerator[AsyncSession, None]:
    """Create a standalone async session for use outside FastAPI (e.g., Celery tasks)."""
    async with AsyncSession(engine) as session:
        try:
            yield session
        finally:
            await session.close()
