# External services — integration guide (comprehensive)

Every integration below is optional: with nothing configured the app runs
fully on local equivalents and says so honestly (`logged-only`, `501`).
Each section: purpose → env vars → steps → verify → fallback.

Conventions: put secrets in shell env or `.env` (git-ignored, never commit).
After setting vars, restart the API (`uvicorn ... --port 8000`).

## 1. Inbound email — Gmail / Outlook (IMAP)

Purpose: agents reply to RFQs, customers write in; replies auto-ingest.
Env: `MAIL_SECRET_KEY` (required, generates below), per-mailbox creds via UI.
Steps:
1. `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` → `MAIL_SECRET_KEY`.
2. Gmail: Google Account → Security → 2-Step → App passwords → 16-char password. Outlook: account.microsoft.com → Security → App passwords.
3. App → Mailbox → Connect: host `imap.gmail.com` / `outlook.office365.com`, username, app password.
4. "Poll now" or wait for the 30-min worker cron.
Verify: reply to an RFQ email (keep `[RFQ:xxxxxxxx]` in subject) → quotation appears, recipient flips to Responded.
Fallback: manual paste into the RFQ card; `POST /mailboxes/{id}/poll` returns 502 with reason instead of crashing.

## 2. Outbound email — SMTP (RFQ + quote delivery)

Purpose: real RFQ emails to agents, real quote emails to customers.
Env: `SMTP_HOST`, `SMTP_PORT` (587, 465 = SSL), `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`.
Steps: Gmail/Outlook as above (same app password); set vars; restart API; send an RFQ/quote choosing email channel.
Verify: `deliveries[].status == "sent"`, audited under `quote.sent` / RFQ send.
Fallback: `logged-only` recorded in audit — never pretends.

## 3. WhatsApp Cloud API (outbound ready, inbound planned)

Purpose: quote delivery + follow-ups over WhatsApp.
Env: `WHATSAPP_TOKEN` (Meta permanent token), `WHATSAPP_PHONE_ID`.
Steps: developers.facebook.com → create Business app → WhatsApp → API Setup → test number, then add a real business number; set vars; choose WhatsApp channel on send.
Verify: `status == "sent"`. Inbound webhook (`POST /webhooks/whatsapp`, verify via `WHATSAPP_VERIFY_TOKEN`) is Phase B scope — see `docs/PLAN_NEXT.md`.
Fallback: `logged-only`.

## 4. Stripe (cards, international)

Purpose: SaaS subscriptions. Env: `STRIPE_SECRET_KEY` (`sk_test_...` first), `STRIPE_WEBHOOK_SECRET`.
Steps: dashboard.stripe.com → Developers → API keys → test key; set vars; as Owner open `/billing` → Subscribe → redirected to Checkout → pay with `4242 4242 4242 4242`.
Local webhooks: `stripe listen --forward-to localhost:8000/billing/webhook/stripe`.
Verify: entitlement flips to `active` (watch API log); `/billing` shows green.
Fallback: honest 501 naming the missing key.

## 5. Paystack (NGN cards/transfers) — full steps in docs/PAYSTACK.md

Env: `PAYSTACK_SECRET_KEY` (`sk_test_...` first). Subscribe → Checkout → test card `4084 0840 8408 4081`. Local webhooks need `ngrok http 8000` (Paystack can't reach localhost) or flip to `active` from `/admin` after confirming in Paystack dashboard. HMAC-SHA512 verified on every webhook.

## 6. Attachment storage — S3 API (MinIO local / R2 / AWS)

Purpose: quotation PDFs/Excel persist outside the DB.
Default: local disk (`STORAGE_DIR`, default `./var/storage`). To switch: set `S3_ENDPOINT` (+ `S3_BUCKET`, `MINIO_USER`, `MINIO_PASSWORD` or AWS keys) — `services/storage.py` switches automatically, same locator shape.
Local MinIO (no admin): download `minio.exe` (GitHub releases — dl.min.io 410s the old builds), run `minio.exe server C:\minio-data --address 127.0.0.1:9000`, set endpoint to it.
Verify: upload a PDF in any RFQ card → stored; re-download path in locator.

## 7. Image OCR — Tesseract (only missing parser)

Purpose: read photographed/scanned quotations. Install: `winget install UB-Mannheim.TesseractOCR`, add `tesseract.exe` to PATH, `pip install pytesseract`, then extend `services/parse_files.py:extract_text` image branch (currently a clear 422). Verify with a photo quote → extracted totals.

## 8. Carrier rate feeds (Maersk Spot, Freightos, airlines)

Need your carrier contracts + API keys — no code conjures those. Plug point is single: `services/rates.py` history source. Add `services/carriers/<name>.py` returning `{agent, total, transit_days, ...}` dicts, merge into the pool — comparison, badges, guidelines, quote page work unchanged. Until then: `/agents` + seeded sample lines (marked SAMPLE).

## 9. Hosting the frontend — Netlify

`netlify.toml` declares base `frontend`, build `npm run build`, publish `.next`, Node 20. Dashboard must set: `DATABASE_URL` (Neon/Supabase, plain `postgresql://`), `BETTER_AUTH_SECRET` (32+ chars), `BETTER_AUTH_URL` + `NEXT_PUBLIC_BETTER_AUTH_URL` (site URL). Then Clear-cache redeploy; expect `/`, `/login`, `/design-system` 200. Backend (FastAPI/worker/Postgres) does NOT run on Netlify — host on a VPS (compose file in `infra/`) or keep local.

## 10. Provider-status checklist (run before pilot)

`/billing` shows Stripe/Paystack on-off · test RFQ email arrives · test agent reply auto-ingests · test quote email arrives · test checkout in test mode · `erase_org.py` on a throwaway org · backup `C:\Users\user\pgdata` + `.env` copies offline.
