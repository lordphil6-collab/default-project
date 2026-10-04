"""Alembic env — async engine, URL from DATABASE_URL. Works on Postgres and SQLite."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.db import Base  # noqa: F401  (model registration)
from backend.app import models  # noqa: F401

config = context.config
target_metadata = Base.metadata


def get_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite://"):
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url or "postgresql+asyncpg://postgres:postgres@localhost:5432/quote_desk"


def run_migrations_offline() -> None:
    context.configure(url=get_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_async_engine(get_url(), pool_pre_ping=True)

    async def run() -> None:
        async with engine.connect() as conn:
            await conn.run_sync(do_run)

    def do_run(conn) -> None:
        context.configure(connection=conn, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    asyncio.run(run())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
