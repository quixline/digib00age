"""
ComicVault — Home Router
GET /api/ping                Unauthenticated liveness check (BUG-019 — client apps need a
                             connectivity probe that isn't behind require_admin_auth)
GET /api/home/strips        Home page strips — defaults + admin-added (HOME_STRIPS_SPEC.md)
"""

from __future__ import annotations

import random
from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import CustomTab, HomeStrip, Issue, IssueGenre, Person, ReadingProgress
from backend.path_utils import is_under, matches_field

router = APIRouter(tags=["home"])

STRIP_SIZE = 15


@router.get("/ping")
async def ping():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_progress_map(db: Session) -> tuple[dict[int, str], dict[int, "ReadingProgress"]]:
    """Single query returning ({issue_id: status}, {issue_id: row}) for all progress rows."""
    rows = db.query(ReadingProgress).all()
    return (
        {r.issue_id: r.status for r in rows},
        {r.issue_id: r for r in rows},
    )


def _issue_card(issue: Issue, progress_map: dict[int, str], *,
                issue_count: int | None = None,
                series_anchor_id: int | None = None,
                progress_rows: dict | None = None) -> dict:
    prog = (progress_rows or {}).get(issue.id)
    return {
        "id": issue.id,
        "series": issue.series,
        "number": issue.number,
        "year": issue.year,
        "publisher": issue.publisher,
        "format_group": issue.format_group,
        "cover_path": f"/api/cover/{issue.id}",
        "read_status": progress_map.get(issue.id, "unread"),
        "issue_count": issue_count,
        "series_anchor_id": series_anchor_id or issue.id,
        "page_count": issue.page_count,
        "current_page": prog.current_page if prog else 0,
        "genres": [g.genre_name for g in issue.genres],
        "personal_rating": issue.personal_rating,
        "favorites": issue.favorites,
        "flagged_for_review": issue.flagged_for_review,
    }


def _issue_sort_key(i: Issue) -> tuple:
    try:
        return (0, float(i.number), i.id)
    except (ValueError, TypeError):
        return (1, 0, i.id)


# ---------------------------------------------------------------------------
# Strip builders — all use SQL-level RANDOM() / LIMIT to avoid loading the
# full issue table into Python.
# ---------------------------------------------------------------------------

def _strip_random_unread(db: Session, pm: dict[int, str], pr: dict) -> list[dict]:
    """
    Up to STRIP_SIZE random series, each represented by the FIRST unread issue
    in reading order — so a completely unread series shows #1, a partially-read
    series shows the issue immediately after the last read one.
    """
    all_unread = (
        db.query(Issue)
        .outerjoin(ReadingProgress, Issue.id == ReadingProgress.issue_id)
        .filter(
            Issue.missing == False,
            or_(
                ReadingProgress.issue_id == None,
                ReadingProgress.status == "unread",
            ),
        )
        .all()
    )

    next_per_series: dict[str, Issue] = {}
    for issue in all_unread:
        key = issue.series
        if key not in next_per_series or _issue_sort_key(issue) < _issue_sort_key(next_per_series[key]):
            next_per_series[key] = issue

    pool = list(next_per_series.values())
    if len(pool) > STRIP_SIZE:
        pool = random.sample(pool, STRIP_SIZE)

    return [_issue_card(i, pm, progress_rows=pr) for i in pool]


def _strip_recently_added(db: Session, pm: dict[int, str], pr: dict) -> list[dict]:
    """15 most recently added issues — simple ORDER BY date_added DESC."""
    issues = (
        db.query(Issue)
        .filter(Issue.missing == False)
        .order_by(Issue.date_added.desc())
        .limit(STRIP_SIZE)
        .all()
    )
    return [_issue_card(i, pm, progress_rows=pr) for i in issues]


def _strip_random_genre(db: Session, pm: dict[int, str], pr: dict) -> tuple[str, list[dict]]:
    """Pick one genre at random, return 15 random issues from it."""
    genre_rows = db.query(IssueGenre.genre_name).distinct().all()
    if not genre_rows:
        return ("", [])

    genre_name = random.choice(genre_rows).genre_name

    issues = (
        db.query(Issue)
        .join(IssueGenre, Issue.id == IssueGenre.issue_id)
        .filter(
            Issue.missing == False,
            IssueGenre.genre_name == genre_name,
        )
        .order_by(func.random())
        .limit(STRIP_SIZE)
        .all()
    )
    return (genre_name, [_issue_card(i, pm, progress_rows=pr) for i in issues])


def _strip_continue_reading(db: Session, pm: dict[int, str], pr: dict) -> list[dict]:
    """Issues with status='reading', most recently read first — same query as
    the standalone GET /api/reading/continue (library.py), which keeps serving
    the Flutter app unchanged; this is the web home page's copy of that logic,
    now resolved as a builtin home_strips row instead of a separate fetch."""
    issues = (
        db.query(Issue)
        .join(ReadingProgress, Issue.id == ReadingProgress.issue_id)
        .filter(ReadingProgress.status == "reading", Issue.missing == False)
        .order_by(ReadingProgress.last_read_at.desc())
        .limit(STRIP_SIZE)
        .all()
    )
    return [_issue_card(i, pm, progress_rows=pr) for i in issues]


# ---------------------------------------------------------------------------
# Field/folder strip resolution (HOME_STRIPS_SPEC.md Section 4.3)
# ---------------------------------------------------------------------------

def _sort_issues(issues: list[Issue], sort_field: str | None) -> list[Issue]:
    if sort_field == "newest":
        return sorted(issues, key=lambda i: i.year or 0, reverse=True)
    if sort_field == "recent":
        return sorted(issues, key=lambda i: i.date_added, reverse=True)
    return sorted(issues, key=lambda i: (i.series or "").lstrip("'\"").lower())


def _resolve_added_strip(row: HomeStrip, db: Session, pm: dict[int, str], pr: dict) -> dict:
    issues = db.query(Issue).filter(Issue.missing == False).all()
    if row.basis_type == "field":
        issues = [i for i in issues if matches_field(i, row.field_name, row.field_value)]
    else:
        issues = [i for i in issues if is_under(i.file_path, row.folder_path)]

    if row.order_mode == "fixed":
        issues = _sort_issues(issues, row.sort_field)[:STRIP_SIZE]
    else:
        issues = random.sample(issues, min(STRIP_SIZE, len(issues)))

    # BUG-015: writer/artist field_value is a Person.id, not human-readable —
    # resolve a display label server-side so the frontend's fieldview banner
    # doesn't have to show a raw id (mirrors admin.js's ensureHsPersonNameCache()).
    field_value_label = None
    if row.basis_type == "field" and row.field_name in ("writer", "artist"):
        try:
            person = db.query(Person).filter(Person.id == int(row.field_value)).first()
        except (TypeError, ValueError):
            person = None
        if person:
            field_value_label = person.name

    return {
        "id": row.id,
        "title": row.name,
        "items": [_issue_card(i, pm, progress_rows=pr) for i in issues],
        "basis_type": row.basis_type,
        "field_name": row.field_name,
        "field_value": row.field_value,
        "field_value_label": field_value_label,
        "folder_path": row.folder_path,
    }


def _resolve_builtin_strip(row: HomeStrip, db: Session, pm: dict[int, str], pr: dict) -> dict:
    if row.name == "Continue Reading":
        items = _strip_continue_reading(db, pm, pr)
        title = row.name
    elif row.name == "Recently Added":
        items = _strip_recently_added(db, pm, pr)
        title = row.name
    elif row.name == "Random Unread":
        items = _strip_random_unread(db, pm, pr)
        title = row.name
    elif row.name == "Random Genre":
        title, items = _strip_random_genre(db, pm, pr)
        title = title or row.name
    else:
        items, title = [], row.name
    return {"id": row.id, "title": title, "items": items, "basis_type": "builtin"}


# ---------------------------------------------------------------------------
# GET /api/home/strips
# ---------------------------------------------------------------------------

@router.get("/home/strips")
def get_home_strips(db: Session = Depends(get_db)):
    """
    All visible home_strips rows (default + admin-added), in position order,
    each resolved to up to 15 covers. Continue Reading (a default row) is
    rendered first whenever it has any matching issues, ahead of stored
    position — per HOME_STRIPS_SPEC.md Section 4.4, this overrides ordering
    for every other row, not just its own.
    """
    pm, pr = _load_progress_map(db)

    rows = db.query(HomeStrip).order_by(HomeStrip.position).all()
    rows = [r for r in rows if r.is_default or r.visible]  # visible is ignored/always-true for defaults

    continue_row = next((r for r in rows if r.is_default and r.name == "Continue Reading"), None)
    ordered_rows = [r for r in rows if r is not continue_row]

    strips = []
    if continue_row:
        strips.append(_resolve_builtin_strip(continue_row, db, pm, pr))
    for row in ordered_rows:
        if row.basis_type == "builtin":
            strips.append(_resolve_builtin_strip(row, db, pm, pr))
        else:
            strips.append(_resolve_added_strip(row, db, pm, pr))

    return {"strips": strips}


# ---------------------------------------------------------------------------
# GET /api/nav/config
# ---------------------------------------------------------------------------

@router.get("/nav/config")
def get_nav_config(db: Session = Depends(get_db)):
    """Visible custom tabs (CUSTOM_TABS_SPEC.md), creation order, for dynamic nav rendering."""
    tabs = (
        db.query(CustomTab)
        .filter(CustomTab.visible == True)  # noqa: E712
        .order_by(CustomTab.created_at)
        .all()
    )
    return {"custom_tabs": [
        {"id": t.id, "name": t.name, "view_mode": t.view_mode, "basis_type": t.basis_type}
        for t in tabs
    ]}


