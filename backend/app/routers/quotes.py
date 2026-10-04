"""Customer quotes + L4 approval gate — org-scoped, role-enforced."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import CurrentUser, get_current_user, require_roles
from ..models import AgentQuotation, CustomerQuotation, MarkupRule
from ..services import pricing as p
from ..services.audit import log_action
from ..services.billing import require_entitlement
from .intake import _session

router = APIRouter()


class QuoteCreateIn(BaseModel):
    situation_id: str
    agent_quotation_id: str
    markup_rule_id: str | None = None
    markup_kind: str = "percent"  # ad-hoc when no rule id
    markup_value: float = 12.0
    min_margin: float = 0.0
    terms: str = ""
    validity_days: int = 7


class QuoteOut(BaseModel):
    id: str
    status: str
    agent_total: float
    markup_amount: float
    final_price: float


def _total_of(q: AgentQuotation) -> float | None:
    parts = [q.freight, q.origin_charges, q.destination_charges, q.other_charges]
    if q.freight is None or q.destination_charges is None:
        return None  # Unknown blocks customer pricing — must resolve first
    return round(sum(parts), 2)


@router.post("/customer-quotes", response_model=QuoteOut)
async def create_quote(
    payload: QuoteCreateIn, user: CurrentUser = Depends(get_current_user), _: CurrentUser = Depends(require_entitlement), s: AsyncSession = Depends(_session)
):
    aq = (
        (await s.execute(select(AgentQuotation).where(
            AgentQuotation.id == payload.agent_quotation_id, AgentQuotation.org_id == user.org_id)))
        .scalars()
        .first()
    )
    if not aq:
        raise HTTPException(status_code=404, detail="Agent quotation not found in org")
    total = _total_of(aq)
    if total is None:
        raise HTTPException(status_code=422, detail="Agent quote has Unknown charges — resolve before pricing")
    kind, value, floor, rule_id = payload.markup_kind, payload.markup_value, payload.min_margin, None
    if payload.markup_rule_id:
        rule = (
            (await s.execute(select(MarkupRule).where(
                MarkupRule.id == payload.markup_rule_id, MarkupRule.org_id == user.org_id)))
            .scalars()
            .first()
        )
        if not rule:
            raise HTTPException(status_code=404, detail="Markup rule not found in org")
        kind, value, floor, rule_id = rule.kind, rule.value, rule.min_margin, rule.id
    calc = p.apply_markup(total, kind, value, floor)
    quote = CustomerQuotation(
        org_id=user.org_id,
        situation_id=payload.situation_id,
        agent_quotation_id=aq.id,
        markup_rule_id=rule_id,
        agent_total=calc["agent_total"],
        markup_amount=calc["markup_amount"],
        status="Approval Required",
        final_price=calc["final_price"],
        currency=aq.currency,
        terms=payload.terms,
        validity_days=payload.validity_days,
    )
    s.add(quote)
    await s.commit()
    return QuoteOut(id=quote.id, status=quote.status, agent_total=quote.agent_total,
                    markup_amount=quote.markup_amount, final_price=quote.final_price)


@router.post("/customer-quotes/{qid}/approve", response_model=QuoteOut)
async def approve_quote(
    qid: str,
    approver: CurrentUser = Depends(require_roles("Manager", "Owner")),
    s: AsyncSession = Depends(_session),
):
    q = (
        (await s.execute(select(CustomerQuotation).where(
            CustomerQuotation.id == qid, CustomerQuotation.org_id == approver.org_id)))
        .scalars()
        .first()
    )
    if not q:
        raise HTTPException(status_code=404, detail="Not found")
    if q.status != "Approval Required":
        raise HTTPException(status_code=409, detail=f"Cannot approve from status {q.status}")
    q.status = "Approved"
    await log_action(
        s, org_id=approver.org_id, actor=approver.user_id, action="quote.approved",
        detail={"quote_id": q.id, "final_price": q.final_price},
    )
    await s.commit()
    return QuoteOut(id=q.id, status=q.status, agent_total=q.agent_total,
                    markup_amount=q.markup_amount, final_price=q.final_price)


@router.post("/customer-quotes/{qid}/send", response_model=QuoteOut)
async def send_quote(
    qid: str, user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)
):
    q = (
        (await s.execute(select(CustomerQuotation).where(
            CustomerQuotation.id == qid, CustomerQuotation.org_id == user.org_id)))
        .scalars()
        .first()
    )
    if not q:
        raise HTTPException(status_code=404, detail="Not found")
    if q.status != "Approved":
        # L4 gate: binding send blocked without approval
        raise HTTPException(status_code=409, detail="Send blocked: quote needs approval first")
    q.status = "Sent"
    await log_action(
        s, org_id=user.org_id, actor=user.user_id, action="quote.sent",
        detail={"quote_id": q.id, "final_price": q.final_price},
    )
    await s.commit()
    return QuoteOut(id=q.id, status=q.status, agent_total=q.agent_total,
                    markup_amount=q.markup_amount, final_price=q.final_price)
