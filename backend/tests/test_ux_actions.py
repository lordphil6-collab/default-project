"""UX action endpoints — inbox reply + follow-up completion (sqlite, no network)."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

def _user(**kw):
    d = {"org_id": "o1", "user_id": "u1", "role": "CSR"}
    d.update(kw)
    return SimpleNamespace(**d)


@pytest.mark.asyncio
async def test_post_message_and_org_isolation():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from backend.app.db import Base
    from backend.app.models import Conversation, Customer, Message, Situation
    from backend.app.routers.inbox import post_message
    from backend.app.routers.inbox import MessageIn

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        s.add(Customer(id="c1", org_id="o1", name="C"))
        s.add(Situation(id="s1", org_id="o1", customer_id="c1"))
        s.add(Conversation(id="conv1", org_id="o1", situation_id="s1"))
        await s.commit()

    async with factory() as s:
        out = await post_message("conv1", MessageIn(body="  On it — quoting now "), _user(), s)
    assert out["conversation_id"] == "conv1" and out["body"] == "On it — quoting now"

    async with factory() as s:
        with pytest.raises(HTTPException) as e:
            await post_message("conv1", MessageIn(body="hi"), _user(org_id="o2"), s)
        assert e.value.status_code == 404
    async with factory() as s:
        with pytest.raises(HTTPException) as e:
            await post_message("conv1", MessageIn(body="   "), _user(), s)
        assert e.value.status_code == 422
    await engine.dispose()


@pytest.mark.asyncio
async def test_complete_followup():
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from backend.app.db import Base
    from backend.app.models import Customer, FollowUp, Situation
    from backend.app.routers.followups import complete_followup

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        s.add(Customer(id="c1", org_id="o1", name="C"))
        s.add(Situation(id="s1", org_id="o1", customer_id="c1"))
        s.add(FollowUp(id="f1", org_id="o1", situation_id="s1", status="Due"))
        await s.commit()

    async with factory() as s:
        out = await complete_followup("f1", _user(), s)
    assert out == {"id": "f1", "status": "Done"}

    async with factory() as s:
        with pytest.raises(HTTPException) as e:
            await complete_followup("f1", _user(org_id="o2"), s)
        assert e.value.status_code == 404
    await engine.dispose()
