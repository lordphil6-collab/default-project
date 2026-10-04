# Phase 9 — Close-out: migrations, billing gate, cron, login UI (DONE, verified 2026-10-04)
Date: 2026-10-04

Implemented:
- backend/alembic.ini + alembic/env.py (async, DATABASE_URL-driven, PG + SQLite) + versions/0001_initial.py (all 14 tables)
- backend/scripts/verify_migration.py — upgrade head + table assert + downgrade; MIGRATION OK
- backend/app/services/billing.py — entitlement_allows + require_entitlement (402 on expired); wired into POST /intake, /rfqs, /customer-quotes; unknown stub orgs pass through
- worker/main.py — send_due_reminders cron daily 07:00 (follow-ups due + trials expiring 7/3/1d), infra-failure-safe
- frontend/lib/{db,auth-server,auth-client}.ts + app/api/auth/[...all]/route.ts + app/login/page.tsx (email login, org plugin, JWT plugin → FastAPI JWKS)
- frontend/drizzle/auth-schema.ts — generated via Better Auth CLI (user, session, account, verification, organization, member, invitation, jwks)
- backend/tests/test_phase9.py — entitlement matrix, JWKS HS256 real-path + org-mismatch 403, cron config
- .env.example += ALLOW_AUTH_STUB, NEXT_PUBLIC_BETTER_AUTH_URL; requirements += aiosqlite (local verify)

Verified:
- ruff clean; pytest — 23 passed, EXIT=0; evalharness GATE PASS; frontend build green (/, /login, /design-system, /api/auth dynamic)
- migration upgrade+downgrade proven on SQLite

Bugs fixed this round:
- alembic env.py sys.path pointed at backend/ instead of root (import would fail)
- alembic.ini script_location pointed at ./alembic instead of backend/alembic
- verify script ROOT miscalculation; UTC deprecation warning (naive _utcnow helper)
- auth _get_jwks_keys checked URL before cache (broke cached-key path + tests)
- arq CronJob attr is .coroutine not .function; frontend @/ alias missing (relative imports); auth.handler is single fn in 1.7
- @types/pg install noise (already present); PowerShell tail missing (use Select-Object)

Still pending (blocked on infra, in progress):
- Live Postgres: portable 16 bootstrap running in background (no admin) → then `alembic upgrade head` with PG URL + `drizzle-kit push` for auth tables
- Live JWKS round-trip + ARQ against Redis/MinIO (needs Docker Compose services — manual step remains)

## Live proof (achieved 2026-10-04)
- Postgres: pgserver PG16 on 127.0.0.1:58226 (see .pg_url) + EDB PG16 on :5433 (earlier bootstrap completed too)
- Backend migration on live PG: 14 tables + alembic 0001_initial + insert/select roundtrip OK
- Auth tables: frontend/drizzle/0000 SQL applied via backend/scripts/apply_auth_schema.py (push needs TTY; generate+apply used instead) — all 8 tables present
- Full roundtrip OK (backend/scripts/live_roundtrip.py): signup → org → set-active → JWT(organizationId via jwt.definePayload) → FastAPI PyJWT Ed25519 JWKS verify → PG-backed GET /situations 200; cross-org 403; org-less token 401
- Fixes en route: python-jose lacks Ed25519 → PyJWT; tokens without org rejected; relative imports; auth.handler single-fn (1.7)
- Dev servers (restart after reboot): pg_serve (PG), Next dev :3000, uvicorn :800x with ALLOW_AUTH_STUB=false
