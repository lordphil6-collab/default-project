"""DB base + engine factory. Postgres in prod/compose, SQLite for unit tests."""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/quote_desk")


def make_async_session_factory(url: str | None = None):
    url = url or get_database_url()
    engine = create_async_engine(url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


def make_sync_test_engine():
    engine = create_engine("sqlite:///:memory:")
    return sessionmaker(engine)
