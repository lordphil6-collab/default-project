"""Agent matcher tests — lane > service > capability, explained, inactive out."""
from backend.app.services import agents as m

SHIP = {"origin": "China", "destination": "Lagos", "quantity": "1 x 20ft",
        "equipment": "20ft", "mode": "ocean"}


def _agent(company, **kw):
    d = {"id": company, "company": company, "routes": [], "services": [],
         "capabilities": [], "status": "Active"}
    d.update(kw)
    return d


def test_full_match_ranks_first_with_reasons():
    a = _agent("A", routes=["China>Lagos"], services=["ocean"], capabilities=["20ft"])
    b = _agent("B", routes=["China>Lagos"], services=["air"])
    ranked = m.match_agents(SHIP, [b, a])
    assert ranked[0]["agent"] == "A" and ranked[0]["score"] == 100.0
    assert any("lane" in r for r in ranked[0]["reasons"])
    assert any("ocean" in r for r in ranked[0]["reasons"])


def test_inactive_excluded_and_partial_match_kept():
    a = _agent("A", routes=["China>Lagos"], status="Inactive")
    b = _agent("B", routes=["Lagos>New York"])  # destination-only match
    ranked = m.match_agents(SHIP, [a, b])
    assert [r["agent"] for r in ranked] == ["B"]
    assert ranked[0]["score"] == 20.0
    assert any("Lagos" in r for r in ranked[0]["reasons"])


def test_empty_agents_scores_zero():
    s, reasons = m.score_agent(SHIP, _agent("X"))
    assert s == 0.0 and reasons == ["no lane/service match — general fallback only"]
