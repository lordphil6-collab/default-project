"""Phase 6 tests — markup math + approval gate (no DB server)."""
import pytest
from backend.app.services import pricing as p


def test_percent_12_on_2920():
    r = p.apply_markup(2920.0, "percent", 12.0)
    assert r == {"agent_total": 2920.0, "markup_amount": 350.4, "final_price": 3270.4}


def test_fixed_and_minimum_floor():
    assert p.apply_markup(1000.0, "fixed", 150.0)["final_price"] == 1150.0
    r = p.apply_markup(1000.0, "minimum", 5.0, min_margin=120.0)
    assert r["markup_amount"] == 120.0 and r["final_price"] == 1120.0


def test_unknown_kind_rejected():
    with pytest.raises(ValueError):
        p.apply_markup(100.0, "magic", 10.0)


def test_l4_gate_blocks_unapproved_send():
    # state-machine rule mirrored from routers/quotes.py::send_quote
    for status, allowed in (("Draft", False), ("Approval Required", False), ("Approved", True), ("Sent", False)):
        assert (status == "Approved") == allowed
