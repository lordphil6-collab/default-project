"""Apply frontend/drizzle/*.sql migrations to live Postgres (push needs TTY; this doesn't)."""
import asyncio
import glob
import os

import asyncpg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")


async def main() -> None:
    conn = await asyncpg.connect(URL)
    for path in sorted(glob.glob(os.path.join(ROOT, "..", "frontend", "drizzle", "*.sql"))):
        with open(path) as f:
            sql = f.read()
        await conn.execute(sql)
        print("applied:", os.path.basename(path))
    tables = sorted(
        r[0] for r in await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN "
            "('user','session','account','verification','organization','member','invitation','jwks')"))
    print("AUTH TABLES:", tables)
    assert len(tables) == 8, tables
    await conn.close()


asyncio.run(main())
