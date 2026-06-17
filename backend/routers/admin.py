"""
ComicVault — Admin Router
GET  /api/admin/stats        Library statistics
POST /api/scan               Trigger full background rescan
POST /api/scan/file?path=    Rescan single file (called by Flask editor)
GET  /api/scan/status        Live scan progress for admin UI
POST /api/admin/backup       Copy comicvault.db to dated backup file
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import get_config, PROJECT_ROOT
from backend.database import get_db, SessionLocal
from backend.models import Issue, ReadingProgress

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

    return {
        "total_issues": total_issues,
        "series_count": series_count,
        "singles_count": singles_count,
        "read_count": read_count,
        "reading_count": reading_count,
        "missing_count": missing_count,
        "filename_metadata_count": filename_metadata_count,
        "library_root": config.get("library_root"),
        "db_path": str(PROJECT_ROOT / config.get("db_path", "backend/comicvault.db")),
        "scan_state": {
            "running": sp.running,
            "finished_at": (sp.finished_at.isoformat() + "Z") if sp.finished_at else None,
            "total_files": sp.total,
            "new_files": sp.new,
            "updated_files": get_changes_last_cycle(),
        },
    }


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
        "current_file": "",
        "log": sp.log[-200:],
        "error": None,
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

    if not path.lower().endswith(".cbz"):
        raise HTTPException(status_code=400, detail="Only CBZ files are supported")

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
    }


# ---------------------------------------------------------------------------
# POST /api/admin/config  — write editable config values
# ---------------------------------------------------------------------------

@router.post("/admin/config")
def save_admin_config(data: dict):
    config_path = PROJECT_ROOT / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    if "library_roots" in data:
        roots = [r.strip() for r in data["library_roots"] if r.strip()]
        cfg["library_roots"] = roots
        if roots:
            cfg["library_root"] = roots[0]
    elif "library_root" in data and data["library_root"].strip():
        cfg["library_root"] = data["library_root"].strip()

    if "scan_exclude" in data:
        cfg["scan_exclude"] = [e.strip() for e in data["scan_exclude"] if e.strip()]

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    return {"message": "Config saved"}


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
# POST /api/admin/backup
# ---------------------------------------------------------------------------

@router.post("/admin/backup")
def backup_database():
    """
    Copies comicvault.db to a dated backup file in the same directory.
    e.g. comicvault_backup_2025-01-15_14-32-00.db
    """
    config = get_config()
    db_path = PROJECT_ROOT / config.get("db_path", "backend/comicvault.db")

    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Database file not found")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"comicvault_backup_{timestamp}.db"
    backup_path = db_path.parent / backup_name

    try:
        shutil.copy2(str(db_path), str(backup_path))
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Backup failed: {exc}")

    return {
        "message": "Backup created successfully",
        "backup_file": str(backup_path),
        "size_bytes": backup_path.stat().st_size,
    }
