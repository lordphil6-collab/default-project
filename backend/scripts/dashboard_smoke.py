"""Live dashboard proof: signup -> intake -> situations + today counts (all real)."""
import os
import time

import httpx

BASE = os.getenv("WEB_BASE", "http://localhost:3001")
API = os.getenv("API_BASE", "http://localhost:8005")


def main() -> None:
    c = httpx.Client(base_url=BASE, timeout=15, headers={"Origin": BASE})
    email = f"csr-{int(time.time())}@acme.test"
    assert c.post("/api/auth/sign-up/email",
                  json={"name": "CSR", "email": email, "password": "correct-horse-99"}).status_code in (200, 201)
    assert c.post("/api/auth/sign-in/email",
                  json={"email": email, "password": "correct-horse-99"}).status_code == 200
    slug = f"dash-{int(time.time())}"
    r = c.post("/api/auth/organization/create", json={"name": "Dash Co", "slug": slug})
    assert r.status_code in (200, 201), r.text[:200]
    org = r.json().get("id") or r.json()["organization"]["id"]
    assert c.post("/api/auth/organization/set-active", json={"organizationId": org}).status_code == 200
    token = c.get("/api/auth/token").json()["token"]
    h = {"Authorization": f"Bearer {token}", "X-Org-Id": org, "X-Role": "CSR"}
    r = httpx.post(f"{API}/intake",
                   json={"customer_name": "Dash Client", "channel": "email",
                         "body": "quote for 5 cartons from Guangzhou to Lagos"},
                   headers=h, timeout=15)
    assert r.status_code == 200, r.text[:300]
    sits = httpx.get(f"{API}/situations", headers=h, timeout=15).json()
    counts = httpx.get(f"{API}/dashboard/today", headers=h, timeout=15).json()
    print("SITUATIONS:", len(sits), sits[0]["status"], sits[0]["missing"])
    print("COUNTS:", counts)
    assert len(sits) >= 1 and counts["follow_ups"] >= 0
    print("DASHBOARD LIVE OK")


if __name__ == "__main__":
    main()
