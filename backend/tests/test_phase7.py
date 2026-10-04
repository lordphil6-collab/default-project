"""Phase 7 tests — buckets, counts, outcome rules (no DB server)."""
from datetime import datetime, timedelta
from backend.app.services import followup as f


def test_buckets_never_silent():
    now = datetime(2026, 10, 4, 12, 0, 0)
    assert f.bucket(now - timedelta(days=1), now) == "overdue"
    assert f.bucket(now, now) == "due_today"
    assert f.bucket(now + timedelta(days=3), now) == "upcoming"
    assert f.bucket(None, now) == "no_due"


def test_today_counts_urgent_includes_overdue_and_exceptions():
    c = f.today_counts(overdue_followups=2, due_today=5, pending_rfqs=4, awaiting_approval=2, open_exceptions=2)
    assert c == {"urgent": 4, "follow_ups": 7, "pending_agents": 4, "awaiting_approval": 2, "exceptions": 2}


def test_terminal_outcomes_always_recordable():
    for st in ("Quote Sent", "Follow Up Due", "Negotiation", "New"):
        for out in ("Accepted", "Rejected", "Expired"):
            assert f.outcome_allowed(st, out) is True
    assert f.outcome_allowed("Follow Up Due", "Negotiation") is True
    assert f.outcome_allowed("New", "Negotiation") is False
