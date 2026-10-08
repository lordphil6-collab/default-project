# Implementation plan — closing the gaps (post-review 2026-10-08)

Principle: connect before adding. Each phase is independently shippable and
ends with `ruff + pytest + build + live proof`, as before.

## Phase A — trust & abuse (security first)
- A1. Real roles: set Better Auth member roles at invite/signup (owner/admin/
  member → CSR/Manager/Owner mapping), JWT carries role; remove localStorage
  switch (keep only as explicit demo flag). Fixes approval gates being UI-deep.
- A2. Forgot-password page + route (`/forgot-password`, reset form).
- A3. Invite-member UI (Owner/Manager): create invitation + accept flow.
- A4. Rate limiting on `/public/*` (slowapi or middleware, per-IP burst caps).
- A5. PII redaction in logs/prompts + data-retention doc (delete-my-data path).

## Phase B — interconnections (multiplies existing value)
- B1. `agent_id` on quotations: migration, ingest auto-matches sender/agent
  picker, backfill best-effort. Unlocks scorecards.
- B2. Agent scorecards: response rate, win rate, avg deviation (new
  `/agents/[id]` + API from existing recipients/quotations data).
- B3. Guideline outlier flags on compare rows + RFQ budget pre-fill.
- B4. Pricing-rule dropdown in the quote form (uses saved rules).
- B5. Inbox reply (pre-filled Email/WhatsApp send stored to the thread).
- B6. Tracking questions: customer posts → CSR inbox thread (two-way).
- B7. Dashboard drill-down (pills link to filtered lists) + working global search.
- B8. Customer 360 (all situations/quotes per customer) + per-situation audit timeline.
- B9. WhatsApp inbound webhook (Cloud API) mirroring the IMAP poller.

## Phase C — value features
- C1. Quote PDF export (server-rendered, stores to storage backend).
- C2. Delivered reminders (ARQ → notify service) + notification center.
- C3. SLA timers on follow-ups + overdue escalation.
- C4. Duplicate-enquiry detection (same customer + lane + 7 days → merge suggest).
- C5. Canned replies/templates; multi-currency display (FX reference rate).
- C6. Customer API keys (scoped tokens for the forwarder's own integrations).

## Phase D — readiness
- D1. Provider secrets live (SMTP/WhatsApp/Stripe/Paystack) + Tesseract OCR.
- D2. Netlify deploy verified end-to-end (env vars + redeploy + route checks).
- D3. Backup/restore runbook for pgdata + retention policy.
- D4. Mobile polish pass + a11y sweep on new pages.

Acceptance per phase: new/changed behavior covered by unit tests + a live proof
script, `docs/PILOT_GATE.md` extended, PRD §10 row marked ✅.
