"""Hard-delete one org's data (retention path, docs/RETENTION.md).

Usage: DATABASE_URL=... python backend/scripts/erase_org.py ORG_ID
Prints per-table counts. Plans (global templates) are kept.
"""
import asyncio
import os
import sys

import asyncpg

URL = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")

TABLES = ["messages", "conversations", "agent_quotations", "rfq_recipients", "rfqs",
          "customer_quotations", "follow_ups", "exceptions", "customers", "agents",
          "situations", "mailboxes", "entitlements", "audit_log", "users", "organizations"]


async def main(org_id: str) -> None:
    conn = await asyncpg.connect(URL)
    total = 0
    for table in TABLES:
        col = "id" if table == "organizations" else "org_id"
        n = await conn.execute(f"DELETE FROM {table} WHERE {col}=$1", org_id)
        print(f"{table}: {n.split()[-1]}")
        total += 1
    await conn.close()
    print(f"erased org {org_id} ({total} tables)")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
