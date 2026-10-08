"""Agent database + matching — org-scoped."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import CurrentUser, get_current_user
from ..models import Agent, Situation
from ..services import agents as matcher
from ..services.billing import require_entitlement
from .intake import _session

router = APIRouter()


class AgentIn(BaseModel):
    company: str
    routes: list[str] = []
    services: list[str] = []
    capabilities: list[str] = []
    contact: str = ""
    email: str = ""
    notes: str = ""


class AgentOut(BaseModel):
    id: str
    company: str
    routes: list[str] = []
    services: list[str] = []
    capabilities: list[str] = []
    email: str = ""
    status: str


def _to_dict(r: Agent) -> dict:
    return {"id": r.id, "company": r.company, "routes": r.routes, "services": r.services,
            "capabilities": r.capabilities, "status": r.status}


@router.post("/agents", response_model=AgentOut)
async def create_agent(payload: AgentIn, user: CurrentUser = Depends(get_current_user),
                       _: CurrentUser = Depends(require_entitlement), s: AsyncSession = Depends(_session)):
    row = Agent(org_id=user.org_id, company=payload.company, routes=payload.routes,
                services=[x.lower() for x in payload.services], capabilities=payload.capabilities,
                contact=payload.contact, email=payload.email, notes=payload.notes)
    s.add(row)
    await s.commit()
    return AgentOut(id=row.id, company=row.company, routes=row.routes, services=row.services,
                    capabilities=row.capabilities, email=row.email, status=row.status)


@router.get("/agents", response_model=list[AgentOut])
async def list_agents(user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    rows = ((await s.execute(select(Agent).where(Agent.org_id == user.org_id).limit(200))).scalars().all())
    return [AgentOut(id=r.id, company=r.company, routes=r.routes, services=r.services,
                     capabilities=r.capabilities, email=r.email or "", status=r.status) for r in rows]


@router.get("/agents/match")
async def match(situation_id: str, user: CurrentUser = Depends(get_current_user),
                s: AsyncSession = Depends(_session)):
    sit = ((await s.execute(select(Situation).where(
        Situation.id == situation_id, Situation.org_id == user.org_id))).scalars().first())
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found in org")
    agents = ((await s.execute(select(Agent).where(Agent.org_id == user.org_id).limit(200))).scalars().all())
    return matcher.match_agents(sit.shipment or {}, [_to_dict(a) for a in agents])


SAMPLE_LINES = [
    ("Maersk", ["China>Lagos", "Guangzhou>Lagos", "Shanghai>Apapa"], ["ocean"], ["20ft", "40ft"]),
    ("MSC", ["China>Lagos", "Shanghai>Tincan"], ["ocean"], ["20ft", "40ft"]),
    ("CMA CGM", ["China>Lagos", "Guangzhou>Apapa"], ["ocean"], ["20ft", "40ft"]),
    ("Hapag-Lloyd", ["China>Lagos", "Shanghai>Lagos"], ["ocean"], ["20ft"]),
    ("COSCO", ["Guangzhou>Lagos", "China>Onne"], ["ocean"], ["20ft", "40ft"]),
    ("Evergreen", ["China>Lagos"], ["ocean"], ["20ft", "40ft"]),
    ("Lufthansa Cargo", ["Lagos>London", "Guangzhou>Lagos"], ["air"], ["cartons", "pallets"]),
    ("Emirates SkyCargo", ["Guangzhou>Lagos", "Lagos>London"], ["air"], ["cartons"]),
]


@router.post("/agents/seed-samples")
async def seed_samples(user: CurrentUser = Depends(get_current_user),
                       _: CurrentUser = Depends(require_entitlement),
                       s: AsyncSession = Depends(_session)):
    """One-click sample shipping lines for the caller's own org (idempotent).

    Clearly labeled SAMPLE — replace with contracted lines. Nothing is shared
    across orgs; tenant isolation holds.
    """
    existing = set((await s.execute(select(Agent.company).where(Agent.org_id == user.org_id))).scalars().all())
    added = 0
    for company, routes, services, caps in SAMPLE_LINES:
        if company in existing:
            continue
        s.add(Agent(org_id=user.org_id, company=company, routes=list(routes),
                    services=list(services), capabilities=list(caps),
                    notes="SAMPLE DATA — replace with contracted line"))
        added += 1
    await s.commit()
    return {"added": added, "note": "SAMPLE DATA — replace with contracted lines"}
