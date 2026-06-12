import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.automation import Automation
from app.models.queue_item import QueueItem, QueueStatus
from app.models.user import User
from app.schemas.queue_item import BulkUrlSubmission, BulkUrlResult, QueueItemOut, ScheduleUpdate
from app.services.filter_engine import filter_and_enqueue_urls

router = APIRouter(prefix="/automations/{automation_id}/queue", tags=["queue"])

ALLOWED_THUMBNAIL_TYPES = {"png", "jpg", "jpeg", "webp"}


@router.get("", response_model=list[QueueItemOut])
async def list_queue_items(
    automation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_owned_automation(db, automation_id, user)
    result = await db.execute(
        select(QueueItem)
        .where(QueueItem.automation_id == automation_id)
        .order_by(QueueItem.scheduled_at.asc().nulls_last(), QueueItem.created_at.asc())
    )
    return result.scalars().all()


@router.post("", response_model=BulkUrlResult)
async def submit_urls(
    automation_id: uuid.UUID,
    payload: BulkUrlSubmission,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if len(payload.urls) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A maximum of 100 URLs may be submitted per batch.",
        )

    automation = await _get_owned_automation(db, automation_id, user)
    return await filter_and_enqueue_urls(db, automation, payload.urls)


@router.patch("/{queue_item_id}/schedule", response_model=QueueItemOut)
async def update_schedule(
    automation_id: uuid.UUID,
    queue_item_id: uuid.UUID,
    payload: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_owned_automation(db, automation_id, user)
    item = await _get_queue_item(db, automation_id, queue_item_id)

    if item.status not in (QueueStatus.QUEUED, QueueStatus.WAITING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule can only be edited before processing begins.",
        )

    item.scheduled_at = payload.scheduled_at
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/{queue_item_id}/retry", response_model=QueueItemOut)
async def retry_queue_item(
    automation_id: uuid.UUID,
    queue_item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_owned_automation(db, automation_id, user)
    item = await _get_queue_item(db, automation_id, queue_item_id)

    retryable = (QueueStatus.FORCE_STOPPED, QueueStatus.FAILED, QueueStatus.COOKIE_EXPIRED)
    if item.status not in retryable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed, force-stopped or cookie-expired items can be manually retried.",
        )

    item.retry_count = 0
    item.last_error = None

    if item.uploaded_reel_url:
        # Already published to Instagram — never re-upload a duplicate;
        # resume at the Clipster submission stage.
        item.status = QueueStatus.SUBMITTING
        await db.commit()
        await db.refresh(item)
        from app.workers.tasks.pipeline_tasks import submit_to_clipster
        submit_to_clipster.delay(str(item.id))
    else:
        item.status = QueueStatus.QUEUED
        await db.commit()
        await db.refresh(item)

    return item


@router.post("/{queue_item_id}/thumbnail", response_model=QueueItemOut)
async def upload_thumbnail(
    automation_id: uuid.UUID,
    queue_item_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_owned_automation(db, automation_id, user)
    item = await _get_queue_item(db, automation_id, queue_item_id)

    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in ALLOWED_THUMBNAIL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported thumbnail file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_THUMBNAIL_TYPES))}.",
        )

    thumbs_dir = Path(settings.assets_storage_path) / "thumbnails"
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    for old in thumbs_dir.glob(f"{item.id}.*"):
        old.unlink(missing_ok=True)

    dest = thumbs_dir / f"{item.id}.{ext}"
    dest.write_bytes(await file.read())

    item.thumbnail_path = str(dest)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/{queue_item_id}/thumbnail")
async def get_thumbnail(
    automation_id: uuid.UUID,
    queue_item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    # Unauthenticated so it can be used directly as an <img src>; the
    # queue item id is an unguessable UUID.
    result = await db.execute(
        select(QueueItem).where(QueueItem.id == queue_item_id, QueueItem.automation_id == automation_id)
    )
    item = result.scalar_one_or_none()
    if item is None or not item.thumbnail_path or not Path(item.thumbnail_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No thumbnail available")
    return FileResponse(item.thumbnail_path)


async def _get_owned_automation(db: AsyncSession, automation_id: uuid.UUID, user: User) -> Automation:
    result = await db.execute(
        select(Automation).where(Automation.id == automation_id, Automation.user_id == user.id)
    )
    automation = result.scalar_one_or_none()
    if automation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")
    return automation


async def _get_queue_item(db: AsyncSession, automation_id: uuid.UUID, queue_item_id: uuid.UUID) -> QueueItem:
    result = await db.execute(
        select(QueueItem).where(QueueItem.id == queue_item_id, QueueItem.automation_id == automation_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue item not found")
    return item
