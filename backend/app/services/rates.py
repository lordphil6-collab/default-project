"""Instant guideline rates from quotation history (Freightos-style).

No waiting for agents: estimate low/typical/high from past identifiable totals
on the same lane. Unknown stays Unknown — thin history lowers confidence,
never invents precision.
"""
import statistics

from sqlalchemy import select

from ..models import AgentQuotation, RFQ, Situation


async def org_history(s, org_id: str) -> list[dict]:
    """Identifiable past totals with lane + agent context."""
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
        out.append({"agent": aq.agent, "rfq_id": aq.rfq_id, "origin": ship.get("origin"), "destination": ship.get("destination"),
                    "mode": ship.get("mode"), "total": total, "transit_days": aq.transit_days})
    return out


def _lane(q: dict) -> str:
    return f"{(q.get('origin') or '').strip().lower()}>{(q.get('destination') or '').strip().lower()}"


def lane_stats(quotes: list[dict]) -> dict:
    """quotes: [{origin, destination, mode, total, transit_days}]. Totals must be identifiable."""
    usable = [q for q in quotes if q.get("total") is not None]
    if not usable:
        return {"count": 0}
    totals = sorted(q["total"] for q in usable)
    transits = sorted(q["transit_days"] for q in usable if q.get("transit_days"))
    return {
        "count": len(usable),
        "low": totals[0],
        "typical": round(statistics.median(totals), 2),
        "high": totals[-1],
        "fastest_transit_days": transits[0] if transits else None,
    }


def guideline(shipment: dict, history: list[dict]) -> dict:
    """Best-effort instant estimate with explicit basis + confidence."""
    lane = _lane({"origin": shipment.get("origin"), "destination": shipment.get("destination")})
    mode = (shipment.get("mode") or "").strip().lower()

    def pool(pred) -> list[dict]:
        return [q for q in history if q.get("total") is not None and pred(q)]

    exact = pool(lambda q: _lane(q) == lane and (q.get("mode") or "").strip().lower() == mode) if mode else []
    lane_only = pool(lambda q: _lane(q) == lane)
    if len(exact) >= 1:
        stats, basis, used = lane_stats(exact), "same lane + mode", exact
    elif lane_only:
        stats, basis, used = lane_stats(lane_only), "same lane, any mode", lane_only
    else:
        stats, basis, used = {"count": 0}, "no history", []
    if not stats.get("count"):
        return {"available": False, "basis": basis, "confidence": "Low",
                "note": "No comparable history — send the RFQ and compare live quotes."}
    n = stats["count"]
    confidence = "High" if n >= 5 else ("Medium" if n >= 2 else "Low")
    out = {"available": True, "basis": basis, "confidence": confidence, **stats}
    opts = carrier_options(used)
    if opts:
        out["options"] = opts
    return out


def carrier_options(history: list[dict], limit: int = 8) -> list[dict]:
    """Per-carrier lane averages from identifiable past totals.

    history items: {agent, total, transit_days}. Sorted cheapest first —
    the Freightos-style options list. Agents without identifiable totals
    never appear (no invented prices).
    """
    from collections import defaultdict

    groups: dict[str, list[dict]] = defaultdict(list)
    for q in history:
        if q.get("total") is not None and q.get("agent"):
            groups[q["agent"]].append(q)
    opts = []
    for agent, rows in groups.items():
        totals = sorted(r["total"] for r in rows)
        transits = sorted(r["transit_days"] for r in rows if r.get("transit_days"))
        opts.append({
            "agent": agent,
            "trips": len(rows),
            "low": totals[0],
            "avg": round(sum(totals) / len(totals), 2),
            "high": totals[-1],
            "transit_days": transits[0] if transits else None,
        })
    opts.sort(key=lambda o: o["avg"])
    return opts[:limit]
