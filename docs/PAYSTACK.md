# Connecting Paystack — direct steps

Takes ~15 minutes. You need a Paystack account (paystack.com → Sign up →
Activate business for live, or use Test mode free immediately).

## 1. Get keys (5 min)

1. Log in at dashboard.paystack.com → Settings → API Keys & Webhooks.
2. Copy the **Secret Key**. Start with the **Test** secret (`sk_test_...`) —
   test cards work without real money.
3. Copy it locally (never commit it).

## 2. Give the API the key (2 min)

On this machine, add to the shell before starting uvicorn:

```powershell
$env:PAYSTACK_SECRET_KEY = 'sk_test_...'
```

For production, set `PAYSTACK_SECRET_KEY` (live `sk_live_...`) in the host
environment (Netlify dashboard → Environment variables for a hosted API, or
your VPS `.env`). Restart the API after setting it.

Verify it sees the key: open `/billing` in the app — providers line should read
`Paystack on`.

## 3. Subscribe flow (2 min, as Owner)

1. Sign in, switch role to **Owner** (topbar dropdown).
2. Open `/billing` → pick Starter/Pro → **Subscribe**.
3. The API calls `transaction/initialize` and returns `authorization_url` —
   the page redirects you to Paystack Checkout.
4. Pay with a [test card](https://paystack.com/docs/payments/test-payments/)
   (e.g. `4084 0840 8408 4081`, any future expiry/CVV) for `sk_test_...`.

## 4. Webhook back to us (5 min local / 1 min hosted)

Paystack must reach `POST /billing/webhook/paystack` to flip the entitlement
to `active`. Localhost is not reachable from the internet, so for local testing:

- Option A (recommended): run `ngrok http 8000`, then in Paystack dashboard →
  Settings → API Keys & Webhooks → Webhook URL =
  `https://<you>.ngrok.io/billing/webhook/paystack`, and re-run a test payment.
- Option B: skip the webhook locally — after test payment, verify in Paystack
  dashboard → Payments, then set the org `active` from the app's `/admin` page
  (Owner → Set entitlement). The webhook path is unit-tested
  (`test_phase11.py::test_paystack_signature`) and activates automatically
  wherever the API is publicly reachable.

Signature check: every webhook is HMAC-SHA512 verified against your secret
(`verify_paystack_signature`) — 401 otherwise. Nothing activates without it.

## 5. Amounts

`amount` is sent in **kobo** (`monthly_price × 100`). Plan prices live in the
`plans` table (seeded Starter 29 / Pro 99) — set real NGN prices via SQL or a
future pricing-admin edit before going live.

## Stripe (alternative)

Same shape: set `STRIPE_SECRET_KEY` (+ `STRIPE_WEBHOOK_SECRET`), Subscribe
redirects to Stripe Checkout, `checkout.session.completed` activates. Stripe
CLI (`stripe listen --forward-to localhost:8000/billing/webhook/stripe`)
replaces ngrok for local webhook testing.
