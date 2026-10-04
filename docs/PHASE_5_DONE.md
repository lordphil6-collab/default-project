# Phase 5 — Modules 3+4: Quotation ingest + comparison (DONE, verified 2026-10-04)
Date: 2026-10-04

Implemented (deterministic, free — no LLM calls):
- backend/app/models.py — AgentQuotation += origin_charges (NULL=Unknown), other_charges, raw_text
- backend/app/services/quotation.py — parse_quote_text, identifiable_total (None when core Unknown), compare_quotes (High/Medium/Low + explained recommendation)
- backend/app/routers/quotations.py — POST /rfqs/{id}/quotations (structured override wins; "Unknown" lines stay Unknown), GET /rfqs/{id}/compare
- backend/tests/test_phase5.py — PRD fixture: A $2,920 complete, B freight-only + Unknown dest, C $3,050
- main.py v0.5.0 — 13 routes incl. /rfqs/{id}/quotations, /rfqs/{id}/compare

Verified:
- ruff clean; pytest backend/tests/ — 6 passed
- frontend build green (untouched this phase)

Bugs caught by tests and fixed:
- Amount regex matched "172" of "$1,720" (alternation order) → simplified to digits after comma-strip
- Fixture had Agent C cheapest, contradicting PRD narrative → C set to $3,050 so Agent A (complete, competitive) is recommended with B-caution reasoning

Deferred: binary PDF/Excel/Word upload parsing (text path ready), LLM parity eval, frontend live wiring.

Next: Phase 6 Module 5 — markup engine + customer quote + approval gate.
