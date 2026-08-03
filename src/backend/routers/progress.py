"""
digib00age — Progress Router
POST /api/progress/{issue_id}   Update reading status and current page
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from backend.config import THUMBNAIL_DIR
from backend.database import get_db
from backend.models import Issue, ReadingProgress



router = APIRouter(tags=["progress"])

VALID_STATUSES = {"unread", "reading", "read"}


# ---------------------------------------------------------------------------
# Request body
# ---------------------------------------------------------------------------

class ProgressUpdate(BaseModel):
    status: Optional[str] = None      # "unread" | "reading" | "read"
    current_page: Optional[int] = None  # 0-indexed page number

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(VALID_STATUSES)}")
        return v

    @field_validator("current_page")
    @classmethod
    def validate_page(cls, v):
        if v is not None and v < 0:
            raise ValueError("current_page cannot be negative")
        return v


# ---------------------------------------------------------------------------
# POST /api/progress/{issue_id}
# ---------------------------------------------------------------------------

def _get_or_create_progress(issue_id: int, db: Session) -> ReadingProgress:
    """Find an issue's ReadingProgress row, or create a default one. Shared
    by the single-issue and bulk mark-read/unread paths."""
    progress = (
        db.query(ReadingProgress)
        .filter(ReadingProgress.issue_id == issue_id)
        .first()
    )
    if not progress:
        progress = ReadingProgress(
            issue_id=issue_id,
            status="unread",
            current_page=0,
        )
        db.add(progress)
    return progress


@router.post("/progress/{issue_id}")
def update_progress(
    issue_id: int,
    body: ProgressUpdate,
    db: Session = Depends(get_db),
):
    """
    Create or update reading progress for an issue.

    Called by the reader on every page turn, and when the user manually
    marks an issue read/unread from the issue detail page.

    Auto-promotion rules:
    - If current_page > 0 and status is still "unread" → promote to "reading"
    - If current_page is the last page → caller should pass status="read"
      (the reader JS does this automatically on reaching the final page)
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    progress = _get_or_create_progress(issue_id, db)

    # Apply updates
    if body.current_page is not None:
        progress.current_page = body.current_page

    if body.status is not None:
        progress.status = body.status
    elif body.current_page is not None and body.current_page > 0:
        # Auto-promote from unread to reading when pages are being turned
        if progress.status == "unread":
            progress.status = "reading"

    # Always update last_read_at when anything changes
    progress.last_read_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(progress)

    return {
        "issue_id": issue_id,
        "status": progress.status,
        "current_page": progress.current_page,
        "last_read_at": progress.last_read_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Bulk endpoints — multi-select Read/Unread/Favorite/Rate
# Registered before the /progress/{issue_id}/mark-read /mark-unread routes
# below: Starlette matches path templates in registration order, and
# "/progress/bulk/mark-read" would otherwise match "/progress/{issue_id}/mark-read"
# first (with "bulk" parsed as issue_id) since both are two path segments.
#
# Missing/unknown issue ids in the list are silently skipped (no 404) —
# unlike admin.py's home-strip reorder, there's no ordering invariant to
# protect here, so a soft no-op is friendlier than failing the whole batch.
# ---------------------------------------------------------------------------

class BulkIssueIds(BaseModel):
    issue_ids: list[int]


class BulkRating(BaseModel):
    issue_ids: list[int]
    rating: int   # 0 (clear) or 1-5

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if not 0 <= v <= 5:
            raise ValueError("rating must be between 0 (clear) and 5")
        return v


@router.post("/progress/bulk/mark-read")
def bulk_mark_read(body: BulkIssueIds, db: Session = Depends(get_db)):
    for issue_id in body.issue_ids:
        progress = _get_or_create_progress(issue_id, db)
        progress.status = "read"
        progress.last_read_at = datetime.now(timezone.utc)
    db.commit()
    return {"updated": body.issue_ids}


@router.post("/progress/bulk/mark-unread")
def bulk_mark_unread(body: BulkIssueIds, db: Session = Depends(get_db)):
    for issue_id in body.issue_ids:
        progress = _get_or_create_progress(issue_id, db)
        progress.status = "unread"
        progress.current_page = 0
        progress.last_read_at = datetime.now(timezone.utc)
    db.commit()
    return {"updated": body.issue_ids}


@router.post("/progress/bulk/favorite")
def bulk_add_favorite(body: BulkIssueIds, db: Session = Depends(get_db)):
    issues = db.query(Issue).filter(Issue.id.in_(body.issue_ids)).all()
    for issue in issues:
        issue.favorites = True
    db.commit()
    return {"updated": [i.id for i in issues]}


@router.post("/progress/bulk/unfavorite")
def bulk_remove_favorite(body: BulkIssueIds, db: Session = Depends(get_db)):
    issues = db.query(Issue).filter(Issue.id.in_(body.issue_ids)).all()
    for issue in issues:
        issue.favorites = False
    db.commit()
    return {"updated": [i.id for i in issues]}


@router.post("/progress/bulk/queue-reading")
def bulk_queue_reading(body: BulkIssueIds, db: Session = Depends(get_db)):
    issues = db.query(Issue).filter(Issue.id.in_(body.issue_ids)).all()
    for issue in issues:
        issue.queued_for_reading = True
    db.commit()
    return {"updated": [i.id for i in issues]}


@router.post("/progress/bulk/unqueue-reading")
def bulk_unqueue_reading(body: BulkIssueIds, db: Session = Depends(get_db)):
    issues = db.query(Issue).filter(Issue.id.in_(body.issue_ids)).all()
    for issue in issues:
        issue.queued_for_reading = False
    db.commit()
    return {"updated": [i.id for i in issues]}


@router.post("/progress/bulk/flag-review")
def bulk_flag_review(body: BulkIssueIds, db: Session = Depends(get_db)):
    issues = db.query(Issue).filter(Issue.id.in_(body.issue_ids)).all()
    for issue in issues:
        issue.flagged_for_review = True
    db.commit()
    return {"updated": [i.id for i in issues]}


@router.post("/progress/bulk/unflag-review")
def bulk_unflag_review(body: BulkIssueIds, db: Session = Depends(get_db)):
    issues = db.query(Issue).filter(Issue.id.in_(body.issue_ids)).all()
    for issue in issues:
        issue.flagged_for_review = False
    db.commit()
    return {"updated": [i.id for i in issues]}


@router.post("/progress/bulk/rate")
def bulk_set_rating(body: BulkRating, db: Session = Depends(get_db)):
    issues = db.query(Issue).filter(Issue.id.in_(body.issue_ids)).all()
    for issue in issues:
        issue.personal_rating = body.rating
    db.commit()
    return {"updated": [i.id for i in issues]}


@router.post("/progress/bulk/delete")
def bulk_delete(body: BulkIssueIds, db: Session = Depends(get_db)):
    """Permanently deletes the DB row AND the comic file on disk for each
    given issue. A failed file unlink (locked file, permissions) does not
    block the DB delete — it's reported back via file_errors instead."""
    issues = db.query(Issue).filter(Issue.id.in_(body.issue_ids)).all()
    deleted_ids = []
    file_errors = []
    for issue in issues:
        try:
            Path(issue.file_path).unlink(missing_ok=True)
        except OSError as e:
            file_errors.append({"issue_id": issue.id, "error": str(e)})
        thumb = THUMBNAIL_DIR / f"{issue.id}.jpg"
        try:
            thumb.unlink(missing_ok=True)
        except OSError:
            pass
        db.delete(issue)  # cascades to genres/progress/credits (models.py)
        deleted_ids.append(issue.id)
    db.commit()
    return {"deleted": deleted_ids, "file_errors": file_errors}


# ---------------------------------------------------------------------------
# POST /api/progress/{issue_id}/mark-read   (convenience shortcut)
# POST /api/progress/{issue_id}/mark-unread
# ---------------------------------------------------------------------------

@router.post("/progress/{issue_id}/mark-read")
def mark_read(issue_id: int, db: Session = Depends(get_db)):
    """Mark an issue as fully read. Convenience endpoint for the UI toggle."""
    return update_progress(issue_id, ProgressUpdate(status="read"), db)


@router.post("/progress/{issue_id}/mark-unread")
def mark_unread(issue_id: int, db: Session = Depends(get_db)):
    """Reset an issue to unread. Convenience endpoint for the UI toggle."""
    return update_progress(
        issue_id,
        ProgressUpdate(status="unread", current_page=0),
        db,
    )


@router.post("/progress/{issue_id}/flag-review")
def flag_review(issue_id: int, db: Session = Depends(get_db)):
    """Flag a single issue for review. Convenience endpoint for the Issue Detail toggle."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    issue.flagged_for_review = True
    db.commit()
    return {"id": issue.id, "flagged_for_review": True}


@router.post("/progress/{issue_id}/unflag-review")
def unflag_review(issue_id: int, db: Session = Depends(get_db)):
    """Clear the review flag on a single issue. Convenience endpoint for the Issue Detail toggle."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    issue.flagged_for_review = False
    db.commit()
    return {"id": issue.id, "flagged_for_review": False}

