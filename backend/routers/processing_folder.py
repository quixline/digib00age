"""
ComicVault — Processing Folder Automation Router (ADMIN_SPEC.md §11.4).
Three-stage pipeline (Convert Archives -> CT Auto-Tag -> Convert Images,
fixed order) against a single configured folder, triggered by "Run Now" or
the wall-clock scheduler (backend/scheduler.py's processing_folder_loop()).
Invokes each stage's callable directly — not via HTTP — since automation
isn't a browser client. CT Auto-Tag added v2.5 #1 (2026-07-03/07).

GET    /api/admin/processing-folder/config              Read settings
POST   /api/admin/processing-folder/config               Save settings
GET    /api/admin/processing-folder/browse               Folder listing (no path = library_root)
GET    /api/admin/processing-folder/drives               Drive-letter listing ("This PC")
POST   /api/admin/processing-folder/run                  Run Now (background)
GET    /api/admin/processing-folder/status               Poll progress
POST   /api/admin/processing-folder/comicvine-key/test    Save & Test ComicVine API key
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request

from backend import ct_autotag_log, ct_bridge, convert_images_log, convert_log, file_picker
from backend.archive_convert import ConvertResult, convert_archive_file, detect_archive_format
from backend.auth import is_local_request
from backend.config import LIBRARY_ROOT, get_config, save_config
from backend.ct_autotag import CTAutoTagResult, ct_autotag_file
from backend.image_convert import ConvertImagesResult, convert_images_in_archive

logger = logging.getLogger(__name__)


def _require_local(request: Request) -> None:
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})


router = APIRouter(tags=["processing-folder"], dependencies=[Depends(_require_local)])


# ---------------------------------------------------------------------------
# Settings (§11.4.2/11.4.4/11.4.5)
# ---------------------------------------------------------------------------

@router.get("/processing-folder/config")
def get_processing_folder_config():
    cfg = get_config()
    return {
        "processing_folder_path": cfg.get("processing_folder_path", ""),
        "processing_folder_convert_archives_enabled": cfg.get("processing_folder_convert_archives_enabled", False),
        "processing_folder_convert_archives_from": cfg.get("processing_folder_convert_archives_from", "cbr"),
        "processing_folder_convert_images_enabled": cfg.get("processing_folder_convert_images_enabled", False),
        "processing_folder_convert_images_lossless": cfg.get("processing_folder_convert_images_lossless", False),
        "processing_folder_convert_images_quality": cfg.get("processing_folder_convert_images_quality", 95),
        "processing_folder_ct_autotag_enabled": cfg.get("processing_folder_ct_autotag_enabled", False),
        "processing_folder_ct_save_low_confidence": cfg.get("processing_folder_ct_save_low_confidence", True),
        "processing_folder_ct_match_threshold": cfg.get("processing_folder_ct_match_threshold", 80),
        "comicvine_api_key": cfg.get("comicvine_api_key", ""),
        "processing_folder_schedule": cfg.get("processing_folder_schedule", "off"),
        "processing_folder_schedule_time": cfg.get("processing_folder_schedule_time", "00:00"),
        "processing_folder_schedule_day": cfg.get("processing_folder_schedule_day", 0),
        "next_processing_run": cfg.get("next_processing_run"),
    }


_BOOL_KEYS = (
    "processing_folder_convert_archives_enabled",
    "processing_folder_convert_images_enabled",
    "processing_folder_convert_images_lossless",
    "processing_folder_ct_autotag_enabled",
    "processing_folder_ct_save_low_confidence",
)
_STR_KEYS = (
    "processing_folder_path",
    "processing_folder_convert_archives_from",
    "processing_folder_schedule",
    "processing_folder_schedule_time",
    "comicvine_api_key",
)


@router.post("/processing-folder/config")
def save_processing_folder_config(payload: dict = Body(...)):
    update: dict = {}
    for key in _BOOL_KEYS:
        if key in payload:
            update[key] = bool(payload[key])
    for key in _STR_KEYS:
        if key in payload:
            update[key] = str(payload[key])
    if "processing_folder_convert_images_quality" in payload:
        update["processing_folder_convert_images_quality"] = int(payload["processing_folder_convert_images_quality"])
    if "processing_folder_ct_match_threshold" in payload:
        update["processing_folder_ct_match_threshold"] = int(payload["processing_folder_ct_match_threshold"])
    if "processing_folder_schedule_day" in payload:
        update["processing_folder_schedule_day"] = int(payload["processing_folder_schedule_day"])

    # A schedule/time/day change invalidates any previously-computed
    # next_processing_run — let the scheduler loop recompute it fresh on its
    # next poll rather than firing against a stale timestamp.
    if any(k in update for k in ("processing_folder_schedule", "processing_folder_schedule_time", "processing_folder_schedule_day")):
        update["next_processing_run"] = None

    save_config(update)
    return {"message": "Settings saved"}


# ---------------------------------------------------------------------------
# Folder picker (§11.4.2) — single-folder select, same shared picker as
# Rename/Convert Archives/Convert Images, folder-only mode
# ---------------------------------------------------------------------------

@router.get("/processing-folder/browse")
def browse_directory(path: str = None):
    target = path or LIBRARY_ROOT
    try:
        return file_picker.list_directory(target)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Directory not found")
    except PermissionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/processing-folder/drives")
def list_drives():
    return {"drives": file_picker.list_drives()}


# ---------------------------------------------------------------------------
# Progress (§11.4.8)
# ---------------------------------------------------------------------------

@dataclass
class ProcessingFolderProgress:
    running: bool = False
    current_stage: Optional[str] = None  # 'convert_archives' | 'ct_autotag' | 'convert_images'
    stage_results: dict = field(default_factory=dict)
    finished_at: Optional[datetime] = None
    error: Optional[str] = None


processing_folder_progress = ProcessingFolderProgress()


# ---------------------------------------------------------------------------
# Pipeline (§11.4.3) — folder-level, not per-file chaining; each stage picks
# up whatever's in the folder when it starts, including anything the
# previous stage just produced.
# ---------------------------------------------------------------------------

def _list_folder_files(folder: str) -> list[str]:
    try:
        return [
            os.path.join(folder, name) for name in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, name))
        ]
    except (OSError, PermissionError):
        return []


def _convertible_archives(folder: str, from_format: str) -> list[str]:
    """Same content-detected + `.bak`-excluded filter as
    routers/convert.py's picker (cross-review fix applies here too — this
    matters even more for automation, which re-runs on a schedule)."""
    return [
        p for p in _list_folder_files(folder)
        if not p.lower().endswith(".bak") and detect_archive_format(p) == from_format.upper()
    ]


def _convertible_images(folder: str) -> list[str]:
    return [
        p for p in _list_folder_files(folder)
        if not p.lower().endswith(".bak") and detect_archive_format(p) in ("CBZ", "CBR")
    ]


def _ct_taggable_files(folder: str) -> list[str]:
    """CBZ/CBR minus .bak — same filter as _convertible_images, since CT
    Auto-Tag accepts both formats natively (ComicArchive branches on content
    itself; tagging a .cbr rebuilds it as .cbz, same as every other editor
    save path — see CTAutoTagResult.final_path)."""
    return [
        p for p in _list_folder_files(folder)
        if not p.lower().endswith(".bak") and detect_archive_format(p) in ("CBZ", "CBR")
    ]


def _run_convert_archives_stage(folder: str, from_format: str, auto: bool) -> list[dict]:
    results = []
    for path in _convertible_archives(folder, from_format):
        filename = os.path.basename(path)
        result: ConvertResult = convert_archive_file(path, from_format)
        new_name = os.path.basename(os.path.splitext(path)[0] + ".cbz")
        convert_log.append_entry(filename, new_name, pages_skipped=result.pages_skipped, error=result.error, auto=auto)
        status = "failed" if not result.success else ("success_with_warning" if result.pages_skipped else "success")
        results.append({"filename": filename, "new_filename": new_name, "status": status,
                         "pages_skipped": result.pages_skipped, "error": result.error})
    return results


def _run_ct_autotag_stage(folder: str, api_key: str, save_low_confidence: bool) -> list[dict]:
    """Always logs with auto=True — this stage only ever runs as part of
    Processing Folder Automation (Run Now or the scheduler), never
    standalone. XML Tagging (v2.6 Item 1 Phase C2b) is the standalone path
    and logs auto=False."""
    results = []
    for path in _ct_taggable_files(folder):
        filename = os.path.basename(path)
        result: CTAutoTagResult = ct_autotag_file(path, api_key, save_low_confidence)
        # A .cbr source that got tagged rebuilds as a sibling .cbz
        # (CTAutoTagResult.final_path) — log the filename that's actually on
        # disk afterward, not the pre-write one.
        logged_filename = os.path.basename(result.final_path) if result.final_path else filename
        ct_autotag_log.append_entry(
            logged_filename, result.confidence, result.tags_written,
            result.series, result.issue, result.year, result.error, auto=True,
        )
        status = "failed" if not result.success else (
            "success_with_warning" if result.confidence == "low_confidence" else "success"
        )
        results.append({
            "filename": logged_filename, "status": status, "confidence": result.confidence,
            "tags_written": result.tags_written, "series": result.series,
            "issue": result.issue, "year": result.year, "error": result.error,
        })
    return results


def _run_convert_images_stage(folder: str, quality: int, lossless: bool, auto: bool) -> list[dict]:
    results = []
    for path in _convertible_images(folder):
        filename = os.path.basename(path)
        result: ConvertImagesResult = convert_images_in_archive(path, quality=quality, lossless=lossless)
        new_name = os.path.basename(os.path.splitext(path)[0] + ".cbz")
        convert_images_log.append_entry(filename, new_name, images_skipped=result.images_skipped, error=result.error, auto=auto)
        status = "failed" if not result.success else ("success_with_warning" if result.images_skipped else "success")
        results.append({"filename": filename, "new_filename": new_name, "status": status,
                         "images_skipped": result.images_skipped, "error": result.error})
    return results


def run_pipeline(auto: bool = False) -> None:
    """The pipeline entry point — called by the "Run Now" background task
    and by scheduler.py's processing_folder_loop(). Per-stage failures
    (the stage itself erroring, not just individual files within it) are
    caught and logged; the pipeline still runs every enabled stage."""
    global processing_folder_progress
    cfg = get_config()
    folder = cfg.get("processing_folder_path", "")
    processing_folder_progress = ProcessingFolderProgress(running=True)

    if not folder or not os.path.isdir(folder):
        processing_folder_progress.running = False
        processing_folder_progress.error = "No processing folder configured or folder not found"
        processing_folder_progress.finished_at = datetime.now()
        return

    if cfg.get("processing_folder_convert_archives_enabled", False):
        processing_folder_progress.current_stage = "convert_archives"
        try:
            from_format = cfg.get("processing_folder_convert_archives_from", "cbr")
            processing_folder_progress.stage_results["convert_archives"] = _run_convert_archives_stage(folder, from_format, auto)
        except Exception as exc:
            logger.exception("Convert Archives stage failed")
            processing_folder_progress.stage_results["convert_archives_error"] = str(exc)

    if cfg.get("processing_folder_ct_autotag_enabled", False):
        processing_folder_progress.current_stage = "ct_autotag"
        try:
            api_key = cfg.get("comicvine_api_key", "")
            save_low = cfg.get("processing_folder_ct_save_low_confidence", True)
            processing_folder_progress.stage_results["ct_autotag"] = _run_ct_autotag_stage(folder, api_key, save_low)
        except Exception as exc:
            logger.exception("CT Auto-Tag stage failed")
            processing_folder_progress.stage_results["ct_autotag_error"] = str(exc)

    if cfg.get("processing_folder_convert_images_enabled", False):
        processing_folder_progress.current_stage = "convert_images"
        try:
            lossless = cfg.get("processing_folder_convert_images_lossless", False)
            quality = cfg.get("processing_folder_convert_images_quality", 95)
            processing_folder_progress.stage_results["convert_images"] = _run_convert_images_stage(folder, quality, lossless, auto)
        except Exception as exc:
            logger.exception("Convert Images stage failed")
            processing_folder_progress.stage_results["convert_images_error"] = str(exc)

    processing_folder_progress.running = False
    processing_folder_progress.current_stage = None
    processing_folder_progress.finished_at = datetime.now()


# ---------------------------------------------------------------------------
# Run Now (§11.4.7)
# ---------------------------------------------------------------------------

@router.post("/processing-folder/run")
def run_now(background_tasks: BackgroundTasks):
    if processing_folder_progress.running:
        return {"message": "A run is already in progress", "running": True, "started": False}

    cfg = get_config()
    if not any(cfg.get(k) for k in (
        "processing_folder_convert_archives_enabled",
        "processing_folder_ct_autotag_enabled",
        "processing_folder_convert_images_enabled",
    )):
        raise HTTPException(status_code=400, detail="No stages enabled")

    # §11.4.9's [AUTO] tag distinguishes "came through the Processing Folder
    # pipeline" from "manual run via Convert Archives'/Convert Images' own
    # admin-UI tools" — that's true for Run Now just as much as for a
    # scheduled fire, since both go through this same pipeline mechanism,
    # not the standalone per-tool UI. auto=True for both trigger paths.
    background_tasks.add_task(run_pipeline, True)
    return {"message": "Processing folder run started", "running": True, "started": True}


@router.get("/processing-folder/status")
def status():
    return {
        "running": processing_folder_progress.running,
        "current_stage": processing_folder_progress.current_stage,
        "stage_results": processing_folder_progress.stage_results,
        "finished_at": processing_folder_progress.finished_at.isoformat() if processing_folder_progress.finished_at else None,
        "error": processing_folder_progress.error,
    }


# ---------------------------------------------------------------------------
# ComicVine API key — Save & Test (§11.4.4, one deliberate exception to this
# page's auto-save convention)
# ---------------------------------------------------------------------------

@router.post("/processing-folder/comicvine-key/test")
def save_and_test_comicvine_key(payload: dict = Body(...)):
    api_key = str(payload.get("comicvine_api_key", ""))
    save_config({"comicvine_api_key": api_key})  # always persists, regardless of test outcome
    message, is_valid = ct_bridge.check_api_key(api_key)
    return {"saved": True, "valid": is_valid, "message": message}
