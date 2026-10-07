"""Persistent local Postgres for pilot dev (no admin/Docker needed).

Fixed port 5433 so .pg_url/.env stay valid across restarts. Starts pg_ctl
WITHOUT -w (pgserver's 10s wait times out on WAL replay after unclean
shutdowns) and polls pg_isready instead. Run in background; restart after
reboot with the same command.
"""
import asyncio
import os
import subprocess
import sys
import time

import asyncpg

PORT = 5433
PGDATA = r"C:\Users\user\pgdata"
ROOT = r"C:\Users\user\Documents\Default Project"


def binpath() -> str:
    import pgserver

    return os.path.join(os.path.dirname(pgserver.__file__), "pginstall", "bin")


def start() -> None:
    subprocess.run(
        [os.path.join(binpath(), "pg_ctl.exe"), "-D", PGDATA,
         "-o", '-h "127.0.0.1"', "-o", f"-p {PORT}",
         "-l", os.path.join(PGDATA, "log"), "start"],
        check=True,
    )


def wait_ready(timeout_s: int = 300) -> None:
    exe = os.path.join(binpath(), "pg_isready.exe")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = subprocess.run([exe, "-h", "127.0.0.1", "-p", str(PORT)],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return
        time.sleep(5)
    raise RuntimeError("postgres never became ready")


async def ensure_db() -> None:
    conn = await asyncpg.connect(f"postgresql://postgres@127.0.0.1:{PORT}/postgres")
    try:
        await conn.execute("CREATE DATABASE quote_desk")
        print("created database quote_desk")
    except Exception as exc:
        if "already exists" in str(exc):
            print("database quote_desk exists")
        else:
            raise
    finally:
        await conn.close()


def main() -> None:
    if not os.path.exists(os.path.join(PGDATA, "PG_VERSION")):
        import pgserver

        pgserver.get_server(PGDATA)  # first-time init only
    start()
    wait_ready()
    asyncio.run(ensure_db())
    url = f"postgresql+asyncpg://postgres:@127.0.0.1:{PORT}/quote_desk"
    with open(os.path.join(ROOT, ".pg_url"), "w") as f:
        f.write(url)
    print("wrote .pg_url:", url, flush=True)
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    sys.exit(main())
