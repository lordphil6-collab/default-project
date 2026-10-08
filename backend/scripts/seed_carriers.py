"""Seed well-known shipping lines as SAMPLE agents for an org.

Usage: ORG_ID=<your-org-id> python backend/scripts/seed_carriers.py
Clearly labeled SAMPLE DATA — replace routes/contacts with your contracted
lines and rates. Real carrier API feeds (Maersk Spot, Freightos) plug in at
services/rates.py history source; see docs/CARRIERS.md.
"""
import asyncio
import os

import asyncpg

URL = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
ORG = os.environ["ORG_ID"]

LINES = [
    ("Maersk", ["China>Lagos", "Guangzhou>Lagos", "Shanghai>Apapa"], ["ocean"], ["20ft", "40ft"]),
    ("MSC", ["China>Lagos", "Shanghai>Tincan"], ["ocean"], ["20ft", "40ft"]),
    ("CMA CGM", ["China>Lagos", "Guangzhou>Apapa"], ["ocean"], ["20ft", "40ft"]),
    ("Hapag-Lloyd", ["China>Lagos", "Shanghai>Lagos"], ["ocean"], ["20ft"]),
    ("COSCO", ["Guangzhou>Lagos", "China>Onne"], ["ocean"], ["20ft", "40ft"]),
    ("Evergreen", ["China>Lagos"], ["ocean"], ["20ft", "40ft"]),
    ("Lufthansa Cargo", ["Lagos>London", "Guangzhou>Lagos"], ["air"], ["cartons", "pallets"]),
    ("Emirates SkyCargo", ["Guangzhou>Lagos", "Lagos>London"], ["air"], ["cartons"]),
]


async def main() -> None:
    import uuid

    conn = await asyncpg.connect(URL)
    n = 0
    for company, routes, services, caps in LINES:
        exists = await conn.fetchval("SELECT id FROM agents WHERE org_id=$1 AND company=$2", ORG, company)
        if exists:
            print("exists", company)
            continue
        await conn.execute(
            "INSERT INTO agents(id, org_id, company, routes, services, capabilities, contact, email, status, notes)"
            " VALUES($1,$2,$3,$4,$5,$6,$7,$8,'Active','SAMPLE DATA — replace with contracted line')",
            str(uuid.uuid4()), ORG, company, routes, services, caps, "", "")
        n += 1
        print("seeded", company)
    print(f"done: {n} new sample lines")
    await conn.close()


asyncio.run(main())
