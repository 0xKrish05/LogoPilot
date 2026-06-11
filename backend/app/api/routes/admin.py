from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.automation import Automation
from app.models.queue_item import QueueItem, QueueStatus
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.models.platform_settings import PlatformSettings

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview")
async def admin_overview(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    total_users = await db.scalar(select(func.count(User.id)))
    trial_users = await db.scalar(
        select(func.count(Subscription.id)).where(Subscription.status == SubscriptionStatus.TRIAL)
    )
    active_subs = await db.scalar(
        select(func.count(Subscription.id)).where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    total_automations = await db.scalar(select(func.count(Automation.id)))
    queue_size = await db.scalar(
        select(func.count(QueueItem.id)).where(
            QueueItem.status.in_(
                [QueueStatus.QUEUED, QueueStatus.WAITING, QueueStatus.DOWNLOADING,
                 QueueStatus.EDITING, QueueStatus.UPLOADING, QueueStatus.SUBMITTING]
            )
        )
    )
    failed_jobs = await db.scalar(
        select(func.count(QueueItem.id)).where(QueueItem.status == QueueStatus.FORCE_STOPPED)
    )

    return {
        "total_users": total_users or 0,
        "trial_users": trial_users or 0,
        "active_subscriptions": active_subs or 0,
        "total_automations": total_automations or 0,
        "queue_size": queue_size or 0,
        "failed_jobs": failed_jobs or 0,
    }


@router.get("/settings")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(PlatformSettings).limit(1))
    settings_row = result.scalar_one_or_none()
    return settings_row


@router.patch("/settings")
async def update_settings(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(PlatformSettings).limit(1))
    settings_row = result.scalar_one_or_none()
    if settings_row is None:
        settings_row = PlatformSettings()
        db.add(settings_row)

    for field, value in payload.items():
        if hasattr(settings_row, field):
            setattr(settings_row, field, value)

    await db.commit()
    await db.refresh(settings_row)
    return settings_row
