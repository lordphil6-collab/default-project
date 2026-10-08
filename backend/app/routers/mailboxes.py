"""Mailbox connections — Manager+ only. Passwords stored Fernet-encrypted."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import CurrentUser, get_current_user, require_roles
from ..models import Mailbox
from ..services.billing import require_entitlement
from ..services.mail import encrypt_secret
from ..services.mail_poll import poll_mailbox
from .intake import _session

router = APIRouter()
manager = require_roles("Manager", "Owner")


class MailboxIn(BaseModel):
    provider: str = "imap"
    host: str
    username: str
    password: str


@router.post("/mailboxes")
async def connect(payload: MailboxIn, user: CurrentUser = Depends(manager),
                  _: CurrentUser = Depends(require_entitlement),
                  s: AsyncSession = Depends(_session)):
    try:
        secret = encrypt_secret(payload.password)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    row = Mailbox(org_id=user.org_id, provider=payload.provider, host=payload.host,
                  username=payload.username, secret=secret)
    s.add(row)
    await s.commit()
    return {"id": row.id, "host": row.host, "username": row.username, "status": row.status}


@router.get("/mailboxes")
async def list_boxes(user: CurrentUser = Depends(get_current_user),
                     s: AsyncSession = Depends(_session)):
    rows = ((await s.execute(select(Mailbox).where(Mailbox.org_id == user.org_id))).scalars().all())
    return [{"id": r.id, "provider": r.provider, "host": r.host, "username": r.username,
             "last_uid": r.last_uid, "status": r.status} for r in rows]


@router.post("/mailboxes/{mid}/poll")
async def poll_now(mid: str, user: CurrentUser = Depends(manager),
                   s: AsyncSession = Depends(_session)):
    box = ((await s.execute(select(Mailbox).where(
        Mailbox.id == mid, Mailbox.org_id == user.org_id))).scalars().first())
    if not box:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        result = await poll_mailbox(s, box)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"mail poll failed: {exc}"[:300])
    return result
