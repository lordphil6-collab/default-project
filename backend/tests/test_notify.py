"""SMTP delivery tests — TLS paths, failures, fallback (no real servers)."""
import smtplib

from backend.app.services import notify as n


def _env(monkeypatch, **kw):
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM"):
        monkeypatch.delenv(k, raising=False)
    for k, v in kw.items():
        monkeypatch.setenv(k, v)


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port
        self.starttls_called = False
        self.logged_in = None
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.starttls_called = True

    def login(self, user, password):
        self.logged_in = (user, password)

    def send_message(self, msg):
        self.sent = msg


def test_starttls_587(monkeypatch):
    _env(monkeypatch, SMTP_HOST="smtp.gmail.com", SMTP_PORT="587",
         SMTP_USER="u", SMTP_PASSWORD="p", SMTP_FROM="u")
    FakeSMTP.instances.clear()
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    out = n.send_email("to@x.test", "s", "b")
    assert out["status"] == "sent"
    conn = FakeSMTP.instances[-1]
    assert (conn.host, conn.port) == ("smtp.gmail.com", 587)
    assert conn.starttls_called and conn.logged_in == ("u", "p")


def test_implicit_tls_465(monkeypatch):
    _env(monkeypatch, SMTP_HOST="smtp.gmail.com", SMTP_PORT="465",
         SMTP_USER="u", SMTP_PASSWORD="p")
    FakeSMTP.instances.clear()
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    out = n.send_email("to@x.test", "s", "b")
    assert out["status"] == "sent"
    assert len(FakeSMTP.instances) == 1  # SMTP_SSL only, no STARTTLS attempt
    conn = FakeSMTP.instances[-1]
    assert (conn.host, conn.port) == ("smtp.gmail.com", 465)
    assert not conn.starttls_called


def test_auth_failure_reports_failed(monkeypatch):
    _env(monkeypatch, SMTP_HOST="smtp.gmail.com", SMTP_USER="u", SMTP_PASSWORD="bad")

    class BadAuth(FakeSMTP):
        def login(self, user, password):
            raise smtplib.SMTPAuthenticationError(535, b"bad credentials")

    monkeypatch.setattr(smtplib, "SMTP", BadAuth)
    out = n.send_email("to@x.test", "s", "b")
    assert out["status"] == "failed"
    assert out["status"] != "sent"


def test_garbage_port_does_not_crash(monkeypatch):
    _env(monkeypatch, SMTP_HOST="smtp.gmail.com", SMTP_PORT="not-a-port",
         SMTP_USER="u", SMTP_PASSWORD="p")
    FakeSMTP.instances.clear()
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    out = n.send_email("to@x.test", "s", "b")
    assert out["status"] == "sent"
    assert FakeSMTP.instances[-1].port == 587


def test_no_smtp_config_logged_only(monkeypatch):
    _env(monkeypatch)
    out = n.send_email("to@x.test", "s", "b")
    assert out == {"channel": "email", "status": "logged-only", "detail": "SMTP_HOST not set"}
