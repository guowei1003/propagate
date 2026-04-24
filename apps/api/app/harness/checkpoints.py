from __future__ import annotations

from contextlib import asynccontextmanager

from app.config import get_settings


@asynccontextmanager
async def maybe_postgres_checkpointer():
    settings = get_settings()
    if not settings.resolved_checkpoint_database_url().startswith("postgresql://"):
        yield None
        return

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    async with AsyncPostgresSaver.from_conn_string(settings.resolved_checkpoint_database_url()) as saver:
        await saver.setup()
        yield saver
