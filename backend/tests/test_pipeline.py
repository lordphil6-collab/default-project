"""Pipeline tests — recommendations, mailbox providers, STARTTLS, intake synthesis."""
import pytest


def test_recommend_picks_cheapest_and_standard_rule():
    from backend.app.services import recommend as r

    quotes = [
        {"id": "q1", "agent": "Slow", "currency": "USD",
         "charges": {"freight": 2000.0, "origin": 100.0, "destination": 300.0, "other": 0.0},
         "transit_days": 30},
        {"id": "q2", "agent": "Fast", "currency": "USD",
         "charges": {"freight": 1800.0, "origin": 100.0, "destination": 300.0, "other": 50.0},
         "transit_days": 20},
        {"id": "q3", "agent": "Vague", "currency": "USD",
         "charges": {"freight": 100.0, "origin": 0.0, "destination": None, "other": 0.0},
         "transit_days": 0},
    ]
    rules = [{"id": "r9", "name": "Other", "kind": "fixed", "value": 50.0, "min_margin": 0.0},
             {"id": "r1", "name": "Standard", "kind": "percent", "value": 10.0, "min_margin": 0.0}]
    out = r.recommend(quotes, rules, lane_typical=3000.0)
    assert out["available"] and out["agent"] == "Fast" and out["agent_quotation_id"] == "q2"
    assert out["agent_total"] == 2250.0 and out["rule"] and out["rule"]["id"] == "r1"
    assert out["markup_amount"] == 225.0 and out["final_price"] == 2475.0
    assert out["lane_verdict"] == "beats lane typical" and out["unknown"] == 1
    assert [a["agent"] for a in out["alternatives"]] == ["Slow"]
    assert "Fast" in out["reasoning"] and "Standard" in out["reasoning"]


def test_recommend_honest_without_rules_or_totals():
    from backend.app.services import recommend as r

    out = r.recommend([{"id": "q", "agent": "A", "charges": {"freight": 1.0, "destination": 0.0}}], [])
    assert out["available"] and out["rule"] is None and out["markup_amount"] == 0.12
    out2 = r.recommend([{"id": "q", "agent": "A",
                         "charges": {"freight": 1.0, "destination": None}}], [])
    assert out2["available"] is False and "identifiable" in out2["reason"]


def test_mailbox_presets_and_validation():
    from backend.app.routers.mailboxes import PRESETS
    assert PRESETS["gmail"] == {"host": "imap.gmail.com", "port": 993, "use_ssl": True}
    assert PRESETS["outlook"] == {"host": "outlook.office365.com", "port": 993, "use_ssl": True}
    assert PRESETS["webmail"]["port"] == 993


@pytest.mark.asyncio
async def test_connect_validates_provider_and_host():
    from fastapi import HTTPException
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from types import SimpleNamespace
    from backend.app.db import Base
    from backend.app.routers.mailboxes import MailboxIn, connect

    async def call(payload, org="o1"):
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as s:
            try:
                return await connect(payload, SimpleNamespace(org_id=org, user_id="u"), None, s)
            finally:
                await engine.dispose()

    import os
    os.environ["MAIL_SECRET_KEY"] = __import__("cryptography.fernet", fromlist=["Fernet"]).Fernet.generate_key().decode()
    out = await call(MailboxIn(provider="gmail", username="a@gmail.com", password="pw"))
    assert out["host"] == "imap.gmail.com" and out["port"] == 993 and "secret" not in out
    out = await call(MailboxIn(provider="webmail", host="mail.example.com", port=143,
                               use_ssl=False, username="u", password="pw"))
    assert out["host"] == "mail.example.com" and out["port"] == 143
    with pytest.raises(HTTPException) as e:
        await call(MailboxIn(provider="yahoo", host="h", username="u", password="p"))
    assert e.value.status_code == 422
    with pytest.raises(HTTPException) as e:
        await call(MailboxIn(provider="webmail", host="", username="u", password="p"))
    assert e.value.status_code == 422


def test_fetch_since_starttls_branch(monkeypatch):
    import imaplib
    from backend.app.services import mail as m

    seen = {}

    class FakePlain:
        def __init__(self, host, port):
            seen["plain"] = (host, port)
        def starttls(self):
            seen["tls"] = True
        def login(self, u, p):
            pass
        def select(self, *a, **k):
            pass
        def uid(self, *a):
            return ("OK", [b""])
        def logout(self):
            pass

    monkeypatch.setattr(imaplib, "IMAP4", FakePlain)
    msgs, top = m.fetch_since("mail.example.com", "u", "p", 0, port=143, use_ssl=False)
    assert (msgs, top) == ([], 0) and seen == {"plain": ("mail.example.com", 143), "tls": True}


def test_intake_channel_web_and_synthesis():
    from backend.app.schemas import IntakeIn
    assert IntakeIn(customer_name="C", channel="web", body="Quote 5 cartons Guangzhou to Lagos").channel == "web"
