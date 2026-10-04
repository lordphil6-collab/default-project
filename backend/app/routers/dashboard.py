"""Today dashboard — actionable counts, org-scoped (PRD Sec 23)."""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import CurrentUser, get_current_user
from ..models import CustomerQuotation, FollowUp, RFQ, ServiceException
from ..services import followup as f
from .intake import _session

router = APIRouter()


@router.get("/dashboard/today")
async def today(user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    now = datetime.utcnow()
    fus = (
        (await s.execute(select(FollowUp).where(FollowUp.org_id == user.org_id).limit(500))).scalars().all()
    )
    overdue = sum(1 for r in fus if f.bucket(r.due_at, now) == "overdue")
    due_today = sum(1 for r in fus if f.bucket(r.due_at, now) == "due_today")
    pending_rfqs = (
        (await s.execute(select(func.count(RFQ.id)).where(
            RFQ.org_id == user.org_id, RFQ.status.in_(("Draft", "Sent", "Awaiting Response", "Partial Responses")))))
        .scalar()
        or 0
    )
    awaiting = (
        (await s.execute(select(func.count(CustomerQuotation.id)).where(
            CustomerQuotation.org_id == user.org_id, CustomerQuotation.status == "Approval Required")))
        .scalar()
        or 0
    )
    open_exc = (
        (await s.execute(select(func.count(ServiceException.id)).where(
            ServiceException.org_id == user.org_id, ServiceException.status == "Open")))
        .scalar()
        or 0
    )
    return f.today_counts(overdue, due_today, pending_rfqs, awaiting, open_exc)
