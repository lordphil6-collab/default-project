"""Admin backend — platform operations, separate from user workflows.

Owner role only. Covers: organizations + trials, entitlements management,
audit trail. CSR/Sales/Ops get 403 here by design.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import CurrentUser, require_roles
from ..models import AuditLog, Entitlement, Organization
from ..services.audit import log_action
from .intake import _session

router = APIRouter()
owner = require_roles("Owner")


class EntitlementIn(BaseModel):
    org_id: str
    status: str  # trialing|active|past_due|cancelled
    plan_id: str | None = None


@router.get("/admin/orgs")
async def list_orgs(_: CurrentUser = Depends(owner), s: AsyncSession = Depends(_session)):
    orgs = ((await s.execute(select(Organization).limit(200))).scalars().all())
    ents = ((await s.execute(select(Entitlement))).scalars().all())
    by_org = {e.org_id: e for e in ents}
    return [{"org_id": o.id, "name": o.name,
             "trial_ends": o.trial_ends.isoformat() if o.trial_ends else None,
             "entitlement": by_org[o.id].status if o.id in by_org else "none",
             "plan_id": by_org[o.id].plan_id if o.id in by_org else None} for o in orgs]


@router.post("/admin/entitlements")
async def set_entitlement(payload: EntitlementIn, user: CurrentUser = Depends(owner),
                          s: AsyncSession = Depends(_session)):
    if payload.status not in ("trialing", "active", "past_due", "cancelled"):
        raise HTTPException(status_code=422, detail="bad status")
    ent = ((await s.execute(select(Entitlement).where(Entitlement.org_id == payload.org_id)))
           .scalars().first())
    if ent is None:
        ent = Entitlement(org_id=payload.org_id, status=payload.status, plan_id=payload.plan_id)
        s.add(ent)
    else:
        ent.status = payload.status
        ent.plan_id = payload.plan_id or ent.plan_id
    await log_action(s, org_id=payload.org_id, actor=user.user_id, action="admin.entitlement",
                     detail={"status": payload.status, "plan_id": payload.plan_id})
    await s.commit()
    return {"org_id": payload.org_id, "status": ent.status}


@router.get("/admin/audit")
async def list_audit(org_id: str | None = None, limit: int = 100,
                     _: CurrentUser = Depends(owner), s: AsyncSession = Depends(_session)):
    q = select(AuditLog)
    if org_id:
        q = q.where(AuditLog.org_id == org_id)
    rows = ((await s.execute(q.order_by(desc(AuditLog.created_at)).limit(min(limit, 500))))
            .scalars().all())
    return [{"actor": r.actor, "action": r.action, "detail": r.detail, "org_id": r.org_id,
             "at": r.created_at.isoformat() if r.created_at else None} for r in rows]
