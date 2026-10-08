"""PII redaction for logs (Phase A). Business data in the DB stays intact —
only log output is scrubbed, so CSRs keep full fidelity while log files,
error trackers, and pasted logs stop leaking contacts.
"""
import logging
import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+?234[\s-]?)?0?[789]\d{2}[\s-]?\d{3}[\s-]?\d{4}")
GENERIC_PHONE_RE = re.compile(r"\+?\d[\d\s\-().]{7,}\d")


def redact(text: str) -> str:
    text = EMAIL_RE.sub("[redacted-email]", text)
    text = PHONE_RE.sub("[redacted-phone]", text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = redact(str(record.getMessage()))
            record.args = ()
        except Exception:
            pass
        return True


_installed = False


def install() -> None:
    global _installed
    if _installed:
        return
    logging.getLogger().addFilter(RedactingFilter())
    _installed = True
