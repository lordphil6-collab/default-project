# Honest review — Freight Customer Service Desk (2026-10-08)

Basis: full code read + 45 passing tests + live proofs. What works is real;
below is what's missing versus a standard app of this kind.

## What genuinely works
Enquiry → extract → RFQ → agent match → distribution → ingest (text + PDF/
Excel/Word upload) → ranked comparison → markup → approval-gated quote →
follow-up → outcome; auth (Better Auth, orgs, JWKS); trials + 402 gate;
admin backend; inbox; public quote + tracking; guideline rates; audit trail.

## Missing lines (dead or absent UI)
1. **Global search is decorative** — `layout.tsx:13` is a bare input, no handler.
2. **No forgot-password flow** (Better Auth supports it; no UI/route).
3. **No member-invite UI** (org invitations exist in schema only).
4. **No quote PDF export** — quotes can't leave the system except email/WhatsApp text.
5. **No notification center** — reminders are counted, never delivered.
6. **Role switch is localStorage theater** (`role-select.tsx` admits it) — any user
   can claim Owner; server trusts the header claim only via JWT role which
   Better Auth never sets (defaults CSR). Approval gates are thus UI-deep only.

## Missing connections (islands)
7. **Quotations aren't linked to agents** — `AgentQuotation.agent` is free text;
   no `agent_id`. Kills win-rate/response stats and match learning.
8. **Guideline is display-only** — never flags outlier quotes, never seeds RFQ budgets.
9. **Quote form ignores saved pricing rules** — manual kind/value inputs only.
10. **Inbox is read-only** — threads visible, no reply action.
11. **Tracking is one-way** — customers can't ask questions on their quote.
12. **Dashboard pills don't drill down**; no customer-360 view; no per-situation
    audit timeline in CSR UI (audit lives only in /admin).
13. **WhatsApp inbound missing** (PRD channel); only Email IMAP + manual + web form.
14. **No rate limiting on public endpoints** (`/public/*` abusable), no PII
    redaction in logs, no data-retention/delete path.

## Missing standard ops
15. Live provider secrets (SMTP/WhatsApp/Stripe/Paystack/Tesseract) — all stubbed.
16. Multi-currency FX (stored, never converted), SLA timers, duplicate-enquiry
    detection, canned replies, customer API keys, mobile polish, i18n.
17. Netlify deploy still unverified (dashboard-side).

## Verdict
Solid, honest MVP core with real workflow continuity. To be a *standard*
product it needs: auth completed (6), connections closed (7–12), abuse
hardening (14), then value features. Plan: `docs/PLAN_NEXT.md`.
