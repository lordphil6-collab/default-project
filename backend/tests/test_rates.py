"""Guideline-rate tests — history in, honest estimate out."""
from backend.app.services import rates as r

HIST = [
    {"agent": "A", "origin": "China", "destination": "Lagos", "mode": "ocean", "total": 2920.0, "transit_days": 35},
    {"agent": "C", "origin": "China", "destination": "Lagos", "mode": "ocean", "total": 3050.0, "transit_days": 38},
    {"agent": "A", "origin": "China", "destination": "Lagos", "mode": "ocean", "total": 2870.0, "transit_days": 32},
    {"agent": "B", "origin": "China", "destination": "Lagos", "mode": "air", "total": 8900.0, "transit_days": 5},
    {"agent": "B", "origin": "China", "destination": "Lagos", "mode": "ocean", "total": None, "transit_days": 0},
]


def test_lane_stats_ignores_unknown_totals():
    s = r.lane_stats(HIST)
    assert s["count"] == 4 and s["low"] == 2870.0 and s["typical"] == 2985.0 and s["high"] == 8900.0


def test_guideline_prefers_lane_plus_mode():
    g = r.guideline({"origin": "China", "destination": "Lagos", "mode": "ocean"}, HIST)
    assert g["available"] and g["basis"] == "same lane + mode" and g["confidence"] == "Medium"
    assert g["low"] == 2870.0 and g["typical"] == 2920.0


def test_guideline_falls_back_and_admits_empty():
    g = r.guideline({"origin": "China", "destination": "Lagos", "mode": "rail"}, HIST)
    assert g["available"] and g["basis"] == "same lane, any mode"
    g2 = r.guideline({"origin": "Rotterdam", "destination": "New York", "mode": "ocean"}, HIST)
    assert g2["available"] is False and g2["confidence"] == "Low"


def test_carrier_options_sorted_cheapest_first():
    g = r.guideline({"origin": "China", "destination": "Lagos", "mode": "ocean"}, HIST)
    opts = g["options"]
    assert [o["agent"] for o in opts] == ["A", "C"]
    assert opts[0]["avg"] == 2895.0 and opts[0]["trips"] == 2
    assert "B" not in [o["agent"] for o in opts]  # air-only here; Unknown totals never listed
