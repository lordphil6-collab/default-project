"""Quote Desk API - Phase 8: + auth hardening, audit trail, eval gate."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import admin, agents, billing, dashboard, exceptions, followups, inbox, intake, pricing_rules, quotations, quotes, rates, rfqs, situations, understand

app = FastAPI(title="AI Quotation Desk", version="0.9.0")
app.include_router(admin.router, tags=["admin"])
app.include_router(agents.router, tags=["agents"])
app.include_router(billing.router, tags=["billing"])
app.include_router(inbox.router, tags=["inbox"])
app.include_router(pricing_rules.router, tags=["pricing-rules"])

# Browser UI calls this API cross-origin (different port/host), so preflights
# must succeed. Same-origin scripts (httpx/curl) never noticed — the UI did.
origins = [o.strip() for o in os.getenv(
    "FRONTEND_URLS",
    "http://localhost:3000,http://localhost:3001,http://localhost:3002,https://cslogisticsintelligence.netlify.app",
).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(intake.router, tags=["intake"])
app.include_router(situations.router, tags=["situations"])
app.include_router(understand.router, tags=["understanding"])
app.include_router(rfqs.router, tags=["rfqs"])
app.include_router(quotations.router, tags=["quotations"])
app.include_router(rates.router, tags=["rates"])
app.include_router(quotes.router, tags=["customer-quotes"])
app.include_router(followups.router, tags=["follow-ups"])
app.include_router(exceptions.router, tags=["exceptions"])
app.include_router(dashboard.router, tags=["dashboard"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "phase": 8}
