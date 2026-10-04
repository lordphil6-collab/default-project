"""Phase 7 follow-up service — pure date logic (free, no deps).

Buckets: overdue | due_today | upcoming | no_due.
PRD Sec 21: quotes must never silently expire — overdue surfaces as urgent.
"""
from datetime import datetime


def bucket(due_at: datetime | None, now: datetime | None = None) -> str:
    now = now or datetime.utcnow()
    if due_at is None:
        return "no_due"
    if due_at.date() < now.date():
        return "overdue"
    if due_at.date() == now.date():
        return "due_today"
    return "upcoming"


def today_counts(
    overdue_followups: int,
    due_today: int,
    pending_rfqs: int,
    awaiting_approval: int,
    open_exceptions: int,
) -> dict:
    return {
        "urgent": overdue_followups + open_exceptions,
        "follow_ups": overdue_followups + due_today,
        "pending_agents": pending_rfqs,
        "awaiting_approval": awaiting_approval,
        "exceptions": open_exceptions,
    }


OUTCOME_TRANSITIONS = {
    "Follow Up Due": ("Negotiation", "Accepted", "Rejected", "Expired"),
    "Negotiation": ("Accepted", "Rejected", "Expired"),
    "Quote Sent": ("Follow Up Due", "Negotiation", "Accepted", "Rejected", "Expired"),
}


def outcome_allowed(from_status: str, to_outcome: str) -> bool:
    if to_outcome in ("Accepted", "Rejected", "Expired"):
        return True  # terminal outcomes recordable from any active state by an authorized role
    return to_outcome in OUTCOME_TRANSITIONS.get(from_status, ())


def reminder_due(created_day: int, expiry_day: int, today: int = 0) -> bool:
    """7/3/1-day reminder helper shared with SaaS trial logic pattern."""
    deltas = [expiry_day - today]
    return any(d in (7, 3, 1) or d <= 0 for d in deltas) and created_day <= expiry_day
