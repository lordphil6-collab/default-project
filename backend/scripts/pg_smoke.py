"""Smoke-check live Postgres: list tables + alembic version, insert/select one org."""
import asyncio
import os

import asyncpg

URL = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")


async def main() -> None:
    conn = await asyncpg.connect(URL)
    tables = sorted(r[0] for r in await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname='public'"))
    print("TABLES:", tables)
    ver = await conn.fetchval("SELECT version_num FROM alembic_version")
    print("ALEMBIC:", ver)
    await conn.execute("INSERT INTO organizations(id, name, trial_start) VALUES('smoke-org', 'Smoke', now()) "
                       "ON CONFLICT (id) DO NOTHING")
    name = await conn.fetchval("SELECT name FROM organizations WHERE id='smoke-org'")
    print("ROUNDTRIP:", name)
    await conn.close()


asyncio.run(main())
