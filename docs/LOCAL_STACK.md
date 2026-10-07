# Local stack runbook (no admin, no Docker)

Fixed ports: Postgres 5433 · Redis 6379 · Next 3002 · API 8010.
(`NEXT_DIST_DIR` isolates dev servers: two `next dev` on one `.next/` corrupt
each other — Oct 7 incident. API moved 8000→8006→8010: unkillable phantom
servers squat on old ports. CORS middleware added Oct 7 — without it every
browser API call dies on preflight OPTIONS 405 while scripts/curl work fine.)
`.pg_url` is stable (`postgresql+asyncpg://postgres:@127.0.0.1:5433/quote_desk`).

Revive after reboot (each in its own terminal, from repo root):

```powershell
python backend/scripts/pg_serve.py
C:\Users\user\redis\redis-server.exe --port 6379
npm.cmd --prefix frontend run dev -- --port 3000 --hostname 127.0.0.1
$env:DATABASE_URL = (Get-Content .\.pg_url -Raw).Trim()
$env:ALLOW_AUTH_STUB = 'true'
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
$env:REDIS_URL = 'redis://localhost:6379/0'
python -m arq worker.main.WorkerSettings
```

Verify: `python backend/scripts/pg_smoke.py`, `python backend/scripts/arq_proof.py`,
`npm run build` in frontend, `python -m pytest backend/tests/ -q`.

Notes:
- pg_serve starts pg_ctl WITHOUT -w and polls pg_isready: pgserver's 10s
  wait times out on WAL replay after unclean shutdowns (Oct 7 incident).
- Always stop Postgres cleanly before reboot: `pg_ctl -D C:\Users\user\pgdata stop -m fast`
  (pg_ctl lives under `pgserver/pginstall/bin` in site-packages).
- A second cluster exists at C:\Users\user\pgsql (EDB binaries, unused) — ignore it.
- `.env` / `.pg_url` are git-ignored and hold the live URL + secrets.
