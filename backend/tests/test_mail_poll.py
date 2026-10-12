"""Reply threading test — token match creates quotation, flips recipient (no network)."""
from types import SimpleNamespace

import pytest

from backend.app.services import mail_poll as mp


@pytest.mark.asyncio
async def test_reply_token_creates_quotation_and_responded(monkeypatch):
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from backend.app.db import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as s:
        from backend.app.models import Agent, Customer, RFQ, RFQRecipient, Situation
        s.add(Customer(id="c1", org_id="o1", name="C"))
        s.add(Situation(id="situation-1d7cbf4c-xxxx", org_id="o1", customer_id="c1"))
        s.add(RFQ(id="1d7cbf4c-aaaa-bbbb-cccc-dddddddddddd", org_id="o1", situation_id="situation-1d7cbf4c-xxxx"))
        s.add(Agent(id="a1", org_id="o1", company="Agent A", email="rates@agenta.test"))
        s.add(RFQRecipient(org_id="o1", rfq_id="1d7cbf4c-aaaa-bbbb-cccc-dddddddddddd",
                           agent_id="a1", status="Sent"))
        await s.commit()

    def fake_fetch(host, username, password, last_uid):
        assert password == "pw"
        return ([{"uid": 7, "from": "Agent A <rates@agenta.test>",
                  "subject": "Re: [RFQ:1d7cbf4c] rates",
                  "body_text": "Ocean Freight $1,850\nDestination Charges $650"}], 7)

    monkeypatch.setattr(mp, "fetch_since", fake_fetch)
    # stub decrypt: bypass key handling
    monkeypatch.setattr(mp, "decrypt_secret", lambda token: "pw")
    box = SimpleNamespace(org_id="o1", secret="enc", host="h", username="u", last_uid=0)

    async with factory() as s:
        counts = await mp.poll_mailbox(s, box)
    assert counts == {"fetched": 1, "auto_quotations": 1, "situations": 0}
    assert box.last_uid == 7

    async with factory() as s:
        from sqlalchemy import select
        from backend.app.models import AgentQuotation
        from backend.app.models import RFQRecipient as Rec

        quotes = (await s.execute(select(AgentQuotation))).scalars().all()
        assert len(quotes) == 1 and quotes[0].freight == 1850.0
        rec = (await s.execute(select(Rec))).scalars().first()
        assert rec.status == "Responded"
    await engine.dispose()


@pytest.mark.asyncio
async def test_repeat_poll_creates_no_duplicates(monkeypatch):
    """Second poll over the same mailbox must not duplicate quotations.

    The fake honors last_uid exactly like the real IMAP UID query
    (UID {last_uid+1}:*), so already-seen UIDs are never re-fetched.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from backend.app.db import Base
    from backend.app.models import AgentQuotation

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as s:
        from backend.app.models import Agent, Customer, RFQ, RFQRecipient, Situation
        s.add(Customer(id="c1", org_id="o1", name="C"))
        s.add(Situation(id="situation-1d7cbf4c-xxxx", org_id="o1", customer_id="c1"))
        s.add(RFQ(id="1d7cbf4c-aaaa-bbbb-cccc-dddddddddddd", org_id="o1", situation_id="situation-1d7cbf4c-xxxx"))
        s.add(Agent(id="a1", org_id="o1", company="Agent A", email="rates@agenta.test"))
        s.add(RFQRecipient(org_id="o1", rfq_id="1d7cbf4c-aaaa-bbbb-cccc-dddddddddddd",
                           agent_id="a1", status="Sent"))
        await s.commit()

    MSG = {"uid": 7, "from": "Agent A <rates@agenta.test>",
           "subject": "Re: [RFQ:1d7cbf4c] rates",
           "body_text": "Ocean Freight $1,850\nDestination Charges $650"}

    def fake_fetch(host, username, password, last_uid):
        # Mirror the real UID {last_uid+1}:* semantics: nothing new, nothing back.
        if last_uid >= 7:
            return ([], last_uid)
        return ([MSG], 7)

    monkeypatch.setattr(mp, "fetch_since", fake_fetch)
    monkeypatch.setattr(mp, "decrypt_secret", lambda token: "pw")
    box = SimpleNamespace(org_id="o1", secret="enc", host="h", username="u", last_uid=0)

    async with factory() as s:
        assert (await mp.poll_mailbox(s, box))["auto_quotations"] == 1
    async with factory() as s:
        second = await mp.poll_mailbox(s, box)
    assert second == {"fetched": 0, "auto_quotations": 0, "situations": 0}

    async with factory() as s:
        quotes = (await s.execute(select(AgentQuotation))).scalars().all()
        assert len(quotes) == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_unknown_token_skipped_but_watermark_advances(monkeypatch):
    """A reply referencing a nonexistent RFQ must not loop forever."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from backend.app.db import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    def fake_fetch(host, username, password, last_uid):
        return ([{"uid": 3, "from": "x@y.test", "subject": "Re: [RFQ:deadbeef] ?",
                 "body_text": "hello"}], 3)

    monkeypatch.setattr(mp, "fetch_since", fake_fetch)
    monkeypatch.setattr(mp, "decrypt_secret", lambda token: "pw")
    box = SimpleNamespace(org_id="o1", secret="enc", host="h", username="u", last_uid=0)

    async with factory() as s:
        counts = await mp.poll_mailbox(s, box)
    assert counts == {"fetched": 1, "auto_quotations": 0, "situations": 0}
    assert box.last_uid == 3  # consumed, will not be re-fetched
    await engine.dispose()


@pytest.mark.asyncio
async def test_fetch_failure_propagates_for_502_mapping(monkeypatch):
    """IMAP/login errors must reach the route so it can return 502, not crash."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from backend.app.db import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    def boom(host, username, password, last_uid):
        raise OSError("connect ECONNREFUSED")

    monkeypatch.setattr(mp, "fetch_since", boom)
    monkeypatch.setattr(mp, "decrypt_secret", lambda token: "pw")
    box = SimpleNamespace(org_id="o1", secret="enc", host="h", username="u", last_uid=0)

    async with factory() as s:
        with pytest.raises(OSError):
            await mp.poll_mailbox(s, box)
    assert box.last_uid == 0  # watermark untouched on failure
    await engine.dispose()
