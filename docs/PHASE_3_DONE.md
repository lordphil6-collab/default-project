# Phase 3/4 — Modules 1+2: Understanding + RFQ creation (DONE, verified 2026-10-04)
Date: 2026-10-04

Implemented (deterministic v1 rules, free — no LLM calls):
- ai/prompts/v1/{README,extract,summarise}.md — versioned rules mirrored in code
- backend/app/services/understanding.py — extract_shipment, detect_missing, summarize, recommend_next_action
- backend/app/routers/understand.py — POST /understand (stateless), POST /situations/{sid}/extract (persists shipment/missing/next_action, advances New→Information Required / RFQ In Progress)
- backend/app/routers/rfqs.py — POST /rfqs {situation_id} org-scoped, Draft
- backend/tests/test_phase3.py — golden fixtures: 5 cartons Guangzhou→Lagos, 20ft China→Lagos
- main.py v0.3.0 — routes: /health, /intake, /situations, /understand, /situations/{sid}/extract, /rfqs

Verified:
- ruff clean; pytest backend/tests/ — 3 passed
- routes registered (11 incl. docs)
- `npm run build` — green, /, /design-system static (frontend untouched this phase)

Rules enforced: never invent missing (weight_kg None stays missing); Unknown ≠ zero carried from Phase 2.

Deferred: LLM gateway with identical schema, Excel/PDF parsers, agent ingestion (Phase 5).

Next: Phase 5 Modules 3+4 — multi-format ingest, normalization, comparison + confidence + recommendation.
