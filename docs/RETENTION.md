# Data retention & privacy

## What we store (per org/tenant)
Customer names/contacts, conversations, shipment details, agent quotations and
commercials, quotes, follow-ups, auth sessions, billing entitlements, audit log.

## Retention
- Active orgs: everything, needed for the workflow + history.
- Cancelled orgs: kept 90 days for reactivation, then hard-deleted on request.
- Logs: app logs carry NO emails/phones (redacted at write by
  `services/redact.py`); raw DB keeps business fidelity for CSRs.

## Delete-my-data path
Owner writes support (or runs, with `DATABASE_URL` set):
`python backend/scripts/erase_org.py ORG_ID` — deletes customers, situations,
conversations, messages, RFQs, quotations, quotes, follow-ups, exceptions,
entitlements, mailbox secrets, audit rows for that org (Better Auth identity
rows are removed via the user admin API). Prints counts. No soft-delete limbo.
