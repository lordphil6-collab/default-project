"""Inbox — conversations + messages, org-scoped, newest first."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import CurrentUser, get_current_user
from ..models import Conversation, Message, Situation
from .intake import _session

router = APIRouter()


class MessageIn(BaseModel):
    body: str
    channel: str = "web"


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


@router.post("/conversations/{cid}/messages")
async def post_message(cid: str, payload: MessageIn, user: CurrentUser = Depends(get_current_user),
                       s: AsyncSession = Depends(_session)):
    conv = ((await s.execute(select(Conversation).where(
        Conversation.id == cid, Conversation.org_id == user.org_id))).scalars().first())
    if not conv:
        raise HTTPException(status_code=404, detail="Not found")
    body = (payload.body or "").strip()
    if not body:
        raise HTTPException(status_code=422, detail="Message body required")
    m = Message(org_id=user.org_id, conversation_id=cid, channel=payload.channel or "web",
                body=body[:4000])
    s.add(m)
    await s.commit()
    return {"id": m.id, "conversation_id": cid, "channel": m.channel, "body": m.body}


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


@router.post("/conversations/{cid}/brief")
async def conversation_brief(cid: str, user: CurrentUser = Depends(get_current_user),
                             s: AsyncSession = Depends(_session)):
    """Synthesize a thread into an RFQ-ready brief for agents.

    Collects every message, extracts the shipment, flags what's missing, and
    suggests the next action — so a CSR can hand database agents a clean,
    organized brief instead of raw inbox text.
    """
    from ..services import understanding as u

    conv = ((await s.execute(select(Conversation).where(
        Conversation.id == cid, Conversation.org_id == user.org_id))).scalars().first())
    if not conv:
        raise HTTPException(status_code=404, detail="Not found")
    msgs = ((await s.execute(select(Message).where(Message.conversation_id == cid).limit(200)))
            .scalars().all())
    if not msgs:
        raise HTTPException(status_code=422, detail="No messages to synthesize")
    combined = "\n\n".join(f"[{m.channel}] {m.body}" for m in msgs)[:6000]
    ext = u.extract_shipment(combined)
    missing = u.detect_missing(ext)
    channels = sorted({m.channel for m in msgs})
    return {
        "conversation_id": cid,
        "situation_id": conv.situation_id,
        "messages": len(msgs),
        "channels": channels,
        "combined": combined,
        "extraction": ext,
        "missing": missing,
        "summary": u.summarize(ext, missing),
        "next_action": u.recommend_next_action(missing),
        "default_channel": channels[0] if channels else "web",
    }
