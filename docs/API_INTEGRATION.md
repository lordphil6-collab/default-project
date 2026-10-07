# API integration guide — step by step

Base URLs (local): Web `http://localhost:3002`, API `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`. All org routes need auth headers.

## 1. Authenticate (Better Auth → JWT → FastAPI)

Every org-scoped call sends three headers:

```
Authorization: Bearer <JWT>
X-Org-Id: <organization-id>
X-Role: CSR|Sales|Ops|Manager|Owner
```

Get them in order (see `backend/scripts/live_roundtrip.py` for runnable code):

```bash
# 1. sign up (also signs you in via cookie)
curl -c jar.txt -H 'Origin: http://localhost:3002' -H 'Content-Type: application/json' \
  -d '{"name":"Ada","email":"ada@acme.test","password":"correct-horse-99"}' \
  http://localhost:3002/api/auth/sign-up/email

# 2. create company workspace
curl -b jar.txt -c jar.txt -H 'Origin: http://localhost:3002' -H 'Content-Type: application/json' \
  -d '{"name":"Acme Forwarders","slug":"acme-ORG"}' \
  http://localhost:3002/api/auth/organization/create   # -> {"id": "ORG", ...}

# 3. set it active (this puts organizationId into the JWT)
curl -b jar.txt -c jar.txt -H 'Origin: http://localhost:3002' -H 'Content-Type: application/json' \
  -d '{"organizationId":"ORG"}' \
  http://localhost:3002/api/auth/organization/set-active

# 4. mint JWT (Ed25519, 15 min)
TOKEN=$(curl -s -b jar.txt http://localhost:3002/api/auth/token | python -c "import json,sys; print(json.load(sys.stdin)['token'])")

# 5. call the API
curl -H "Authorization: Bearer $TOKEN" -H "X-Org-Id: ORG" -H "X-Role: Manager" \
  http://localhost:8000/situations
```

Rules enforced server-side (`backend/app/auth.py`): signature via JWKS
(`FASTAPI_JWKS_URL`), token must carry an org claim, and it must match
`X-Org-Id` (403 otherwise). Set `ALLOW_AUTH_STUB=true` only for throwaway dev.

## 2. Core workflow (happy path)

```
POST /intake {customer_name, channel: email|whatsapp, body, external_id?}
  -> {id, status, missing[], next_action}                      # trial auto-provisions here
POST /situations/{id}/extract {body}  -> extraction + missing + summary
POST /rfqs {situation_id}             -> RFQ Draft
POST /rfqs/{id}/quotations {agent, body_text}  (repeat per agent)
GET  /rfqs/{id}/compare              -> rows, confidence High|Medium|Low, recommendation+reasoning
POST /customer-quotes {situation_id, agent_quotation_id, markup_kind, markup_value}
POST /customer-quotes/{id}/approve   # Manager|Owner only (403 otherwise)
POST /customer-quotes/{id}/send      # 409 unless Approved
POST /follow-ups {situation_id, quote_id?, due_at?}
POST /situations/{id}/outcome {outcome: Negotiation|Accepted|Rejected|Expired}
GET  /dashboard/today  |  GET /situations  |  GET /exceptions (+ POST, POST /{id}/resolve)
```

`Unknown` charges stay `null` and block totals/pricing (422 on premature pricing).
First write from a new org creates a 30-day trial; expired trials get 402.

## 3. Error codes

401 missing/bad token or org-less token · 403 wrong org or role · 402 trial
expired · 404 not in your org · 409 illegal state transition · 422 Unknown
charges or bad category · 500 with traceback in server log (report it).

## 4. Frontend pattern (`frontend/lib/api.ts`)

Same-origin `GET /api/auth/token` (session cookie) → JWT; `GET
/api/auth/get-session` → `session.activeOrganizationId`; fetch
`NEXT_PUBLIC_API_URL` with the three headers. Role comes from localStorage
`qd-role` (demo switch; server enforces it).

## 5. Plugging external integrations

- **Email/WhatsApp sending:** add `backend/app/services/notify.py` (provider
  clients) and call it from `quotes.send` + a nightly ARQ job; credentials go in
  `.env` (never committed). Inbound stays as-is (`POST /intake`).
- **Billing providers:** add `POST /billing/checkout` (create Stripe/Paystack/
  Flutterwave session, return URL) + `POST /billing/webhook/{provider}`
  (verify signature, flip `entitlements.status`); Owner-only checkout.
- **S3 attachments:** set `S3_ENDPOINT`/`S3_BUCKET`/keys — `services/storage.py`
  switches from local disk automatically, same locator shape.
- **New orgs from other apps:** replicate §1; the backend provisions trials itself.

## 6. Local URLs

UI :3002 · API :8000 (`/docs`) · PG :5433 · Redis :6379. Revive: `docs/LOCAL_STACK.md`.
