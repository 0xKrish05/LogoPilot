"""Core processing pipeline: schedule -> download -> edit -> upload -> submit.

Each stage is a separate Celery task routed to its own queue so worker pools
can be scaled independently. Stages chain via .delay() on success, or
schedule a retry / mark FORCE_STOPPED on repeated failure.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

import yt_dlp
from sqlalchemy import select

from app.core.config import settings
from app.models.automation import Automation, AutomationStatus
from app.models.platform_settings import PlatformSettings
from app.models.queue_item import QueueItem, QueueStatus
from app.services.edit_engine import apply_logo_overlay, generate_thumbnail
from app.services.media_storage import cleanup_item_dir, item_dir
from app.services.scheduler_sync import schedule_new_item_sync
from app.services.url_utils import sanitize_url
from app.workers.celery_app import celery_app
from app.workers.db import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.pipeline_tasks.assign_schedule")
def assign_schedule(queue_item_id: str) -> None:
    """Called after the filter engine approves an item. Gives it a
    scheduled_at slot via the Scheduling Engine."""
    db = SessionLocal()
    try:
        item = db.get(QueueItem, queue_item_id)
        if item is None:
            return
        automation = db.get(Automation, item.automation_id)
        schedule_new_item_sync(db, automation, item)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.pipeline_tasks.dispatch_due_items")
def dispatch_due_items() -> None:
    """Periodic task (every 30s). Finds QueueItems with status=QUEUED and
    scheduled_at <= now, marks them WAITING, and dispatches download_reel.

    Also rescues items stranded in WAITING for over 10 minutes — their
    dispatched task was lost (e.g. Redis restarted during a deploy) and no
    worker will ever pick them up otherwise."""
    from datetime import timedelta

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        due_items = db.execute(
            select(QueueItem).where(
                QueueItem.status == QueueStatus.QUEUED,
                QueueItem.scheduled_at <= now,
            )
        ).scalars().all()

        for item in due_items:
            item.status = QueueStatus.WAITING
            db.commit()
            download_reel.delay(str(item.id))

        stranded = db.execute(
            select(QueueItem).where(
                QueueItem.status == QueueStatus.WAITING,
                QueueItem.updated_at <= now - timedelta(minutes=10),
            )
        ).scalars().all()

        for item in stranded:
            logger.warning("Re-dispatching stranded WAITING item %s", item.id)
            item.updated_at = now  # reset the 10-minute window
            db.commit()
            download_reel.delay(str(item.id))
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.pipeline_tasks.download_reel", bind=True, max_retries=3)
def download_reel(self, queue_item_id: str) -> None:
    """Downloads the source reel via yt-dlp into TEMP_STORAGE_PATH.
    On success -> status=EDITING, dispatches edit_reel.
    On failure -> retry, then FORCE_STOPPED + admin notification."""
    db = SessionLocal()
    try:
        item = db.get(QueueItem, queue_item_id)
        if item is None:
            return

        item.status = QueueStatus.DOWNLOADING
        item.processing_started_at = item.processing_started_at or datetime.now(timezone.utc)
        db.commit()

        work_dir = item_dir(str(item.id))
        output_template = str(work_dir / "source.%(ext)s")

        ydl_opts = {
            "outtmpl": output_template,
            "format": "mp4/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([sanitize_url(item.source_url)])
        except Exception as exc:
            return _retry_or_force_stop(self, db, item, exc, "download")

        downloaded = next(work_dir.glob("source.*"), None)
        if downloaded is None:
            return _retry_or_force_stop(self, db, item, RuntimeError("Download produced no file"), "download")

        if not item.thumbnail_path:
            automation = db.get(Automation, item.automation_id)
            if automation and automation.thumbnail_path and Path(automation.thumbnail_path).exists():
                # A single custom thumbnail (set in Settings) is reused for every reel.
                item.thumbnail_path = automation.thumbnail_path
            else:
                try:
                    thumbs_dir = Path(settings.assets_storage_path) / "thumbnails"
                    thumbs_dir.mkdir(parents=True, exist_ok=True)
                    thumb_path = thumbs_dir / f"{item.id}.jpg"
                    generate_thumbnail(downloaded, thumb_path)
                    item.thumbnail_path = str(thumb_path)
                except Exception:
                    logger.exception("Failed to auto-generate thumbnail for queue item %s", item.id)

        item.status = QueueStatus.EDITING
        db.commit()

        edit_reel.delay(str(item.id))
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.pipeline_tasks.edit_reel", bind=True, max_retries=3)
def edit_reel(self, queue_item_id: str) -> None:
    """Applies the automation's logo overlay via FFmpeg (position, size,
    opacity, chroma key, looping animated logos to match reel duration).
    On success -> status=UPLOADING, dispatches upload_reel."""
    db = SessionLocal()
    try:
        item = db.get(QueueItem, queue_item_id)
        if item is None:
            return
        automation = db.get(Automation, item.automation_id)

        work_dir = item_dir(str(item.id))
        source_video = next(work_dir.glob("source.*"), None)
        if source_video is None:
            return _retry_or_force_stop(self, db, item, RuntimeError("Source video missing"), "edit")

        if not automation.logo_file_path:
            return _retry_or_force_stop(self, db, item, RuntimeError("Automation has no logo configured"), "edit")

        logo_path = Path(automation.logo_file_path)
        output_video = work_dir / "edited.mp4"

        try:
            apply_logo_overlay(automation, source_video, logo_path, output_video)
        except Exception as exc:
            return _retry_or_force_stop(self, db, item, exc, "edit")

        item.status = QueueStatus.UPLOADING
        db.commit()

        upload_reel.delay(str(item.id))
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.pipeline_tasks.upload_reel", bind=True, max_retries=3)
def upload_reel(self, queue_item_id: str) -> None:
    """Uploads the edited video to the connected Instagram account via the
    Instagram Graph API (Content Publishing). Stores uploaded_reel_url on
    success -> status=SUBMITTING, dispatches submit_to_clipster.
    On 3rd failure -> status=FORCE_STOPPED + admin notification."""
    from app.core.security import decrypt_secret
    from app.models.instagram_account import InstagramAccount
    from app.services.instagram_publish import publish_reel

    db = SessionLocal()
    try:
        item = db.get(QueueItem, queue_item_id)
        if item is None:
            return
        automation = db.get(Automation, item.automation_id)

        if not automation.instagram_account_id:
            return _retry_or_force_stop(
                self, db, item,
                RuntimeError("No Instagram account connected to this automation"),
                "upload",
            )
        account = db.get(InstagramAccount, automation.instagram_account_id)
        if account is None or not account.is_active:
            return _retry_or_force_stop(
                self, db, item,
                RuntimeError("Connected Instagram account is missing or inactive"),
                "upload",
            )

        edited = item_dir(str(item.id)) / "edited.mp4"
        if not edited.exists():
            return _retry_or_force_stop(self, db, item, RuntimeError("Edited video missing"), "upload")

        public_base = settings.next_public_api_url.rstrip("/")
        if not public_base:
            return _retry_or_force_stop(
                self, db, item,
                RuntimeError("NEXT_PUBLIC_API_URL is not configured — cannot expose video to Instagram"),
                "upload",
            )
        video_url = f"{public_base}/api/media/{item.id}/reel.mp4"
        cover_url = (
            f"{public_base}/api/automations/{automation.id}/queue/{item.id}/thumbnail"
            if item.thumbnail_path and Path(item.thumbnail_path).exists()
            else None
        )

        try:
            _media_id, permalink = publish_reel(
                ig_user_id=account.ig_user_id,
                access_token=decrypt_secret(account.access_token_encrypted),
                video_url=video_url,
                caption=automation.caption_template or None,
                cover_url=cover_url,
            )
        except Exception as exc:
            return _retry_or_force_stop(self, db, item, exc, "upload")

        item.uploaded_reel_url = permalink
        item.status = QueueStatus.SUBMITTING
        item.retry_count = 0  # fresh retry budget for the submission stage
        db.commit()

        submit_to_clipster.delay(str(item.id))
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.pipeline_tasks.submit_to_clipster", bind=True, max_retries=3)
def submit_to_clipster(self, queue_item_id: str) -> None:
    """Loads the automation's encrypted Clipster cookies via Playwright,
    opens clipster_submission_url, and submits uploaded_reel_url.
    On success -> status=COMPLETED, deletes all temp media for this item.
    On cookie expiration -> status=COOKIE_EXPIRED (no retry burned) and the
    automation is flagged so the user uploads fresh cookies.
    On 3rd failure -> FORCE_STOPPED + admin notification."""
    from app.core.security import decrypt_secret
    from app.models.automation import AutomationStatus as AutoStatus
    from app.services.clipster import (
        ClipsterCookiesExpired,
        sanitize_cookies,
        submit_reel,
    )
    from app.services.cookies import parse_netscape_cookies

    db = SessionLocal()
    try:
        item = db.get(QueueItem, queue_item_id)
        if item is None:
            return
        automation = db.get(Automation, item.automation_id)

        # Upload-only automation: no submission configured -> done.
        if not automation.clipster_submission_url:
            item.status = QueueStatus.COMPLETED
            item.completed_at = datetime.now(timezone.utc)
            db.commit()
            cleanup_item_dir(str(item.id))
            return

        if not automation.clipster_cookies_encrypted:
            item.status = QueueStatus.COOKIE_EXPIRED
            item.last_error = "[submit] No Clipster cookies uploaded — add cookies in Settings."
            automation.clipster_error = "Clipster cookies missing — upload a cookies.txt in Settings."
            automation.status = AutoStatus.ERROR
            db.commit()
            return

        cookies = sanitize_cookies(
            parse_netscape_cookies(decrypt_secret(automation.clipster_cookies_encrypted))
        )

        try:
            submit_reel(
                cookies=cookies,
                submission_url=automation.clipster_submission_url,
                reel_url=item.uploaded_reel_url,
                proxy_url=automation.proxy_url,
            )
        except ClipsterCookiesExpired as exc:
            # Cookie expiry never consumes retry attempts.
            item.status = QueueStatus.COOKIE_EXPIRED
            item.last_error = f"[submit] {exc}"
            automation.clipster_error = str(exc)
            automation.status = AutoStatus.ERROR
            db.commit()
            return
        except Exception as exc:
            return _retry_or_force_stop(self, db, item, exc, "submit")

        item.status = QueueStatus.COMPLETED
        item.completed_at = datetime.now(timezone.utc)
        item.last_error = None
        automation.clipster_error = None
        db.commit()
        cleanup_item_dir(str(item.id))
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.pipeline_tasks.cleanup_old_logs")
def cleanup_old_logs() -> None:
    """Periodic task (hourly). Deletes orphaned temp media directories for
    queue items that finished (COMPLETED/FORCE_STOPPED/REJECTED)."""
    db = SessionLocal()
    try:
        finished = db.execute(
            select(QueueItem).where(
                QueueItem.status.in_(
                    [QueueStatus.COMPLETED, QueueStatus.FORCE_STOPPED, QueueStatus.REJECTED]
                )
            )
        ).scalars().all()
        for item in finished:
            cleanup_item_dir(str(item.id))
    finally:
        db.close()


def _retry_or_force_stop(task, db, item: QueueItem, exc: Exception, stage: str):
    settings_row = db.execute(select(PlatformSettings).limit(1)).scalar_one_or_none()
    max_retries = settings_row.max_upload_retries if settings_row else 3

    item.last_error = f"[{stage}] {exc}"
    item.retry_count += 1

    if item.retry_count > max_retries:
        item.status = QueueStatus.FORCE_STOPPED
        db.commit()
        logger.error("Queue item %s force-stopped at %s: %s", item.id, stage, exc)
        # TODO: send admin notification (in-app notification system)
        return

    item.status = QueueStatus.RETRYING
    db.commit()
    raise task.retry(exc=exc, countdown=60 * item.retry_count)
