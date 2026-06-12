import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{queue_item_id}/reel.mp4")
async def get_edited_reel(queue_item_id: uuid.UUID):
    # Unauthenticated: the Instagram Graph API must be able to download the
    # edited video from this URL during upload. The queue item id is an
    # unguessable UUID and the file is deleted right after publishing.
    path = Path(settings.temp_storage_path) / str(queue_item_id) / "edited.mp4"
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No edited reel available")
    return FileResponse(path, media_type="video/mp4", filename="reel.mp4")
