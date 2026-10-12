"""Quote delivery — Email (SMTP, stdlib) + WhatsApp Cloud API (httpx).

Configured via env; when unconfigured, delivery is recorded as logged-only
(audit trail) and the quote still advances — sending must never silently fail.
"""
import os
import smtplib
from email.message import EmailMessage

import httpx


def _smtp_config() -> dict | None:
    host = os.getenv("SMTP_HOST", "")
    if not host:
        return None
    try:
        port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        port = 587
    return {"host": host, "port": port,
            "user": os.getenv("SMTP_USER", ""), "password": os.getenv("SMTP_PASSWORD", ""),
            "from": os.getenv("SMTP_FROM", os.getenv("SMTP_USER", ""))}


def _whatsapp_config() -> dict | None:
    token, phone_id = os.getenv("WHATSAPP_TOKEN", ""), os.getenv("WHATSAPP_PHONE_ID", "")
    if not (token and phone_id):
        return None
    return {"token": token, "phone_id": phone_id}


def quote_text(customer: str, route: str, total: float, currency: str, validity: int, terms: str) -> str:
    lines = [f"Quotation for {customer}", route, f"Total: {currency} {total:,.2f}",
             f"Valid {validity} days"]
    if terms:
        lines.append(f"Terms: {terms}")
    return "\n".join(lines)


def send_email(to: str, subject: str, body: str) -> dict:
    cfg = _smtp_config()
    if not cfg:
        return {"channel": "email", "status": "logged-only", "detail": "SMTP_HOST not set"}
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = cfg["from"], to, subject
    msg.set_content(body)
    try:
        if cfg["port"] == 465:
            # Implicit TLS (Gmail/Outlook port 465): no STARTTLS upgrade.
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=20) as s:
                if cfg["user"]:
                    s.login(cfg["user"], cfg["password"])
                s.send_message(msg)
        else:
            # STARTTLS (port 587 for Gmail/Outlook and most others).
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as s:
                s.starttls()
                if cfg["user"]:
                    s.login(cfg["user"], cfg["password"])
                s.send_message(msg)
        return {"channel": "email", "status": "sent", "detail": f"to {to}"}
    except Exception as exc:
        return {"channel": "email", "status": "failed", "detail": str(exc)[:300]}


def send_whatsapp(to: str, body: str) -> dict:
    cfg = _whatsapp_config()
    if not cfg:
        return {"channel": "whatsapp", "status": "logged-only", "detail": "WHATSAPP_TOKEN not set"}
    try:
        r = httpx.post(
            f"https://graph.facebook.com/v21.0/{cfg['phone_id']}/messages",
            headers={"Authorization": f"Bearer {cfg['token']}"},
            json={"messaging_product": "whatsapp", "to": to,
                  "type": "text", "text": {"body": body}},
            timeout=20,
        )
        if r.status_code >= 400:
            return {"channel": "whatsapp", "status": "failed", "detail": r.text[:300]}
        return {"channel": "whatsapp", "status": "sent", "detail": f"to {to}"}
    except Exception as exc:
        return {"channel": "whatsapp", "status": "failed", "detail": str(exc)[:300]}
