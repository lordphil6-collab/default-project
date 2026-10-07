"""Agent matching — deterministic rules with explained reasons (free, no LLM).

Scores route > service > capability matches. Inactive agents are excluded.
Every recommendation carries reasons; never a bare label (PRD Sec 17 style).
"""


def _norm(text: str) -> str:
    return (text or "").strip().lower()


def score_agent(shipment: dict, agent: dict) -> tuple[float, list[str]]:
    """shipment: {origin, destination, quantity, equipment, mode, ...}.
    agent: {company, routes[], services[], capabilities[], status}.
    Returns (score 0..100, reasons[])."""
    if (agent.get("status") or "Active") != "Active":
        return 0.0, ["inactive — excluded"]
    score = 0.0
    reasons: list[str] = []
    origin, dest = _norm(shipment.get("origin", "")), _norm(shipment.get("destination", ""))
    routes = [_norm(r) for r in agent.get("routes", [])]
    lane = f"{origin}>{dest}" if origin and dest else ""
    if lane and any(lane in r or r in lane for r in routes):
        score += 50.0
        reasons.append(f"covers lane {shipment.get('origin')}>{shipment.get('destination')}")
    elif origin and any(origin in r for r in routes):
        score += 20.0
        reasons.append(f"covers origin {shipment.get('origin')}")
    elif dest and any(dest in r for r in routes):
        score += 20.0
        reasons.append(f"covers destination {shipment.get('destination')}")
    mode = _norm(shipment.get("mode", ""))
    services = [_norm(s) for s in agent.get("services", [])]
    if mode and mode in services:
        score += 30.0
        reasons.append(f"offers {shipment.get('mode')} service")
    equipment = _norm(shipment.get("equipment", ""))
    quantity = _norm(shipment.get("quantity", ""))
    caps = [_norm(c) for c in agent.get("capabilities", [])]
    if equipment and any(equipment in c or c in equipment for c in caps):
        score += 20.0
        reasons.append(f"handles {shipment.get('equipment')}")
    elif quantity and any(c in quantity or quantity in c for c in caps):
        score += 10.0
        reasons.append("handles similar cargo sizes")
    if not reasons:
        reasons.append("no lane/service match — general fallback only")
    return round(min(score, 100.0), 1), reasons


def match_agents(shipment: dict, agents: list[dict], limit: int = 5) -> list[dict]:
    ranked = [
        {"agent": a.get("company"), "agent_id": a.get("id"), "score": s, "reasons": r}
        for a in agents
        for s, r in [score_agent(shipment, a)]
        if s > 0
    ]
    ranked.sort(key=lambda x: -x["score"])
    return ranked[:limit]
