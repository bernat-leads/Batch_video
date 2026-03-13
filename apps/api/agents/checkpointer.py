"""LangGraph checkpointer — Postgres-backed state persistence for the agent graph."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from agents.settings import settings


async def _configure_conn(conn: AsyncConnection) -> None:
    """Set search_path on each new connection from the pool."""
    await conn.execute(f"""SET search_path TO {settings.DATABASE_SCHEMA}""")

pool = AsyncConnectionPool(
    conninfo=str(settings.DATABASE_URL),
    open=False,
    min_size=2,
    max_size=10,
    kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    configure=_configure_conn,
)

async def init_checkpointer() -> None:
    """Open the pool, create the langgraph schema, and run checkpointer migrations."""
    await pool.open(wait=True)
    async with pool.connection() as conn:
        await conn.execute(f"""CREATE SCHEMA IF NOT EXISTS {settings.DATABASE_SCHEMA}""")
    saver = AsyncPostgresSaver(conn=pool)
    await saver.setup()
    # await pool.close()

async def get_checkpointer() -> AsyncGenerator[AsyncPostgresSaver, None]:
    """Yield a checkpointer backed by the connection pool."""
    await pool.open(wait=True)
    yield AsyncPostgresSaver(conn=pool)
    # await pool.close()


CheckpointerDep = Annotated[AsyncPostgresSaver, Depends(get_checkpointer)]
