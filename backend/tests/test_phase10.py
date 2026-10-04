"""Phase 10 tests — trial auto-provision + 402, local storage roundtrip."""
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from backend.app.auth import CurrentUser


@pytest.mark.asyncio
async def test_first_write_provisions_trial_then_402_on_expiry():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from backend.app.db import Base
    from backend.app.models import Entitlement, Organization
    from backend.app.services import billing as b

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    b._session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        u = await b.require_entitlement(CurrentUser("u", "new-org", "CSR"))
        assert u.org_id == "new-org"
        async with b._factory()() as s:
            ent = (await s.execute(select(Entitlement).where(Entitlement.org_id == "new-org"))).scalars().first()
            assert ent is not None and ent.status == "trialing"
            org = (await s.execute(select(Organization).where(Organization.id == "new-org"))).scalars().first()
            assert (org.trial_ends - org.trial_start).days == 30
            org.trial_ends = datetime(2000, 1, 1)
            await s.commit()
        with pytest.raises(HTTPException) as e:
            await b.require_entitlement(CurrentUser("u", "new-org", "CSR"))
        assert e.value.status_code == 402
    finally:
        b._session_factory = None
        await engine.dispose()


def test_local_storage_roundtrip(tmp_path, monkeypatch):
    from backend.app.services import storage as st

    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    monkeypatch.delenv("S3_ENDPOINT", raising=False)
    st._DIR = None
    try:
        loc = st.save_attachment("org-1", "quote.pdf", b"%PDF-1.4 fake")
        assert loc["backend"] == "local"
        assert st.open_attachment(loc) == b"%PDF-1.4 fake"
    finally:
        st._DIR = None


def test_billing_grace_window():
    from backend.app.services import billing as b

    now = datetime(2026, 10, 4, 12, 0, 0)
    assert b.entitlement_allows("trialing", now + timedelta(seconds=1), now) is True
    assert b.entitlement_allows("trialing", now - timedelta(seconds=1), now) is False
