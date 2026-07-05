"""
ComicVault — Sync Router (v2.5 Item 3)
POST /api/sync/progress   Batch-reconcile reading progress pushed from an
                          offline mobile client (last-write-wins by timestamp).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Issue
from backend.routers.progress import _get_or_create_progress

router = APIRouter(tags=["sync"])


# ---------------------------------------------------------------------------
# Request body
# ---------------------------------------------------------------------------

class SyncItem(BaseModel):
    issue_id: int
    current_page: Optional[int] = None
    status: Optional[str] = None
    updated_at: str  # ISO 8601 — client-captured page-turn/status-change moment


class SyncBatch(BaseModel):
    items: list[SyncItem]


def _parse_client_ts(raw: str) -> datetime:
    """
    Parse the client's captured timestamp. Accepts a trailing "Z" regardless
    of Python version (datetime.fromisoformat only gained native "Z" support
    in 3.11). A naive result is treated as UTC — this should only happen if
    the client ever sends a naive string, which the Flutter side must not do
    (it always captures via DateTime.now().toUtc(), never the local-time
    DateTime.now() — see flutter_app/lib/services/sync_store.dart). Getting
    this wrong would silently skew every last-write-wins comparison by the
    device's UTC offset.
    """
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# POST /api/sync/progress
# ---------------------------------------------------------------------------

@router.post("/sync/progress")
def sync_progress(body: SyncBatch, db: Session = Depends(get_db)):
    """
    Reconcile a batch of offline-captured progress updates against the
    server's canonical reading_progress rows. Last-write-wins by timestamp:
    the client's captured updated_at is compared against the server's
    last_read_at. A missing server row (never read on this issue before) or
    a tie always goes to the incoming client write.

    Each item commits independently — a dropped connection mid-batch leaves
    already-applied rows committed and the rest simply retried by the client
    on the next sync trigger. Unknown issue_id is skipped (not_found) rather
    than failing the whole batch, matching progress.py's bulk-endpoint
    "silently skip unknown ids" pattern.
    """
    results = []
    for item in body.items:
        issue = db.query(Issue).filter(Issue.id == item.issue_id).first()
        if not issue:
            results.append({"issue_id": item.issue_id, "outcome": "not_found"})
            continue

        progress = _get_or_create_progress(item.issue_id, db)
        client_ts = _parse_client_ts(item.updated_at)

        server_ts = progress.last_read_at
        if server_ts is not None and server_ts.tzinfo is None:
            server_ts = server_ts.replace(tzinfo=timezone.utc)

        client_wins = server_ts is None or client_ts >= server_ts

        if client_wins:
            if item.current_page is not None:
                progress.current_page = item.current_page
            if item.status is not None:
                progress.status = item.status
            elif (
                item.current_page is not None
                and item.current_page > 0
                and progress.status == "unread"
            ):
                progress.status = "reading"
            progress.last_read_at = client_ts
            db.commit()
            db.refresh(progress)
            results.append({
                "issue_id": item.issue_id,
                "outcome": "client_applied",
                "status": progress.status,
                "current_page": progress.current_page,
                "last_read_at": progress.last_read_at.isoformat(),
            })
        else:
            results.append({
                "issue_id": item.issue_id,
                "outcome": "server_kept",
                "status": progress.status,
                "current_page": progress.current_page,
                "last_read_at": progress.last_read_at.isoformat(),
            })

    return {"results": results}
