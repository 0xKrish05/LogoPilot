from sqlalchemy import String, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPKMixin, TimestampMixin


class PlatformSettings(UUIDPKMixin, TimestampMixin, Base):
    """Single-row table holding admin-configurable, runtime-editable
    platform-wide settings (no redeploy required)."""

    __tablename__ = "platform_settings"

    max_total_users: Mapped[int] = mapped_column(Integer, default=0)  # 0 = unlimited
    registration_closed_message: Mapped[str] = mapped_column(
        Text,
        default="Registrations are currently full. Contact us on Telegram: @yourhandle",
    )
    registrations_open: Mapped[bool] = mapped_column(Boolean, default=True)

    default_night_mode_start: Mapped[str] = mapped_column(String(5), default="00:00")
    default_night_mode_end: Mapped[str] = mapped_column(String(5), default="06:00")

    max_urls_per_batch: Mapped[int] = mapped_column(Integer, default=100)
    max_upload_retries: Mapped[int] = mapped_column(Integer, default=3)
    max_submission_retries: Mapped[int] = mapped_column(Integer, default=3)
    log_retention_days: Mapped[int] = mapped_column(Integer, default=30)
