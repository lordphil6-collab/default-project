"""Quote Desk API - Phase 8: + auth hardening, audit trail, eval gate."""
from fastapi import FastAPI
from .routers import dashboard, exceptions, followups, intake, quotations, quotes, rfqs, situations, understand

app = FastAPI(title="AI Quotation Desk", version="0.8.0")
app.include_router(intake.router, tags=["intake"])
app.include_router(situations.router, tags=["situations"])
app.include_router(understand.router, tags=["understanding"])
app.include_router(rfqs.router, tags=["rfqs"])
app.include_router(quotations.router, tags=["quotations"])
app.include_router(quotes.router, tags=["customer-quotes"])
app.include_router(followups.router, tags=["follow-ups"])
app.include_router(exceptions.router, tags=["exceptions"])
app.include_router(dashboard.router, tags=["dashboard"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "phase": 8}
