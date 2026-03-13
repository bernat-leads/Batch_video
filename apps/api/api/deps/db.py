from collections.abc import AsyncGenerator
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
    """Initialize database."""
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    async with engine.begin():
        # Tables are created via Alembic migrations; uncomment to create from metadata:
        # from app.core.models import BaseModel
        # await conn.run_sync(Base.metadata.create_all)
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
