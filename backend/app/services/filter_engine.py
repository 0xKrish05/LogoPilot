from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation import Automation
from app.models.queue_item import QueueItem, QueueStatus, RejectionReason
from app.schemas.queue_item import BulkUrlResult, QueueItemOut
from app.services.scheduler import schedule_new_item
from app.services.url_utils import sanitize_url


async def filter_and_enqueue_urls(db: AsyncSession, automation: Automation, urls: list[str]) -> BulkUrlResult:
    """Validates a batch of reel URLs against duration, duplicate, and queue
    capacity rules before admitting them to the scheduling queue.

    NOTE: duration lookups via yt-dlp happen here in production. For now this
    enqueues items in DRAFT/QUEUED status; the actual yt-dlp metadata fetch is
    performed asynchronously by a Celery task (see workers/tasks/filter.py)
    so the API response stays fast.
    """
    approved: list[QueueItem] = []
    rejected: list[dict] = []

    # Existing URLs for this automation (duplicate check)
    existing_result = await db.execute(
        select(QueueItem.source_url).where(QueueItem.automation_id == automation.id)
    )
    existing_urls = set(existing_result.scalars().all())

    # Current queue size (capacity check)
    queue_count_result = await db.execute(
        select(func.count(QueueItem.id)).where(
            QueueItem.automation_id == automation.id,
            QueueItem.status.notin_([QueueStatus.REJECTED, QueueStatus.COMPLETED, QueueStatus.FORCE_STOPPED]),
        )
    )
    current_queue_size = queue_count_result.scalar_one()

    seen_in_batch: set[str] = set()

    for url in urls:
        url = sanitize_url(url)
        if not url:
            continue

        if url in existing_urls or url in seen_in_batch:
            rejected.append({"url": url, "reason": RejectionReason.DUPLICATE.value})
            continue

        if current_queue_size >= automation.queue_capacity:
            rejected.append({"url": url, "reason": RejectionReason.QUEUE_FULL.value})
            continue

        item = QueueItem(
            automation_id=automation.id,
            user_id=automation.user_id,
            source_url=url,
            status=QueueStatus.QUEUED,
        )
        db.add(item)
        approved.append(item)
        seen_in_batch.add(url)
        current_queue_size += 1

    await db.commit()

    for item in approved:
        await db.refresh(item)
        await schedule_new_item(db, automation, item)

    return BulkUrlResult(
        approved=[QueueItemOut.model_validate(i) for i in approved],
        rejected=rejected,
    )
