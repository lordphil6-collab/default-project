"""Verify migration: upgrade head on throwaway SQLite, list tables, downgrade, clean up."""
import os
import sqlite3
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "verify_mig.db")
if os.path.exists(DB):
    os.remove(DB)

env = dict(os.environ, DATABASE_URL=f"sqlite:///{DB}")
r = subprocess.run(
    [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
    cwd=ROOT, env=env, capture_output=True, text=True,
)
print(r.stdout[-500:] if r.stdout else "")
print(r.stderr[-500:] if r.stderr else "")
assert r.returncode == 0, "alembic upgrade failed"

tables = sorted(
    row[0] for row in sqlite3.connect(DB).execute("SELECT name FROM sqlite_master WHERE type='table'")
)
print("TABLES:", tables)
expected = {
    "organizations", "users", "customers", "situations", "conversations", "messages",
    "rfqs", "agent_quotations", "customer_quotations", "follow_ups", "exceptions",
    "plans", "entitlements", "audit_log", "alembic_version",
}
assert expected.issubset(set(tables)), expected - set(tables)

r = subprocess.run(
    [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "downgrade", "base"],
    cwd=ROOT, env=env, capture_output=True, text=True,
)
assert r.returncode == 0, "alembic downgrade failed"
os.remove(DB)
print("MIGRATION OK (upgrade + downgrade)")
