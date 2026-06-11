"""Filter Engine tasks: fetch reel metadata via yt-dlp and validate against
automation rules (minimum duration, etc.) before a queue item can proceed."""

import logging

import yt_dlp

from app.models.automation import Automation
from app.models.queue_item import QueueItem, QueueStatus, RejectionReason
from app.workers.celery_app import celery_app
from app.workers.db import SessionLocal

logger = logging.getLogger(__name__)


def get_reel_duration_seconds(url: str) -> int:
    """Returns the duration of a reel in seconds using yt-dlp, without
    downloading the video."""
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = info.get("duration")
        if duration is None:
            raise ValueError("Could not determine video duration")
        return int(duration)


@celery_app.task(name="app.workers.tasks.filter_tasks.fetch_reel_metadata", bind=True, max_retries=2)
def fetch_reel_metadata(self, queue_item_id: str) -> None:
    """Fetches duration for a queue item's source_url.

    - If the URL is invalid / metadata can't be fetched: REJECTED, INVALID_URL
      (after retries).
    - If duration < automation.min_reel_duration_seconds: REJECTED, TOO_SHORT.
    - Otherwise: stores duration_seconds and triggers the scheduler so the
      item gets a scheduled_at slot.
    """
    db = SessionLocal()
    try:
        item = db.get(QueueItem, queue_item_id)
        if item is None:
            return

        automation = db.get(Automation, item.automation_id)

        try:
            duration = get_reel_duration_seconds(item.source_url)
        except Exception as exc:
            logger.warning("Failed to fetch metadata for %s: %s", item.source_url, exc)
            try:
                raise self.retry(exc=exc, countdown=30)
            except self.MaxRetriesExceededError:
                item.status = QueueStatus.REJECTED
                item.rejection_reason = RejectionReason.INVALID_URL
                item.last_error = str(exc)
                db.commit()
                return

        item.duration_seconds = duration

        if duration < automation.min_reel_duration_seconds:
            item.status = QueueStatus.REJECTED
            item.rejection_reason = RejectionReason.TOO_SHORT
            db.commit()
            return

        db.commit()

        from app.workers.tasks.pipeline_tasks import assign_schedule
        assign_schedule.delay(str(item.id))
    finally:
        db.close()
