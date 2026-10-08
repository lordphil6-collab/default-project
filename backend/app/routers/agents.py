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
