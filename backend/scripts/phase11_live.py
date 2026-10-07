"""Phase-11 live proof: upload PDF, markup rules, delivery logged-only, inbox, billing 501s."""
import io
import os
import time

import httpx
import pymupdf

BASE = os.getenv("WEB_BASE", "http://localhost:3002")
API = os.getenv("API_BASE", "http://localhost:8000")


def main() -> None:
    c = httpx.Client(base_url=BASE, timeout=30, headers={"Origin": BASE})
    email = f"p11-{int(time.time())}@acme.test"
    assert c.post("/api/auth/sign-up/email",
                  json={"name": "P11", "email": email, "password": "correct-horse-99"}).status_code in (200, 201)
    assert c.post("/api/auth/sign-in/email",
                  json={"email": email, "password": "correct-horse-99"}).status_code == 200
    slug = f"p11-{int(time.time())}"
    r = c.post("/api/auth/organization/create", json={"name": "P11 Co", "slug": slug})
    org = r.json().get("id") or r.json()["organization"]["id"]
    assert c.post("/api/auth/organization/set-active", json={"organizationId": org}).status_code == 200
    token = c.get("/api/auth/token").json()["token"]
    h = {"Authorization": f"Bearer {token}", "X-Org-Id": org, "X-Role": "Manager"}

    def call(method: str, path: str, **kw):
        r = httpx.request(method, f"{API}{path}", headers=h, timeout=30, **kw)
        return r

    sit = call("POST", "/intake",
               json={"customer_name": "P11", "channel": "email", "body": "x"}).json()["id"]
    rfq = call("POST", "/rfqs", json={"situation_id": sit}).json()["id"]

    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Ocean Freight $1,850\nOrigin Charges $420\nDestination Charges $650\nValidity 7 days\nTransit 35 days")
    pdf = doc.tobytes()
    r = httpx.post(f"{API}/rfqs/{rfq}/quotations/upload", headers=h, timeout=30,
                   files={"file": ("quote.pdf", pdf, "application/pdf")}, data={"agent": "Agent PDF"})
    assert r.status_code == 200, r.text[:300]
    assert r.json()["total_identifiable"] == 2920.0, r.text[:300]
    print("UPLOAD PDF OK: total 2920.0")

    r = httpx.post(f"{API}/rfqs/{rfq}/quotations/upload", headers=h, timeout=30,
                   files={"file": ("q.png", b"12345", "image/png")}, data={"agent": "X"})
    assert r.status_code == 422, r.status_code
    print("IMAGE REJECTED OK (clear 422)")

    rule = call("POST", "/markup-rules",
                json={"name": "Std12", "kind": "percent", "value": 12}).json()
    rules = call("GET", "/markup-rules").json()
    assert any(x["id"] == rule["id"] for x in rules)
    print("RULES OK:", len(rules))

    aq = call("GET", f"/rfqs/{rfq}/quotations").json()[0]["id"]
    q = call("POST", "/customer-quotes",
             json={"situation_id": sit, "agent_quotation_id": aq,
                   "markup_rule_id": rule["id"]}).json()
    assert q["final_price"] == 3270.4, q
    call("POST", f"/customer-quotes/{q['id']}/approve")
    sent = call("POST", f"/customer-quotes/{q['id']}/send",
                json={"channel": "email", "to": "client@example.com"}).json()
    assert sent["status"] == "Sent" and sent["delivery"]["status"] == "logged-only", sent
    print("RULE PRICING + LOGGED DELIVERY OK:", sent["delivery"])

    inbox = call("GET", "/inbox").json()
    assert any(t["situation_id"] == sit for t in inbox), inbox
    print("INBOX OK:", len(inbox), "threads")

    plans = call("GET", "/billing/plans").json()
    assert len(plans) >= 2, plans
    status = call("GET", "/billing/status").json()
    assert status["status"] in ("trialing", "active"), status
    owner = dict(h, **{"X-Role": "Owner"})
    r = httpx.post(f"{API}/billing/checkout", json={"plan_id": plans[0]["id"]}, headers=owner, timeout=30)
    assert r.status_code == 501, (r.status_code, r.text[:200])
    print("BILLING OK: plans + status live, checkout honest 501 without secrets")
    print("PHASE-11 LIVE OK")


if __name__ == "__main__":
    main()
