# Phase 7 — Module 6: Follow-ups, exceptions, Today dashboard (DONE, verified 2026-10-04)
Date: 2026-10-04

Implemented:
- backend/app/models.py — FollowUp += quote_id; new ServiceException (category/owner/next_action/due/status)
- backend/app/services/followup.py — bucket (overdue|due_today|upcoming|no_due), today_counts (urgent = overdue + open exceptions), outcome transitions
- backend/app/routers/followups.py — POST /follow-ups, GET /follow-ups (bucketed), POST /situations/{sid}/outcome (terminal outcomes sync linked quotes)
- backend/app/routers/exceptions.py — POST /exceptions (8 validated categories), GET /exceptions, POST /exceptions/{eid}/resolve
- backend/app/routers/dashboard.py — GET /dashboard/today (urgent, follow_ups, pending_agents, awaiting_approval, exceptions)
- backend/tests/test_phase7.py — buckets, counts, outcome rules
- main.py v0.7.0 — 23 routes

Verified:
- ruff clean; pytest backend/tests/ — 13 passed
- frontend build green (untouched this phase)

Deferred: reminder scheduler (ARQ cron), frontend live wiring (needs running API + auth session), manager role views.

Next: Phase 8 — approval hardening (real JWKS), audit trail writes, eval harness, pilot gate.
