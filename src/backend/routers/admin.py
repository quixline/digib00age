"""
digib00age — Admin Router
GET  /api/admin/stats        Library statistics
POST /api/scan               Trigger full background rescan
POST /api/scan/file?path=    Rescan single file (called by Flask editor)
GET  /api/scan/status        Live scan progress for admin UI
POST /api/admin/backup       Copy digib00age.db to dated backup file
POST /api/admin/restore-database  Restore digib00age.db from a chosen backup file
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import file_picker, scan_logs
from backend import config as config_module
from backend.auth import is_local_request
from backend.config import get_config, save_config, reset_config, get_library_root, PROJECT_ROOT, REPO_ROOT
from backend.database import get_db, SessionLocal, checkpoint_wal, engine
from backend.models import CustomTab, HomeStrip, Issue, Person, ReadingProgress
from backend.path_utils import is_under, normalize_path

router = APIRouter(tags=["admin"])


# ---------------------------------------------------------------------------
# GET /api/admin/stats
# ---------------------------------------------------------------------------

@router.get("/admin/stats")
def get_stats(db: Session = Depends(get_db)):
    """High-level library statistics for the admin page."""
    total_issues = db.query(func.count(Issue.id)).filter(Issue.missing == False).scalar()
    series_count = (
        db.query(func.count(func.distinct(Issue.series)))
        .filter(Issue.format_group == "Series", Issue.missing == False)
        .scalar()
    )
    singles_count = (
        db.query(func.count(Issue.id))
        .filter(Issue.format_group == "Singles", Issue.missing == False)
        .scalar()
    )
    read_count = (
        db.query(func.count(ReadingProgress.id))
        .filter(ReadingProgress.status == "read")
        .scalar()
    )
    reading_count = (
        db.query(func.count(ReadingProgress.id))
        .filter(ReadingProgress.status == "reading")
        .scalar()
    )
    missing_count = (
        db.query(func.count(Issue.id))
        .filter(Issue.missing == True)
        .scalar()
    )
    filename_metadata_count = (
        db.query(func.count(Issue.id))
        .filter(Issue.metadata_source == "filename")
        .scalar()
    )

    from backend.scanner import scan_progress as sp, get_changes_last_cycle

    config = get_config()
    log_status = _compute_log_status(config)

    return {
        "total_issues": total_issues,
        "series_count": series_count,
        "singles_count": singles_count,
        "read_count": read_count,
        "reading_count": reading_count,
        "missing_count": missing_count,
        "filename_metadata_count": filename_metadata_count,
        "library_root": config.get("library_root"),
        "db_path": str(PROJECT_ROOT / config.get("db_path", "backend/digib00age.db")),
        "scan_state": {
            "running": sp.running,
            "finished_at": (sp.finished_at.isoformat() + "Z") if sp.finished_at else None,
            "last_scan_persisted": scan_logs.read_last_scan_timestamp(),
            "total_files": sp.total,
            "new_files": sp.new,
            "updated_files": get_changes_last_cycle(),
        },
        "log_status": log_status,
        "last_backup_at": config.get("last_backup_at"),
        "last_backup_error": config.get("last_backup_error"),
    }


def _compute_log_status(cfg: dict) -> dict:
    """has_new per log card — on-disk log mtime vs. its last-viewed timestamp."""
    viewed = cfg.get("log_last_viewed", {})
    status = {}
    for log_name in scan_logs._FILENAMES:
        path = scan_logs.log_path(log_name)
        if not path.exists():
            status[log_name] = False
            continue
        viewed_at = viewed.get(log_name)
        if not viewed_at:
            status[log_name] = True
            continue
        log_mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        viewed_dt = datetime.fromisoformat(viewed_at)
        status[log_name] = log_mtime > viewed_dt
    return status


# ---------------------------------------------------------------------------
# GET /api/scan/status
# ---------------------------------------------------------------------------

@router.get("/scan/status")
def scan_status():
    """Polled by the admin page every second during a scan."""
    from backend.scanner import scan_progress as sp, get_changes_last_cycle
    return {
        "running": sp.running,
        "started_at": (sp.started_at.isoformat() + "Z") if sp.started_at else None,
        "finished_at": (sp.finished_at.isoformat() + "Z") if sp.finished_at else None,
        "total_files": sp.total,
        "processed_files": sp.processed,
        "new_files": sp.new,
        "updated_files": get_changes_last_cycle(),
        "missing_files": sp.missing,
        "error_files": sp.errors,
        "current_file": "",
        "log": sp.log[-200:],
        "error": sp.error,
    }


# ---------------------------------------------------------------------------
# POST /api/scan   — trigger full background rescan
# ---------------------------------------------------------------------------

@router.post("/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    """
    Kick off a full library rescan in the background.
    Returns immediately — poll /api/scan/status for progress.
    """
    from backend.scanner import scan_progress as sp
    if sp.running:
        return {"message": "Scan already in progress", "running": True}
    if not config_module.is_library_configured():
        message = "Library not configured. Go to Admin → Library Folders to set it."
        return {"message": message, "running": False, "error": message}
    background_tasks.add_task(_run_scan_background)
    return {"message": "Scan started", "running": True}


def _run_scan_background():
    """Run scan_library in a background thread."""
    from backend.scanner import scan_library
    db = SessionLocal()
    try:
        scan_library(db)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Background scan error: %s", exc)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# POST /api/scan/file?path=   — rescan single file (called by Flask editor)
# ---------------------------------------------------------------------------

@router.post("/scan/file")
def scan_single_file(
    path: str = Query(..., description="Absolute path to the CBZ file"),
    db: Session = Depends(get_db),
):
    """
    Rescan a single file and update its DB row.
    Called automatically by the Flask metadata editor after it saves ComicInfo.xml.
    """
    if not Path(path).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    if not path.lower().endswith((".cbz", ".cbr")):
        raise HTTPException(status_code=400, detail="Only CBZ/CBR files are supported")

    try:
        from backend.scanner import scan_single_file as _scan_file
        _scan_file(path, db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}")

    # Find the updated issue to return
    issue = db.query(Issue).filter(Issue.file_path == path).first()
    if issue:
        return {
            "message": "File rescanned successfully",
            "issue_id": issue.id,
            "series": issue.series,
            "number": issue.number,
        }
    return {"message": "File rescanned successfully"}


# ---------------------------------------------------------------------------
# GET /api/admin/config  — read editable config values
# ---------------------------------------------------------------------------

@router.get("/admin/config")
def get_admin_config():
    cfg = get_config()
    root = cfg.get("library_root", "")
    roots = cfg.get("library_roots", [root] if root else [])
    return {
        "library_roots": roots,
        "scan_exclude": cfg.get("scan_exclude", []),
        "library_root": root,
        "log_size_limit_mb": cfg.get("log_size_limit_mb", 5),
        "auto_scan_frequency": cfg.get("auto_scan_frequency", "off"),
        "autostart_scan": cfg.get("autostart_scan", False),
        "reader_port": cfg.get("reader_port", 9800),
        "backup_folder": cfg.get("backup_folder", ""),
        "backup_frequency": cfg.get("backup_frequency", "off"),
    }


# ---------------------------------------------------------------------------
# POST /api/admin/config  — write editable config values
# ---------------------------------------------------------------------------

@router.post("/admin/config")
def save_admin_config(data: dict):
    update: dict = {}

    if "library_roots" in data:
        roots = [r.strip() for r in data["library_roots"] if r.strip()]
        update["library_roots"] = roots
        if roots:
            update["library_root"] = roots[0]
    elif "library_root" in data and data["library_root"].strip():
        update["library_root"] = data["library_root"].strip()

    if "scan_exclude" in data:
        update["scan_exclude"] = [e.strip() for e in data["scan_exclude"] if e.strip()]

    if "log_size_limit_mb" in data:
        update["log_size_limit_mb"] = int(data["log_size_limit_mb"])

    if "auto_scan_frequency" in data:
        update["auto_scan_frequency"] = data["auto_scan_frequency"]

    if "autostart_scan" in data:
        update["autostart_scan"] = bool(data["autostart_scan"])

    if "reader_port" in data:
        update["reader_port"] = int(data["reader_port"])

    if "backup_folder" in data:
        update["backup_folder"] = data["backup_folder"].strip()

    if "backup_frequency" in data:
        update["backup_frequency"] = data["backup_frequency"]

    save_config(update)

    return {"message": "Config saved"}


# ---------------------------------------------------------------------------
# POST /api/admin/restart  — deliberately exit the process so the tray app's
# existing crash-recovery relaunches it on the freshly-saved port
# (ADMIN_SPEC.md §7.3). Local-only — restarting is disruptive to anyone
# currently using the library, same local-access boundary as the admin
# password controls.
# ---------------------------------------------------------------------------

@router.post("/admin/restart")
async def restart_server(request: Request):
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})

    _schedule_delayed_exit()
    return {"message": "Restarting"}


def _schedule_delayed_exit() -> None:
    """Deliberately exit the process after a short delay, so the tray app's
    crash-recovery relaunches it. Shared by /admin/restart and
    /admin/restore-database (both need the same relaunch behaviour)."""
    import asyncio

    async def _delayed_exit():
        await asyncio.sleep(1)  # let the HTTP response actually reach the client first
        os._exit(0)

    asyncio.create_task(_delayed_exit())


# ---------------------------------------------------------------------------
# GET /api/admin/logs/{log_name}        Log file contents
# POST /api/admin/logs/{log_name}/mark-viewed
# GET /api/admin/logs/folder-path       Logs directory path
# ---------------------------------------------------------------------------

@router.get("/admin/logs/folder-path")
def get_logs_folder_path():
    return {"path": str(scan_logs.LOGS_DIR)}


@router.get("/admin/logs/{log_name}")
def get_log_contents(log_name: str):
    if log_name not in scan_logs._FILENAMES:
        raise HTTPException(status_code=404, detail={"error": "unknown_log"})
    content, exists = scan_logs.read_recent_log(log_name)
    return {"content": content, "exists": exists}


@router.post("/admin/logs/{log_name}/mark-viewed")
def mark_log_viewed(log_name: str):
    if log_name not in scan_logs._FILENAMES:
        raise HTTPException(status_code=404, detail={"error": "unknown_log"})
    cfg = get_config()
    viewed = dict(cfg.get("log_last_viewed", {}))
    viewed[log_name] = datetime.now(timezone.utc).isoformat()
    save_config({"log_last_viewed": viewed})
    return {"ok": True}


# ---------------------------------------------------------------------------
# POST /api/admin/cleanup-missing
# ---------------------------------------------------------------------------

@router.post("/admin/cleanup-missing")
def cleanup_missing(db: Session = Depends(get_db)):
    """
    Hard-delete all issues flagged missing=True.
    Cascade rules on the ORM wipe related issue_genres and reading_progress rows.
    """
    missing = db.query(Issue).filter(Issue.missing == True).all()  # noqa: E712
    count = len(missing)
    for issue in missing:
        db.delete(issue)
    db.commit()
    return {"removed": count}


# ---------------------------------------------------------------------------
# POST /api/admin/clear-database
# POST /api/admin/clear-reading-progress
# Both destructive, irreversible — local-access-only, same tier as
# restart_server / browse_folder_dialog (ADMIN_SPEC.md §7.4, §7.5).
# ---------------------------------------------------------------------------

@router.post("/admin/clear-database")
async def clear_database(request: Request, db: Session = Depends(get_db)):
    """
    Hard-deletes ALL library data: issues, genres, credits, reading progress,
    and now-orphaned people. CustomTab and HomeStrip rows are configuration,
    not library data, and are deliberately left untouched.

    Also sweeps backend/thumbnails/ (everything in it is orphaned once issues
    is empty), resets the four scan log files, and resets config.json down to
    its bare-minimum keys (reader_port, thumbnail_size, thumbnail_dir, db_path)
    — dropping library_root(s), scan_exclude, backup_*, log_last_viewed,
    next_processing_run, and anything else added since setup — then
    checkpoints the WAL, VACUUMs the DB file, and restarts the process the
    same way restore_database() does (BUG-026/BUG-027) — a live pooled
    connection can't otherwise be safely reset, so the endpoint self-restarts
    instead of requiring the caller to stop the server first.
    """
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})

    issue_count = db.query(func.count(Issue.id)).scalar()
    db.query(Issue).delete(synchronize_session=False)
    person_count = db.query(func.count(Person.id)).scalar()
    db.query(Person).delete(synchronize_session=False)
    db.commit()

    thumbs_removed, thumbs_bytes = _clear_all_thumbnails()
    scan_logs.clear_all_logs()
    reset_config()

    config = get_config()
    db_path = PROJECT_ROOT / config.get("db_path", "backend/digib00age.db")
    size_before = db_path.stat().st_size if db_path.exists() else 0

    # Fold pending WAL writes, then dispose the pooled connection so VACUUM
    # (which can't run inside a transaction) and the sidecar cleanup below
    # aren't blocked by a live file handle — same rationale as
    # restore_database()'s BUG-016 fix. Safe to drop here since the process
    # exits via _schedule_delayed_exit() right after.
    checkpoint_wal()
    engine.dispose()
    _vacuum_database(db_path)
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(db_path) + suffix)
        if sidecar.exists():
            sidecar.unlink()

    size_after = db_path.stat().st_size if db_path.exists() else 0

    _schedule_delayed_exit()

    return {
        "message": "Database cleared, restarting",
        "issues_removed": issue_count,
        "people_removed": person_count,
        "thumbnails_removed": thumbs_removed,
        "thumbnail_bytes_freed": thumbs_bytes,
        "db_bytes_before": size_before,
        "db_bytes_after": size_after,
    }


def _clear_all_thumbnails() -> tuple[int, int]:
    """Deletes every file in backend/thumbnails/ — after clear_database()'s
    row deletes above, Issues is empty so every {id}.jpg is orphaned by
    definition (no need to diff filenames against DB rows)."""
    removed, freed = 0, 0
    if config_module.THUMBNAIL_DIR.exists():
        for f in config_module.THUMBNAIL_DIR.glob("*.jpg"):
            freed += f.stat().st_size
            f.unlink()
            removed += 1
    return removed, freed


def _vacuum_database(db_path: Path) -> None:
    """Runs outside the SQLAlchemy pool (engine already disposed by the
    caller) since VACUUM can't run inside a transaction. Reclaims the
    freelist pages the bulk deletes above just created."""
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("VACUUM")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()


@router.post("/admin/clear-reading-progress")
def clear_reading_progress(request: Request, db: Session = Depends(get_db)):
    """Deletes all ReadingProgress rows only. Issues, genres, credits untouched."""
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})

    count = db.query(func.count(ReadingProgress.id)).scalar()
    db.query(ReadingProgress).delete(synchronize_session=False)
    db.commit()
    return {"removed": count}


# ---------------------------------------------------------------------------
# POST /api/admin/backup
# ---------------------------------------------------------------------------

@router.post("/admin/backup")
def backup_database():
    """
    Copies digib00age.db to a dated backup file.
    e.g. digib00age_backup_2025-01-15_14-32-00.db

    Uses the configured Scheduled Backup destination (ADMIN_SPEC.md §9) if one
    is set, otherwise falls back to the DB's own directory (original V1
    behaviour) — this is also the function the scheduled backup loop calls.
    """
    try:
        backup_path = run_database_backup()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Database file not found")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Backup failed: {exc}")

    return {
        "message": "Backup created successfully",
        "backup_file": str(backup_path),
        "size_bytes": backup_path.stat().st_size,
    }


def run_database_backup(prefix: str = "digib00age_backup", sep: str = "_") -> Path:
    """
    Shared by the manual Backup Database button, the scheduled backup loop, and
    the pre-restore safety snapshot (ADMIN_SPEC.md §9, Restore Database subsection)
    — `prefix`/`sep` let the restore path produce `pre-restore-{timestamp}.db`
    instead of the default `digib00age_backup_{timestamp}.db` while reusing the
    same destination-folder and last-backup-tracking logic.
    """
    config = get_config()
    db_path = PROJECT_ROOT / config.get("db_path", "backend/digib00age.db")

    if not db_path.exists():
        raise FileNotFoundError(str(db_path))

    dest_dir = Path(config["backup_folder"]) if config.get("backup_folder") else db_path.parent
    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = dest_dir / f"{prefix}{sep}{timestamp}.db"
    checkpoint_wal()  # fold pending WAL writes into db_path before copying (BUG-016)
    shutil.copy2(str(db_path), str(backup_path))
    save_config({"last_backup_at": datetime.now().isoformat(), "last_backup_error": None})
    return backup_path


# ---------------------------------------------------------------------------
# POST /api/admin/browse-backup-file-dialog
# POST /api/admin/restore-database
# Restore Database (ADMIN_SPEC.md §9, Restore Database — V2.3 Item 12).
# Local-only, same tier as Clear Database (§7.4) — a full DB replacement is at
# least as disruptive.
# ---------------------------------------------------------------------------

@router.post("/admin/browse-backup-file-dialog")
async def browse_backup_file_dialog(request: Request):
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})

    import asyncio

    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, _show_backup_file_dialog)
    return {"path": path}


def _show_backup_file_dialog() -> str | None:
    import tkinter
    from tkinter import filedialog

    config = get_config()
    db_path = PROJECT_ROOT / config.get("db_path", "backend/digib00age.db")
    initial_dir = config.get("backup_folder") or str(db_path.parent)

    root = tkinter.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.askopenfilename(
            title="Choose Backup File to Restore",
            initialdir=initial_dir,
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
        )
    finally:
        root.destroy()
    return selected or None


@router.post("/admin/restore-database")
async def restore_database(request: Request, payload: dict = Body(...)):
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})

    source_path = (payload.get("source_path") or "").strip()
    if not source_path:
        raise HTTPException(status_code=400, detail="source_path is required")

    source = Path(source_path)
    if not source.is_file():
        raise HTTPException(status_code=404, detail="Backup file not found")

    # Safety net: snapshot the current DB before overwriting it, same helper
    # the manual/scheduled backup buttons use, just a distinct filename prefix.
    try:
        snapshot_path = run_database_backup(prefix="pre-restore", sep="-")
    except FileNotFoundError:
        snapshot_path = None  # no existing DB yet — nothing to snapshot

    config = get_config()
    db_path = PROJECT_ROOT / config.get("db_path", "backend/digib00age.db")

    # Fold pending WAL writes into db_path, then clear its -wal/-shm sidecars
    # outright so nothing is left for SQLite to replay back into the restored
    # file on relaunch (BUG-016). dispose() first — the pool's live connection
    # still holds an OS-level handle on -wal/-shm even after TRUNCATE, which
    # blocks unlink() on Windows; safe to drop here since the process exits
    # via _schedule_delayed_exit() right after.
    checkpoint_wal()
    engine.dispose()
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(db_path) + suffix)
        if sidecar.exists():
            sidecar.unlink()

    shutil.copy2(str(source), str(db_path))

    _schedule_delayed_exit()

    return {
        "message": "Database restored, restarting",
        "pre_restore_backup": str(snapshot_path) if snapshot_path else None,
    }


# ---------------------------------------------------------------------------
# Custom Tabs — admin-managed, folder-scoped library tabs (CUSTOM_TABS_SPEC.md)
# ---------------------------------------------------------------------------

VALID_VIEW_MODES = {"flat", "folder"}


def _read_config_fresh() -> dict:
    """
    Reads config.json directly from disk, bypassing get_config()'s lru_cache.
    library_roots written by POST /admin/config must be honoured immediately
    for tab folder validation — get_config()/config.LIBRARY_ROOT are cached
    at import time and would otherwise silently validate against stale roots
    until the process restarts.
    """
    config_path = REPO_ROOT / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _configured_library_roots() -> list[str]:
    cfg = _read_config_fresh()
    root = cfg.get("library_root", "")
    return cfg.get("library_roots", [root] if root else [])


def _custom_tab_to_dict(tab: CustomTab) -> dict:
    return {
        "id": tab.id,
        "name": tab.name,
        "folder_path": tab.folder_path,
        "visible": tab.visible,
        "view_mode": tab.view_mode,
        "basis_type": tab.basis_type,
        "field_value": tab.field_value,
        "created_at": tab.created_at.isoformat() if tab.created_at else None,
    }


def _validate_tab_folder(folder_path: str) -> dict | None:
    """Validates folder_path exists; returns a warning dict (or None) if it
    falls outside every configured library root, or wraps one entirely."""
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder_path}")

    roots = _configured_library_roots()
    if not roots:
        return {"warning": "No library roots are configured — tab content cannot be validated."}

    under_any  = any(is_under(folder_path, root) for root in roots)
    wraps_root = any(is_under(root, folder_path) for root in roots)

    if not under_any:
        return {"warning": "This folder is outside all configured library roots — "
                            "the tab will show 0 issues unless it overlaps a scanned location."}
    if wraps_root:
        return {"warning": "This folder contains an entire library root — "
                            "the tab will show the same content as 'All'."}
    return None


@router.get("/admin/custom-tabs")
def list_custom_tabs(db: Session = Depends(get_db)):
    """List all stored tabs (visible and hidden), creation order."""
    tabs = db.query(CustomTab).order_by(CustomTab.created_at).all()
    return [_custom_tab_to_dict(t) for t in tabs]


@router.post("/admin/custom-tabs")
def create_custom_tab(payload: dict = Body(...), db: Session = Depends(get_db)):
    basis_type = (payload.get("basis_type") or "folder").strip()
    if basis_type not in ("folder", "favorites", "genre", "reading_queue", "writer", "publisher"):
        raise HTTPException(status_code=400, detail="basis_type must be 'folder', 'favorites', 'genre', 'reading_queue', 'writer', or 'publisher'")

    if basis_type == "favorites":
        # CUSTOM_TABS_SPEC.md §10.2 — no name/folder_path required, server
        # assigns fixed values, at most one such tab ever.
        existing = db.query(CustomTab).filter(CustomTab.basis_type == "favorites").first()
        if existing:
            raise HTTPException(status_code=409, detail="A Favourites tab already exists.")

        tab = CustomTab(
            name="Favourites", folder_path="", visible=True,
            view_mode="flat", basis_type="favorites",
        )
        db.add(tab)
        db.commit()
        return _custom_tab_to_dict(tab)

    if basis_type == "reading_queue":
        # CUSTOM_TABS_SPEC.md §10.10 — mirrors the favourites branch above:
        # no name/folder_path required, server assigns fixed values, at most
        # one such tab ever.
        existing = db.query(CustomTab).filter(CustomTab.basis_type == "reading_queue").first()
        if existing:
            raise HTTPException(status_code=409, detail="A Reading Queue tab already exists.")

        tab = CustomTab(
            name="Reading Queue", folder_path="", visible=True,
            view_mode="flat", basis_type="reading_queue",
        )
        db.add(tab)
        db.commit()
        return _custom_tab_to_dict(tab)

    if basis_type == "genre":
        # CUSTOM_TABS_SPEC.md §10.9 — one tab per distinct genre value (not
        # "one ever" like favourites); name is just the genre name, no
        # folder_path. field_value carries which genre this tab is scoped to.
        genre_value = (payload.get("field_value") or "").strip()
        if not genre_value:
            raise HTTPException(status_code=400, detail="field_value (genre name) is required")

        existing = (
            db.query(CustomTab)
            .filter(CustomTab.basis_type == "genre", CustomTab.field_value == genre_value)
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail=f"A Genre Library for '{genre_value}' already exists.")

        tab = CustomTab(
            name=genre_value, folder_path="", visible=True,
            view_mode="flat", basis_type="genre", field_value=genre_value,
        )
        db.add(tab)
        db.commit()
        return _custom_tab_to_dict(tab)

    if basis_type == "publisher":
        # CUSTOM_TABS_SPEC.md §10.11 — mirrors the genre branch above: one tab
        # per distinct publisher value, name is just the publisher name, no
        # folder_path. field_value carries which publisher this tab is scoped to.
        publisher_value = (payload.get("field_value") or "").strip()
        if not publisher_value:
            raise HTTPException(status_code=400, detail="field_value (publisher name) is required")

        existing = (
            db.query(CustomTab)
            .filter(CustomTab.basis_type == "publisher", CustomTab.field_value == publisher_value)
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail=f"A Publisher Library for '{publisher_value}' already exists.")

        tab = CustomTab(
            name=publisher_value, folder_path="", visible=True,
            view_mode="flat", basis_type="publisher", field_value=publisher_value,
        )
        db.add(tab)
        db.commit()
        return _custom_tab_to_dict(tab)

    if basis_type == "writer":
        # CUSTOM_TABS_SPEC.md §10.12 — same shape as genre/publisher, but the
        # dimension is person-based (Tier 4 Item 3): field_value stores the
        # writer's Person.id (as a string), not a raw name, since matches_field()
        # resolves writer credits by person_id. name is set to the resolved
        # Person.name so the tab displays a readable label, not a numeric id.
        person_id_raw = (payload.get("field_value") or "").strip()
        if not person_id_raw:
            raise HTTPException(status_code=400, detail="field_value (writer person_id) is required")
        try:
            person_id = int(person_id_raw)
        except ValueError:
            raise HTTPException(status_code=400, detail="field_value must be a valid person_id")

        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise HTTPException(status_code=400, detail="No such person")

        existing = (
            db.query(CustomTab)
            .filter(CustomTab.basis_type == "writer", CustomTab.field_value == str(person_id))
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail=f"A Writer Library for '{person.name}' already exists.")

        tab = CustomTab(
            name=person.name, folder_path="", visible=True,
            view_mode="flat", basis_type="writer", field_value=str(person_id),
        )
        db.add(tab)
        db.commit()
        return _custom_tab_to_dict(tab)

    name = (payload.get("name") or "").strip()
    folder_path = (payload.get("folder_path") or "").strip()
    view_mode = (payload.get("view_mode") or "flat").strip()
    if not name or not folder_path:
        raise HTTPException(status_code=400, detail="name and folder_path are required")
    if view_mode not in VALID_VIEW_MODES:
        raise HTTPException(status_code=400, detail="view_mode must be 'flat' or 'folder'")

    warning = _validate_tab_folder(folder_path)

    tab = CustomTab(
        name=name, folder_path=normalize_path(folder_path), visible=True,
        view_mode=view_mode, basis_type="folder",
    )
    db.add(tab)
    db.commit()

    result = _custom_tab_to_dict(tab)
    if warning:
        result.update(warning)
    return result


@router.patch("/admin/custom-tabs/{tab_id}")
def update_custom_tab(tab_id: int, payload: dict = Body(...), db: Session = Depends(get_db)):
    tab = db.query(CustomTab).filter(CustomTab.id == tab_id).first()
    if not tab:
        raise HTTPException(status_code=404, detail="Custom tab not found")

    if tab.basis_type in ("favorites", "genre", "reading_queue", "writer", "publisher"):
        # CUSTOM_TABS_SPEC.md §10.4/10.9/10.10/10.11/10.12 — favourites/genre/
        # reading-queue/publisher/writer basis rows only allow name/visible
        # edits; folder_path, basis_type, and field_value are locked, and
        # view_mode is forced to stay Flat.
        locked_keys = {"folder_path", "basis_type", "field_value"} & payload.keys()
        if locked_keys:
            raise HTTPException(
                status_code=400,
                detail=f"This tab does not allow changing: {', '.join(sorted(locked_keys))}",
            )
        if "view_mode" in payload and payload["view_mode"] != "flat":
            raise HTTPException(status_code=400, detail="This tab must stay in Flat view")

    warning = None

    if "name" in payload:
        name = (payload["name"] or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="name cannot be empty")
        tab.name = name

    if "folder_path" in payload:
        folder_path = (payload["folder_path"] or "").strip()
        if not folder_path:
            raise HTTPException(status_code=400, detail="folder_path cannot be empty")
        warning = _validate_tab_folder(folder_path)
        tab.folder_path = normalize_path(folder_path)

    if "visible" in payload:
        tab.visible = bool(payload["visible"])

    if "view_mode" in payload:
        view_mode = (payload["view_mode"] or "").strip()
        if view_mode not in VALID_VIEW_MODES:
            raise HTTPException(status_code=400, detail="view_mode must be 'flat' or 'folder'")
        tab.view_mode = view_mode

    db.commit()

    result = _custom_tab_to_dict(tab)
    if warning:
        result.update(warning)
    return result


@router.delete("/admin/custom-tabs/{tab_id}")
def delete_custom_tab(tab_id: int, db: Session = Depends(get_db)):
    """Hard-deletes the tab definition only — no file-system side effects."""
    tab = db.query(CustomTab).filter(CustomTab.id == tab_id).first()
    if not tab:
        raise HTTPException(status_code=404, detail="Custom tab not found")
    db.delete(tab)
    db.commit()
    return {"message": "Custom tab deleted"}


@router.get("/admin/browse")
def admin_browse_directory(path: str = Query(None)):
    """
    Folder-only directory listing for the Custom Tabs folder picker.
    Scoped to ALL configured library_roots (plural) — distinct from
    /editor/full/browse, which is file/XML-oriented and scoped to a single root.
    """
    roots = _configured_library_roots()
    if not roots:
        raise HTTPException(status_code=400, detail="No library roots configured")

    target = path or roots[0]

    if not any(is_under(target, root) for root in roots):
        raise HTTPException(status_code=403, detail="Path is outside all configured library roots")

    if not os.path.isdir(target):
        raise HTTPException(status_code=404, detail="Directory not found")

    items = []
    try:
        for name in sorted(os.listdir(target), key=str.lower):
            full_path = os.path.join(target, name)
            if os.path.isdir(full_path):
                items.append({"name": name, "path": full_path})
    except (OSError, PermissionError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"path": target, "roots": roots, "items": items}


@router.get("/admin/scan-root/browse")
def browse_scan_root(path: str = Query(None)):
    """
    Unrestricted directory listing for the Scan Root folder picker (Library
    Folders §5) — unlike /admin/browse above, this one is NOT scoped to
    configured library_roots: adding a new scan root means picking a folder
    that is, by definition, not inside any root yet. Same shared file_picker
    pattern already used by Rename/Convert/Processing Folder (ADMIN_SPEC.md
    §12), not the library-scoped Custom Tabs picker.
    """
    target = path
    if not target:
        root = get_library_root()
        # No usable library_root yet (the exact "adding the first scan root"
        # case) — fall back to the server's own install drive rather than a
        # path that doesn't exist, so the picker always opens somewhere real.
        target = root if root and os.path.isdir(root) else os.path.splitdrive(str(REPO_ROOT))[0] + "\\"
    try:
        return file_picker.list_directory(target)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Directory not found")
    except PermissionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/admin/scan-root/drives")
def list_scan_root_drives():
    return {"drives": file_picker.list_drives()}


# ---------------------------------------------------------------------------
# POST /api/admin/browse-folder-dialog
# Native OS folder picker for the Scheduled Backup destination (ADMIN_SPEC.md
# §9) — unlike /admin/browse above, this destination is explicitly meant to
# live outside the library (a different drive, USB, or cloud-sync folder), so
# the library-scoped tree-view picker doesn't apply here. Frontend and backend
# always run on the same machine for this app, so a native dialog opened by
# the backend is the same thing as the user opening one themselves — except
# for a remote-admin session, where it would open on the wrong (server)
# machine, hence the local-only gate.
# ---------------------------------------------------------------------------

@router.post("/admin/browse-folder-dialog")
async def browse_folder_dialog(request: Request):
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})

    import asyncio

    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, _show_folder_dialog)
    return {"path": path}


def _show_folder_dialog() -> str | None:
    import tkinter
    from tkinter import filedialog

    root = tkinter.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.askdirectory(title="Choose Backup Destination")
    finally:
        root.destroy()
    return selected or None


# ---------------------------------------------------------------------------
# Home Page Strips — admin-editable home page strips (HOME_STRIPS_SPEC.md)
# ---------------------------------------------------------------------------

MAX_NON_DEFAULT_HOME_STRIPS = 5
HOME_STRIP_FIELD_NAMES = {"genre", "publisher", "writer", "artist", "format", "decade", "year", "rating", "bw", "reading_queue"}
HOME_STRIP_SORT_FIELDS = {"title", "newest", "recent"}


def _home_strip_to_dict(strip: HomeStrip) -> dict:
    return {
        "id": strip.id,
        "is_default": strip.is_default,
        "name": strip.name,
        "basis_type": strip.basis_type,
        "field_name": strip.field_name,
        "field_value": strip.field_value,
        "folder_path": strip.folder_path,
        "order_mode": strip.order_mode,
        "sort_field": strip.sort_field,
        "visible": strip.visible,
        "position": strip.position,
        "created_at": strip.created_at.isoformat() if strip.created_at else None,
    }


def _validate_strip_payload(payload: dict) -> tuple[str | None, dict | None]:
    """Validates a non-default strip's basis/order fields. Returns (error, warning)."""
    basis_type = payload.get("basis_type")
    if basis_type not in ("field", "folder"):
        return "basis_type must be 'field' or 'folder'", None

    warning = None
    if basis_type == "field":
        field_name = payload.get("field_name")
        field_value = (payload.get("field_value") or "").strip()
        if field_name not in HOME_STRIP_FIELD_NAMES:
            return f"field_name must be one of: {', '.join(sorted(HOME_STRIP_FIELD_NAMES))}", None
        if field_name != "reading_queue" and not field_value:
            return "field_value is required for a field-based strip", None
    else:
        folder_path = (payload.get("folder_path") or "").strip()
        if not folder_path:
            return "folder_path is required for a folder-based strip", None
        warning = _validate_tab_folder(folder_path)

    order_mode = payload.get("order_mode")
    if order_mode not in ("random", "fixed"):
        return "order_mode must be 'random' or 'fixed'", None
    if order_mode == "fixed" and payload.get("sort_field") not in HOME_STRIP_SORT_FIELDS:
        return f"sort_field must be one of: {', '.join(sorted(HOME_STRIP_SORT_FIELDS))} when order_mode is 'fixed'", None

    return None, warning


@router.get("/admin/home-strips")
def list_home_strips(db: Session = Depends(get_db)):
    """List all rows (default + added, visible + hidden), in position order."""
    strips = db.query(HomeStrip).order_by(HomeStrip.position).all()
    return [_home_strip_to_dict(s) for s in strips]


@router.post("/admin/home-strips")
def create_home_strip(payload: dict = Body(...), db: Session = Depends(get_db)):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    error, warning = _validate_strip_payload(payload)
    if error:
        raise HTTPException(status_code=400, detail=error)

    non_default_count = db.query(func.count(HomeStrip.id)).filter(HomeStrip.is_default == False).scalar()  # noqa: E712
    if non_default_count >= MAX_NON_DEFAULT_HOME_STRIPS:
        raise HTTPException(
            status_code=409,
            detail=f"Maximum of {MAX_NON_DEFAULT_HOME_STRIPS} added strips already reached — delete one first.",
        )

    max_position = db.query(func.max(HomeStrip.position)).scalar()
    basis_type = payload["basis_type"]

    strip = HomeStrip(
        is_default=False,
        name=name,
        basis_type=basis_type,
        field_name=payload.get("field_name") if basis_type == "field" else None,
        field_value=(payload.get("field_value") or "").strip() if basis_type == "field" else None,
        folder_path=normalize_path(payload["folder_path"]) if basis_type == "folder" else None,
        order_mode=payload.get("order_mode"),
        sort_field=payload.get("sort_field") if payload.get("order_mode") == "fixed" else None,
        visible=True,
        position=(max_position + 1) if max_position is not None else 0,
    )
    db.add(strip)
    db.commit()

    result = _home_strip_to_dict(strip)
    if warning:
        result.update(warning)
    return result


@router.patch("/admin/home-strips/reorder")
def reorder_home_strips(payload: list[dict] = Body(...), db: Session = Depends(get_db)):
    """Bulk position update: [{id, position}, ...], covering default and
    added rows together since reordering mixes them freely. Registered
    before /admin/home-strips/{strip_id} — that route's int(strip_id)
    conversion would otherwise 422 on the literal path segment "reorder"
    before this handler is ever reached."""
    ids = [item["id"] for item in payload]
    strips = db.query(HomeStrip).filter(HomeStrip.id.in_(ids)).all()
    strip_map = {s.id: s for s in strips}

    for item in payload:
        strip = strip_map.get(item["id"])
        if not strip:
            raise HTTPException(status_code=404, detail=f"Home strip {item['id']} not found")
        strip.position = int(item["position"])

    db.commit()
    return [_home_strip_to_dict(s) for s in db.query(HomeStrip).order_by(HomeStrip.position).all()]


@router.patch("/admin/home-strips/{strip_id}")
def update_home_strip(strip_id: int, payload: dict = Body(...), db: Session = Depends(get_db)):
    strip = db.query(HomeStrip).filter(HomeStrip.id == strip_id).first()
    if not strip:
        raise HTTPException(status_code=404, detail="Home strip not found")

    if strip.is_default:
        # Default rows: only `position` may ever change.
        extra_keys = set(payload.keys()) - {"position"}
        if extra_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Default strips only allow changing position (rejected: {', '.join(sorted(extra_keys))})",
            )
        if "position" in payload:
            strip.position = int(payload["position"])
        db.commit()
        return _home_strip_to_dict(strip)

    warning = None
    if "visible" in payload:
        strip.visible = bool(payload["visible"])
    if "position" in payload:
        strip.position = int(payload["position"])

    basis_keys = {"name", "basis_type", "field_name", "field_value", "folder_path", "order_mode", "sort_field"}
    if basis_keys & payload.keys():
        merged = {
            "basis_type": payload.get("basis_type", strip.basis_type),
            "field_name": payload.get("field_name", strip.field_name),
            "field_value": payload.get("field_value", strip.field_value),
            "folder_path": payload.get("folder_path", strip.folder_path),
            "order_mode": payload.get("order_mode", strip.order_mode),
            "sort_field": payload.get("sort_field", strip.sort_field),
        }
        error, warning = _validate_strip_payload(merged)
        if error:
            raise HTTPException(status_code=400, detail=error)

        if "name" in payload:
            name = (payload["name"] or "").strip()
            if not name:
                raise HTTPException(status_code=400, detail="name cannot be empty")
            strip.name = name

        strip.basis_type = merged["basis_type"]
        if merged["basis_type"] == "field":
            strip.field_name = merged["field_name"]
            strip.field_value = (merged["field_value"] or "").strip()
            strip.folder_path = None
        else:
            strip.folder_path = normalize_path(merged["folder_path"])
            strip.field_name = None
            strip.field_value = None
        strip.order_mode = merged["order_mode"]
        strip.sort_field = merged["sort_field"] if merged["order_mode"] == "fixed" else None

    db.commit()

    result = _home_strip_to_dict(strip)
    if warning:
        result.update(warning)
    return result


@router.delete("/admin/home-strips/{strip_id}")
def delete_home_strip(strip_id: int, db: Session = Depends(get_db)):
    """Hard-deletes a non-default strip's definition only."""
    strip = db.query(HomeStrip).filter(HomeStrip.id == strip_id).first()
    if not strip:
        raise HTTPException(status_code=404, detail="Home strip not found")
    if strip.is_default:
        raise HTTPException(status_code=400, detail="Default strips cannot be deleted")
    db.delete(strip)
    db.commit()
    return {"message": "Home strip deleted"}
