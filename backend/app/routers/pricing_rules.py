"""Markup rules CRUD — company pricing policy (AI never sets policy)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import CurrentUser, get_current_user, require_roles
from ..models import MarkupRule
from .intake import _session

router = APIRouter()


class RuleIn(BaseModel):
    name: str = "Standard"
    kind: str = "percent"  # percent|fixed|minimum|combined
    value: float = 12.0
    min_margin: float = 0.0


class RuleOut(BaseModel):
    id: str
    name: str
    kind: str
    value: float
    min_margin: float


def _out(r: MarkupRule) -> RuleOut:
    return RuleOut(id=r.id, name=r.name, kind=r.kind, value=r.value, min_margin=r.min_margin)


@router.get("/markup-rules", response_model=list[RuleOut])
async def list_rules(user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    rows = ((await s.execute(select(MarkupRule).where(MarkupRule.org_id == user.org_id).limit(100)))
            .scalars().all())
    return [_out(r) for r in rows]


@router.post("/markup-rules", response_model=RuleOut)
async def create_rule(payload: RuleIn, user: CurrentUser = Depends(get_current_user),
                      _: CurrentUser = Depends(require_roles("Manager", "Owner")),
                      s: AsyncSession = Depends(_session)):
    if payload.kind not in ("percent", "fixed", "minimum", "combined"):
        raise HTTPException(status_code=422, detail="kind must be percent|fixed|minimum|combined")
    if payload.value < 0 or payload.min_margin < 0:
        raise HTTPException(status_code=422, detail="value and min_margin must be >= 0")
    row = MarkupRule(org_id=user.org_id, name=payload.name, kind=payload.kind,
                     value=payload.value, min_margin=payload.min_margin)
    s.add(row)
    await s.commit()
    return _out(row)


@router.post("/markup-rules/{rid}/deactivate")
async def deactivate_rule(rid: str, user: CurrentUser = Depends(require_roles("Manager", "Owner")),
                          s: AsyncSession = Depends(_session)):
    row = ((await s.execute(select(MarkupRule).where(
        MarkupRule.id == rid, MarkupRule.org_id == user.org_id))).scalars().first())
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    row.kind = f"archived:{row.kind}"
    await s.commit()
    return {"id": row.id, "archived": True}


def _active_rules(rows: list[MarkupRule]) -> list[MarkupRule]:
    return [r for r in rows if not r.kind.startswith("archived:")]
