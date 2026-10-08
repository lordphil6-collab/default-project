"""Instant guideline rates from quotation history (Freightos-style).

No waiting for agents: estimate low/typical/high from past identifiable totals
on the same lane. Unknown stays Unknown — thin history lowers confidence,
never invents precision.
"""
import statistics


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
    if len(exact) >= 1:
        stats, basis = lane_stats(exact), "same lane + mode"
    else:
        lane_only = pool(lambda q: _lane(q) == lane)
        if lane_only:
            stats, basis = lane_stats(lane_only), "same lane, any mode"
        else:
            stats, basis = {"count": 0}, "no history"
    if not stats.get("count"):
        return {"available": False, "basis": basis, "confidence": "Low",
                "note": "No comparable history — send the RFQ and compare live quotes."}
    n = stats["count"]
    confidence = "High" if n >= 5 else ("Medium" if n >= 2 else "Low")
    return {"available": True, "basis": basis, "confidence": confidence, **stats}
