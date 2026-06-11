"""Scheduling Engine.

Generates natural-looking posting schedules for queued reels:
- First approved reel is scheduled ~1 minute after validation.
- Remaining reels are spread across the day according to daily_upload_target.
- Night Mode (a 6-hour window) is excluded from scheduling.
- Changing daily_upload_target or night mode triggers a reschedule of all
  queued/waiting items that haven't started processing.
"""

import random
from datetime import datetime, timedelta, time, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation import Automation
from app.models.queue_item import QueueItem, QueueStatus


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def _is_in_night_mode(dt: datetime, automation: Automation) -> bool:
    start = _parse_hhmm(automation.night_mode_start)
    end = _parse_hhmm(automation.night_mode_end)
    t = dt.time()
    if start <= end:
        return start <= t < end
    # Window wraps past midnight (e.g. 22:00 - 04:00)
    return t >= start or t < end


def _next_available_time(dt: datetime, automation: Automation) -> datetime:
    while _is_in_night_mode(dt, automation):
        dt += timedelta(minutes=5)
    return dt


async def schedule_new_item(db: AsyncSession, automation: Automation, item: QueueItem) -> None:
    """Schedules a single newly-approved item: first reel goes out in ~1
    minute, subsequent reels are spaced based on the daily target."""
    now = datetime.now(timezone.utc)

    pending_count = await _count_pending(db, automation, exclude_id=item.id)

    if pending_count == 0:
        scheduled_at = now + timedelta(minutes=1)
    else:
        spacing_minutes = max(1, int((24 * 60) / max(automation.daily_upload_target, 1)))
        jitter = random.randint(-spacing_minutes // 4, spacing_minutes // 4) if spacing_minutes > 4 else 0
        scheduled_at = now + timedelta(minutes=spacing_minutes * pending_count + jitter)

    item.scheduled_at = _next_available_time(scheduled_at, automation)
    item.status = QueueStatus.QUEUED
    await db.commit()


async def reschedule_pending_items(db: AsyncSession, automation: Automation) -> None:
    """Recomputes scheduled_at for all items that haven't begun processing,
    in original order, after daily_upload_target or night mode changes."""
    result = await db.execute(
        select(QueueItem)
        .where(
            QueueItem.automation_id == automation.id,
            QueueItem.status.in_([QueueStatus.QUEUED, QueueStatus.WAITING]),
        )
        .order_by(QueueItem.created_at.asc())
    )
    pending_items = result.scalars().all()

    now = datetime.now(timezone.utc)
    spacing_minutes = max(1, int((24 * 60) / max(automation.daily_upload_target, 1)))

    for index, item in enumerate(pending_items):
        if index == 0:
            scheduled_at = now + timedelta(minutes=1)
        else:
            jitter = random.randint(-spacing_minutes // 4, spacing_minutes // 4) if spacing_minutes > 4 else 0
            scheduled_at = now + timedelta(minutes=spacing_minutes * index + jitter)

        item.scheduled_at = _next_available_time(scheduled_at, automation)

    await db.commit()


async def _count_pending(db: AsyncSession, automation: Automation, exclude_id=None) -> int:
    query = select(QueueItem).where(
        QueueItem.automation_id == automation.id,
        QueueItem.status.in_([QueueStatus.QUEUED, QueueStatus.WAITING]),
    )
    if exclude_id is not None:
        query = query.where(QueueItem.id != exclude_id)

    result = await db.execute(query)
    return len(result.scalars().all())
