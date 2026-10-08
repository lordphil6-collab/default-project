"""Quote Desk API - Phase 8: + auth hardening, audit trail, eval gate."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import admin, agents, billing, dashboard, exceptions, followups, inbox, intake, mailboxes, portal, pricing_rules, quotations, quotes, rates, rfqs, situations, understand
from .services.ratelimit import RateLimiter
from .services.redact import install as install_redaction

app = FastAPI(title="Freight Customer Service Desk", version="0.9.0")
install_redaction()

_limiter = RateLimiter(limit=20, window_s=60)


@app.middleware("http")
async def public_rate_limit(request, call_next):
    if request.url.path.startswith("/public/"):
        client = (request.client.host if request.client else "unknown")
        if not _limiter.allowed(client):
            from fastapi.responses import JSONResponse

            return JSONResponse(status_code=429, content={"detail": "Too many requests — slow down"})
    return await call_next(request)
app.include_router(admin.router, tags=["admin"])
app.include_router(agents.router, tags=["agents"])
app.include_router(billing.router, tags=["billing"])
app.include_router(inbox.router, tags=["inbox"])
app.include_router(mailboxes.router, tags=["mailboxes"])
app.include_router(pricing_rules.router, tags=["pricing-rules"])
app.include_router(portal.router, tags=["portal"])

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
