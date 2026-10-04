"""Phase 8 tests — auth modes, audit model, eval gate, pilot route coverage."""
import asyncio
import json
import os
import pathlib

import pytest
from fastapi import HTTPException

from backend.app import auth
from backend.app.main import app
from backend.app.models import AuditLog
from backend.app.services import evalharness as ev

ROOT = pathlib.Path(__file__).resolve().parents[2]


def run(coro):
    return asyncio.run(coro)


def test_stub_mode_accepts_headers(monkeypatch):
    monkeypatch.setenv("ALLOW_AUTH_STUB", "true")
    u = run(auth.get_current_user("Bearer stub-abc", "org-1", "Manager"))
    assert (u.user_id, u.org_id, u.role) == ("stub-user", "org-1", "Manager")


def test_missing_credentials_rejected(monkeypatch):
    monkeypatch.setenv("ALLOW_AUTH_STUB", "true")
    with pytest.raises(HTTPException) as e:
        run(auth.get_current_user("", "org-1", "CSR"))
    assert e.value.status_code == 401


def test_prod_mode_requires_jwks(monkeypatch):
    monkeypatch.setenv("ALLOW_AUTH_STUB", "false")
    monkeypatch.delenv("FASTAPI_JWKS_URL", raising=False)
    with pytest.raises(HTTPException):
        run(auth.get_current_user("Bearer real-token", "org-1", "CSR"))


def test_audit_log_model_shape():
    row = AuditLog(org_id="o", actor="u", action="quote.approved", detail={"final_price": 3270.4})
    assert row.action == "quote.approved" and row.detail["final_price"] == 3270.4


def test_eval_gate_passes_on_golden():
    fixtures = json.loads((ROOT / "ai" / "evals" / "golden.json").read_text())
    scores = ev.run_golden(fixtures)
    ok, fails = ev.gate(scores)
    assert ok, fails
    assert scores["extraction"]["inventions"] == 0


def test_pilot_route_coverage():
    paths = {r.path for r in app.routes}
    required = {
        "/health", "/intake", "/understand", "/situations", "/situations/{sid}",
        "/situations/{sid}/extract", "/rfqs", "/rfqs/{rfq_id}/quotations",
        "/rfqs/{rfq_id}/compare", "/customer-quotes", "/customer-quotes/{qid}/approve",
        "/customer-quotes/{qid}/send", "/follow-ups", "/situations/{sid}/outcome",
        "/exceptions", "/exceptions/{eid}/resolve", "/dashboard/today",
    }
    assert required.issubset(paths), required - paths
    assert os.getenv("ALLOW_AUTH_STUB", "true") == "true"  # pilot runs stubbed auth
