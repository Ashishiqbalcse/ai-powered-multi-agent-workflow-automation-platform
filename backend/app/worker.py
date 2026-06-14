from __future__ import annotations

import asyncio

from celery import Celery

from app.core.config import get_settings
from app.services.run_service import RunService


settings = get_settings()

celery_app = Celery(
    "multi_agent_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


@celery_app.task(name="runs.execute")
def execute_run_task(run_id: str) -> None:
    asyncio.run(RunService().execute_run(run_id))

