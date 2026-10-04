"""Understanding endpoints — stateless extract + persist-to-situation."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import CurrentUser, get_current_user
from ..models import Situation
from ..services import understanding as u
from .intake import _session

router = APIRouter()


class UnderstandIn(BaseModel):
    body: str


class UnderstandOut(BaseModel):
    extraction: dict
    missing: list[str]
    summary: str
    next_action: str


@router.post("/understand", response_model=UnderstandOut)
async def understand(payload: UnderstandIn, _user: CurrentUser = Depends(get_current_user)):
    ext = u.extract_shipment(payload.body)
    missing = u.detect_missing(ext)
    return UnderstandOut(
        extraction=ext, missing=missing, summary=u.summarize(ext, missing), next_action=u.recommend_next_action(missing)
    )


@router.post("/situations/{sid}/extract", response_model=UnderstandOut)
async def extract_into_situation(
    sid: str, payload: UnderstandIn, user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)
):
    sit = (
        (await s.execute(select(Situation).where(Situation.id == sid, Situation.org_id == user.org_id)))
        .scalars()
        .first()
    )
    if not sit:
        raise HTTPException(status_code=404, detail="Not found")
    ext = u.extract_shipment(payload.body)
    missing = u.detect_missing(ext)
    sit.shipment = {"raw": payload.body[:2000], **{k: v for k, v in ext.items() if k != "confidence"}}
    sit.missing = missing
    sit.next_action = u.recommend_next_action(missing)
    if not missing and sit.status == "New":
        sit.status = "RFQ In Progress"
    elif missing and sit.status == "New":
        sit.status = "Information Required"
    await s.commit()
    return UnderstandOut(
        extraction=ext, missing=missing, summary=u.summarize(ext, missing), next_action=sit.next_action
    )
