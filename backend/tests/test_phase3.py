"""Phase 3 tests — golden fixtures from PRD (no LLM, no DB server)."""
from backend.app.services import understanding as u


def test_five_cartons_guangzhou_lagos_missing_weight():
    ext = u.extract_shipment("Please give me a quote for 5 cartons from Guangzhou to Lagos.")
    missing = u.detect_missing(ext)
    assert ext["origin"] == "Guangzhou"
    assert ext["destination"] == "Lagos"
    assert ext["quantity"] == "5 cartons"
    assert ext["weight_kg"] is None  # never invented
    assert "weight" in missing and "dimensions" in missing and "mode" in missing
    s = u.summarize(ext, missing)
    assert "Guangzhou" in s and "Lagos" in s and "Missing" in s
    assert u.recommend_next_action(missing).startswith("Request missing info")


def test_twenty_ft_china_lagos_equipment():
    ext = u.extract_shipment("We need a quote for one 20 foot container from China to Lagos.")
    assert ext["equipment"] in ("20ft", "1x20ft") or "20ft" in (ext.get("equipment") or "")
    assert ext["destination"] == "Lagos"
    missing = u.detect_missing(ext)
    assert "weight" in missing
    assert u.recommend_next_action([]) == "Create RFQ"
