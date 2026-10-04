"""Lightweight exceptions — org-scoped (PRD Sec 22, not full incident management)."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import CurrentUser, get_current_user
from ..models import ServiceException, Situation
from ..services.audit import log_action
from .intake import _session

router = APIRouter()

CATEGORIES = ("complaint", "delay", "missing_info", "charge", "mismatch", "approval", "conflict", "requirement_change")


class ExceptionIn(BaseModel):
    situation_id: str
    category: str
    detail: str = ""
    owner: str = ""
    next_action: str = ""
    due_at: datetime | None = None


class ExceptionOut(BaseModel):
    id: str
    status: str


@router.post("/exceptions", response_model=ExceptionOut)
async def create_exception(
    payload: ExceptionIn, user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)
):
    if payload.category not in CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Unknown category. Use one of {CATEGORIES}")
    sit = (
        (await s.execute(select(Situation).where(
            Situation.id == payload.situation_id, Situation.org_id == user.org_id)))
        .scalars()
        .first()
    )
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found in org")
    row = ServiceException(
        org_id=user.org_id, situation_id=sit.id, category=payload.category, detail=payload.detail,
        owner=payload.owner, next_action=payload.next_action, due_at=payload.due_at, status="Open",
    )
    s.add(row)
    await log_action(
        s, org_id=user.org_id, actor=user.user_id, action="exception.created",
        detail={"exception_id": row.id, "category": row.category, "situation_id": sit.id},
    )
    await s.commit()
    return ExceptionOut(id=row.id, status=row.status)


@router.get("/exceptions")
async def list_exceptions(user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    rows = (
        (await s.execute(select(ServiceException).where(ServiceException.org_id == user.org_id).limit(200)))
        .scalars()
        .all()
    )
    return [{"id": r.id, "situation_id": r.situation_id, "category": r.category, "owner": r.owner,
             "next_action": r.next_action, "status": r.status} for r in rows]


@router.post("/exceptions/{eid}/resolve")
async def resolve_exception(
    eid: str, user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)
):
    row = (
        (await s.execute(select(ServiceException).where(
            ServiceException.id == eid, ServiceException.org_id == user.org_id)))
        .scalars()
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    row.status = "Resolved"
    await log_action(
        s, org_id=user.org_id, actor=user.user_id, action="exception.resolved",
        detail={"exception_id": row.id},
    )
    await s.commit()
    return {"id": row.id, "status": row.status}
