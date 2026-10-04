"""Audit trail writer (Phase 8). Every consequential action logs source + actor.

PRD Sec 37: record source, extraction, interpretation, correction,
recommendation, decision, final action.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import AuditLog


async def log_action(
    s: AsyncSession, *, org_id: str, actor: str, action: str, detail: dict | None = None
) -> None:
    s.add(AuditLog(org_id=org_id, actor=actor, action=action, detail=detail or {}))
