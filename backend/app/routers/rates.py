"""Instant rates — benchmark + per-situation guideline from quote history."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import CurrentUser, get_current_user
from ..models import AgentQuotation, RFQ, Situation
from ..services import rates as rt
from ..services.carriers import CarrierRequest, adapter_names, quote_all
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


@router.get("/rates/live")
async def live_rates(situation_id: str = "", origin_country: str = "", destination_country: str = "",
                     origin_city: str = "", destination_city: str = "", weight_kg: float | None = None,
                     user: CurrentUser = Depends(get_current_user),
                     s: AsyncSession = Depends(_session)):
    """Live carrier feed rates (DHL Express + registered adapters) + history basis.

    ISO-2 country codes may come from the query or from a situation's shipment
    (`origin_country`/`destination_country` keys when extraction stored them).
    Unconfigured feeds are listed under `skipped`, never hidden, never fatal.
    """
    ship: dict = {}
    if situation_id:
        sit = ((await s.execute(select(Situation).where(
            Situation.id == situation_id, Situation.org_id == user.org_id))).scalars().first())
        if not sit:
            raise HTTPException(status_code=404, detail="Not found")
        ship = sit.shipment or {}
    req = CarrierRequest(
        origin_country=(origin_country or ship.get("origin_country") or "").strip(),
        destination_country=(destination_country or ship.get("destination_country") or "").strip(),
        origin_city=(origin_city or ship.get("origin") or "").strip(),
        destination_city=(destination_city or ship.get("destination") or "").strip(),
        weight_kg=weight_kg if weight_kg is not None else ship.get("weight_kg"),
        mode=(ship.get("mode") or "").strip(),
    )
    live = await quote_all(req)
    return {"adapters": adapter_names(), "request": req.__dict__, "rates": live.rates,
            "skipped": live.skipped, "errors": live.errors}
