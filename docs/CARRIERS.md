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

Live rates from Maersk Spot, Freightos, or airline APIs plug in at one place:
`services/rates.py` history source (currently past `agent_quotations`). Add a
`services/carriers/<name>.py` adapter returning the same
`{agent, total, transit_days, ...}` dicts and merge it into the history pool —
comparison, badges, guidelines, and the quote page work unchanged. No UI
changes needed; Unknown stays Unknown for anything a feed can't confirm.
