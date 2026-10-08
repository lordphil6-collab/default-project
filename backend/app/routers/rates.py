"""Instant rates — benchmark + per-situation guideline from quote history."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import CurrentUser, get_current_user
from ..models import AgentQuotation, RFQ, Situation
from ..services import rates as rt
from .intake import _session

router = APIRouter()


async def _history(s: AsyncSession, org_id: str) -> list[dict]:
    """Identifiable past totals with lane context (situation shipment)."""
    rows = ((await s.execute(
        select(AgentQuotation, RFQ, Situation)
        .join(RFQ, AgentQuotation.rfq_id == RFQ.id)
        .join(Situation, RFQ.situation_id == Situation.id)
        .where(AgentQuotation.org_id == org_id)
        .limit(2000)
    )).all())
    out = []
    for aq, _rfq, sit in rows:
        ship = sit.shipment or {}
        total = None
        if aq.freight is not None and aq.destination_charges is not None:
            total = round(aq.freight + (aq.origin_charges or 0.0)
                          + aq.destination_charges + (aq.other_charges or 0.0), 2)
        out.append({"agent": aq.agent, "origin": ship.get("origin"), "destination": ship.get("destination"),
                    "mode": ship.get("mode"), "total": total, "transit_days": aq.transit_days})
    return out


@router.get("/rates/benchmark")
async def benchmark(origin: str = "", destination: str = "", mode: str = "",
                    user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    hist = await _history(s, user.org_id)

    def lane_of(origin: str | None, destination: str | None) -> str:
        return f"{(origin or '').strip().lower()}>{(destination or '').strip().lower()}"

    want = lane_of(origin, destination)
    pool = [q for q in hist if lane_of(q["origin"], q["destination"]) == want]
    if mode.strip():
        pool = [q for q in pool if (q.get("mode") or "").lower() == mode.strip().lower()]
    stats = rt.lane_stats(pool)
    return {"origin": origin, "destination": destination, "mode": mode or None, **stats}


@router.get("/situations/{sid}/guideline")
async def guideline(sid: str, user: CurrentUser = Depends(get_current_user),
                    s: AsyncSession = Depends(_session)):
    sit = ((await s.execute(select(Situation).where(
        Situation.id == sid, Situation.org_id == user.org_id))).scalars().first())
    if not sit:
        raise HTTPException(status_code=404, detail="Not found")
    return rt.guideline(sit.shipment or {}, await _history(s, user.org_id))
