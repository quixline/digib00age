"""
digib00age — Convert Archives Router (ADMIN_SPEC.md §11.2). CBR->CBZ and
PDF->CBZ only. Background job + polling progress, modelled on
backend/scanner.py's existing scan_progress pattern (not a blocking request
like Rename — conversion work is meaningfully slower per file).

GET    /api/admin/convert/browse         Directory listing (no path = library_root),
                                          content-filtered to the current from_format
GET    /api/admin/convert/drives         Drive-letter listing ("This PC")
POST   /api/admin/convert/files/add      Add specific files by path
GET    /api/admin/convert/files          List working set
DELETE /api/admin/convert/files/clear    Clear working set
DELETE /api/admin/convert/files/{file_id}  Remove one file
POST   /api/admin/convert/run            Start the batch (background)
GET    /api/admin/convert/status         Poll progress
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request

from backend import convert_log, file_picker
from backend.archive_convert import convert_archive_file, detect_archive_format
from backend.auth import is_local_request
from backend.config import get_library_root


def _require_local(request: Request) -> None:
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})


router = APIRouter(tags=["convert"], dependencies=[Depends(_require_local)])

_working_files: dict[str, dict] = {}
_next_id = 1


def _new_id() -> str:
    global _next_id
    file_id = str(_next_id)
    _next_id += 1
    return file_id


# ---------------------------------------------------------------------------
# Progress (§11.2.5)
# ---------------------------------------------------------------------------

@dataclass
class ConvertProgress:
    running: bool = False
    current_file_index: int = 0
    total_files: int = 0
    current_filename: str = ""
    finished_at: Optional[datetime] = None
    results: list[dict] = field(default_factory=list)


convert_progress = ConvertProgress()


# ---------------------------------------------------------------------------
# Picker (§11.2.2) — content-detected CBR/PDF only, `.bak` files excluded
# (cross-review finding — Convert Images already excluded `.bak`, Convert
# Archives' content filter didn't, which would let a kept `.bak` from a
# success-with-warnings run get silently reprocessed as a fresh input).
# ---------------------------------------------------------------------------

def _matches_from_format(file_path: str, from_format: str) -> bool:
    if file_path.lower().endswith(".bak"):
        return False
    detected = detect_archive_format(file_path)
    return detected == from_format.upper()


@router.get("/convert/browse")
def browse_directory(path: str = None, from_format: str = "cbr"):
    target = path or get_library_root()
    try:
        listing = file_picker.list_directory(target)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Directory not found")
    except PermissionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    listing["files"] = [
        f for f in listing["files"] if _matches_from_format(f["path"], from_format)
    ]
    return listing


@router.get("/convert/drives")
def list_drives():
    return {"drives": file_picker.list_drives()}


# ---------------------------------------------------------------------------
# Working file list
# ---------------------------------------------------------------------------

@router.post("/convert/files/add")
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


@router.get("/convert/files")
def list_files():
    return {"files": [{"id": fid, **entry} for fid, entry in _working_files.items()]}


@router.delete("/convert/files/clear")
def clear_files():
    _working_files.clear()
    return {"success": True}


@router.delete("/convert/files/{file_id}")
def remove_file(file_id: str):
    if file_id not in _working_files:
        raise HTTPException(status_code=404, detail="File not found in working set")
    del _working_files[file_id]
    return {"success": True}


# ---------------------------------------------------------------------------
# Run (§11.2.5) — background job with live polling
# ---------------------------------------------------------------------------

def _run_batch(file_ids: list[str], from_format: str) -> None:
    global convert_progress
    entries = [(fid, _working_files[fid]) for fid in file_ids if fid in _working_files]
    convert_progress = ConvertProgress(running=True, total_files=len(entries))

    for idx, (file_id, entry) in enumerate(entries):
        convert_progress.current_file_index = idx
        convert_progress.current_filename = entry["filename"]

        result = convert_archive_file(entry["path"], from_format)
        new_name = os.path.basename(os.path.splitext(entry["path"])[0] + ".cbz")

        convert_log.append_entry(
            entry["filename"], new_name,
            pages_skipped=result.pages_skipped, error=result.error,
        )

        status = "failed" if not result.success else ("success_with_warning" if result.pages_skipped else "success")
        convert_progress.results.append({
            "file_id": file_id, "filename": entry["filename"], "new_filename": new_name,
            "status": status, "pages_skipped": result.pages_skipped, "error": result.error,
        })

        if result.success:
            _working_files.pop(file_id, None)

    convert_progress.running = False
    convert_progress.finished_at = datetime.now()


@router.post("/convert/run")
def run_convert(background_tasks: BackgroundTasks, payload: dict = Body(...)):
    if convert_progress.running:
        # `running: True` reflects actual current state either way — callers
        # must check `started`, not `running`, to tell "your request kicked
        # off a new run" from "rejected, one was already in progress".
        return {"message": "Conversion already in progress", "running": True, "started": False}

    from_format = (payload.get("from_format") or "cbr").lower()
    if from_format not in ("cbr", "pdf"):
        raise HTTPException(status_code=400, detail="from_format must be 'cbr' or 'pdf'")

    file_ids = payload.get("file_ids") or list(_working_files.keys())
    if not file_ids:
        raise HTTPException(status_code=400, detail="No files loaded")

    background_tasks.add_task(_run_batch, file_ids, from_format)
    return {"message": "Conversion started", "running": True, "started": True}


@router.get("/convert/status")
def convert_status():
    return {
        "running": convert_progress.running,
        "current_file_index": convert_progress.current_file_index,
        "total_files": convert_progress.total_files,
        "current_filename": convert_progress.current_filename,
        "finished_at": convert_progress.finished_at.isoformat() if convert_progress.finished_at else None,
        "results": convert_progress.results,
    }
