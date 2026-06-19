"""
ComicVault — Home & 2000 AD Router
GET /api/home/strips        Home page strips — defaults + admin-added (HOME_STRIPS_SPEC.md)
GET /api/2000ad/years       Year list with issue counts (series='2000 AD')
GET /api/2000ad/year/{year} Issue list for one year
"""

from __future__ import annotations

import random
from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import CustomTab, HomeStrip, Issue, IssueGenre, ReadingProgress
from backend.path_utils import is_under, matches_field

router = APIRouter(tags=["home"])

STRIP_SIZE = 15


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

    return {
        "id": row.id,
        "title": row.name,
        "items": [_issue_card(i, pm, progress_rows=pr) for i in issues],
        "basis_type": row.basis_type,
        "field_name": row.field_name,
        "field_value": row.field_value,
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
    return {"custom_tabs": [{"id": t.id, "name": t.name} for t in tabs]}


# ---------------------------------------------------------------------------
# GET /api/2000ad/years
# ---------------------------------------------------------------------------

@router.get("/2000ad/years")
def get_2000ad_years(db: Session = Depends(get_db)):
    """
    Year list for the 2000 AD prog collection.
    Each entry: year, issue_count, cover path, first/last prog number.
    """
    year_rows = (
        db.query(Issue.year, func.count(Issue.id).label("issue_count"))
        .filter(Issue.series == "2000 AD", Issue.missing == False)
        .group_by(Issue.year)
        .order_by(Issue.year)
        .all()
    )

    result = []
    for row in year_rows:
        # Load only the issues for this year (≈52 rows — small)
        year_issues = (
            db.query(Issue)
            .filter(Issue.series == "2000 AD", Issue.year == row.year, Issue.missing == False)
            .all()
        )
        prog_numbers = []
        cover_issue = year_issues[0] if year_issues else None
        for iss in year_issues:
            try:
                n = int(iss.number)
                prog_numbers.append(n)
                if cover_issue is None or n < int(cover_issue.number):
                    cover_issue = iss
            except (ValueError, TypeError):
                pass

        result.append({
            "year": row.year,
            "issue_count": row.issue_count,
            "cover_path": f"/api/cover/{cover_issue.id}" if cover_issue else None,
            "first_prog": min(prog_numbers) if prog_numbers else None,
            "last_prog":  max(prog_numbers) if prog_numbers else None,
        })

    return result


# ---------------------------------------------------------------------------
# GET /api/2000ad/year/{year}
# ---------------------------------------------------------------------------

@router.get("/2000ad/year/{year}")
def get_2000ad_year(year: int, db: Session = Depends(get_db)):
    """All 2000 AD progs for one year in prog-number order, with read status."""
    issues = (
        db.query(Issue)
        .filter(Issue.series == "2000 AD", Issue.year == year, Issue.missing == False)
        .all()
    )

    def sort_key(i: Issue):
        try:
            return int(i.number)
        except (ValueError, TypeError):
            return 9999

    issues_sorted = sorted(issues, key=sort_key)

    issue_ids = [i.id for i in issues_sorted]
    prog_rows = (
        db.query(ReadingProgress)
        .filter(ReadingProgress.issue_id.in_(issue_ids))
        .all()
    )
    prog_map = {p.issue_id: p for p in prog_rows}

    return {
        "year": year,
        "issue_count": len(issues_sorted),
        "issues": [
            {
                "id": iss.id,
                "number": iss.number,
                "year": iss.year,
                "title": iss.title,
                "cover_path": f"/api/cover/{iss.id}",
                "story_arc": iss.story_arc,
                "story_arc_number": iss.story_arc_number,
                "page_count": iss.page_count,
                "missing": iss.missing,
                "read_status": prog_map[iss.id].status if iss.id in prog_map else "unread",
                "current_page": prog_map[iss.id].current_page if iss.id in prog_map else 0,
            }
            for iss in issues_sorted
        ],
    }
