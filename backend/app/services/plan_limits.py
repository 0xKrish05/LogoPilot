from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation import Automation
from app.models.plan import Plan
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User


async def get_active_plan(db: AsyncSession, user: User) -> Plan:
    """Returns the user's currently active plan (trial or paid).
    Falls back to the lowest-tier active plan if no subscription exists yet."""
    result = await db.execute(
        select(Plan)
        .join(Subscription, Subscription.plan_id == Plan.id)
        .where(
            Subscription.user_id == user.id,
            Subscription.status.in_([SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE]),
        )
    )
    plan = result.scalar_one_or_none()
    if plan is not None:
        return plan

    fallback = await db.execute(
        select(Plan).where(Plan.is_trial.is_(True), Plan.is_active.is_(True)).limit(1)
    )
    plan = fallback.scalar_one_or_none()
    if plan is None:
        raise RuntimeError("No trial plan configured. Seed default plans first.")
    return plan


async def count_user_automations(db: AsyncSession, user: User) -> int:
    result = await db.execute(
        select(func.count(Automation.id)).where(Automation.user_id == user.id)
    )
    return result.scalar_one()


async def count_user_uploads_today(db: AsyncSession, user: User) -> int:
    """Counts uploads (queue items that reached UPLOADING or beyond) across all
    of the user's automations today. Upload limits are global per account."""
    from datetime import datetime, timezone
    from app.models.queue_item import QueueItem, QueueStatus

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(QueueItem.id)).where(
            QueueItem.user_id == user.id,
            QueueItem.status.in_(
                [QueueStatus.UPLOADING, QueueStatus.SUBMITTING, QueueStatus.COMPLETED]
            ),
            QueueItem.processing_started_at >= today_start,
        )
    )
    return result.scalar_one()
