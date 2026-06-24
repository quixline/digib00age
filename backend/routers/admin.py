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
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import scan_logs
from backend.config import get_config, save_config, PROJECT_ROOT
from backend.database import get_db, SessionLocal
from backend.models import CustomTab, HomeStrip, Issue, ReadingProgress
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
        "db_path": str(PROJECT_ROOT / config.get("db_path", "backend/comicvault.db")),
        "scan_state": {
            "running": sp.running,
            "finished_at": (sp.finished_at.isoformat() + "Z") if sp.finished_at else None,
            "total_files": sp.total,
            "new_files": sp.new,
            "updated_files": get_changes_last_cycle(),
        },
        "log_status": log_status,
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
        "log_size_limit_mb": cfg.get("log_size_limit_mb", 5),
        "auto_scan_frequency": cfg.get("auto_scan_frequency", "off"),
        "autostart_scan": cfg.get("autostart_scan", False),
    }


# ---------------------------------------------------------------------------
# POST /api/admin/config  — write editable config values
# ---------------------------------------------------------------------------

@router.post("/admin/config")
def save_admin_config(data: dict):
    cfg = get_config()
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

    save_config(update)

    return {"message": "Config saved"}


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
    content, exists = scan_logs.read_log(log_name)
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


# ---------------------------------------------------------------------------
# Custom Tabs — admin-managed, folder-scoped library tabs (CUSTOM_TABS_SPEC.md)
# ---------------------------------------------------------------------------

MAX_VISIBLE_CUSTOM_TABS = 4
VALID_VIEW_MODES = {"flat", "folder"}


def _read_config_fresh() -> dict:
    """
    Reads config.json directly from disk, bypassing get_config()'s lru_cache.
    library_roots written by POST /admin/config must be honoured immediately
    for tab folder validation — get_config()/config.LIBRARY_ROOT are cached
    at import time and would otherwise silently validate against stale roots
    until the process restarts.
    """
    config_path = PROJECT_ROOT / "config.json"
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
    name = (payload.get("name") or "").strip()
    folder_path = (payload.get("folder_path") or "").strip()
    view_mode = (payload.get("view_mode") or "flat").strip()
    if not name or not folder_path:
        raise HTTPException(status_code=400, detail="name and folder_path are required")
    if view_mode not in VALID_VIEW_MODES:
        raise HTTPException(status_code=400, detail="view_mode must be 'flat' or 'folder'")

    warning = _validate_tab_folder(folder_path)

    visible_count = db.query(func.count(CustomTab.id)).filter(CustomTab.visible == True).scalar()  # noqa: E712
    if visible_count >= MAX_VISIBLE_CUSTOM_TABS:
        raise HTTPException(
            status_code=409,
            detail=f"Maximum of {MAX_VISIBLE_CUSTOM_TABS} visible tabs already reached — hide one first.",
        )

    tab = CustomTab(name=name, folder_path=normalize_path(folder_path), visible=True, view_mode=view_mode)
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
        new_visible = bool(payload["visible"])
        if new_visible and not tab.visible:
            visible_count = db.query(func.count(CustomTab.id)).filter(CustomTab.visible == True).scalar()  # noqa: E712
            if visible_count >= MAX_VISIBLE_CUSTOM_TABS:
                raise HTTPException(
                    status_code=409,
                    detail=f"Maximum of {MAX_VISIBLE_CUSTOM_TABS} visible tabs already reached — hide one first.",
                )
        tab.visible = new_visible

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


# ---------------------------------------------------------------------------
# Home Page Strips — admin-editable home page strips (HOME_STRIPS_SPEC.md)
# ---------------------------------------------------------------------------

MAX_NON_DEFAULT_HOME_STRIPS = 5
HOME_STRIP_FIELD_NAMES = {"genre", "publisher", "writer", "artist", "format", "decade", "year", "rating", "bw"}
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
        if not field_value:
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
