"""Mailbox polling: new mail -> RFQ auto-quotations or new situations.

Replies carrying [RFQ:xxxxxxxx] in the subject attach to that RFQ as an agent
quotation (sender matched by email, else auto-created agent) and flip the
recipient to Responded. Everything else becomes a new Customer Situation.
"""
import asyncio

from sqlalchemy import select

from ..models import Agent, AgentQuotation, Conversation, Customer, Message, RFQ, RFQRecipient, Situation
from . import quotation as qmod
from . import understanding as u
from .mail import decrypt_secret, fetch_since, rfq_token


async def poll_mailbox(s, box) -> dict:
    password = decrypt_secret(box.secret)
    msgs, top = await asyncio.to_thread(fetch_since, box.host, box.username, password, box.last_uid or 0)
    counts = {"fetched": len(msgs), "auto_quotations": 0, "situations": 0}
    for m in msgs:
        token = rfq_token(m["subject"])
        if token:
            rfqs = ((await s.execute(select(RFQ).where(RFQ.org_id == box.org_id))).scalars().all())
            rfq = next((r for r in rfqs if r.id.lower().startswith(token)), None)
            if rfq is None:
                continue
            sender = (m["from"] or "").lower()
            agents = ((await s.execute(select(Agent).where(Agent.org_id == box.org_id))).scalars().all())
            agent = next((a for a in agents if (a.email or "").lower() and (a.email or "").lower() in sender), None)
            if agent is None:
                agent = Agent(org_id=box.org_id, company=(m["from"] or "email-agent")[:200],
                              email=(m["from"] or "")[:320], notes="auto-created from email reply")
                s.add(agent)
                await s.flush()
            parsed = qmod.parse_quote_text(m["body_text"])
            s.add(AgentQuotation(
                org_id=box.org_id, rfq_id=rfq.id, agent=agent.company, agent_id=agent.id, currency=parsed["currency"],
                freight=parsed["charges"]["freight"] or 0.0, origin_charges=parsed["charges"]["origin"],
                destination_charges=parsed["charges"]["destination"],
                other_charges=parsed["charges"]["other"] or 0.0,
                validity_days=parsed["validity_days"], transit_days=parsed["transit_days"],
                raw_text=m["body_text"][:4000]))
            recs = ((await s.execute(select(RFQRecipient).where(
                RFQRecipient.rfq_id == rfq.id, RFQRecipient.agent_id == agent.id))).scalars().all())
            for rec in recs:
                rec.status = "Responded"
            counts["auto_quotations"] += 1
            continue
        customer = Customer(org_id=box.org_id, name=(m["from"] or "email sender")[:200])
        s.add(customer)
        await s.flush()
        ext = u.extract_shipment(m["body_text"])
        missing = u.detect_missing(ext)
        sit = Situation(org_id=box.org_id, customer_id=customer.id, status="New",
                        shipment={"raw": m["body_text"][:2000]}, missing=missing,
                        next_action=u.recommend_next_action(missing))
        s.add(sit)
        await s.flush()
        conv = Conversation(org_id=box.org_id, situation_id=sit.id)
        s.add(conv)
        await s.flush()
        s.add(Message(org_id=box.org_id, conversation_id=conv.id, channel="email",
                      external_id=f"uid:{m['uid']}", body=m["body_text"]))
        counts["situations"] += 1
    box.last_uid = top
    await s.commit()
    return counts
