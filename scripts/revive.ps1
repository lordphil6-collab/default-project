# Double-click (or: powershell -ExecutionPolicy Bypass -File scripts\revive.ps1)
# Restarts the full local stack after a reboot. Run each block in its own terminal.
$ErrorActionPreference = "Stop"
Set-Location "C:\Users\user\Documents\Default Project"
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')

Write-Output "[1/5] Postgres :5433 ..."
Start-Process powershell -ArgumentList "-NoExit","-Command","python backend/scripts/pg_serve.py" -WorkingDirectory $PWD
Write-Output "[2/5] Redis :6379 ..."
Start-Process powershell -ArgumentList "-NoExit","-Command","C:\Users\user\redis\redis-server.exe --port 6379" -WorkingDirectory $PWD
Write-Output "[3/5] Web UI :3002 ..."
Start-Process powershell -ArgumentList "-NoExit","-Command","$env:NEXT_DIST_DIR='.next-3002'; npm.cmd --prefix frontend run dev -- --port 3002 --hostname 127.0.0.1" -WorkingDirectory $PWD
Write-Output "[4/5] API :8000 ..."
$pg = (Get-Content .\.pg_url -Raw).Trim()
$mk = ((Get-Content .env | Select-String '^MAIL_SECRET_KEY=').ToString().Split('=',2)[1])
Start-Process powershell -ArgumentList "-NoExit","-Command","$env:DATABASE_URL='$pg'; $env:ALLOW_AUTH_STUB='false'; $env:FASTAPI_JWKS_URL='http://localhost:3002/api/auth/jwks'; $env:DEFAULT_PORTAL_ORG_ID='XgeQBonnByHUV5xfgljiSOL1iYxjnLOf'; $env:MAIL_SECRET_KEY='$mk'; python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory $PWD
Write-Output "[5/5] Worker ..."
Start-Process powershell -ArgumentList "-NoExit","-Command","$env:REDIS_URL='redis://localhost:6379/0'; $env:DATABASE_URL='$pg'; python -m arq worker.main.WorkerSettings" -WorkingDirectory $PWD
Write-Output "Done. App: http://localhost:3002/  API docs: http://localhost:8000/docs"
