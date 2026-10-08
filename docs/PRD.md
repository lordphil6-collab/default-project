# Product Requirements Document — Freight Customer Service Desk
**Living document** (supersedes `PRODUCT REQUIREMENTS DOCUMENT.pdf`, kept as v1 record).
Last updated: 2026-10-08 (v3). Status markers: ✅ shipped & live-proven · 🔶 partial · ⬜ planned.

## Changelog
- v1 (PDF): original 41-section MVP — CSR workspace, 6 modules, Email/WhatsApp, human approval.
- v2: + Better Auth · + SaaS billing · + agent matching & distribution · + file
  ingest · + quote delivery · + public portal · + admin · + guideline rates.
- v3 (honest corrections + roadmap): WhatsApp marked 🔶 (outbound only, no
  inbound webhook); PII redaction moved to plan (was wrongly listed enforced);
  added §§12–13 roadmap from `docs/REVIEW.md`.

## 1. Product overview
Unchanged: lightweight AI workspace for logistics CSRs — enquiries, situations,
RFQs, comparison, quotes, follow-ups, exceptions. NOT a TMS (non-goals stand).

## 2. Vision — the five daily questions (unchanged)
What needs attention? What is happening? What is missing? What do quotes mean?
What next? Added: **a sixth — what should the customer see?** (public portal).

## 3. Modules
| # | Module | Status | Where |
|---|--------|--------|-------|
| 1 | Unified Enquiry Desk (Email IMAP, web form; 🔶 WhatsApp outbound only) | ✅/🔶 | `POST /intake`, `/public/enquiries`, `/quote`, `/inbox` |
| 2 | Situation Intelligence | ✅ | `/situations`, `/situations/[id]` |
| 3 | RFQ Intelligence + **agent matching & distribution** | ✅ | `/agents`, match, recipients, send |
| 4 | Comparison (confidence + explained rec + **rank/badges**) | ✅ | compare table, cheapest/fastest |
| 5 | Markup + customer quote + **rules CRUD + delivery** | ✅ | `/pricing`, approve/send + channel |
| 6 | Follow-up + exceptions + Today dashboard | ✅ | `/follow-ups`, `/exceptions`, `/dashboard/today` |
| 7 | **Guideline rates (instant, history-based)** | ✅ NEW | Estimate card, `/rates/*` |
| 8 | **Public quote + tracking portal** | ✅ NEW | `/quote`, `/track`, share links |
| 9 | **SaaS billing (30-day trial)** | ✅ NEW | `/billing`, 402 gate, Stripe/Paystack |
| 10 | **Admin backend (Owner-only)** | ✅ NEW | `/admin`, orgs/entitlements/audit |

## 4. Auth — Better Auth (changed from v1)
Better Auth in Next.js (organization plugin = company tenancy, JWT plugin feeds
FastAPI JWKS). Email+password + Google/Microsoft OAuth, TOTP/passkeys for
approvers. FastAPI verifies Ed25519 JWTs, enforces token-org == header-org,
role gates (CSR/Sales/Ops/Manager/Owner). Public portal routes need no auth.

## 5. Controlled autonomy (unchanged, now enforced in code)
L1 Understand → L2 Recommend → L3 Draft → **L4 Human Approval** (approve before
send; 409 otherwise; audit on every consequential action).

## 6. Data model additions (beyond v1 §27)
`agents`, `rfq_recipients`, `markup_rules`, `plans`, `entitlements`,
`exceptions`, `audit_log.created_at`, `situations.public_token`.
Migrations `0001`–`0005` (Alembic), auth tables via Better Auth CLI + drizzle.

## 7. Key rules (unchanged, enforced + tested)
Unknown ≠ zero · every comparison has confidence · every recommendation explains
itself · markup is company-defined · AI never commits pricing/sends binding
quotes alone · tenant isolation (`company_id`/`org_id` everywhere).
Planned (not yet true): PII redaction in logs/prompts.

## 8. Metrics (v1 §33–34 + new)
Add: trial→paid conversion, recommendation agreement rate, extraction
correction rate, eval gate (`ai/evals/golden.json` must pass), E2E proof scripts.

## 9. Risks (updated)
Resolved: integration complexity (OAuth webhooks live), doc quality (confidence +
Unknown path), liability (mandatory approval + audit). Open: provider secrets
for live money movement, Tesseract for image OCR, cloud deployment target.

## 10. Acceptance (v1 §38–39, now executable)
The 19-step walkthrough is `backend/scripts/e2e_flow.py` (green);
portal is `portal_proof.py`; billing is `billing_proof.py`. Pilot gate: `docs/PILOT_GATE.md`.

## 11. Out of scope (unchanged + clarified)
No TMS/marketplace/booking-as-contract, no autonomous negotiation/pricing,
no accounting ledger (provider-hosted invoices only), no image OCR yet.

## 12. Honest review (2026-10-08)
Full findings: `docs/REVIEW.md`. Headline gaps: decorative global search; no
forgot-password/invite UI; no quote PDF export; no delivered notifications; demo-grade
role switch (approval gates UI-deep until Phase A); quotations unlinked to agents;
guideline display-only; quote form ignores saved rules; read-only inbox; one-way
tracking; no drill-downs/customer-360/audit timeline UI; no public rate limits,
PII redaction, or retention path; live provider secrets pending.

## 13. Roadmap to standard (from review)
Full plan: `docs/PLAN_NEXT.md`. **A** trust & abuse (real roles, password reset,
invites, rate limits, PII/retention) → **B** interconnections (agent_id link +
scorecards, outlier flags, rule dropdown, inbox reply, two-way tracking,
drill-downs + search, customer 360, WhatsApp inbound) → **C** value features
(PDF export, delivered reminders, SLAs, dedupe, templates, FX, customer API
keys) → **D** readiness (live secrets, verified deploy, backups, mobile/a11y).
Each phase ships independently with tests + live proof; §10 rows flip to ✅.
