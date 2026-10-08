"""Public portal — no-auth website enquiry form + tracking links.

Enquiries land in the pilot forwarder's org (DEFAULT_PORTAL_ORG_ID) as channel
"web". Tracking tokens are unguessable; the track view exposes only the
customer's own shipment summary, status, and their quoted price — never other
customers, contacts, or agent internals.
"""
import os
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import CurrentUser, get_current_user
from datetime import datetime, timedelta, timezone

from ..models import Conversation, Customer, CustomerQuotation, Message, Organization, Situation
from ..services import understanding as u
from .intake import _session

router = APIRouter()


class PublicEnquiryIn(BaseModel):
    customer_name: str
    contact: str = ""
    body: str


@router.post("/public/enquiries")
async def public_enquiry(payload: PublicEnquiryIn, s: AsyncSession = Depends(_session)):
    org_id = os.getenv("DEFAULT_PORTAL_ORG_ID", "")
    if not org_id:
        raise HTTPException(
            status_code=503,
            detail="Public portal not configured — set DEFAULT_PORTAL_ORG_ID to the forwarder org",
        )
    name = payload.customer_name.strip()
    body = payload.body.strip()
    if not name or len(body) < 10:
        raise HTTPException(status_code=422, detail="Give your company name and a few words about the shipment")
    if len(body) > 4000:
        raise HTTPException(status_code=422, detail="Enquiry too long (4000 chars max)")
    org = ((await s.execute(select(Organization).where(Organization.id == org_id))).scalars().first())
    if org is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        org = Organization(id=org_id, name="Portal forwarder", trial_start=now,
                           trial_ends=now + timedelta(days=30))
        s.add(org)
        await s.flush()
    customer = Customer(org_id=org.id, name=name[:200], contact=payload.contact[:320])
    s.add(customer)
    await s.flush()
    ext = u.extract_shipment(body)
    missing = u.detect_missing(ext)
    situation = Situation(
        org_id=org_id, customer_id=customer.id, status="New",
        shipment={"raw": body[:2000], **{k: v for k, v in ext.items() if k != "confidence"}},
        missing=missing, next_action=u.recommend_next_action(missing),
    )
    s.add(situation)
    await s.flush()
    conv = Conversation(org_id=org_id, situation_id=situation.id)
    s.add(conv)
    await s.flush()
    s.add(Message(org_id=org_id, conversation_id=conv.id, channel="web",
                  external_id="", body=f"From {name} ({payload.contact[:320]}): {body}"))
    await s.commit()
    return {"reference": situation.id[:8], "summary": u.summarize(ext, missing), "missing": missing}


@router.post("/situations/{sid}/share")
async def share_situation(sid: str, user: CurrentUser = Depends(get_current_user),
                          s: AsyncSession = Depends(_session)):
    sit = ((await s.execute(select(Situation).where(
        Situation.id == sid, Situation.org_id == user.org_id))).scalars().first())
    if not sit:
        raise HTTPException(status_code=404, detail="Not found")
    if not sit.public_token:
        sit.public_token = secrets.token_urlsafe(16)
        await s.commit()
    return {"token": sit.public_token, "track_path": f"/track?token={sit.public_token}"}


@router.get("/public/track/{token}")
async def track(token: str, s: AsyncSession = Depends(_session)):
    sit = ((await s.execute(select(Situation).where(Situation.public_token == token)))
           .scalars().first())
    if not sit:
        raise HTTPException(status_code=404, detail="Unknown tracking reference")
    ship = sit.shipment or {}
    quotes = ((await s.execute(select(CustomerQuotation).where(
        CustomerQuotation.situation_id == sit.id,
        CustomerQuotation.status == "Sent").limit(1))).scalars().all())
    price = ({"total": quotes[0].final_price, "currency": quotes[0].currency,
              "validity_days": quotes[0].validity_days} if quotes else None)
    route = "Route being confirmed"
    if ship.get("origin") and ship.get("destination"):
        route = f"{ship['origin']} → {ship['destination']}"
    return {"reference": sit.id[:8], "route": route, "status": sit.status,
            "outcome": sit.outcome or None, "price": price,
            "missing": [m for m in (sit.missing or []) if m in ("weight", "dimensions", "pickup")]}
