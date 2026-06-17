"""
ComicVault — Progress Router
POST /api/progress/{issue_id}   Update reading status and current page
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

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


# ---------------------------------------------------------------------------
# GET /api/reading/continue
# ---------------------------------------------------------------------------

@router.get("/reading/continue")
def get_continue_reading(db: Session = Depends(get_db)):
    """
    Issues currently in-progress (status='reading'), ordered by most recently
    read. Used by the home page 'Continue Reading' strip.
    """
    rows = (
        db.query(ReadingProgress, Issue)
        .join(Issue, ReadingProgress.issue_id == Issue.id)
        .filter(ReadingProgress.status == "reading", Issue.missing == False)
        .order_by(ReadingProgress.last_read_at.desc())
        .limit(15)
        .all()
    )
    return [
        {
            "id": iss.id,
            "series": iss.series,
            "number": iss.number,
            "year": iss.year,
            "cover_path": f"/api/cover/{iss.id}",
            "current_page": rp.current_page,
            "page_count": iss.page_count,
            "status": rp.status,
        }
        for rp, iss in rows
    ]
