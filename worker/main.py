"""ARQ worker — nightly reminder sweep (Phase 9).

cron: send_due_reminders daily 07:00 — follow-ups due/overdue + trials
expiring in 7/3/1 days. Run: arq worker.main.WorkerSettings
Requires REDIS_URL + DATABASE_URL (compose or local services).
"""
import logging
import os
from datetime import datetime, timedelta, timezone

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from backend.app.db import make_async_session_factory
from backend.app.models import Entitlement, FollowUp, Organization

log = logging.getLogger("quote-desk-worker")


async def send_due_reminders(ctx) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    counts = {"followups_due": 0, "trials_expiring": 0}
    try:
        async with make_async_session_factory()() as s:
            fus = (
                (await s.execute(select(FollowUp).where(FollowUp.due_at <= now + timedelta(days=1))))
                .scalars()
                .all()
            )
            counts["followups_due"] = len(fus)
            ents = (await s.execute(select(Entitlement).where(Entitlement.status == "trialing"))).scalars().all()
            orgs = {o.id: o for o in (await s.execute(select(Organization))).scalars().all()}
            for e in ents:
                ends = (orgs.get(e.org_id) or Organization()).trial_ends if orgs.get(e.org_id) else None
                if ends and 0 <= (ends - now).days <= 7:
                    counts["trials_expiring"] += 1
    except Exception as exc:  # infra down (no DB in CI) — log, don't crash the worker
        log.warning("reminder sweep skipped: %s", exc)
    log.info("reminder sweep: %s", counts)
    return counts


async def startup(ctx) -> None:
    log.info("worker startup phase 9")


async def shutdown(ctx) -> None:
    log.info("worker shutdown")


class WorkerSettings:
    functions = [send_due_reminders]
    cron_jobs = [cron(send_due_reminders, hour=7, minute=0)]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
