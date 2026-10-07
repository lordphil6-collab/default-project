"""Live round-trip proof: Better Auth signup+org -> JWT -> FastAPI JWKS verify -> PG.

Expects Next.js on :3000 and uvicorn on :8000 (see docs/PHASE_9_DONE.md).
Retries until both are up (max ~3 min), then asserts 200 on GET /situations.
"""
import os
import sys
import time

import httpx

BASE = os.getenv("WEB_BASE", "http://localhost:3000")
API = os.getenv("API_BASE", "http://localhost:8000")


def wait(url: str, tries: int = 36) -> None:
    for _ in range(tries):
        try:
            httpx.get(url, timeout=3)
            return
        except Exception:
            time.sleep(5)
    raise RuntimeError(f"never came up: {url}")


def main() -> None:
    wait(f"{BASE}/api/auth/jwks")
    wait(f"{API}/health")
    c = httpx.Client(base_url=BASE, timeout=10, headers={"Origin": BASE})
    r = c.post("/api/auth/sign-up/email", json={
        "name": "Pilot Owner", "email": "owner@acme.test", "password": "correct-horse-99"})
    assert r.status_code in (200, 201, 422), (r.status_code, r.text[:200])
    r = c.post("/api/auth/sign-in/email", json={"email": "owner@acme.test", "password": "correct-horse-99"})
    assert r.status_code == 200, (r.status_code, r.text[:200])
    slug = f"acme-{int(time.time())}"
    r = c.post("/api/auth/organization/create", json={"name": "Acme Forwarders", "slug": slug})
    assert r.status_code in (200, 201), (r.status_code, r.text[:300])
    org_id = r.json().get("id") or r.json().get("organization", {}).get("id")
    assert org_id, r.text[:300]
    r = c.post("/api/auth/organization/set-active", json={"organizationId": org_id})
    assert r.status_code == 200, (r.status_code, r.text[:300])
    r = c.get("/api/auth/token")
    assert r.status_code == 200, (r.status_code, r.text[:300])
    token = r.json().get("token")
    assert token, r.text[:300]
    a = httpx.get(f"{API}/situations",
                  headers={"Authorization": f"Bearer {token}", "X-Org-Id": org_id, "X-Role": "Owner"},
                  timeout=10)
    print("FASTAPI:", a.status_code, a.text[:200])
    assert a.status_code == 200, a.text[:500]
    # cross-org token reuse must 403
    b = httpx.get(f"{API}/situations",
                  headers={"Authorization": f"Bearer {token}", "X-Org-Id": "other-org", "X-Role": "Owner"},
                  timeout=10)
    assert b.status_code == 403, b.text[:200]
    print("ROUNDTRIP OK: signup -> org -> JWT -> JWKS verify -> PG-backed /situations; cross-org 403")


if __name__ == "__main__":
    sys.exit(main())
