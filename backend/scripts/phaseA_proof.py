"""Phase A live proof: real roles in JWT, invite flow, rate limits, reset request."""
import base64
import json
import os
import time

import httpx

BASE = os.getenv("WEB_BASE", "http://localhost:3002")
API = os.getenv("API_BASE", "http://localhost:8000")


def claims(token: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=="))


def main() -> None:
    c = httpx.Client(base_url=BASE, timeout=20, headers={"Origin": BASE})
    stamp = str(int(time.time()))
    email = f"owner-{stamp}@acme.test"
    c.post("/api/auth/sign-up/email", json={"name": "Own", "email": email, "password": "correct-horse-99"})
    c.post("/api/auth/sign-in/email", json={"email": email, "password": "correct-horse-99"})
    o = c.post("/api/auth/organization/create", json={"name": "AOrg", "slug": f"aorg-{stamp}"}).json()
    oid = o.get("id") or o["organization"]["id"]
    c.post("/api/auth/organization/set-active", json={"organizationId": oid})
    token = c.get("/api/auth/token").json()["token"]
    assert claims(token).get("role") == "Owner", claims(token)
    print("ROLE Owner in JWT OK")
    h = {"Authorization": f"Bearer {token}", "X-Org-Id": oid, "X-Role": "CSR"}
    assert httpx.get(f"{API}/admin/orgs", headers=h, timeout=20).status_code == 200
    print("OWNER GATE OK (claims role wins over CSR header)")

    mem_email = f"mem-{stamp}@acme.test"
    r = c.post("/api/auth/organization/invite-member",
               json={"email": mem_email, "role": "member", "organizationId": oid})
    assert r.status_code == 200, r.text[:200]
    inv_id = r.json().get("id") or r.json().get("invitation", {}).get("id")
    m = httpx.Client(base_url=BASE, timeout=20, headers={"Origin": BASE})
    m.post("/api/auth/sign-up/email", json={"name": "Mem", "email": mem_email, "password": "correct-horse-99"})
    m.post("/api/auth/sign-in/email", json={"email": mem_email, "password": "correct-horse-99"})
    assert m.post("/api/auth/organization/accept-invitation",
                  json={"invitationId": inv_id}).status_code == 200
    m.post("/api/auth/organization/set-active", json={"organizationId": oid})
    mtok = m.get("/api/auth/token").json()["token"]
    assert claims(mtok).get("role") == "CSR", claims(mtok)
    mh = {"Authorization": f"Bearer {mtok}", "X-Org-Id": oid, "X-Role": "CSR"}
    assert httpx.get(f"{API}/admin/orgs", headers=mh, timeout=20).status_code == 403
    assert httpx.post(f"{API}/intake",
                      json={"customer_name": "M", "channel": "email", "body": "x"},
                      headers=mh, timeout=20).status_code == 200
    print("INVITE FLOW OK (member=CSR: admin 403, intake 200)")

    codes = [httpx.get(f"{API}/public/track/nope", timeout=20).status_code for _ in range(25)]
    assert 429 in codes, codes
    print("RATE LIMIT OK (burst -> 429)")

    r = c.post("/api/auth/request-password-reset",
               json={"email": email, "redirectTo": "http://localhost:3002/reset-password"})
    assert r.status_code == 200, r.text[:200]
    print("RESET REQUEST OK (logged-only without SMTP)")
    print("PHASE-A LIVE OK")


if __name__ == "__main__":
    main()
