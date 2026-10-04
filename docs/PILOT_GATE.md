# Pilot gate — 19-step acceptance (PRD Sec 38) mapped to implementation
Date: 2026-10-04. Run `python -m pytest -q backend/tests/` + `python -m backend.app.services.evalharness`.

| # | Step | Endpoint / test |
|---|------|-----------------|
| 1 | Receive enquiry | POST /intake (test_phase2) |
| 2 | AI summary | POST /understand → summary (test_phase3) |
| 3 | Shipment info | extraction fields (evalharness origin/dest 1.0) |
| 4 | Missing info | missing recall 1.0, never invented |
| 5 | Situation create/update | POST /situations/{sid}/extract |
| 6 | RFQ create | POST /rfqs |
| 7 | Agent quotes in | POST /rfqs/{id}/quotations (test_phase5) |
| 8 | Extract | parse_quote_text keeps Unknown |
| 9 | Normalize | Included/Excluded/Unknown split |
| 10 | Compare | GET /rfqs/{id}/compare, confidence set |
| 11 | Flag Unknown | total None blocks comparison |
| 12 | Review recommendation | explained reasoning (evalharness) |
| 13 | Markup rules | 2920+12%=3270.40 (test_phase6) |
| 14 | Prepare quote | POST /customer-quotes → Approval Required |
| 15 | Approve | POST .../approve Manager/Owner only; audited |
| 16 | Track status | GET /situations, /follow-ups |
| 17 | Customer response | POST /situations/{sid}/outcome |
| 18 | Follow-up | POST /follow-ups, bucketed; dashboard counts |
| 19 | Outcome | terminal sync to quotes; audited |

Gates: pytest all-pass, evalharness GATE PASS, ruff clean, frontend build green.
Auth: ALLOW_AUTH_STUB=true for pilot; prod sets false + FASTAPI_JWKS_URL.
Billing: trial enforcement live-proven — first write auto-provisions 30-day trial, expired trial returns 402 (scripts/billing_proof.py).
Migrations: backend/alembic 0001 verified upgrade+downgrade (SQLite-proven; rerun same command with Postgres DATABASE_URL once DB is up). Auth tables: frontend/drizzle/auth-schema.ts generated — apply with drizzle-kit push once Postgres runs.
