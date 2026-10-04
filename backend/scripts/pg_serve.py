"""Persistent local Postgres for pilot dev (no admin/Docker needed).

Uses pgserver wheels. Starts PG 16 on 127.0.0.1, ensures quote_desk DB,
writes the asyncpg URL to .pg_url, then blocks to keep the server alive.
Run in background: it must stay alive while the API/migrations use it.
Restart after reboot with the same command.
"""
import asyncio
import time

import asyncpg
import pgserver

ROOT = r"C:\Users\user\Documents\Default Project"


async def ensure_db(admin_uri: str) -> None:
    conn = await asyncpg.connect(admin_uri)
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


def to_asyncpg(uri: str, dbname: str) -> str:
    uri = uri.replace("postgresql://", "postgresql+asyncpg://", 1)
    base = uri.rsplit("/", 1)[0]
    return f"{base}/{dbname}"


def main() -> None:
    srv = pgserver.get_server(r"C:\Users\user\pgdata", cleanup_mode=None)
    admin_uri = srv.get_uri()
    print("postgres up:", admin_uri, flush=True)
    asyncio.run(ensure_db(admin_uri))
    url = to_asyncpg(admin_uri, "quote_desk")
    with open(ROOT + "\\.pg_url", "w") as f:
        f.write(url)
    print("wrote .pg_url:", url, flush=True)
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
