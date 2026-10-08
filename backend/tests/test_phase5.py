"""Phase 5 tests — PRD Sec 13-17 golden fixture (no LLM, no DB server)."""
from backend.app.services import quotation as q


A = {"agent": "Agent A", "charges": {"freight": 1850.0, "origin": 420.0, "destination": 650.0, "other": 0.0},
     "validity_days": 7, "transit_days": 35}
B = {"agent": "Agent B", "charges": {"freight": 1720.0, "origin": 600.0, "destination": None, "other": 0.0},
     "validity_days": 5, "transit_days": 32}
C = {"agent": "Agent C", "charges": {"freight": 1900.0, "origin": 390.0, "destination": 580.0, "other": 180.0},
     "validity_days": 10, "transit_days": 38}  # identifiable total $3,050 — highest, per PRD example


def test_unknown_never_zero_and_totals():
    assert q.identifiable_total(A["charges"]) == 2920.0
    assert q.identifiable_total(B["charges"]) is None  # Unknown destination blocks total


def test_compare_confidence_and_explained_recommendation():
    res = q.compare_quotes([A, B, C])
    assert res["confidence"] in ("Medium", "Low")  # B incomplete => not High
    assert res["recommendation"]["agent"] == "Agent A"
    assert "complete cost structure" in res["recommendation"]["reasoning"]
    assert "Agent B" in res["recommendation"]["reasoning"] and "unknown" in res["recommendation"]["reasoning"].lower()
    by_agent = {r["agent"]: r for r in res["rows"]}
    assert by_agent["Agent A"]["rank"] == 1 and "cheapest" in by_agent["Agent A"]["badges"]
    assert by_agent["Agent B"]["rank"] is None and "incomplete" in by_agent["Agent B"]["badges"]
    assert "fastest" in by_agent["Agent B"]["badges"]  # 32d transit known even though total unknown


def test_parse_quote_text_keeps_unknown():
    parsed = q.parse_quote_text("Ocean Freight $1,720\nOrigin Charges $600\nDestination Charges Unknown\nTransit 32 days")
    assert parsed["charges"]["freight"] == 1720.0
    assert parsed["charges"]["destination"] is None


def test_parse_other_charges_label():
    parsed = q.parse_quote_text("Ocean Freight $1,900\nOther Charges $180")
    assert parsed["charges"]["other"] == 180.0
