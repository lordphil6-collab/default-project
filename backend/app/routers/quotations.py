"""Quotation ingest + comparison endpoints — org-scoped."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import CurrentUser, get_current_user
from ..models import AgentQuotation, RFQ
from ..services import quotation as q
from .intake import _session

router = APIRouter()


class IngestIn(BaseModel):
    agent: str
    body_text: str = ""
    # structured override wins over parsed text when provided
    freight: float | None = None
    origin_charges: float | None = None
    destination_charges: float | None = None  # None = Unknown
    other_charges: float | None = None  # None = fall back to parsed text
    currency: str = "USD"
    validity_days: int = 0
    transit_days: int = 0


class IngestOut(BaseModel):
    id: str
    total_identifiable: float | None
    missing: list[str]


@router.post("/rfqs/{rfq_id}/quotations", response_model=IngestOut)
async def ingest(
    rfq_id: str, payload: IngestIn, user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)
):
    rfq = (
        (await s.execute(select(RFQ).where(RFQ.id == rfq_id, RFQ.org_id == user.org_id))).scalars().first()
    )
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found in org")
    parsed = q.parse_quote_text(payload.body_text) if payload.body_text else None
    freight = payload.freight if payload.freight is not None else (parsed["charges"]["freight"] if parsed else 0.0)
    origin = (
        payload.origin_charges
        if payload.origin_charges is not None
        else (parsed["charges"]["origin"] if parsed else None)
    )
    dest = (
        payload.destination_charges
        if payload.destination_charges is not None
        else (parsed["charges"]["destination"] if parsed else None)
    )
    other = (
        payload.other_charges
        if payload.other_charges is not None
        else (parsed["charges"]["other"] if parsed else 0.0)
    )
    row = AgentQuotation(
        org_id=user.org_id,
        rfq_id=rfq.id,
        agent=payload.agent,
        currency=payload.currency if payload.currency != "USD" else (parsed["currency"] if parsed else "USD"),
        freight=freight or 0.0,
        origin_charges=origin,
        destination_charges=dest,
        other_charges=other if other is not None else 0.0,
        validity_days=payload.validity_days or (parsed["validity_days"] if parsed else 0),
        transit_days=payload.transit_days or (parsed["transit_days"] if parsed else 0),
        raw_text=payload.body_text[:4000],
    )
    s.add(row)
    await s.flush()
    charges = {"freight": row.freight, "origin": row.origin_charges, "destination": row.destination_charges,
               "other": row.other_charges}
    missing = [k for k in ("freight", "origin", "destination") if charges.get(k) is None]
    total = q.identifiable_total(charges)
    if rfq.status == "Draft":
        rfq.status = "Partial Responses"
    await s.commit()
    return IngestOut(id=row.id, total_identifiable=total, missing=missing)


@router.get("/rfqs/{rfq_id}/quotations")
async def list_quotations(rfq_id: str, user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    rfq = (
        (await s.execute(select(RFQ).where(RFQ.id == rfq_id, RFQ.org_id == user.org_id))).scalars().first()
    )
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found in org")
    rows = (
        (await s.execute(select(AgentQuotation).where(AgentQuotation.rfq_id == rfq.id))).scalars().all()
    )
    out = []
    for r in rows:
        charges = {"freight": r.freight, "origin": r.origin_charges,
                   "destination": r.destination_charges, "other": r.other_charges}
        out.append({"id": r.id, "agent": r.agent, "currency": r.currency, "charges": charges,
                    "missing": [k for k in ("freight", "origin", "destination") if charges.get(k) is None],
                    "validity_days": r.validity_days, "transit_days": r.transit_days})
    return out


@router.get("/rfqs/{rfq_id}/compare")
async def compare(rfq_id: str, user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    rfq = (
        (await s.execute(select(RFQ).where(RFQ.id == rfq_id, RFQ.org_id == user.org_id))).scalars().first()
    )
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found in org")
    rows = (
        (await s.execute(select(AgentQuotation).where(AgentQuotation.rfq_id == rfq.id))).scalars().all()
    )
    quotes = [
        {"agent": r.agent,
         "charges": {"freight": r.freight, "origin": r.origin_charges, "destination": r.destination_charges,
                     "other": r.other_charges},
         "validity_days": r.validity_days, "transit_days": r.transit_days}
        for r in rows
    ]
    return q.compare_quotes(quotes)
