"""
ComicVault — Convert Images Router (ADMIN_SPEC.md §11.3). Converts supported
raster images inside a CBZ or CBR to WebP and repacks the archive — both
formats load into the same working list together (no From-format selector,
unlike Convert Archives). Background job + polling progress, own
`convert_images_progress` singleton (separate from Convert Archives').

GET    /api/admin/convert-images/browse         Directory listing (no path = library_root),
                                                 content-filtered to CBZ/CBR, `.bak` excluded
GET    /api/admin/convert-images/drives         Drive-letter listing ("This PC")
POST   /api/admin/convert-images/files/add      Add specific files by path
GET    /api/admin/convert-images/files          List working set
DELETE /api/admin/convert-images/files/clear    Clear working set
DELETE /api/admin/convert-images/files/{file_id}  Remove one file
POST   /api/admin/convert-images/run            Start the batch (background)
GET    /api/admin/convert-images/status         Poll progress
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request

from backend import convert_images_log, file_picker
from backend.archive_convert import detect_archive_format
from backend.auth import is_local_request
from backend.config import get_library_root
from backend.image_convert import convert_images_in_archive


def _require_local(request: Request) -> None:
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})


router = APIRouter(tags=["convert-images"], dependencies=[Depends(_require_local)])

_working_files: dict[str, dict] = {}
_next_id = 1


def _new_id() -> str:
    global _next_id
    file_id = str(_next_id)
    _next_id += 1
    return file_id


# ---------------------------------------------------------------------------
# Progress (§11.3.6) — own singleton, not shared with Convert Archives'
# ---------------------------------------------------------------------------

@dataclass
class ConvertImagesProgress:
    running: bool = False
    current_file_index: int = 0
    total_files: int = 0
    current_filename: str = ""
    finished_at: Optional[datetime] = None
    results: list[dict] = field(default_factory=list)


convert_images_progress = ConvertImagesProgress()


# ---------------------------------------------------------------------------
# Picker (§11.3.1/11.3.2) — content-detected CBZ/CBR, `.bak` files excluded
# by filename suffix (a `.bak` is still a structurally valid zip/rar by
# content, so without this a previous run's backups would reappear as
# convertible inputs in their own right).
# ---------------------------------------------------------------------------

def _is_convertible(file_path: str) -> bool:
    if file_path.lower().endswith(".bak"):
        return False
    return detect_archive_format(file_path) in ("CBZ", "CBR")


@router.get("/convert-images/browse")
def browse_directory(path: str = None):
    target = path or get_library_root()
    try:
        listing = file_picker.list_directory(target)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Directory not found")
    except PermissionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    listing["files"] = [f for f in listing["files"] if _is_convertible(f["path"])]
    return listing


@router.get("/convert-images/drives")
def list_drives():
    return {"drives": file_picker.list_drives()}


# ---------------------------------------------------------------------------
# Working file list
# ---------------------------------------------------------------------------

@router.post("/convert-images/files/add")
def add_files(payload: dict = Body(...)):
    file_paths = payload.get("file_paths", [])
    if not file_paths:
        raise HTTPException(status_code=400, detail="No paths provided")

    added = []
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            continue
        file_id = _new_id()
        entry = {"filename": os.path.basename(file_path), "path": file_path}
        _working_files[file_id] = entry
        added.append({"id": file_id, **entry})

    return {"success": True, "files": added}


@router.get("/convert-images/files")
def list_files():
    return {"files": [{"id": fid, **entry} for fid, entry in _working_files.items()]}


@router.delete("/convert-images/files/clear")
def clear_files():
    _working_files.clear()
    return {"success": True}


@router.delete("/convert-images/files/{file_id}")
def remove_file(file_id: str):
    if file_id not in _working_files:
        raise HTTPException(status_code=404, detail="File not found in working set")
    del _working_files[file_id]
    return {"success": True}


# ---------------------------------------------------------------------------
# Run (§11.3.6) — background job with live polling
# ---------------------------------------------------------------------------

def _run_batch(file_ids: list[str], quality: int, lossless: bool) -> None:
    global convert_images_progress
    entries = [(fid, _working_files[fid]) for fid in file_ids if fid in _working_files]
    convert_images_progress = ConvertImagesProgress(running=True, total_files=len(entries))

    for idx, (file_id, entry) in enumerate(entries):
        convert_images_progress.current_file_index = idx
        convert_images_progress.current_filename = entry["filename"]

        result = convert_images_in_archive(entry["path"], quality=quality, lossless=lossless)
        new_name = os.path.basename(os.path.splitext(entry["path"])[0] + ".cbz")

        convert_images_log.append_entry(
            entry["filename"], new_name,
            images_skipped=result.images_skipped, error=result.error,
        )

        status = "failed" if not result.success else ("success_with_warning" if result.images_skipped else "success")
        convert_images_progress.results.append({
            "file_id": file_id, "filename": entry["filename"], "new_filename": new_name,
            "status": status, "images_skipped": result.images_skipped, "error": result.error,
        })

        if result.success:
            _working_files.pop(file_id, None)

    convert_images_progress.running = False
    convert_images_progress.finished_at = datetime.now()


@router.post("/convert-images/run")
def run_convert_images(background_tasks: BackgroundTasks, payload: dict = Body(...)):
    if convert_images_progress.running:
        return {"message": "Conversion already in progress", "running": True, "started": False}

    lossless = bool(payload.get("lossless", False))
    quality = int(payload.get("quality", 95))

    file_ids = payload.get("file_ids") or list(_working_files.keys())
    if not file_ids:
        raise HTTPException(status_code=400, detail="No files loaded")

    background_tasks.add_task(_run_batch, file_ids, quality, lossless)
    return {"message": "Conversion started", "running": True, "started": True}


@router.get("/convert-images/status")
def convert_images_status():
    return {
        "running": convert_images_progress.running,
        "current_file_index": convert_images_progress.current_file_index,
        "total_files": convert_images_progress.total_files,
        "current_filename": convert_images_progress.current_filename,
        "finished_at": convert_images_progress.finished_at.isoformat() if convert_images_progress.finished_at else None,
        "results": convert_images_progress.results,
    }
