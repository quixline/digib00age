"""
digib00age — XML Tagging Processing Tool Router (ADMIN_SPEC.md §11.6).
Standalone, single-folder CT Auto-Tag run — same core logic as Processing
Folder Automation's CT Auto-Tag stage (backend/ct_autotag.py's
ct_autotag_file()), triggered manually against any folder rather than only
as one stage of the automated pipeline. Match Ratio Threshold, Save on Low
Confidence, and the ComicVine API Key are shared config — read from the same
processing_folder_ct_match_threshold / processing_folder_ct_save_low_
confidence / comicvine_api_key keys Processing Folder Automation already
uses, saved via that router's existing /processing-folder/config and
/processing-folder/comicvine-key/test endpoints (this tool's admin-UI pane
calls those directly, no duplicate config endpoint here).

GET    /api/admin/xml-tagging/browse    Directory listing (no path = library_root)
GET    /api/admin/xml-tagging/drives    Drive-letter listing ("This PC")
POST   /api/admin/xml-tagging/run       Run Now (background)
GET    /api/admin/xml-tagging/status    Poll progress
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException

from backend import ct_autotag_log, file_picker
from backend.archive_convert import detect_archive_format
from backend.config import get_config, get_library_root
from backend.ct_autotag import CTAutoTagResult, ct_autotag_file

router = APIRouter(tags=["xml-tagging"])


# ---------------------------------------------------------------------------
# Folder picker — same shared picker/backend as every other Processing Tool
# ---------------------------------------------------------------------------

@router.get("/xml-tagging/browse")
def browse_directory(path: str = None):
    target = path or get_library_root()
    try:
        return file_picker.list_directory(target)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Directory not found")
    except PermissionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/xml-tagging/drives")
def list_drives():
    return {"drives": file_picker.list_drives()}


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

@dataclass
class XmlTaggingProgress:
    running: bool = False
    result: Optional[dict] = None
    error: Optional[str] = None
    finished_at: Optional[datetime] = None


xml_tagging_progress = XmlTaggingProgress()


def _is_taggable(path: str) -> bool:
    return (
        os.path.isfile(path)
        and not os.path.basename(path).lower().endswith(".bak")
        and detect_archive_format(path) in ("CBZ", "CBR")
    )


def _taggable_files(folder: str, include_subfolders: bool = False) -> list[str]:
    """CBZ/CBR minus .bak — same filter as processing_folder.py's private
    _ct_taggable_files(), duplicated here rather than imported to keep this
    router independent (matches filename_sort.py's existing precedent).
    Recurses into subfolders only when asked; default stays the original
    single-folder behaviour."""
    if not include_subfolders:
        try:
            entries = os.listdir(folder)
        except (OSError, PermissionError):
            return []
        return [
            os.path.join(folder, name) for name in entries
            if _is_taggable(os.path.join(folder, name))
        ]

    files = []
    for root, _dirs, names in os.walk(folder):
        for name in names:
            path = os.path.join(root, name)
            if _is_taggable(path):
                files.append(path)
    return files


def _run(folder: str, include_subfolders: bool = False) -> None:
    global xml_tagging_progress
    xml_tagging_progress = XmlTaggingProgress(running=True)

    if not os.path.isdir(folder):
        xml_tagging_progress.running = False
        xml_tagging_progress.error = "Folder not found"
        xml_tagging_progress.finished_at = datetime.now()
        return

    cfg = get_config()
    api_key = cfg.get("comicvine_api_key", "")
    save_low_confidence = cfg.get("processing_folder_ct_save_low_confidence", True)

    files = []
    for path in _taggable_files(folder, include_subfolders):
        filename = os.path.basename(path)
        result: CTAutoTagResult = ct_autotag_file(path, api_key, save_low_confidence)
        # A .cbr source that got tagged rebuilds as a sibling .cbz
        # (CTAutoTagResult.final_path) — log the filename that's actually on
        # disk afterward, not the pre-write one.
        logged_filename = os.path.basename(result.final_path) if result.final_path else filename
        ct_autotag_log.append_entry(
            logged_filename, result.confidence, result.tags_written,
            result.series, result.issue, result.year, result.error, auto=False,
        )
        status = "failed" if not result.success else (
            "success_with_warning" if result.confidence == "low_confidence" else "success"
        )
        files.append({
            "filename": logged_filename, "status": status, "confidence": result.confidence,
            "tags_written": result.tags_written, "series": result.series,
            "issue": result.issue, "year": result.year, "error": result.error,
        })

    xml_tagging_progress.running = False
    xml_tagging_progress.result = {"total": len(files), "files": files}
    xml_tagging_progress.finished_at = datetime.now()


@router.post("/xml-tagging/run")
def run_now(background_tasks: BackgroundTasks, payload: dict = Body(...)):
    if xml_tagging_progress.running:
        return {"message": "A run is already in progress", "running": True, "started": False}

    folder = (payload.get("folder") or "").strip()
    if not folder:
        raise HTTPException(status_code=400, detail="No folder selected")
    include_subfolders = bool(payload.get("include_subfolders"))

    background_tasks.add_task(_run, folder, include_subfolders)
    return {"message": "XML Tagging started", "running": True, "started": True}


@router.get("/xml-tagging/status")
def status():
    return {
        "running": xml_tagging_progress.running,
        "result": xml_tagging_progress.result,
        "error": xml_tagging_progress.error,
        "finished_at": xml_tagging_progress.finished_at.isoformat() if xml_tagging_progress.finished_at else None,
    }
