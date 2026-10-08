"""Mail service tests — parsing, tokens, crypto (no servers)."""
import pytest

from backend.app.services import mail as m


RAW = (b"From: Agent A <rates@agenta.test>\r\n"
       b"Subject: Re: [RFQ:1d7cbf4c] Rate request\r\n"
       b"Content-Type: text/plain; charset=utf-8\r\n"
       b"\r\n"
       b"Ocean Freight $1,850\nOrigin Charges $420\n")


def test_parse_eml_and_token():
    p = m.parse_eml(RAW)
    assert "agenta" in p["from"].lower()
    assert "1,850" in p["body_text"]
    assert m.rfq_token(p["subject"]) == "1d7cbf4c"
    assert m.rfq_token("no token here") is None
    assert m.rfq_subject("1d7cbf4c-xxxx", "China to Lagos").startswith("[RFQ:1d7cbf4c]")


def test_secret_roundtrip(monkeypatch):
    from cryptography.fernet import Fernet

    monkeypatch.setenv("MAIL_SECRET_KEY", Fernet.generate_key().decode())
    assert m.decrypt_secret(m.encrypt_secret("app-password-123")) == "app-password-123"


def test_secret_missing_errors(monkeypatch):
    monkeypatch.delenv("MAIL_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MAIL_SECRET_KEY"):
        m.encrypt_secret("x")
