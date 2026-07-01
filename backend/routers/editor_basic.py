"""
ComicVault — Editor (Basic) Router
GET    /api/editor/genres          Editable genre list — shared by Basic and Full editor UIs
POST   /api/editor/genres          Add a genre (Admin page) — Tier 4 Item 1, comicvault-changes.md
DELETE /api/editor/genres/{name}   Remove a genre (Admin page); blocked if it's the last one
GET    /api/editor/formats         Editable format list — same mechanism as genres
POST   /api/editor/formats         Add a format (Admin page)
DELETE /api/editor/formats/{name}  Remove a format (Admin page); blocked if it's the last one
GET    /api/editor/{issue_id}      Load current field values for the popup (live from the file)
POST   /api/editor/{issue_id}      Save field values, rewrite the archive, rescan in-process
"""

import os

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
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

    return {"issue_id": issue.id, "fields": fields}


@router.post("/editor/{issue_id}")
def save_editor_fields(
    issue_id: int, payload: dict = Body(...), db: Session = Depends(get_db)
):
    """
    Save submitted field values: merge into the live XML, rebuild the
    archive, then rescan this one file in-process (the in-app replacement
    for the old POST /api/scan/file webhook — Section 6.1).
    """
    issue = _load_issue_or_404(issue_id, db)

    raw_fields = payload.get("fields", {})
    field_values = {k: v for k, v in raw_fields.items() if k in COMICINFO_TAGS}

    errors = validate_enforced_fields(field_values)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    original_xml = _read_original_xml(issue)
    xml_content = build_xml_from_fields(field_values, original_xml)

    try:
        new_path = write_comicinfo_to_cbz(issue.file_path, xml_content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to write archive: {exc}")

    # CBR source rebuilds as a sibling .cbz (EDITOR_SPEC.md §3.2, v2.4 Item
    # 5/11) — update this row's tracking to the new path *and flush* before
    # rescanning, since the session is autoflush=False and scan_single_file
    # looks up the row by file_path.
    if new_path != issue.file_path:
        issue.file_path = new_path
        issue.container_format = "cbz"
        db.flush()

    scan_single_file(new_path, db)

    updated = db.query(Issue).filter(Issue.id == issue_id).first()
    return {
        "success": True,
        "issue_id": updated.id,
        "series": updated.series,
        "number": updated.number,
    }
