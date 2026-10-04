"""Live ARQ proof: enqueue send_due_reminders, await result from the worker."""
import asyncio
import os

from arq import create_pool
from arq.connections import RedisSettings


async def main() -> None:
    pool = await create_pool(RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0")))
    pong = await pool.ping()
    print("REDIS PING:", pong)
    job = await pool.enqueue_job("send_due_reminders")
    print("ENQUEUED:", job.job_id)
    result = await job.result(timeout=60)
    print("JOB RESULT:", result)
    assert isinstance(result, dict) and "followups_due" in result
    print("ARQ LIVE OK")


asyncio.run(main())
