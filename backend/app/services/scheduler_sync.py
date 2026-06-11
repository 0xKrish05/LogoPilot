"""Sync (Celery-worker-side) counterparts of app.services.scheduler.

Same scheduling rules (1-minute first slot, daily-target spacing, night mode
avoidance) but using a plain SQLAlchemy Session instead of AsyncSession."""

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.automation import Automation
from app.models.queue_item import QueueItem, QueueStatus
from app.services.scheduler import _next_available_time


def schedule_new_item_sync(db: Session, automation: Automation, item: QueueItem) -> None:
    now = datetime.now(timezone.utc)

    pending_count = db.execute(
        select(QueueItem).where(
            QueueItem.automation_id == automation.id,
            QueueItem.status.in_([QueueStatus.QUEUED, QueueStatus.WAITING]),
            QueueItem.id != item.id,
        )
    ).scalars().all()
    pending_count = len(pending_count)

    if pending_count == 0:
        scheduled_at = now + timedelta(minutes=1)
    else:
        spacing_minutes = max(1, int((24 * 60) / max(automation.daily_upload_target, 1)))
        jitter = random.randint(-spacing_minutes // 4, spacing_minutes // 4) if spacing_minutes > 4 else 0
        scheduled_at = now + timedelta(minutes=spacing_minutes * pending_count + jitter)

    item.scheduled_at = _next_available_time(scheduled_at, automation)
    item.status = QueueStatus.QUEUED
    db.commit()
