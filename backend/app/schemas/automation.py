import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.automation import Platform, LogoPosition, AutomationStatus


class AutomationBase(BaseModel):
    name: str
    instagram_account_id: Optional[uuid.UUID] = None
    platform: Platform = Platform.INSTAGRAM

    min_reel_duration_seconds: int = 0

    logo_position: LogoPosition = LogoPosition.BOTTOM_RIGHT
    logo_size_percent: float = 20.0
    logo_opacity_percent: float = 100.0
    chroma_key_color: Optional[str] = None

    caption_template: Optional[str] = None

    daily_upload_target: int = 5
    night_mode_start: str = "00:00"
    night_mode_end: str = "06:00"
    timezone: str = "Asia/Kolkata"

    queue_capacity: int = 250

    clipster_submission_url: Optional[str] = None
    proxy_url: Optional[str] = None


class AutomationCreate(AutomationBase):
    pass


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    instagram_account_id: Optional[uuid.UUID] = None
    status: Optional[AutomationStatus] = None

    min_reel_duration_seconds: Optional[int] = None

    logo_position: Optional[LogoPosition] = None
    logo_size_percent: Optional[float] = None
    logo_opacity_percent: Optional[float] = None
    chroma_key_color: Optional[str] = None

    caption_template: Optional[str] = None

    daily_upload_target: Optional[int] = None
    night_mode_start: Optional[str] = None
    night_mode_end: Optional[str] = None
    timezone: Optional[str] = None

    clipster_submission_url: Optional[str] = None
    clipster_cookies: Optional[str] = None
    proxy_url: Optional[str] = None


class AutomationOut(AutomationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: AutomationStatus
    logo_file_path: Optional[str] = None
    logo_type: Optional[str] = None
    clipster_error: Optional[str] = None
    clipster_cookies_encrypted: Optional[str] = Field(default=None, exclude=True)

    @computed_field
    @property
    def has_clipster_cookies(self) -> bool:
        return bool(self.clipster_cookies_encrypted)
