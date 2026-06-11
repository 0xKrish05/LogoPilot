import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.queue_item import QueueStatus, RejectionReason


class QueueItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    automation_id: uuid.UUID
    source_url: str
    status: QueueStatus
    rejection_reason: Optional[RejectionReason] = None
    duration_seconds: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    uploaded_reel_url: Optional[str] = None
    retry_count: int
    last_error: Optional[str] = None


class BulkUrlSubmission(BaseModel):
    urls: list[str]


class BulkUrlResult(BaseModel):
    approved: list[QueueItemOut]
    rejected: list[dict]


class ScheduleUpdate(BaseModel):
    scheduled_at: datetime
