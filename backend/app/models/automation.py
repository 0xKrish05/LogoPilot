import enum
import uuid
from typing import Optional

from sqlalchemy import String, Integer, Float, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPKMixin, TimestampMixin


class Platform(str, enum.Enum):
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"  # coming soon
    TIKTOK = "tiktok"  # coming soon


class LogoPosition(str, enum.Enum):
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER = "center"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"
    FULL_OVERLAY = "full_overlay"


class AutomationStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"  # e.g. expired Clipster cookies


class Automation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "automations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    instagram_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instagram_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255))
    platform: Mapped[Platform] = mapped_column(
        Enum(Platform, name="platform"), default=Platform.INSTAGRAM
    )
    status: Mapped[AutomationStatus] = mapped_column(
        Enum(AutomationStatus, name="automation_status"),
        default=AutomationStatus.ACTIVE,
    )

    # Filter settings
    min_reel_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Logo / overlay settings
    logo_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    logo_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # png/mp4/webm/gif
    logo_position: Mapped[LogoPosition] = mapped_column(
        Enum(LogoPosition, name="logo_position"), default=LogoPosition.BOTTOM_RIGHT
    )
    logo_size_percent: Mapped[float] = mapped_column(Float, default=20.0)
    logo_opacity_percent: Mapped[float] = mapped_column(Float, default=100.0)
    chroma_key_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # e.g. #00FF00

    # Caption
    caption_template: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Single thumbnail applied to every reel uploaded by this automation.
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Scheduling
    daily_upload_target: Mapped[int] = mapped_column(Integer, default=5)
    # Per-day overrides for the next 5 days (index 0 = today, 1 = tomorrow, ...).
    # null entries (or days beyond index 4) fall back to daily_upload_target.
    daily_target_overrides: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    night_mode_start: Mapped[str] = mapped_column(String(5), default="00:00")  # HH:MM
    night_mode_end: Mapped[str] = mapped_column(String(5), default="06:00")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata")

    # Queue
    queue_capacity: Mapped[int] = mapped_column(Integer, default=250)

    # Clipster submission
    clipster_cookies_encrypted: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    clipster_submission_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    clipster_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Optional proxy
    proxy_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
