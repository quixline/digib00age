"""
digib00age — Sort by Filename Processing Tool Router (ADMIN_SPEC.md §11.5).
Moves each CBZ/CBR file directly inside a chosen folder into its own
same-named subfolder — ported from the standalone `create-folders-from-file.py`
script. Background job + polling progress, mirroring
routers/processing_folder.py's /run + /status shape (single-folder
operation, no working-file-list — the folder itself is the only input).

GET    /api/admin/filename-sort/browse    Directory listing (no path = library_root)
GET    /api/admin/filename-sort/drives    Drive-letter listing ("This PC")
POST   /api/admin/filename-sort/run       Run Now (background)
GET    /api/admin/filename-sort/status    Poll progress
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request

from backend import file_picker, filename_sort_log
from backend.auth import is_local_request
from backend.config import get_library_root
from backend.filename_sort import FilenameSortResult, sort_by_filename


def _require_local(request: Request) -> None:
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})


router = APIRouter(tags=["filename-sort"], dependencies=[Depends(_require_local)])


# ---------------------------------------------------------------------------
# Folder picker — same shared picker/backend as every other Processing Tool
# ---------------------------------------------------------------------------

@router.get("/filename-sort/browse")
def browse_directory(path: str = None):
    target = path or get_library_root()
    try:
        return file_picker.list_directory(target)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Directory not found")
    except PermissionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/filename-sort/drives")
def list_drives():
    return {"drives": file_picker.list_drives()}


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

@dataclass
class FilenameSortProgress:
    running: bool = False
    result: Optional[dict] = None
    error: Optional[str] = None
    finished_at: Optional[datetime] = None


filename_sort_progress = FilenameSortProgress()


def _run(folder: str, auto: bool = False) -> None:
    global filename_sort_progress
    filename_sort_progress = FilenameSortProgress(running=True)

    result: FilenameSortResult = sort_by_filename(folder)

    if result.error:
        # Folder-not-found/unreachable path — clean error, nothing logged as a run.
        filename_sort_progress.running = False
        filename_sort_progress.error = result.error
        filename_sort_progress.finished_at = datetime.now()
        return

    files = []
    for f in result.files:
        filename_sort_log.append_entry(f.filename, f.folder_name, error=f.error, auto=auto)
        files.append({"filename": f.filename, "folder_name": f.folder_name, "success": f.success, "error": f.error})

    filename_sort_progress.running = False
    filename_sort_progress.result = {
        "total": len(files),
        "moved": sum(1 for f in files if f["success"]),
        "folders": len({f["folder_name"] for f in files if f["success"]}),
        "files": files,
    }
    filename_sort_progress.finished_at = datetime.now()


@router.post("/filename-sort/run")
def run_now(background_tasks: BackgroundTasks, payload: dict = Body(...)):
    if filename_sort_progress.running:
        return {"message": "A run is already in progress", "running": True, "started": False}

    folder = (payload.get("folder") or "").strip()
    if not folder:
        raise HTTPException(status_code=400, detail="No folder selected")

    background_tasks.add_task(_run, folder, False)
    return {"message": "Sort by Filename started", "running": True, "started": True}


@router.get("/filename-sort/status")
def status():
    return {
        "running": filename_sort_progress.running,
        "result": filename_sort_progress.result,
        "error": filename_sort_progress.error,
        "finished_at": filename_sort_progress.finished_at.isoformat() if filename_sort_progress.finished_at else None,
    }
