# Phase A — trust & abuse (DONE, verified 2026-10-08)
Date: 2026-10-08

Implemented:
- Real roles: Better Auth member role → JWT claim (owner→Owner, admin→Manager,
  else CSR); FastAPI enforces claims (header is fallback); localStorage role
  switch removed. `frontend/lib/auth-server.ts`, `mailer.ts` (SMTP or logged).
- Forgot/reset password pages + server send hook; invite-member UI at `/team`
  (pending list); accept flow via API.
- Rate limiting: sliding-window middleware on `/public/*` (20/min/IP, 429).
- PII redaction logging filter + `docs/RETENTION.md` + `erase_org.py` hard delete.
- `backend/scripts/phaseA_proof.py` — full live proof.

Verified:
- ruff clean; pytest 50 passed; frontend build green.
- Live: Owner claim in JWT, Owner gate beats CSR header, invite→member=CSR
  (admin 403, intake 200), burst→429, reset request 200.
