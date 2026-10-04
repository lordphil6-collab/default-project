# Phase 6 — Module 5: Markup + customer quote + approval gate (DONE, verified 2026-10-04)
Date: 2026-10-04

Implemented:
- backend/app/services/pricing.py — percent|fixed|minimum|combined, min_margin floor, 2dp
- backend/app/models.py — CustomerQuotation += agent_quotation_id, markup_rule_id, agent_total, markup_amount, terms, validity_days; new MarkupRule (kind/value/min_margin)
- backend/app/routers/quotes.py — POST /customer-quotes (422 if agent Unknown; starts Approval Required), POST /customer-quotes/{id}/approve (Manager/Owner only, 409 unless Approval Required), POST /customer-quotes/{id}/send (409 unless Approved — L4 gate)
- backend/tests/test_phase6.py — 2920+12%=3270.40, fixed/minimum floor, unknown-kind reject, gate matrix
- frontend/lib/pricing.ts — preview mirror of backend math (must stay in sync)
- main.py v0.6.0 — 16 routes

Verified:
- ruff clean; pytest backend/tests/ — 10 passed
- frontend build green (pricing.ts typechecks in build)

Deferred: markup-rule CRUD UI, quote PDF render, send via Email/WhatsApp (needs Docker mail provider + Phase 7 follow-ups).

Next: Phase 7 Module 6 — follow-ups, exceptions, Today dashboard wiring.
