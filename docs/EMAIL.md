# Email in/out — setup guide

Inbound (agents reply, customers write) and outbound (RFQ send, quote send)
run through this flow. No OAuth apps needed for the pilot: plain IMAP + SMTP
with app passwords, passwords Fernet-encrypted at rest.

## 1. Secrets (2 min, once per machine/host)

```powershell
# 32-byte urlsafe key:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
$env:MAIL_SECRET_KEY = '<output>'   # encrypts stored mailbox passwords
```

Production: set `MAIL_SECRET_KEY` in the host env (same value everywhere or
stored passwords become unreadable).

## 2. Gmail (5 min)

1. Google Account → Security → 2-Step Verification ON → **App passwords** →
   create one for Mail.
2. App → Mailbox page → Connect: host `imap.gmail.com`, username your Gmail,
   password = the 16-char app password (spaces optional).
3. Outbound: set `SMTP_HOST=smtp.gmail.com SMTP_PORT=587 SMTP_USER=<gmail>
   SMTP_PASSWORD=<same app password> SMTP_FROM=<gmail>`, restart API.

## 3. Outlook / Microsoft 365 (5 min)

1. account.microsoft.com → Security → Advanced → **App passwords** → create.
2. Connect: host `outlook.office365.com`, username your address, app password.
3. Outbound: `SMTP_HOST=smtp.office365.com`, port 587, same credentials.

## 4. How the loop works

- **Out:** RFQ "Send to selected" emails each recipient agent with subject
  `[RFQ:xxxxxxxx] Rate request — …`. Without agent emails or SMTP it records
  `logged-only` — never silently pretends.
- **In:** worker polls every 30 min (`poll_all_mailboxes`) + "Poll now" button.
  Replies carrying `[RFQ:…]` auto-create the agent quotation and flip the
  recipient to Responded; anything else becomes a new Situation (channel email).
- Quote send: choose email/WhatsApp/record-only per send; result is audited.

## 5. OAuth webhooks (later, optional)

Gmail Pub/Sub (`watch`) and Outlook Graph subscriptions replace polling with
push; both need Google Cloud / Azure app registrations + public HTTPS. The
poll endpoint shape (`POST /mailboxes/{id}/poll`) already matches what a
webhook handler would call — swap transport, keep logic.
