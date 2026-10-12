# Shipping lines — how carriers connect

Your agents ARE your connected lines: `/agents` holds each line's routes,
services, and capabilities, and quote search (`/quote`) ranks them with
guideline averages from your own quote history.

## Sample lines (demo only)

`ORG_ID=<your-org-id> python backend/scripts/seed_carriers.py` adds Maersk,
MSC, CMA CGM, Hapag-Lloyd, COSCO, Evergreen, Lufthansa Cargo, Emirates
SkyCargo with typical lanes — every row marked `SAMPLE DATA`. Replace routes
and contacts with your contracted lines, or delete them. They only ever appear
inside your own org (tenant isolation holds).

## Real carrier APIs (need contracts)

### DHL Express — live now (needs your DHL account)
The app ships a working DHL Express adapter (`backend/app/services/carriers/dhl_express.py`)
against the MyDHL Rating API (https://developer.dhl.com → DHL Express → Get Access):
1. You need an **active DHL Express customer account** — rates are account-based.
2. Your DHL consultant provisions API credentials (HTTP Basic user/password).
3. Set in the API shell before launch (test env allows 500 calls/day):
   `DHL_API_USER`, `DHL_API_PASSWORD`, `DHL_ACCOUNT_NUMBER`,
   optional `DHL_API_BASE` (default = test env; set to the prod URL for live money).
4. Get Quote → "Live carrier rates": enter ISO country codes (e.g. CN → NG) +
   optional kg → one row per DHL product with account total + transit estimate.
Without the vars the feed reports itself skipped (never silent, never fatal).
Rates are indicative; DHL terms forbid storing/revealing rating data without
consent, so the app never caches them — every lookup is fresh.

### Other feeds (Maersk Spot, Freightos, airlines, forwarder networks)
Live rates from Maersk Spot, Freightos, or airline APIs plug in at one place:
`backend/app/services/carriers/` — copy `dhl_express.py`, implement
`configured()` + `quote(req)`, `register()` it. It joins the same fan-out
(timeout-isolated, errors recorded per feed) and appears in Get Quote +
`GET /rates/live` unchanged. Honest notes: Freightos offers no self-serve
quote API (Terminal market data is enterprise-contract; Marketplace is a
shipper booking UI), so there is no Freightos adapter to configure — contracted
forwarder-network feeds arrive the same way (adapter returning the same
`{carrier, service, total, transit_days, ...}` dicts).
