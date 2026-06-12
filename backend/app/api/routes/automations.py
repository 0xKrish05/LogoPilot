import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import encrypt_secret
from app.db.session import get_db
from app.models.automation import Automation
from app.models.user import User
from app.schemas.automation import AutomationCreate, AutomationOut, AutomationUpdate
from app.services.plan_limits import get_active_plan, count_user_automations

router = APIRouter(prefix="/automations", tags=["automations"])

ALLOWED_LOGO_TYPES = {"png", "jpg", "jpeg", "webp", "gif", "mp4", "webm"}


@router.get("", response_model=list[AutomationOut])
async def list_automations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Automation).where(Automation.user_id == user.id))
    return result.scalars().all()


@router.post("", response_model=AutomationOut, status_code=status.HTTP_201_CREATED)
async def create_automation(
    payload: AutomationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plan = await get_active_plan(db, user)
    current_count = await count_user_automations(db, user)
    if current_count >= plan.max_automations:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Automation limit reached for your plan ({plan.max_automations}).",
        )

    automation = Automation(user_id=user.id, **payload.model_dump())
    db.add(automation)
    await db.commit()
    await db.refresh(automation)
    return automation


@router.get("/{automation_id}", response_model=AutomationOut)
async def get_automation(
    automation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    automation = await _get_owned_automation(db, automation_id, user)
    return automation


@router.patch("/{automation_id}", response_model=AutomationOut)
async def update_automation(
    automation_id: uuid.UUID,
    payload: AutomationUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    automation = await _get_owned_automation(db, automation_id, user)

    schedule_affecting_fields = {"daily_upload_target", "night_mode_start", "night_mode_end"}
    updates = payload.model_dump(exclude_unset=True)
    needs_reschedule = any(f in updates for f in schedule_affecting_fields)

    clipster_cookies = updates.pop("clipster_cookies", None)
    if clipster_cookies is not None:
        automation.clipster_cookies_encrypted = encrypt_secret(clipster_cookies) if clipster_cookies else None

    for field, value in updates.items():
        setattr(automation, field, value)

    await db.commit()
    await db.refresh(automation)

    if needs_reschedule:
        from app.services.scheduler import reschedule_pending_items
        await reschedule_pending_items(db, automation)

    return automation


@router.post("/{automation_id}/logo", response_model=AutomationOut)
async def upload_logo(
    automation_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    automation = await _get_owned_automation(db, automation_id, user)

    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in ALLOWED_LOGO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported logo file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_LOGO_TYPES))}.",
        )

    logos_dir = Path(settings.assets_storage_path) / "logos"
    logos_dir.mkdir(parents=True, exist_ok=True)

    # Remove any previous logo for this automation (different extension).
    for old in logos_dir.glob(f"{automation.id}.*"):
        old.unlink(missing_ok=True)

    dest = logos_dir / f"{automation.id}.{ext}"
    contents = await file.read()
    dest.write_bytes(contents)

    automation.logo_file_path = str(dest)
    automation.logo_type = ext

    await db.commit()
    await db.refresh(automation)
    return automation


@router.get("/{automation_id}/logo")
async def get_logo(
    automation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    # Unauthenticated so it can be used directly as an <img src>; the
    # automation id is an unguessable UUID.
    result = await db.execute(select(Automation).where(Automation.id == automation_id))
    automation = result.scalar_one_or_none()
    if automation is None or not automation.logo_file_path or not Path(automation.logo_file_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No logo uploaded")
    return FileResponse(automation.logo_file_path)


@router.delete("/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    automation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    automation = await _get_owned_automation(db, automation_id, user)
    await db.delete(automation)
    await db.commit()


async def _get_owned_automation(db: AsyncSession, automation_id: uuid.UUID, user: User) -> Automation:
    result = await db.execute(
        select(Automation).where(Automation.id == automation_id, Automation.user_id == user.id)
    )
    automation = result.scalar_one_or_none()
    if automation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")
    return automation
