"""Helpers for the temporary media working directory.

The platform never persists downloaded/edited reels: each queue item gets
its own subdirectory under TEMP_STORAGE_PATH that is wiped after the item
reaches COMPLETED or FORCE_STOPPED.
"""

import shutil
from pathlib import Path

from app.core.config import settings


def item_dir(queue_item_id: str) -> Path:
    path = Path(settings.temp_storage_path) / str(queue_item_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup_item_dir(queue_item_id: str) -> None:
    path = Path(settings.temp_storage_path) / str(queue_item_id)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
