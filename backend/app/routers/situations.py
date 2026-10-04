"""Situation reads, always org-scoped."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import CurrentUser, get_current_user
from ..models import Situation
from ..schemas import SituationOut
from .intake import _session

router = APIRouter()


@router.get("/situations", response_model=list[SituationOut])
async def list_situations(user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    rows = (await s.execute(select(Situation).where(Situation.org_id == user.org_id).limit(50))).scalars().all()
    return [SituationOut(id=r.id, status=r.status, missing=r.missing, next_action=r.next_action) for r in rows]


@router.get("/situations/{sid}", response_model=SituationOut)
async def get_situation(sid: str, user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    r = (
        (await s.execute(select(Situation).where(Situation.id == sid, Situation.org_id == user.org_id)))
        .scalars()
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return SituationOut(id=r.id, status=r.status, missing=r.missing, next_action=r.next_action)
