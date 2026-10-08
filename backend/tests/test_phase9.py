"""Phase 9 tests — billing gate, cron config, JWKS real-path (no network)."""
import time
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from jwt import encode as jwt_encode

from backend.app import auth
from backend.app.services import billing as b


def run(coro):
    import asyncio
    return asyncio.run(coro)


def test_entitlement_matrix():
    now = datetime(2026, 10, 4, 12, 0, 0)
    assert b.entitlement_allows("active", None, now) is True
    assert b.entitlement_allows("trialing", now + timedelta(days=22), now) is True
    assert b.entitlement_allows("trialing", None, now) is True  # dev orgs
    assert b.entitlement_allows("trialing", now - timedelta(days=1), now) is False
    assert b.entitlement_allows("past_due", None, now) is False
    assert b.entitlement_allows("cancelled", None, now) is False


def test_jwks_real_path_hs256(monkeypatch):
    monkeypatch.setenv("ALLOW_AUTH_STUB", "false")
    monkeypatch.setitem(auth._jwks_cache, "keys", ["test-secret"])
    monkeypatch.setitem(auth._jwks_cache, "fetched_at", time.time())
    token = jwt_encode({"sub": "u1", "org_id": "org-9", "role": "Manager"}, "test-secret", algorithm="HS256")
    u = run(auth.get_current_user(f"Bearer {token}", "org-9", "CSR"))
    assert (u.user_id, u.org_id, u.role) == ("u1", "org-9", "Manager")  # role from claims, not header


def test_jwks_org_mismatch_rejected(monkeypatch):
    monkeypatch.setenv("ALLOW_AUTH_STUB", "false")
    monkeypatch.setitem(auth._jwks_cache, "keys", ["test-secret"])
    monkeypatch.setitem(auth._jwks_cache, "fetched_at", time.time())
    token = jwt_encode({"sub": "u1", "org_id": "org-9"}, "test-secret", algorithm="HS256")
    with pytest.raises(HTTPException) as e:
        run(auth.get_current_user(f"Bearer {token}", "org-other", "CSR"))
    assert e.value.status_code == 403


def test_token_without_org_rejected(monkeypatch):
    monkeypatch.setenv("ALLOW_AUTH_STUB", "false")
    monkeypatch.setitem(auth._jwks_cache, "keys", ["test-secret"])
    monkeypatch.setitem(auth._jwks_cache, "fetched_at", time.time())
    token = jwt_encode({"sub": "u1"}, "test-secret", algorithm="HS256")
    with pytest.raises(HTTPException) as e:
        run(auth.get_current_user(f"Bearer {token}", "org-9", "CSR"))
    assert e.value.status_code == 401


def test_cron_configured():
    from worker.main import WorkerSettings
    names = sorted(
        (getattr(job, "coroutine", None) or getattr(job, "function", None)).__name__
        for job in WorkerSettings.cron_jobs
    )
    assert names == ["poll_all_mailboxes", "send_due_reminders"]
    assert WorkerSettings.functions and WorkerSettings.functions[0].__name__ == "send_due_reminders"
