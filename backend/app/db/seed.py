"""Seeds default plans and platform settings on first startup.
Idempotent: safe to run on every container start."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import Plan
from app.models.platform_settings import PlatformSettings

DEFAULT_PLANS = [
    dict(
        code="trial",
        name="Trial",
        price_usd_monthly=0,
        max_automations=3,
        max_instagram_accounts=1,
        max_uploads_per_day=20,
        max_queue_size=250,
        is_trial=True,
        trial_duration_days=3,
    ),
    dict(
        code="starter",
        name="Starter",
        price_usd_monthly=19.99,
        max_automations=20,
        max_instagram_accounts=3,
        max_uploads_per_day=100,
        max_queue_size=250,
        is_trial=False,
        trial_duration_days=None,
    ),
    dict(
        code="pro",
        name="Pro",
        price_usd_monthly=35.99,
        max_automations=100,
        max_instagram_accounts=10,
        max_uploads_per_day=500,
        max_queue_size=500,
        is_trial=False,
        trial_duration_days=None,
    ),
]


async def seed_defaults(db: AsyncSession) -> None:
    for plan_data in DEFAULT_PLANS:
        result = await db.execute(select(Plan).where(Plan.code == plan_data["code"]))
        if result.scalar_one_or_none() is None:
            db.add(Plan(**plan_data))

    settings_result = await db.execute(select(PlatformSettings).limit(1))
    if settings_result.scalar_one_or_none() is None:
        db.add(PlatformSettings())

    await db.commit()
