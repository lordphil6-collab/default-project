"""Follow-ups + outcome recording — org-scoped."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import CurrentUser, get_current_user
from ..models import CustomerQuotation, FollowUp, Situation
from ..services import followup as f
from ..services.audit import log_action
from .intake import _session

router = APIRouter()


class FollowUpIn(BaseModel):
    situation_id: str
    quote_id: str | None = None
    due_at: datetime | None = None


class FollowUpOut(BaseModel):
    id: str
    bucket: str
    status: str


class OutcomeIn(BaseModel):
    outcome: str  # Accepted|Rejected|Expired (+ Negotiation/Follow Up Due transitions)


@router.post("/follow-ups", response_model=FollowUpOut)
async def create_followup(
    payload: FollowUpIn, user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)
):
    sit = (
        (await s.execute(select(Situation).where(
            Situation.id == payload.situation_id, Situation.org_id == user.org_id)))
        .scalars()
        .first()
    )
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found in org")
    row = FollowUp(org_id=user.org_id, situation_id=sit.id, quote_id=payload.quote_id,
                   due_at=payload.due_at, status="Due")
    s.add(row)
    await s.commit()
    return FollowUpOut(id=row.id, bucket=f.bucket(row.due_at), status=row.status)


@router.get("/follow-ups")
async def list_followups(user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    rows = (
        (await s.execute(select(FollowUp).where(FollowUp.org_id == user.org_id).limit(200))).scalars().all()
    )
    return [{"id": r.id, "situation_id": r.situation_id, "bucket": f.bucket(r.due_at), "status": r.status,
             "due_at": r.due_at.isoformat() if r.due_at else None} for r in rows]


@router.post("/situations/{sid}/outcome")
async def record_outcome(
    sid: str, payload: OutcomeIn, user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)
):
    sit = (
        (await s.execute(select(Situation).where(Situation.id == sid, Situation.org_id == user.org_id)))
        .scalars()
        .first()
    )
    if not sit:
        raise HTTPException(status_code=404, detail="Not found")
    if not f.outcome_allowed(sit.status, payload.outcome):
        raise HTTPException(status_code=409, detail=f"Outcome {payload.outcome} not allowed from {sit.status}")
    sit.outcome = payload.outcome
    if payload.outcome in ("Accepted", "Rejected", "Expired"):
        sit.status = payload.outcome
        # keep linked customer quotes consistent
        quotes = (
            (await s.execute(select(CustomerQuotation).where(
                CustomerQuotation.situation_id == sit.id, CustomerQuotation.org_id == user.org_id)))
            .scalars()
            .all()
        )
        for q in quotes:
            if q.status in ("Sent", "Approved"):
                q.status = payload.outcome
    else:
        sit.status = payload.outcome
    await log_action(
        s, org_id=user.org_id, actor=user.user_id, action="situation.outcome",
        detail={"situation_id": sit.id, "outcome": payload.outcome},
    )
    await s.commit()
    return {"id": sit.id, "status": sit.status, "outcome": sit.outcome}
