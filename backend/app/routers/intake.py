"""POST /intake — Email/WhatsApp normalized into Situation + Conversation + Message."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import CurrentUser, get_current_user
from ..db import make_async_session_factory
from ..models import Conversation, Customer, Message, Situation
from ..schemas import IntakeIn, SituationOut
from ..services import understanding as u
from ..services.audit import log_action
from ..services.billing import require_entitlement

router = APIRouter()


async def _session() -> AsyncSession:
    async with make_async_session_factory()() as s:
        yield s  # type: ignore[misc]


@router.post("/intake", response_model=SituationOut)
async def intake(payload: IntakeIn, user: CurrentUser = Depends(get_current_user), _: CurrentUser = Depends(require_entitlement), s: AsyncSession = Depends(_session)):
    customer = Customer(org_id=user.org_id, name=payload.customer_name)
    s.add(customer)
    await s.flush()
    # Synthesize on entry: extract defined fields so the pipeline table
    # populates immediately and Get Quote can consume the situation at once.
    ext = u.extract_shipment(payload.body)
    missing = u.detect_missing(ext)
    next_action = u.recommend_next_action(missing)
    situation = Situation(
        org_id=user.org_id,
        customer_id=customer.id,
        status="New" if missing else "RFQ In Progress",
        shipment={"raw": payload.body[:500], **{k: v for k, v in ext.items() if k != "confidence"}},
        missing=missing,
        next_action=next_action,
    )
    s.add(situation)
    await s.flush()
    conv = Conversation(org_id=user.org_id, situation_id=situation.id)
    s.add(conv)
    await s.flush()
    s.add(
        Message(
            org_id=user.org_id,
            conversation_id=conv.id,
            channel=payload.channel,
            external_id=payload.external_id,
            body=payload.body,
        )
    )
    await log_action(
        s, org_id=user.org_id, actor=user.user_id, action="intake.created",
        detail={"channel": payload.channel, "situation_id": situation.id, "missing": missing},
    )
    await s.commit()
    ship = situation.shipment or {}
    return SituationOut(id=situation.id, status=situation.status, missing=missing, next_action=situation.next_action,
                        origin=str(ship.get("origin") or ""), destination=str(ship.get("destination") or ""),
                        mode=str(ship.get("mode") or ""))
