"""SaaS trial enforcement (Phase 9). Writes require trialing/active entitlement.

First write from an unknown org auto-provisions a 30-day trial
(Organization + trialing Entitlement) — no separate signup webhook needed.
Past-due orgs keep read-only access; writes 402.
"""
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from sqlalchemy import select

from ..auth import CurrentUser, get_current_user
from ..db import make_async_session_factory
from ..models import Entitlement, Organization

TRIAL_DAYS = 30

_session_factory = None  # seam for tests


def _factory():
    return _session_factory or make_async_session_factory()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def entitlement_allows(status: str, trial_ends: datetime | None, now: datetime | None = None) -> bool:
    now = now or _now()
    if status == "active":
        return True
    if status == "trialing":
        return trial_ends is None or trial_ends >= now
    return False  # past_due|cancelled|expired block writes (grace is read-only)


async def require_entitlement(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    now = _now()
    async with _factory()() as s:
        org = (
            (await s.execute(select(Organization).where(Organization.id == user.org_id))).scalars().first()
        )
        if org is None:
            org = Organization(id=user.org_id, name=user.org_id,
                               trial_start=now, trial_ends=now + timedelta(days=TRIAL_DAYS))
            s.add(org)
            await s.flush()
        ent = (
            (await s.execute(select(Entitlement).where(Entitlement.org_id == user.org_id))).scalars().first()
        )
        if ent is None:
            ent = Entitlement(org_id=user.org_id, status="trialing")
            s.add(ent)
            await s.flush()
        status, trial_ends = ent.status, org.trial_ends
        await s.commit()
    if not entitlement_allows(status, trial_ends, now):
        raise HTTPException(status_code=402, detail="Trial expired — subscribe to continue writing")
    return user
