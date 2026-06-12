import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, Enum, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPKMixin, TimestampMixin


class QueueStatus(str, enum.Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    WAITING = "waiting"
    DOWNLOADING = "downloading"
    EDITING = "editing"
    UPLOADING = "uploading"
    SUBMITTING = "submitting"
    COMPLETED = "completed"
    RETRYING = "retrying"
    FAILED = "failed"
    FORCE_STOPPED = "force_stopped"
    REJECTED = "rejected"
    COOKIE_EXPIRED = "cookie_expired"


class RejectionReason(str, enum.Enum):
    TOO_SHORT = "too_short"
    DUPLICATE = "duplicate"
    QUEUE_FULL = "queue_full"
    INVALID_URL = "invalid_url"


class QueueItem(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "queue_items"

    automation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("automations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    source_url: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[QueueStatus] = mapped_column(
        Enum(QueueStatus, name="queue_status"), default=QueueStatus.DRAFT, index=True
    )
    rejection_reason: Mapped[Optional[RejectionReason]] = mapped_column(
        Enum(RejectionReason, name="rejection_reason"), nullable=True
    )

    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    uploaded_reel_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
