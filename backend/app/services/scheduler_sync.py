"""Sync (Celery-worker-side) counterpart of app.services.scheduler.

Same scheduling rules (1-minute first slot, day-by-day targets via
daily_target_overrides / daily_upload_target, night mode avoidance) but using
a plain SQLAlchemy Session instead of AsyncSession."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.automation import Automation
from app.models.queue_item import QueueItem, QueueStatus
from app.services.scheduler import compute_schedule_times


def schedule_new_item_sync(db: Session, automation: Automation, item: QueueItem) -> None:
    pending_count = len(
        db.execute(
            select(QueueItem).where(
                QueueItem.automation_id == automation.id,
                QueueItem.status.in_([QueueStatus.QUEUED, QueueStatus.WAITING]),
                QueueItem.id != item.id,
            )
        ).scalars().all()
    )

    times = compute_schedule_times(automation, pending_count + 1)

    item.scheduled_at = times[pending_count]
    item.status = QueueStatus.QUEUED
    db.commit()
