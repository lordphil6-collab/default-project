"""RFQ creation from a situation — org-scoped."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import CurrentUser, get_current_user
from ..models import Agent, RFQ, RFQRecipient, Situation
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


class RecipientsIn(BaseModel):
    agent_ids: list[str]


@router.post("/rfqs/{rfq_id}/recipients")
async def set_recipients(rfq_id: str, payload: RecipientsIn, user: CurrentUser = Depends(get_current_user),
                         s: AsyncSession = Depends(_session)):
    rfq = ((await s.execute(select(RFQ).where(RFQ.id == rfq_id, RFQ.org_id == user.org_id))).scalars().first())
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found in org")
    if rfq.status != "Draft":
        raise HTTPException(status_code=409, detail=f"Recipients locked after {rfq.status}")
    agents = ((await s.execute(select(Agent).where(Agent.org_id == user.org_id))).scalars().all())
    known = {a.id for a in agents if a.status == "Active"}
    unknown = [i for i in payload.agent_ids if i not in known]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown or inactive agents: {unknown}")
    old = ((await s.execute(select(RFQRecipient).where(RFQRecipient.rfq_id == rfq.id))).scalars().all())
    for r in old:
        await s.delete(r)
    for aid in dict.fromkeys(payload.agent_ids):
        s.add(RFQRecipient(org_id=user.org_id, rfq_id=rfq.id, agent_id=aid, status="Selected"))
    await s.commit()
    return {"rfq_id": rfq.id, "recipients": list(dict.fromkeys(payload.agent_ids))}


@router.get("/rfqs/{rfq_id}/recipients")
async def list_recipients(rfq_id: str, user: CurrentUser = Depends(get_current_user),
                          s: AsyncSession = Depends(_session)):
    rows = ((await s.execute(select(RFQRecipient).where(
        RFQRecipient.rfq_id == rfq_id, RFQRecipient.org_id == user.org_id))).scalars().all())
    return [{"agent_id": r.agent_id, "status": r.status} for r in rows]


@router.post("/rfqs/{rfq_id}/send")
async def send_rfq(rfq_id: str, user: CurrentUser = Depends(get_current_user),
                   _: CurrentUser = Depends(require_entitlement), s: AsyncSession = Depends(_session)):
    rfq = ((await s.execute(select(RFQ).where(RFQ.id == rfq_id, RFQ.org_id == user.org_id))).scalars().first())
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found in org")
    if rfq.status != "Draft":
        raise HTTPException(status_code=409, detail=f"Already {rfq.status}")
    recips = ((await s.execute(select(RFQRecipient).where(RFQRecipient.rfq_id == rfq.id))).scalars().all())
    if not recips:
        raise HTTPException(status_code=422, detail="Select at least one recipient agent first")
    rfq.status = "Sent"
    for r in recips:
        r.status = "Sent"
    await s.commit()
    return {"rfq_id": rfq.id, "status": rfq.status, "sent_to": len(recips)}
