# Phase 8 — Hardening, audit, evals, pilot gate (DONE, verified 2026-10-04)
Date: 2026-10-04

Implemented:
- backend/app/auth.py — JWKS verification (cached, 10m TTL) via FASTAPI_JWKS_URL; token org must match X-Org-Id. ALLOW_AUTH_STUB=true preserves dev/pilot behavior; prod sets false.
- backend/app/services/audit.py — log_action helper; wired into intake.created, quote.approved/sent, situation.outcome, exception.created/resolved
- ai/evals/golden.json — 3 extraction + 3-quote comparison fixtures
- backend/app/services/evalharness.py — `python -m backend.app.services.evalharness` scores origin/dest acc, missing recall, inventions, winner, confidence, explained; GATE PASS
- backend/tests/test_phase8.py — stub/401/prod-missing-JWKS modes, audit shape, eval gate, 17-route pilot coverage
- docs/PILOT_GATE.md — 19-step acceptance mapped to endpoints/tests
- main.py v0.8.0

Verified:
- ruff clean; pytest backend/tests/ — 19 passed
- evalharness GATE PASS; frontend build green (untouched)

Bugs caught: audit.py relative import (`backend.app.services.models`) → fixed to `..models`.

Deferred (need Docker/prod env): live Postgres + Alembic, real Better Auth JWKS round-trip, ARQ reminder cron, SaaS trial enforcement, login UI.

MVP backend complete per plan. Remaining: pilot run (needs Docker Desktop step) + frontend live wiring.
