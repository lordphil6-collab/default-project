"""Mail live proof: connect fake mailbox, poll errors cleanly, RFQ email logged-only."""
import os
import time

import httpx

BASE = os.getenv("WEB_BASE", "http://localhost:3002")
API = os.getenv("API_BASE", "http://localhost:8000")


def main() -> None:
    c = httpx.Client(base_url=BASE, timeout=30, headers={"Origin": BASE})
    email = f"m-{int(time.time())}@acme.test"
    c.post("/api/auth/sign-up/email", json={"name": "M", "email": email, "password": "correct-horse-99"})
    c.post("/api/auth/sign-in/email", json={"email": email, "password": "correct-horse-99"})
    o = c.post("/api/auth/organization/create", json={"name": "M", "slug": f"m-{int(time.time())}"}).json()
    oid = o.get("id") or o["organization"]["id"]
    c.post("/api/auth/organization/set-active", json={"organizationId": oid})
    token = c.get("/api/auth/token").json()["token"]
    h = {"Authorization": f"Bearer {token}", "X-Org-Id": oid, "X-Role": "Manager"}

    r = httpx.post(f"{API}/mailboxes",
                   json={"host": "invalid.invalid", "username": "u", "password": "p"},
                   headers=h, timeout=20)
    assert r.status_code == 200, r.text[:200]
    mid = r.json()["id"]
    boxes = httpx.get(f"{API}/mailboxes", headers=h, timeout=20).json()
    assert any(b["id"] == mid for b in boxes) and "secret" not in boxes[0], boxes
    print("MAILBOX CONNECT OK (password never listed)")
    r = httpx.post(f"{API}/mailboxes/{mid}/poll", headers=h, timeout=60)
    assert r.status_code == 502, (r.status_code, r.text[:200])
    print("POLL FAILS CLEANLY OK (unreachable host -> 502, no crash):", r.json()["detail"][:80])

    sit = httpx.post(f"{API}/intake",
                     json={"customer_name": "M", "channel": "email", "body": "x"},
                     headers=h, timeout=20).json()["id"]
    rfq = httpx.post(f"{API}/rfqs", json={"situation_id": sit}, headers=h, timeout=20).json()["id"]
    a = httpx.post(f"{API}/agents",
                   json={"company": "NoMail Agent", "routes": ["China>Lagos"]},
                   headers=h, timeout=20).json()["id"]
    httpx.post(f"{API}/rfqs/{rfq}/recipients", json={"agent_ids": [a]}, headers=h, timeout=20)
    sent = httpx.post(f"{API}/rfqs/{rfq}/send", headers=h, timeout=20).json()
    assert sent["status"] == "Sent", sent
    d = sent["deliveries"][0]
    assert d["status"] == "logged-only", sent
    print("RFQ EMAIL LOGGED-ONLY OK (no SMTP configured, recorded not pretended)")
    print("MAIL LIVE OK")


if __name__ == "__main__":
    main()
