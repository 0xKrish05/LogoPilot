"""Scheduling Engine.

Generates natural-looking posting schedules for queued reels:
- The very first queued reel (across the whole automation) is scheduled
  ~1 minute after approval.
- Remaining reels are distributed day-by-day according to
  daily_target_overrides (per-day targets for the next 5 days) and fall back
  to daily_upload_target for any day beyond that / without an override.
- Each day's items are spread evenly across that day (from "now" for today,
  from midnight for future days), with a small jitter.
- Night Mode (a window in the automation's own timezone) is excluded from
  scheduling.
- Changing daily_upload_target, daily_target_overrides, or night mode
  triggers a reschedule of all queued/waiting items that haven't started
  processing.
"""

import random
from datetime import datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation import Automation
from app.models.queue_item import QueueItem, QueueStatus


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def _automation_tz(automation: Automation) -> ZoneInfo:
    try:
        return ZoneInfo(automation.timezone)
    except Exception:
        return ZoneInfo("UTC")


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


def _day_capacity(automation: Automation, day_index: int) -> int:
    """Upload target for the given day (0 = today, 1 = tomorrow, ...).

    The next 5 days (index 0-4) can be overridden individually via
    daily_target_overrides. Any day beyond that, or a day with no override
    set, falls back to daily_upload_target (default 5)."""
    overrides = automation.daily_target_overrides or []
    if day_index < len(overrides) and overrides[day_index] is not None:
        return max(0, int(overrides[day_index]))
    return max(1, automation.daily_upload_target)


def compute_schedule_times(
    automation: Automation, count: int, now: datetime | None = None
) -> list[datetime]:
    """Returns `count` UTC datetimes for upcoming queue items, distributed
    across days according to _day_capacity, in chronological order.

    The very first slot overall is always now + 1 minute. Remaining slots
    within a day are spread evenly across that day's active window (from
    `now` for today, from midnight for future days), with jitter, then
    nudged past Night Mode windows."""
    if count <= 0:
        return []

    now = now or datetime.now(timezone.utc)
    tz = _automation_tz(automation)
    now_local = now.astimezone(tz)

    times: list[datetime] = []
    remaining = count
    day_index = 0
    cursor_date = now_local.date()

    while remaining > 0:
        capacity = _day_capacity(automation, day_index)
        if capacity > 0:
            take = min(capacity, remaining)
            day_start = datetime.combine(cursor_date, time(0, 0), tzinfo=tz)
            day_end = day_start + timedelta(days=1)
            window_start = max(now_local, day_start) if day_index == 0 else day_start
            span_seconds = max((day_end - window_start).total_seconds(), 60)
            spacing_seconds = span_seconds / take

            for i in range(take):
                if not times:
                    slot_local = now_local + timedelta(minutes=1)
                else:
                    jitter = (
                        random.randint(-int(spacing_seconds * 0.2), int(spacing_seconds * 0.2))
                        if spacing_seconds > 240
                        else 0
                    )
                    slot_local = window_start + timedelta(seconds=spacing_seconds * i + jitter)
                    if slot_local < now_local:
                        slot_local = now_local + timedelta(minutes=1)

                slot_local = _next_available_time(slot_local, automation)
                times.append(slot_local.astimezone(timezone.utc))
                remaining -= 1
                if remaining == 0:
                    break

        cursor_date += timedelta(days=1)
        day_index += 1

    return times


async def schedule_new_item(db: AsyncSession, automation: Automation, item: QueueItem) -> None:
    """Schedules a single newly-approved item. Its position is its index
    among all pending items (ordered by creation), so the very first item
    ever gets now + 1 minute and later items fall into later day-slots
    according to daily_target_overrides / daily_upload_target."""
    position = await _count_pending(db, automation, exclude_id=item.id)
    times = compute_schedule_times(automation, position + 1)

    item.scheduled_at = times[position]
    item.status = QueueStatus.QUEUED
    await db.commit()


async def reschedule_pending_items(db: AsyncSession, automation: Automation) -> None:
    """Recomputes scheduled_at for all items that haven't begun processing,
    in original order, after daily_upload_target / overrides / night mode
    changes."""
    result = await db.execute(
        select(QueueItem)
        .where(
            QueueItem.automation_id == automation.id,
            QueueItem.status.in_([QueueStatus.QUEUED, QueueStatus.WAITING]),
        )
        .order_by(QueueItem.created_at.asc())
    )
    pending_items = result.scalars().all()

    times = compute_schedule_times(automation, len(pending_items))
    for item, scheduled_at in zip(pending_items, times):
        item.scheduled_at = scheduled_at

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
