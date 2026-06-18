"""
ComicVault — Editor (Basic) Router
GET  /api/editor/genres        Editable genre list — shared by Basic and Full editor UIs
GET  /api/editor/{issue_id}    Load current field values for the popup (live from the file)
POST /api/editor/{issue_id}    Save field values, rewrite the archive, rescan in-process
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
from backend.editor.constants import AGE_RATING_OPTIONS, FORMAT_OPTIONS
from backend.editor.field_merge import build_xml_from_fields
from backend.editor.genres import load_genres
from backend.editor.xml_parser import COMICINFO_TAGS, parse_comicinfo_xml
from backend.models import Issue
from backend.scanner import scan_single_file

router = APIRouter(tags=["editor"])


@router.get("/editor/genres")
def get_genres():
    """Current genre list, read fresh from genres.json on every call (no caching) —
    EDITOR_SPEC.md Section 4.1, Tez edits the file directly."""
    return load_genres()


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


def _validate_enforced_fields(field_values: dict) -> list[str]:
    """
    Hard validation gate per EDITOR_SPEC.md Section 4.4 — Genre/Format/AgeRating
    must each resolve to enforced values. Mirrored server-side as the source of
    truth; the popup UI also gates Save client-side so this should rarely fire
    in normal use.
    """
    errors = []

    genre_value = (field_values.get("Genre") or "").strip()
    genre_names = [g.strip() for g in genre_value.split(",") if g.strip()]
    enforced_genres = set(load_genres())
    if not genre_names:
        errors.append("Genre: at least one value is required")
    else:
        for name in genre_names:
            if name not in enforced_genres:
                errors.append(f"Genre: '{name}' is not in the enforced list")

    format_value = (field_values.get("Format") or "").strip()
    if format_value not in FORMAT_OPTIONS:
        errors.append(f"Format: '{format_value or '(blank)'}' is not in the enforced list")

    rating_value = (field_values.get("AgeRating") or "").strip()
    if rating_value not in AGE_RATING_OPTIONS:
        errors.append(f"AgeRating: '{rating_value or '(blank)'}' is not in the enforced list")

    return errors


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

    errors = _validate_enforced_fields(field_values)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    original_xml = _read_original_xml(issue)
    xml_content = build_xml_from_fields(field_values, original_xml)

    try:
        write_comicinfo_to_cbz(issue.file_path, xml_content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to write archive: {exc}")

    scan_single_file(issue.file_path, db)

    updated = db.query(Issue).filter(Issue.id == issue_id).first()
    return {
        "success": True,
        "issue_id": updated.id,
        "series": updated.series,
        "number": updated.number,
    }
