# Product Requirements Document — Freight Customer Service Desk
**Living document** (supersedes `PRODUCT REQUIREMENTS DOCUMENT.pdf`, kept as v1 record).
Last updated: 2026-10-12 (v5). Status markers: ✅ shipped & live-proven · 🔶 partial · ⬜ planned.

## Changelog
- v5 (live carriers + inbox synthesis): carrier adapter framework
  (`backend/app/services/carriers/`) with timeout-isolated fan-out; DHL Express
  MyDHL Rating adapter live (account-gated, skipped honestly when unconfigured);
  `GET /rates/live` + "Live carrier rates" card on Get Quote; pricing-rule
  dropdown on Price quote (uses saved `/pricing` rules); inbox thread → RFQ
  brief synthesis (`POST /conversations/{id}/brief`) with one-click situation
  creation for agents to quote.
- v4 (UX overhaul): all §12 review gaps that were UI-fixable are now shipped —
  working global search, quotation picker (no more hand-typed IDs), role badge +
  gated actions, trial-days pill, nav badges, inbox reply, follow-up completion,
  team member management, track auto-lookup, friendly errors, confirmations,
  pagination/filters, a11y pass. New endpoints: `POST /conversations/{id}/messages`,
  `POST /follow-ups/{id}/done`, `GET /api/auth/role`.
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
| 1b | **Inbox RFQ-brief synthesis for agents** | ✅ NEW | `POST /conversations/{id}/brief`, Inbox brief card → situation |
| 2 | Situation Intelligence | ✅ | `/situations`, `/situations/[id]` |
| 3 | RFQ Intelligence + **agent matching & distribution** | ✅ | `/agents`, match, recipients, send |
| 3b | **Live carrier feeds (DHL Express + adapter fan-out)** | ✅ NEW | `GET /rates/live`, Get Quote live card, `services/carriers/` |
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

## 12. Honest review (2026-10-08; resolved 2026-10-12 in v4 unless noted)
Full findings: `docs/REVIEW.md`. Headline gaps: decorative global search ✅
(now searches situations); no forgot-password/invite UI ✅ (both shipped
earlier); no quote PDF export ⬜ (still open); no delivered notifications 🔶
(worker sends reminders; in-app notification center still open); demo-grade
role switch ✅ (real role badge + gated Approve); quotations unlinked to agents
✅ (agent link + dropdown picker); guideline display-only ✅ (estimate actions
on every page); quote form ignores saved rules ✅ (pricing-rule dropdown on
Price quote, ad-hoc fallback kept); read-only inbox ✅ (reply
box shippable via new endpoint); one-way tracking 🔶 (auto-lookup added;
customer replies still one-way); no drill-downs/customer-360/audit timeline UI
🔶 (nav badges + filters added; customer-360 still open); no public rate limits
✅, PII redaction ✅, retention path ✅ (Phase A, shipped earlier); live
provider secrets pending (unchanged — operator step).

## 13. Roadmap to standard (from review; v4 progress noted)
Full plan: `docs/PLAN_NEXT.md`. **A** trust & abuse ✅ shipped (real roles,
password reset, invites, rate limits, PII/retention) → **B** interconnections
🔶 mostly shipped (agent_id link ✅ + dropdown picker ✅, rule dropdown 🔶,
inbox reply ✅, track auto-lookup ✅, drill-downs + search ✅, customer 360
⬜, WhatsApp inbound ⬜; outlier flags + scorecards ⬜) → **C** value features
⬜ (PDF export, delivered reminders, SLAs, dedupe, templates, FX, customer API
keys) → **D** readiness 🔶 (verified deploy ⬜, backups ⬜, mobile/a11y 🔶 —
screen-reader + keyboard pass done, mobile layout still basic).
Each phase ships independently with tests + live proof; §10 rows flip to ✅.
