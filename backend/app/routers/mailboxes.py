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

# Provider presets: Gmail + Outlook on 993/SSL; anything else is plain webmail
# IMAP (host + port supplied by the operator, SSL by default).
PRESETS = {
    "gmail": {"host": "imap.gmail.com", "port": 993, "use_ssl": True},
    "outlook": {"host": "outlook.office365.com", "port": 993, "use_ssl": True},
    "webmail": {"host": "", "port": 993, "use_ssl": True},
    "imap": {"host": "", "port": 993, "use_ssl": True},
}


class MailboxIn(BaseModel):
    provider: str = "imap"  # gmail|outlook|webmail|imap
    host: str = ""
    port: int | None = None
    use_ssl: bool | None = None
    username: str
    password: str


@router.post("/mailboxes")
async def connect(payload: MailboxIn, user: CurrentUser = Depends(manager),
                  _: CurrentUser = Depends(require_entitlement),
                  s: AsyncSession = Depends(_session)):
    provider = (payload.provider or "imap").lower()
    if provider not in PRESETS:
        raise HTTPException(status_code=422, detail="provider must be gmail|outlook|webmail|imap")
    preset = PRESETS[provider]
    host = payload.host.strip() or preset["host"]
    if not host:
        raise HTTPException(status_code=422, detail="IMAP host required for webmail providers")
    port = payload.port or preset["port"]
    use_ssl = preset["use_ssl"] if payload.use_ssl is None else payload.use_ssl
    try:
        secret = encrypt_secret(payload.password)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    row = Mailbox(org_id=user.org_id, provider=provider, host=host, port=port, use_ssl=use_ssl,
                  username=payload.username, secret=secret)
    s.add(row)
    await s.commit()
    return {"id": row.id, "provider": row.provider, "host": row.host, "port": row.port,
            "username": row.username, "status": row.status}


@router.get("/mailboxes")
async def list_boxes(user: CurrentUser = Depends(get_current_user),
                     s: AsyncSession = Depends(_session)):
    rows = ((await s.execute(select(Mailbox).where(Mailbox.org_id == user.org_id))).scalars().all())
    return [{"id": r.id, "provider": r.provider, "host": r.host, "port": getattr(r, "port", 993),
             "username": r.username, "last_uid": r.last_uid, "status": r.status} for r in rows]


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
