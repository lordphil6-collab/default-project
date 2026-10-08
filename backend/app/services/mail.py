"""Inbound email: IMAP poll + parse + RFQ-reply threading (stdlib only).

Flow: poll mailbox (UIDs > last_uid) -> parse .eml -> if subject carries
[RFQ:xxxxxxxx], attach body as that agent's quotation (auto-ingested);
otherwise create a Customer Situation like POST /intake.
Secrets are Fernet-encrypted with MAIL_SECRET_KEY (cryptography lib).
"""
import email
import email.policy
import imaplib
import os
import re

from cryptography.fernet import Fernet, InvalidToken

RFQ_TOKEN = re.compile(r"\[RFQ:([0-9a-fA-F]{8})\]")


def rfq_token(subject: str) -> str | None:
    m = RFQ_TOKEN.search(subject or "")
    return m.group(1).lower() if m else None


def rfq_subject(rfq_id: str, route: str) -> str:
    return f"[RFQ:{rfq_id[:8]}] Rate request — {route}"


def _key() -> bytes:
    key = os.getenv("MAIL_SECRET_KEY", "")
    if not key:
        raise RuntimeError("MAIL_SECRET_KEY not set — cannot store mailbox passwords")
    return key.encode()


def encrypt_secret(raw: str) -> str:
    return Fernet(_key()).encrypt(raw.encode()).decode()


def decrypt_secret(token: str) -> str:
    try:
        return Fernet(_key()).decrypt(token.encode()).decode()
    except InvalidToken:
        raise RuntimeError("cannot decrypt mailbox password — MAIL_SECRET_KEY changed?")


def parse_eml(raw: bytes) -> dict:
    """Parse raw .eml into {from, subject, body_text}. Never raises on content."""
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    subject = str(msg.get("Subject", ""))
    sender = str(msg.get("From", ""))
    parts: list[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart" or part.get_filename():
                continue
            if part.get_content_type() in ("text/plain",):
                try:
                    parts.append(part.get_content())
                except Exception:
                    continue
    else:
        try:
            parts.append(msg.get_content())
        except Exception:
            parts.append("")
    return {"from": sender, "subject": subject, "body_text": "\n".join(parts).strip()[:8000]}


def fetch_since(host: str, username: str, password: str, last_uid: int) -> tuple[list[dict], int]:
    """IMAP UID fetch; returns (messages, new_last_uid). Pure fetch, no deletes."""
    box = imaplib.IMAP4_SSL(host)
    try:
        box.login(username, password)
        box.select("INBOX", readonly=True)
        typ, data = box.uid("search", None, f"UID {last_uid + 1}:*")
        uids = [int(u) for u in (data[0] or b"").split()] if typ == "OK" else []
        out, top = [], last_uid
        for uid in uids:
            typ, data = box.uid("fetch", str(uid), "(RFC822)")
            if typ != "OK" or not data or not data[0]:
                continue
            raw = data[0][1] if isinstance(data[0], tuple) else b""
            if raw:
                out.append({"uid": uid, **parse_eml(raw)})
                top = max(top, uid)
        return out, top
    finally:
        try:
            box.logout()
        except Exception:
            pass
