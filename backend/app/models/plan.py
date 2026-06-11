from typing import Optional

from sqlalchemy import String, Integer, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPKMixin, TimestampMixin


class Plan(UUIDPKMixin, TimestampMixin, Base):
    """Admin-configurable subscription plan. Seeded with Trial/Starter/Pro
    defaults on first startup, but all values are editable at runtime."""

    __tablename__ = "plans"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    price_usd_monthly: Mapped[Numeric] = mapped_column(Numeric(10, 2), default=0)

    max_automations: Mapped[int] = mapped_column(Integer)
    max_instagram_accounts: Mapped[int] = mapped_column(Integer)
    max_uploads_per_day: Mapped[int] = mapped_column(Integer)
    max_queue_size: Mapped[int] = mapped_column(Integer)

    is_trial: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
