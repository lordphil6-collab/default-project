"""RFQ creation from a situation — org-scoped."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import CurrentUser, get_current_user
from ..models import RFQ, Situation
from ..services.billing import require_entitlement
from .intake import _session

router = APIRouter()


class RFQCreateIn(BaseModel):
    situation_id: str


class RFQOut(BaseModel):
    id: str
    status: str
    situation_id: str


@router.get("/rfqs", response_model=list[RFQOut])
async def list_rfqs(situation_id: str, user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    rows = (
        (await s.execute(select(RFQ).where(RFQ.org_id == user.org_id, RFQ.situation_id == situation_id).limit(50)))
        .scalars()
        .all()
    )
    return [RFQOut(id=r.id, status=r.status, situation_id=r.situation_id) for r in rows]


@router.post("/rfqs", response_model=RFQOut)
async def create_rfq(payload: RFQCreateIn, user: CurrentUser = Depends(get_current_user), _: CurrentUser = Depends(require_entitlement), s: AsyncSession = Depends(_session)):
    sit = (
        (await s.execute(select(Situation).where(Situation.id == payload.situation_id, Situation.org_id == user.org_id)))
        .scalars()
        .first()
    )
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found in org")
    rfq = RFQ(org_id=user.org_id, situation_id=sit.id, status="Draft", scope={})
    s.add(rfq)
    await s.flush()
    if sit.status in ("New", "Information Required") and not sit.missing:
        sit.status = "RFQ In Progress"
    await s.commit()
    return RFQOut(id=rfq.id, status=rfq.status, situation_id=sit.id)
