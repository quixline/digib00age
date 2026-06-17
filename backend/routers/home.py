"""
ComicVault — Home & 2000 AD Router
GET /api/home/strips        Five curated cover strips for the home page
GET /api/2000ad/years       Year list with issue counts (series='2000 AD')
GET /api/2000ad/year/{year} Issue list for one year
"""

from __future__ import annotations

import random
from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Issue, IssueGenre, ReadingProgress

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


# ---------------------------------------------------------------------------
# GET /api/home/strips
# ---------------------------------------------------------------------------

@router.get("/home/strips")
def get_home_strips(db: Session = Depends(get_db)):
    """Three curated cover strips for the home page."""
    pm, pr = _load_progress_map(db)
    genre_name, genre_items = _strip_random_genre(db, pm, pr)

    return {
        "strips": [
            {
                "id": "recently_added",
                "title": "Recently Added",
                "items": _strip_recently_added(db, pm, pr),
            },
            {
                "id": "random_unread",
                "title": "Random Unread",
                "items": _strip_random_unread(db, pm, pr),
            },
            {
                "id": "random_genre",
                "title": genre_name,
                "items": genre_items,
            },
        ]
    }


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
