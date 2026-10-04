"""Live billing proof: first write provisions trial, expired trial gets 402."""
import os

import asyncpg
import httpx

API = os.getenv("API_BASE", "http://localhost:8004")
ORG = "bill-test-1"
H = {"Authorization": "Bearer stub-proof", "X-Org-Id": ORG, "X-Role": "CSR"}
PG = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")


def post_intake():
    return httpx.post(f"{API}/intake",
                      json={"customer_name": "Billed Co", "channel": "email", "body": "x"},
                      headers=H, timeout=15)


async def expire():
    conn = await asyncpg.connect(PG)
    await conn.execute("UPDATE organizations SET trial_ends='2000-01-01' WHERE id='bill-test-1'")
    await conn.close()


async def main() -> None:
    r1 = post_intake()
    print("first write:", r1.status_code)
    assert r1.status_code == 200, r1.text[:300]
    await expire()
    r2 = post_intake()
    print("expired write:", r2.status_code, r2.text[:120])
    assert r2.status_code == 402, r2.text[:300]
    print("BILLING LIVE OK: provision-on-write + 402 on expiry")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
