"""Live billing proof: first write provisions trial, expired trial gets 402 (real JWT)."""
import os
import time

import asyncpg
import httpx

BASE = os.getenv("WEB_BASE", "http://localhost:3002")
API = os.getenv("API_BASE", "http://localhost:8000")
PG = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://") \
    if "DATABASE_URL" in os.environ else None


async def expire(org: str, pg_url: str) -> None:
    conn = await asyncpg.connect(pg_url)
    await conn.execute("UPDATE organizations SET trial_ends='2000-01-01' WHERE id=$1", org)
    await conn.close()


def main() -> None:
    c = httpx.Client(base_url=BASE, timeout=20, headers={"Origin": BASE})
    email = f"bill-{int(time.time())}@acme.test"
    assert c.post("/api/auth/sign-up/email",
                  json={"name": "Bill", "email": email, "password": "correct-horse-99"}).status_code in (200, 201)
    assert c.post("/api/auth/sign-in/email",
                  json={"email": email, "password": "correct-horse-99"}).status_code == 200
    slug = f"bill-{int(time.time())}"
    r = c.post("/api/auth/organization/create", json={"name": "Bill Co", "slug": slug})
    org = r.json().get("id") or r.json()["organization"]["id"]
    assert c.post("/api/auth/organization/set-active", json={"organizationId": org}).status_code == 200
    token = c.get("/api/auth/token").json()["token"]
    h = {"Authorization": f"Bearer {token}", "X-Org-Id": org, "X-Role": "CSR"}
    body = {"customer_name": "Billed Co", "channel": "email", "body": "hello"}
    r1 = httpx.post(f"{API}/intake", json=body, headers=h, timeout=20)
    print("first write:", r1.status_code)
    assert r1.status_code == 200, r1.text[:300]
    import asyncio
    asyncio.run(expire(org, PG))
    r2 = httpx.post(f"{API}/intake", json=body, headers=h, timeout=20)
    print("expired write:", r2.status_code, r2.text[:120])
    assert r2.status_code == 402, r2.text[:300]
    print("BILLING LIVE OK: provision-on-write + 402 on expiry")


if __name__ == "__main__":
    main()
