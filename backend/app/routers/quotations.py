"""Quotation ingest + comparison endpoints — org-scoped."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import CurrentUser, get_current_user
from ..models import Agent, AgentQuotation, RFQ
from ..services import quotation as q
from ..services.parse_files import extract_text
from .intake import _session

router = APIRouter()


class IngestIn(BaseModel):
    agent: str
    agent_id: str | None = None  # explicit link; else matched by name/email
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


@router.post("/rfqs/{rfq_id}/quotations/upload", response_model=IngestOut)
async def ingest_upload(
    rfq_id: str, agent: str = Form(...), file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session),
):
    data = await file.read()
    try:
        text = extract_text(file.filename or "", file.content_type or "", data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not text.strip():
        raise HTTPException(status_code=422, detail="no readable text in file")
    return await ingest(rfq_id, IngestIn(agent=agent, body_text=text[:8000]), user, s)


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
    agent_id = payload.agent_id
    if agent_id is None:
        want = (payload.agent or "").strip().lower()
        if want:
            hit = ((await s.execute(select(Agent).where(Agent.org_id == user.org_id))).scalars().all())
            match = next((a for a in hit
                          if a.company.strip().lower() == want or (a.email or "").strip().lower() == want), None)
            agent_id = match.id if match else None
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
        agent_id=agent_id,
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
    result = q.compare_quotes(quotes)
    # Outlier flags vs lane history (needs the situation's lane, not this RFQ's own quotes).
    from ..models import Situation as _Sit
    from ..services.rates import guideline as _guideline, org_history as _org_history

    sit = ((await s.execute(select(_Sit).where(_Sit.id == rfq.situation_id))).scalars().first())
    if sit is not None:
        hist = [h for h in await _org_history(s, user.org_id) if h.get("rfq_id") != rfq.id]
        g = _guideline(sit.shipment or {}, hist)
        if g.get("available"):
            result["rows"] = q.flag_outliers(result["rows"], g.get("typical"))
            result["lane_typical"] = g.get("typical")
    return result
