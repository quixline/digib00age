"""
ComicVault — Move Series Folders / Move Singles Folders Processing Tool
Router (ADMIN_SPEC.md §11.7). Moves each immediate subfolder of a chosen
folder into its correct place in the library structure — the final stage
of processing before a library scan. Background job + polling progress,
mirroring routers/filename_sort.py's /run + /status shape. One router
serves both scripts (group="series"|"singles"), each with its own progress
singleton so a Series run and a Singles run can't collide on state.

GET    /api/admin/library-move/browse           Directory listing (no path = library_root)
GET    /api/admin/library-move/drives            Drive-letter listing ("This PC")
POST   /api/admin/library-move/run               Run Now (background) — body: {folder, group}
GET    /api/admin/library-move/status?group=...  Poll progress for that group
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Request

from backend import file_picker, series_move_log, singles_move_log
from backend.auth import is_local_request
from backend.config import get_library_root
from backend.database import SessionLocal
from backend.library_move import LibraryMoveResult, move_folders, sync_moved_paths_to_db


def _require_local(request: Request) -> None:
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})


router = APIRouter(tags=["library-move"], dependencies=[Depends(_require_local)])


# ---------------------------------------------------------------------------
# Folder picker — same shared picker/backend as every other Processing Tool
# ---------------------------------------------------------------------------

@router.get("/library-move/browse")
def browse_directory(path: str = None):
    target = path or get_library_root()
    try:
        return file_picker.list_directory(target)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Directory not found")
    except PermissionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/library-move/drives")
def list_drives():
    return {"drives": file_picker.list_drives()}


# ---------------------------------------------------------------------------
# Progress — one singleton per group, so a Series run and a Singles run
# can be tracked independently (mirrors the "callers must check `started`
# not `running`" contract other Processing Tools use).
# ---------------------------------------------------------------------------

@dataclass
class LibraryMoveProgress:
    running: bool = False
    result: Optional[dict] = None
    error: Optional[str] = None
    finished_at: Optional[datetime] = None


library_move_progress: dict[str, LibraryMoveProgress] = {
    "series": LibraryMoveProgress(),
    "singles": LibraryMoveProgress(),
}


def _log_module(group: str):
    return series_move_log if group == "series" else singles_move_log


def _run(folder: str, group: str, auto: bool = False) -> None:
    library_move_progress[group] = LibraryMoveProgress(running=True)

    result: LibraryMoveResult = move_folders(folder, group)
    log = _log_module(group)

    if result.error:
        library_move_progress[group].running = False
        library_move_progress[group].error = result.error
        library_move_progress[group].finished_at = datetime.now()
        return

    db = SessionLocal()
    try:
        sync_counts = sync_moved_paths_to_db(db, result)
    finally:
        db.close()

    folders = []
    for f in result.folders:
        issues_updated = sync_counts.get(f.folder_name, 0)
        log.append_entry(
            f.folder_name, f.destination, error=f.error, auto=auto,
            issues_updated=issues_updated, db_sync_error=f.db_sync_error,
        )
        folders.append({
            "folder_name": f.folder_name,
            "destination": f.destination,
            "success": f.success,
            "error": f.error,
            "files_moved": f.files_moved,
            "files_failed": f.files_failed,
            "issues_updated": issues_updated,
            "db_sync_error": f.db_sync_error,
        })

    near_misses = [
        {
            "folder_name": nm.folder_name,
            "destination": nm.destination,
            "existing_match": nm.existing_match,
        }
        for nm in result.near_misses
    ]

    library_move_progress[group].running = False
    library_move_progress[group].result = {
        "total": len(folders),
        "moved": sum(1 for f in folders if f["success"]),
        "folders": folders,
        "near_misses": near_misses,
    }
    library_move_progress[group].finished_at = datetime.now()


@router.post("/library-move/run")
def run_now(background_tasks: BackgroundTasks, payload: dict = Body(...)):
    group = (payload.get("group") or "").strip()
    if group not in ("series", "singles"):
        raise HTTPException(status_code=400, detail="group must be 'series' or 'singles'")

    if library_move_progress[group].running:
        return {"message": "A run is already in progress", "running": True, "started": False}

    folder = (payload.get("folder") or "").strip()
    if not folder:
        raise HTTPException(status_code=400, detail="No folder selected")

    label = "Move Series Folders" if group == "series" else "Move Singles Folders"
    background_tasks.add_task(_run, folder, group, False)
    return {"message": f"{label} started", "running": True, "started": True}


@router.get("/library-move/status")
def status(group: str = Query(...)):
    if group not in ("series", "singles"):
        raise HTTPException(status_code=400, detail="group must be 'series' or 'singles'")

    p = library_move_progress[group]
    return {
        "running": p.running,
        "result": p.result,
        "error": p.error,
        "finished_at": p.finished_at.isoformat() if p.finished_at else None,
    }
