"""Full E2E proof: intake > extract > RFQ > 3 quotes > compare > price > approve > send > follow-up > outcome."""
import os

import httpx

BASE = os.getenv("WEB_BASE", "http://localhost:3002")
API = os.getenv("API_BASE", "http://localhost:8006")


def main() -> None:
    import time
    c = httpx.Client(base_url=BASE, timeout=20, headers={"Origin": BASE})
    email = f"e2e-{int(time.time())}@acme.test"
    assert c.post("/api/auth/sign-up/email",
                  json={"name": "E2E", "email": email, "password": "correct-horse-99"}).status_code in (200, 201)
    assert c.post("/api/auth/sign-in/email",
                  json={"email": email, "password": "correct-horse-99"}).status_code == 200
    slug = f"e2e-{int(time.time())}"
    r = c.post("/api/auth/organization/create", json={"name": "E2E Co", "slug": slug})
    org = r.json().get("id") or r.json()["organization"]["id"]
    assert c.post("/api/auth/organization/set-active", json={"organizationId": org}).status_code == 200
    token = c.get("/api/auth/token").json()["token"]
    h = {"Authorization": f"Bearer {token}", "X-Org-Id": org, "X-Role": "Manager"}

    def call(method: str, path: str, body: dict | None = None):
        r = httpx.request(method, f"{API}{path}", json=body, headers=h, timeout=20)
        assert r.status_code in (200, 201), f"{method} {path}: {r.status_code} {r.text[:200]}"
        return r.json()

    sit = call("POST", "/intake", {"customer_name": "E2E Client", "channel": "email",
                                   "body": "quote for 5 cartons from Guangzhou to Lagos"})["id"]
    ext = call("POST", f"/situations/{sit}/extract", {"body": "quote for 5 cartons from Guangzhou to Lagos"})
    assert "weight" in ext["missing"], ext
    rfq = call("POST", "/rfqs", {"situation_id": sit})["id"]
    call("POST", f"/rfqs/{rfq}/quotations",
         {"agent": "Agent A", "body_text": "Ocean Freight $1,850\nOrigin Charges $420\nDestination Charges $650\nTransit 35 days\nValidity 7 days"})
    call("POST", f"/rfqs/{rfq}/quotations",
         {"agent": "Agent B", "body_text": "Ocean Freight $1,720\nOrigin Charges $600\nDestination Charges Unknown\nTransit 32 days"})
    call("POST", f"/rfqs/{rfq}/quotations",
         {"agent": "Agent C", "body_text": "Ocean Freight $1,900\nOrigin Charges $390\nDestination Charges $580\nOther Charges $180\nTransit 38 days\nValidity 10 days"})
    comp = call("GET", f"/rfqs/{rfq}/compare")
    assert comp["recommendation"]["agent"] == "Agent A", comp
    quotes = call("GET", f"/rfqs/{rfq}/quotations")
    aq = next(q["id"] for q in quotes if q["agent"] == "Agent A")
    quote = call("POST", "/customer-quotes",
                 {"situation_id": sit, "agent_quotation_id": aq, "markup_kind": "percent", "markup_value": 12})
    assert quote["final_price"] == 3270.4, quote
    assert call("POST", f"/customer-quotes/{quote['id']}/approve")["status"] == "Approved"
    assert call("POST", f"/customer-quotes/{quote['id']}/send")["status"] == "Sent"
    fu = call("POST", "/follow-ups", {"situation_id": sit, "quote_id": quote["id"], "due_at": None})
    assert fu["bucket"] == "no_due"
    out = call("POST", f"/situations/{sit}/outcome", {"outcome": "Accepted"})
    assert out["status"] == "Accepted", out
    counts = call("GET", "/dashboard/today")
    print("E2E OK: intake>extract>rfq>3 quotes>compare(A)>3270.40>approve>send>followup>Accepted; dashboard:", counts)


if __name__ == "__main__":
    main()
