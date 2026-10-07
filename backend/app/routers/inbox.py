"""Inbox — conversations + messages, org-scoped, newest first."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import CurrentUser, get_current_user
from ..models import Conversation, Message, Situation
from .intake import _session

router = APIRouter()


@router.get("/conversations")
async def list_conversations(situation_id: str | None = None,
                             user: CurrentUser = Depends(get_current_user),
                             s: AsyncSession = Depends(_session)):
    q = select(Conversation).where(Conversation.org_id == user.org_id)
    if situation_id:
        q = q.where(Conversation.situation_id == situation_id)
    rows = ((await s.execute(q.order_by(desc(Conversation.id)).limit(100))).scalars().all())
    return [{"id": r.id, "situation_id": r.situation_id} for r in rows]


@router.get("/conversations/{cid}/messages")
async def list_messages(cid: str, user: CurrentUser = Depends(get_current_user),
                        s: AsyncSession = Depends(_session)):
    conv = ((await s.execute(select(Conversation).where(
        Conversation.id == cid, Conversation.org_id == user.org_id))).scalars().first())
    if not conv:
        raise HTTPException(status_code=404, detail="Not found")
    rows = ((await s.execute(select(Message).where(Message.conversation_id == cid).limit(200)))
            .scalars().all())
    return [{"id": m.id, "channel": m.channel, "body": m.body,
             "attachments": m.attachments} for m in rows]


@router.get("/inbox")
async def inbox(user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    """Latest message per conversation with its situation status — the CSR inbox."""
    convs = ((await s.execute(select(Conversation).where(Conversation.org_id == user.org_id).limit(100)))
             .scalars().all())
    out = []
    for c in convs:
        msgs = ((await s.execute(select(Message).where(Message.conversation_id == c.id)
                                 .order_by(desc(Message.id)).limit(1))).scalars().all())
        sit = ((await s.execute(select(Situation).where(Situation.id == c.situation_id))).scalars().first())
        if msgs:
            out.append({"conversation_id": c.id, "situation_id": c.situation_id,
                        "status": sit.status if sit else "?", "channel": msgs[0].channel,
                        "preview": msgs[0].body[:160]})
    return out
