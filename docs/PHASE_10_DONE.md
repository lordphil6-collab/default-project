# Phase 10 — Live close-out: billing, worker, storage, secrets (DONE, verified 2026-10-04)

Implemented:
- Trial auto-provision on first write (billing.py) — no signup webhook needed; unknown orgs get 30-day trial + trialing entitlement
- require_entitlement wired into POST /intake, /rfqs, /customer-quotes (402 on expiry)
- backend/app/services/storage.py — local-disk first, S3 shape-compatible when S3_ENDPOINT set (MinIO upstream 410s; local is the minimal-cost dev answer)
- worker live: Windows Redis 5.0.14.1 port on :6379 (tporadowski zip), arq worker connected, job executed against live PG
- backend/scripts/{arq_proof,billing_proof,pg_smoke,apply_auth_schema,live_roundtrip,pg_serve}.py
- backend/tests/test_phase10.py — provision→402 cycle (async SQLite), storage roundtrip, grace boundary
- .env generated locally (gitignored) with strong secret + live PG URL

Verified live:
- ARQ: REDIS PING True → enqueue → worker ran send_due_reminders → JOB RESULT {followups_due: 0, trials_expiring: 0}
- BILLING: first write 200 (trial auto-created) → trial expired via SQL → second write 402
- ruff clean; pytest 27 passed EXIT=0; eval GATE PASS (unchanged); frontend build green (unchanged since)

Running dev processes (restart after reboot; kill by closing shell/reboot):
- pgserver PG16 (:58226, .pg_url) + EDB PG16 (:5433, from completed bootstrap)
- redis-server :6379, Next dev :3000, uvicorn :8000–:8004 (latest code on :8004)
- MinIO: NOT running — dl.min.io 410s open-source builds; storage.py local backend covers dev

Docs: PILOT_GATE billing line now live-proven. Deployment to cloud (secrets per env, TLS, backups) remains the only manual step — needs a target account.
