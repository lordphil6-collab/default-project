"""Seed Starter/Pro plans (idempotent). Run once against live Postgres."""
import asyncio
import os
import uuid

import asyncpg

URL = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
PLANS = [("Starter", 29.0), ("Pro", 99.0)]


async def main() -> None:
    conn = await asyncpg.connect(URL)
    for name, price in PLANS:
        row = await conn.fetchrow("SELECT id FROM plans WHERE name=$1", name)
        if row is None:
            pid = str(uuid.uuid4())
            await conn.execute("INSERT INTO plans(id, name, monthly_price) VALUES($1,$2,$3)", pid, name, price)
            print("seeded", name, pid)
        else:
            print("exists", name, row["id"])
    await conn.close()


asyncio.run(main())
