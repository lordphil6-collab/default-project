"""Instant rates — benchmark + per-situation guideline from quote history."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import CurrentUser, get_current_user
from ..models import AgentQuotation, RFQ, Situation
from ..services import rates as rt
from ..services.rates import org_history
from .intake import _session

router = APIRouter()


@router.get("/rates/benchmark")
async def benchmark(origin: str = "", destination: str = "", mode: str = "",
                    user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    hist = await org_history(s, user.org_id)

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
    return rt.guideline(sit.shipment or {}, await org_history(s, user.org_id))
