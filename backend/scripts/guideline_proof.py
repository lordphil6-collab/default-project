"""Guideline positive-path proof: seed 2 ocean quotes, expect available estimate."""
import os
import time

import httpx

BASE = os.getenv("WEB_BASE", "http://localhost:3002")
API = os.getenv("API_BASE", "http://localhost:8000")


def main() -> None:
    c = httpx.Client(base_url=BASE, timeout=20, headers={"Origin": BASE})
    e = f"g2-{int(time.time())}@acme.test"
    c.post("/api/auth/sign-up/email", json={"name": "G", "email": e, "password": "correct-horse-99"})
    c.post("/api/auth/sign-in/email", json={"email": e, "password": "correct-horse-99"})
    o = c.post("/api/auth/organization/create", json={"name": "G", "slug": f"g2-{int(time.time())}"}).json()
    oid = o.get("id") or o["organization"]["id"]
    c.post("/api/auth/organization/set-active", json={"organizationId": oid})
    token = c.get("/api/auth/token").json()["token"]
    h = {"Authorization": f"Bearer {token}", "X-Org-Id": oid, "X-Role": "Manager"}
    body = "quote for 5 cartons from Guangzhou to Lagos"
    s = httpx.post(f"{API}/intake", json={"customer_name": "G", "channel": "email", "body": body},
                   headers=h, timeout=20).json()["id"]
    httpx.post(f"{API}/situations/{s}/extract", json={"body": body}, headers=h, timeout=20)
    r = httpx.post(f"{API}/rfqs", json={"situation_id": s}, headers=h, timeout=20).json()["id"]
    qa = "Ocean Freight $1,850\nOrigin Charges $420\nDestination Charges $650"
    qc = "Ocean Freight $1,900\nOrigin Charges $390\nDestination Charges $580\nOther Charges $180"
    httpx.post(f"{API}/rfqs/{r}/quotations", json={"agent": "A", "body_text": qa}, headers=h, timeout=20)
    httpx.post(f"{API}/rfqs/{r}/quotations", json={"agent": "C", "body_text": qc}, headers=h, timeout=20)
    g = httpx.get(f"{API}/situations/{s}/guideline", headers=h, timeout=20).json()
    print("guideline:", g)
    assert g["available"] and g["low"] == 2920.0 and g["typical"] == 2985.0, g
    print("GUIDELINE POSITIVE OK")


if __name__ == "__main__":
    main()
