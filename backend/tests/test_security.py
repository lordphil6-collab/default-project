"""Phase A tests — rate limits, redaction (pure, no servers)."""
import logging

from backend.app.services import ratelimit as rl
from backend.app.services import redact as rd


def test_sliding_window_blocks_burst_then_recovers():
    lim = rl.RateLimiter(limit=3, window_s=60)
    assert [lim.allowed("ip", now=100 + i) for i in range(3)] == [True, True, True]
    assert lim.allowed("ip", now=103) is False
    assert lim.allowed("other", now=103) is True  # per-key isolation
    assert lim.allowed("ip", now=161) is True  # window slid past


def test_redact_emails_and_phones():
    s = rd.redact("mail ada@acme.test or call +234 803 123 4567, alt 08031234567")
    assert "ada@acme.test" not in s and "@" not in s.replace("[redacted-email]", "")
    assert "803" not in s and "4567" not in s
    assert "[redacted-email]" in s and "[redacted-phone]" in s


def test_redact_keeps_business_numbers():
    s = rd.redact("Total $2,920.40 for 5 cartons, 20ft, validity 7 days")
    assert "$2,920.40" in s and "5 cartons" in s and "20ft" in s


def test_logging_filter_scrubs(caplog):
    f = rd.RedactingFilter()
    rec = logging.LogRecord("x", logging.INFO, __file__, 1, "user %s wrote %s", ("a@b.co", "+2348012345678"), None)
    assert f.filter(rec) is True
    assert "a@b.co" not in rec.msg and "080" not in rec.msg and "234" not in rec.msg


def test_install_idempotent():
    rd.install()
    n = sum(isinstance(f, rd.RedactingFilter) for f in logging.getLogger().filters)
    rd.install()
    assert sum(isinstance(f, rd.RedactingFilter) for f in logging.getLogger().filters) == n
