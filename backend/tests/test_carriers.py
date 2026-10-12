"""Carrier + brief tests — registry isolation, DHL mapping, brief synthesis (no network)."""
import os

import pytest


def test_unconfigured_adapters_skipped_not_fatal(monkeypatch):
    import asyncio

    from backend.app.services import carriers as c

    for k in ("DHL_API_USER", "DHL_API_PASSWORD", "DHL_ACCOUNT_NUMBER"):
        monkeypatch.delenv(k, raising=False)
    out = asyncio.run(c.quote_all(c.CarrierRequest(origin_country="CN", destination_country="NG")))
    assert out.rates == [] and out.errors == []
    assert any(s.startswith("dhl-express:") for s in out.skipped)


def test_broken_adapter_cannot_block_others(monkeypatch):
    import asyncio

    from backend.app.services import carriers as c

    class Boom(c.CarrierAdapter):
        name = "boom-test"
        def configured(self):
            return None
        async def quote(self, req):
            raise RuntimeError("kaput")

    class Fine(c.CarrierAdapter):
        name = "fine-test"
        def configured(self):
            return None
        async def quote(self, req):
            return [{"carrier": "Fine", "total": 10.0}]

    monkeypatch.setattr(c, "_ADAPTERS", [Boom(), Fine()])
    out = asyncio.run(c.quote_all(c.CarrierRequest()))
    assert [r["carrier"] for r in out.rates] == ["Fine"]
    assert out.errors == ["boom-test: kaput"]


def test_dhl_parse_maps_products_defensively():
    from backend.app.services.carriers.dhl_express import DHLExpressAdapter

    payload = {"products": [
        {"productName": "EXPRESS WORLDWIDE", "currency": "USD",
         "totalPrice": [{"price": 128.5, "priceCurrency": "USD"}],
         "deliveryCapabilities": {"totalTransitDays": 3}},
        {"productCode": "E", "prices": {"value": 99.0, "currency": "EUR"}},
        "garbage-entry",
        {"productName": "No price product"},
    ]}
    rows = DHLExpressAdapter._parse(payload)
    assert len(rows) == 3
    assert rows[0]["carrier"] == "DHL Express" and rows[0]["total"] == 128.5
    assert rows[0]["transit_days"] == 3
    assert rows[1]["total"] == 99.0 and rows[1]["currency"] == "EUR"
    assert rows[2]["total"] is None  # Unknown stays Unknown


def test_dhl_requires_country_codes(monkeypatch):
    from backend.app.services.carriers import CarrierRequest
    from backend.app.services.carriers.dhl_express import DHLExpressAdapter

    for k, v in (("DHL_API_USER", "u"), ("DHL_API_PASSWORD", "p"), ("DHL_ACCOUNT_NUMBER", "123")):
        monkeypatch.setenv(k, v)
    with pytest.raises(ValueError, match="ISO-2"):
        DHLExpressAdapter()._params(CarrierRequest(origin_city="Guangzhou"))


@pytest.mark.asyncio
async def test_brief_synthesizes_thread():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from backend.app.db import Base
    from backend.app.models import Conversation, Customer, Message, Situation
    from backend.app.routers.inbox import conversation_brief
    from types import SimpleNamespace

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        s.add(Customer(id="c1", org_id="o1", name="Acme"))
        s.add(Situation(id="s1", org_id="o1", customer_id="c1"))
        s.add(Conversation(id="conv1", org_id="o1", situation_id="s1"))
        s.add(Message(org_id="o1", conversation_id="conv1", channel="email",
                      body="Quote for 5 cartons from Guangzhou to Lagos"))
        s.add(Message(org_id="o1", conversation_id="conv1", channel="email",
                      body="Weight is 200kg, ocean please"))
        await s.commit()

    async with factory() as s:
        out = await conversation_brief("conv1", SimpleNamespace(org_id="o1", user_id="u1"), s)
    assert out["messages"] == 2 and out["situation_id"] == "s1"
    assert "Guangzhou" in out["combined"] and "200kg" in out["combined"]
    assert out["extraction"]["destination"] == "Lagos"
    assert isinstance(out["missing"], list) and out["next_action"]
    await engine.dispose()
