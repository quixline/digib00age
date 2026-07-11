"""
ComicVault — Editor (Basic) Router
GET    /api/editor/genres          Editable genre list — shared by Basic and Full editor UIs
POST   /api/editor/genres          Add a genre (Admin page) — Tier 4 Item 1, comicvault-changes.md
DELETE /api/editor/genres/{name}   Remove a genre (Admin page); blocked if it's the last one
GET    /api/editor/formats         Editable format list — same mechanism as genres
POST   /api/editor/formats         Add a format (Admin page)
DELETE /api/editor/formats/{name}  Remove a format (Admin page); blocked if it's the last one
GET    /api/editor/{issue_id}             Load current field values for the popup (live from the file)
POST   /api/editor/{issue_id}             Validate + merge synchronously, then queue the archive
                                           rewrite + rescan in the background; returns immediately
GET    /api/editor/{issue_id}/save-status Poll target for the above
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import SessionLocal, get_db
from backend.editor.archive_io import (
    extract_xml_from_archive,
    find_xml_in_archive,
    get_archive_page_count,
    write_comicinfo_to_cbz,
)
from backend.editor.field_merge import build_xml_from_fields
from backend.editor.formats import add_format, load_formats, remove_format
from backend.editor.genres import add_genre, load_genres, remove_genre
from backend.editor.validation import validate_enforced_fields
from backend.editor.xml_parser import COMICINFO_TAGS, parse_comicinfo_xml
from backend.models import Issue
from backend.scanner import scan_single_file

router = APIRouter(tags=["editor"])


@router.get("/editor/genres")
def get_genres():
    """Current genre list, read fresh from genres.json on every call (no caching)."""
    return load_genres()


@router.post("/editor/genres")
def post_genre(payload: dict = Body(...)):
    """Add a genre to the editable list (Admin page)."""
    try:
        return add_genre(payload.get("name", ""))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/editor/genres/{name}")
def delete_genre(name: str):
    """Remove a genre from the editable list. Blocked if it's the last remaining value.
    Existing issues tagged with it are not touched (no cascade) — the Admin UI is
    expected to confirm with the user first when the issue count is non-zero (counts
    come from GET /api/browse/genres, fetched before this call)."""
    try:
        return remove_genre(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/editor/formats")
def get_formats():
    """Current format list, read fresh from formats.json on every call (no caching)."""
    return load_formats()


@router.post("/editor/formats")
def post_format(payload: dict = Body(...)):
    """Add a format to the editable list (Admin page)."""
    try:
        return add_format(payload.get("name", ""))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/editor/formats/{name}")
def delete_format(name: str):
    """Remove a format from the editable list. Blocked if it's the last remaining value.
    Existing issues with this Format value are not touched (no cascade) — the Admin UI
    is expected to confirm with the user first when the issue count is non-zero (counts
    come from GET /api/browse/formats, fetched before this call)."""
    try:
        return remove_format(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _load_issue_or_404(issue_id: int, db: Session) -> Issue:
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if not os.path.exists(issue.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return issue


def _read_original_xml(issue: Issue) -> str | None:
    xml_files = find_xml_in_archive(issue.file_path)
    if not xml_files:
        return None
    return extract_xml_from_archive(issue.file_path, xml_files[0])


# ---------------------------------------------------------------------------
# Save progress — per-issue (not a single global singleton like the
# Processing Tools use), since the Basic Editor can be opened against
# different issues from different tabs/devices at once. Never pruned —
# grows one entry per issue ever saved this process's lifetime, acceptable
# at home-server scale.
# ---------------------------------------------------------------------------

@dataclass
class EditorSaveProgress:
    running: bool = False
    result: Optional[dict] = None
    error: Optional[str] = None
    finished_at: Optional[datetime] = None


_save_progress: dict[int, EditorSaveProgress] = {}


@router.get("/editor/{issue_id}")
def get_editor_fields(issue_id: int, db: Session = Depends(get_db)):
    """
    Load current field values for the Basic editor popup. Reads the live XML
    out of the file — the DB may be slightly stale relative to it, so the
    file is the source of truth (EDITOR_SPEC.md Section 6.1).
    """
    issue = _load_issue_or_404(issue_id, db)

    original_xml = _read_original_xml(issue)
    fields = (
        parse_comicinfo_xml(original_xml)
        if original_xml
        else {tag: "" for tag in COMICINFO_TAGS}
    )

    # PageCount is auto-counted from the archive, not trusted from a
    # possibly-stale XML value (Section 4, More tab).
    fields["PageCount"] = str(get_archive_page_count(issue.file_path))

    progress = _save_progress.get(issue_id)
    return {
        "issue_id": issue.id,
        "fields": fields,
        "saving": bool(progress and progress.running),
    }


def _finish_save(issue_id: int, original_path: str, xml_content: str) -> None:
    """
    Background half of a save: the slow archive rebuild + rescan, run after
    the request has already returned. Uses its own DB session — the
    request-scoped session (and the `issue` ORM object loaded from it) is
    already closed by the time this runs, so everything here is looked up
    fresh by id (mirrors backend/routers/admin.py's _run_scan_background()).
    """
    db = SessionLocal()
    try:
        try:
            new_path = write_comicinfo_to_cbz(original_path, xml_content)
        except Exception as exc:
            _save_progress[issue_id] = EditorSaveProgress(
                running=False,
                error=f"Failed to write archive: {exc}",
                finished_at=datetime.now(),
            )
            return

        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        # CBR source rebuilds as a sibling .cbz (EDITOR_SPEC.md §3.2, v2.4
        # Item 5/11) — update this row's tracking to the new path *and
        # flush* before rescanning, since the session is autoflush=False and
        # scan_single_file looks up the row by file_path.
        if issue and new_path != issue.file_path:
            issue.file_path = new_path
            issue.container_format = "cbz"
            db.flush()

        # Commits internally (backend/scanner.py) — no separate commit call
        # needed here, same as the original synchronous code relied on.
        scan_single_file(new_path, db)

        updated = db.query(Issue).filter(Issue.id == issue_id).first()
        _save_progress[issue_id] = EditorSaveProgress(
            running=False,
            result={
                "issue_id": issue_id,
                "series": updated.series if updated else None,
                "number": updated.number if updated else None,
            },
            finished_at=datetime.now(),
        )
    except Exception as exc:
        logging.getLogger(__name__).error(
            "Editor background save failed for issue %s: %s", issue_id, exc
        )
        _save_progress[issue_id] = EditorSaveProgress(
            running=False, error=str(exc), finished_at=datetime.now()
        )
    finally:
        db.close()


@router.post("/editor/{issue_id}")
def save_editor_fields(
    issue_id: int,
    background_tasks: BackgroundTasks,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Validate and merge submitted field values into the live XML
    synchronously (422 immediately on bad input), then queue the archive
    rebuild + rescan as a background task and return right away — the
    in-app replacement for the old POST /api/scan/file webhook, now
    fire-and-forget rather than blocking the modal on the rebuild
    (EDITOR_SPEC.md Section 6.1).
    """
    issue = _load_issue_or_404(issue_id, db)

    existing = _save_progress.get(issue_id)
    if existing and existing.running:
        raise HTTPException(
            status_code=409, detail="A save is already in progress for this issue"
        )

    raw_fields = payload.get("fields", {})
    field_values = {k: v for k, v in raw_fields.items() if k in COMICINFO_TAGS}
    # NeedsReview is never part of the submitted form (EDITOR_SPEC.md 9.2) —
    # build_xml_from_fields only touches tags present in the payload, so it
    # won't self-clear via the normal preservation rule without this.
    field_values["NeedsReview"] = ""

    errors = validate_enforced_fields(field_values)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    original_xml = _read_original_xml(issue)
    xml_content = build_xml_from_fields(field_values, original_xml)

    # Set running=True synchronously, before queuing — closes the race
    # window between two fast back-to-back POSTs for the same issue.
    _save_progress[issue_id] = EditorSaveProgress(running=True)
    background_tasks.add_task(_finish_save, issue_id, issue.file_path, xml_content)

    return {"success": True, "pending": True, "issue_id": issue_id}


@router.get("/editor/{issue_id}/save-status")
def get_save_status(issue_id: int):
    progress = _save_progress.get(issue_id)
    if progress is None:
        return {"running": False, "result": None, "error": None, "finished_at": None}
    return {
        "running": progress.running,
        "result": progress.result,
        "error": progress.error,
        "finished_at": progress.finished_at.isoformat() if progress.finished_at else None,
    }
