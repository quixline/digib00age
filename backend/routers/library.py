"""
ComicVault — Library Router
GET /api/library          All series with cover, issue count, unread count
GET /api/library?group=   Filter by Series or Singles
GET /api/series/{id}      Series detail + all issues with read status
GET /api/issue/{id}       Full issue metadata
GET /api/search?q=        Full-text search
GET /api/browse/publishers
GET /api/browse/genres
GET /api/browse/arcs
GET /api/browse/formats
GET /api/reading/continue
GET /api/reading/unread
GET /api/people/fuzzy-match  Closest existing Person to a typed name (editor warn-on-save)
"""

from __future__ import annotations

import difflib
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import CustomTab, Issue, IssueCredit, IssueGenre, Person, ReadingProgress
from backend.path_utils import is_under, matches_field

router = APIRouter(tags=["library"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _progress_for(issue_id: int, db: Session) -> ReadingProgress | None:
    return db.query(ReadingProgress).filter(ReadingProgress.issue_id == issue_id).first()


def _credited_people(issue: Issue, role: str) -> list[dict]:
    """
    {person_id, name} per person credited on `issue` for `role` (Tier 4 Item 3) —
    feeds the issue detail page's clickable Writer/Artist credit links. Only
    writer/penciller are surfaced anywhere in the UI today (Section 20.8).
    """
    return [
        {"person_id": c.person_id, "name": c.person.name}
        for c in issue.credits if c.role == role
    ]


def _issue_to_dict(issue: Issue, progress: ReadingProgress | None) -> dict:
    """Full issue metadata dict, used by /issue/{id} and series lists."""
    return {
        "id": issue.id,
        "series": issue.series,
        "volume": issue.volume,
        "number": issue.number,
        "title": issue.title,
        "year": issue.year,
        "month": issue.month,
        "publisher": issue.publisher,
        "format": issue.format,
        "format_group": issue.format_group,
        "summary": issue.summary,
        "story_arc": issue.story_arc,
        "story_arc_number": issue.story_arc_number,
        "writer": issue.writer,
        "penciller": issue.penciller,
        "writers": _credited_people(issue, "writer"),
        "pencillers": _credited_people(issue, "penciller"),
        "inker": issue.inker,
        "colorist": issue.colorist,
        "letterer": issue.letterer,
        "cover_artist": issue.cover_artist,
        "characters": issue.characters,
        "teams": issue.teams,
        "locations": issue.locations,
        "age_rating": issue.age_rating,
        "language": issue.language,
        "black_and_white": issue.black_and_white,
        "manga": issue.manga,
        "favorites": issue.favorites,
        "personal_rating": issue.personal_rating,
        "page_count": issue.page_count,
        "count": issue.count,
        "genres": [g.genre_name for g in issue.genres],
        "cover_path": f"/api/cover/{issue.id}",
        "metadata_source": issue.metadata_source,
        "missing": issue.missing,
        "date_added": issue.date_added.isoformat() if issue.date_added else None,
        # Reading progress
        "read_status": progress.status if progress else "unread",
        "current_page": progress.current_page if progress else 0,
        "last_read_at": progress.last_read_at.isoformat() if progress and progress.last_read_at else None,
    }


def _series_cover_issue(series_name: str, db: Session) -> Issue | None:
    """
    Returns the representative cover issue for a series:
    lowest issue number, or first by id if numbers aren't numeric.
    """
    issues = (
        db.query(Issue)
        .filter(Issue.series == series_name, Issue.missing == False)
        .all()
    )
    if not issues:
        return None

    def sort_key(i: Issue):
        try:
            return float(i.number) if i.number else 9999
        except (ValueError, TypeError):
            return 9999

    return sorted(issues, key=sort_key)[0]


# ---------------------------------------------------------------------------
# GET /api/library
# ---------------------------------------------------------------------------

@router.get("/library")
def get_library(
    group: Optional[str] = Query(None, description="Filter by 'Series' or 'Singles'"),
    tab_id: Optional[int] = Query(None, description="Filter to a custom tab's folder_path"),
    folder_path: Optional[str] = Query(None, description="Filter to an ad-hoc folder (e.g. a home strip's 'view all' link)"),
    field: Optional[str] = Query(None, description="One of: genre, publisher, writer, artist, format, decade, year, rating, bw"),
    value: Optional[str] = Query(None, description="Value to match for `field`"),
    db: Session = Depends(get_db),
):
    """
    Returns one entry per unique series name, with cover, issue count,
    and unread count. Optionally filtered by format_group, by a custom
    tab's folder (CUSTOM_TABS_SPEC.md), by an ad-hoc folder_path, or by a
    single field+value (HOME_STRIPS_SPEC.md's field-based strips) — issues
    are filtered by file_path/field BEFORE the per-series groupby below, so
    a series spanning both sides of the filter shows counts scoped to the
    matching issues only (intended for folder/field-scoped views).
    """
    query = db.query(Issue).filter(Issue.missing == False)
    if group:
        query = query.filter(Issue.format_group == group)

    tab_folder = folder_path
    if tab_id is not None:
        tab = db.query(CustomTab).filter(CustomTab.id == tab_id).first()
        if not tab:
            raise HTTPException(status_code=404, detail="Custom tab not found")
        tab_folder = tab.folder_path

    all_issues = query.all()
    if tab_folder:
        all_issues = [i for i in all_issues if is_under(i.file_path, tab_folder)]
    if field and value is not None:
        all_issues = [i for i in all_issues if matches_field(i, field, value)]

    # Group by series name
    series_map: dict[str, list[Issue]] = {}
    for issue in all_issues:
        series_map.setdefault(issue.series, []).append(issue)

    result = []
    for series_name, issues in sorted(series_map.items(), key=lambda x: x[0].lstrip("'\"").lower()):
        cover_issue = sorted(
            issues,
            key=lambda i: (float(i.number) if i.number and _is_numeric(i.number) else 9999, i.id)
        )[0]

        # Count unread
        issue_ids = [i.id for i in issues]
        read_statuses = (
            db.query(ReadingProgress)
            .filter(ReadingProgress.issue_id.in_(issue_ids))
            .all()
        )
        read_map = {p.issue_id: p.status for p in read_statuses}
        unread_count = sum(
            1 for i in issues if read_map.get(i.id, "unread") == "unread"
        )

        # Aggregate values across all issues in the series
        genres       = sorted({g.genre_name for i in issues for g in i.genres})
        read_count   = sum(1 for i in issues if read_map.get(i.id, "unread") == "read")
        reading_count= sum(1 for i in issues if read_map.get(i.id, "unread") == "reading")
        writers      = sorted({i.writer    for i in issues if i.writer})
        artists      = sorted({i.penciller for i in issues if i.penciller})
        formats      = sorted({i.format    for i in issues if i.format})
        age_ratings  = sorted({i.age_rating for i in issues if i.age_rating})
        has_bw       = any(i.black_and_white for i in issues)

        result.append({
            "series": series_name,
            "issue_count": len(issues),
            "unread_count": unread_count,
            "read_count": read_count,
            "reading_count": reading_count,
            "cover_issue_id": cover_issue.id,
            "cover_path": f"/api/cover/{cover_issue.id}",
            "publisher": cover_issue.publisher,
            "year": cover_issue.year,
            "format_group": cover_issue.format_group,
            "page_count": cover_issue.page_count,
            "summary": cover_issue.summary,
            "genres": genres,
            "writers": writers,
            "artists": artists,
            "formats": formats,
            "age_ratings": age_ratings,
            "has_bw": has_bw,
            "series_anchor_id": cover_issue.id,
            "favorites": cover_issue.favorites,
            "personal_rating": cover_issue.personal_rating,
        })

    return result


def _is_numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# GET /api/series/{id}
# id here is any issue id belonging to the series — we look up by series name
# ---------------------------------------------------------------------------

@router.get("/series/{issue_id}")
def get_series(issue_id: int, db: Session = Depends(get_db)):
    """
    Returns series header info + all issues in that series, with read status.
    The {issue_id} is used to identify which series — any issue id in the series works.
    """
    anchor = db.query(Issue).filter(Issue.id == issue_id).first()
    if not anchor:
        raise HTTPException(status_code=404, detail="Issue not found")

    series_name = anchor.series

    issues = (
        db.query(Issue)
        .filter(Issue.series == series_name)
        .order_by(Issue.volume, Issue.number, Issue.id)
        .all()
    )

    # Sort issues: numeric numbers first, then non-numeric, then None
    def issue_sort(i: Issue):
        if i.number is None:
            return (2, 0, i.id)
        try:
            return (0, float(i.number), i.id)
        except (ValueError, TypeError):
            return (1, 0, i.id)

    issues_sorted = sorted(issues, key=issue_sort)

    # Build issue list with progress
    issue_list = []
    for iss in issues_sorted:
        prog = _progress_for(iss.id, db)
        issue_list.append({
            "id": iss.id,
            "number": iss.number,
            "title": iss.title,
            "year": iss.year,
            "cover_path": f"/api/cover/{iss.id}",
            "story_arc": iss.story_arc,
            "story_arc_number": iss.story_arc_number,
            "format": iss.format,
            "black_and_white": iss.black_and_white,
            "missing": iss.missing,
            "read_status": prog.status if prog else "unread",
            "current_page": prog.current_page if prog else 0,
            "page_count": iss.page_count,
            "summary": iss.summary,
            "favorites": iss.favorites,
            "personal_rating": iss.personal_rating,
        })

    # Cover issue for series header
    cover_issue = _series_cover_issue(series_name, db)

    # Genres for the series
    all_genres = list({
        g.genre_name
        for i in issues
        for g in i.genres
    })

    return {
        "series": series_name,
        "publisher": anchor.publisher,
        "year": anchor.year,
        "format_group": anchor.format_group,
        "cover_path": f"/api/cover/{cover_issue.id}" if cover_issue else None,
        "genres": sorted(all_genres),
        "issue_count": len(issues),
        "issues": issue_list,
    }


# ---------------------------------------------------------------------------
# GET /api/issue/{id}
# ---------------------------------------------------------------------------

@router.get("/issue/{issue_id}")
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    """Full issue metadata including reading progress."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    progress = _progress_for(issue_id, db)

    # Find next issue in series (by number)
    next_issue = _find_adjacent_issue(issue, db, direction="next")
    prev_issue = _find_adjacent_issue(issue, db, direction="prev")

    data = _issue_to_dict(issue, progress)
    data["next_issue_id"] = next_issue.id if next_issue else None
    data["prev_issue_id"] = prev_issue.id if prev_issue else None
    return data


def _find_adjacent_issue(issue: Issue, db: Session, direction: str) -> Issue | None:
    """Find next or previous issue in the same series by number."""
    siblings = (
        db.query(Issue)
        .filter(Issue.series == issue.series, Issue.missing == False)
        .all()
    )

    def sort_key(i: Issue):
        if i.number is None:
            return (2, 0, i.id)
        try:
            return (0, float(i.number), i.id)
        except (ValueError, TypeError):
            return (1, 0, i.id)

    sorted_siblings = sorted(siblings, key=sort_key)
    ids = [i.id for i in sorted_siblings]

    if issue.id not in ids:
        return None

    idx = ids.index(issue.id)
    if direction == "next" and idx + 1 < len(sorted_siblings):
        return sorted_siblings[idx + 1]
    if direction == "prev" and idx - 1 >= 0:
        return sorted_siblings[idx - 1]
    return None


# ---------------------------------------------------------------------------
# GET /api/search?q=
# ---------------------------------------------------------------------------

@router.get("/search")
def search(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """
    Search across series, title, writer, characters, story_arc.
    Returns up to 100 results.
    """
    pattern = f"%{q}%"
    issues = (
        db.query(Issue)
        .filter(
            Issue.missing == False,
            or_(
                Issue.series.ilike(pattern),
                Issue.title.ilike(pattern),
                Issue.writer.ilike(pattern),
                Issue.characters.ilike(pattern),
                Issue.story_arc.ilike(pattern),
                Issue.publisher.ilike(pattern),
            ),
        )
        .order_by(Issue.series, Issue.number)
        .limit(100)
        .all()
    )

    results = []
    for issue in issues:
        prog = _progress_for(issue.id, db)
        results.append({
            "id": issue.id,
            "series": issue.series,
            "number": issue.number,
            "title": issue.title,
            "year": issue.year,
            "publisher": issue.publisher,
            "format_group": issue.format_group,
            "cover_path": f"/api/cover/{issue.id}",
            "read_status": prog.status if prog else "unread",
        })

    return {"query": q, "count": len(results), "results": results}


# ---------------------------------------------------------------------------
# GET /api/browse/publishers
# ---------------------------------------------------------------------------

@router.get("/browse/publishers")
def browse_publishers(db: Session = Depends(get_db)):
    """Publisher list with series counts."""
    rows = (
        db.query(Issue.publisher, func.count(func.distinct(Issue.series)).label("series_count"))
        .filter(Issue.missing == False, Issue.publisher != None, Issue.publisher != "")
        .group_by(Issue.publisher)
        .order_by(Issue.publisher)
        .all()
    )
    return [{"publisher": r.publisher, "series_count": r.series_count} for r in rows]


# ---------------------------------------------------------------------------
# GET /api/browse/genres
# ---------------------------------------------------------------------------

@router.get("/browse/genres")
def browse_genres(db: Session = Depends(get_db)):
    """Genre list with issue counts."""
    rows = (
        db.query(IssueGenre.genre_name, func.count(IssueGenre.issue_id).label("issue_count"))
        .group_by(IssueGenre.genre_name)
        .order_by(IssueGenre.genre_name)
        .all()
    )
    return [{"genre": r.genre_name, "issue_count": r.issue_count} for r in rows]


# ---------------------------------------------------------------------------
# GET /api/browse/arcs
# ---------------------------------------------------------------------------

@router.get("/browse/arcs")
def browse_arcs(db: Session = Depends(get_db)):
    """Story arc list with issue counts."""
    rows = (
        db.query(Issue.story_arc, func.count(Issue.id).label("issue_count"))
        .filter(Issue.missing == False, Issue.story_arc != None, Issue.story_arc != "")
        .group_by(Issue.story_arc)
        .order_by(Issue.story_arc)
        .all()
    )
    return [{"story_arc": r.story_arc, "issue_count": r.issue_count} for r in rows]


# ---------------------------------------------------------------------------
# GET /api/browse/formats
# ---------------------------------------------------------------------------

@router.get("/browse/formats")
def browse_formats(db: Session = Depends(get_db)):
    """All Format values with counts (for format badge filtering)."""
    rows = (
        db.query(Issue.format, func.count(Issue.id).label("issue_count"))
        .filter(Issue.missing == False, Issue.format != None, Issue.format != "")
        .group_by(Issue.format)
        .order_by(Issue.format)
        .all()
    )
    return [{"format": r.format, "issue_count": r.issue_count} for r in rows]


# ---------------------------------------------------------------------------
# GET /api/reading/continue
# ---------------------------------------------------------------------------

@router.get("/reading/continue")
def reading_continue(db: Session = Depends(get_db)):
    """Issues with status='reading', sorted by most recently read."""
    progress_rows = (
        db.query(ReadingProgress)
        .filter(ReadingProgress.status == "reading")
        .order_by(ReadingProgress.last_read_at.desc())
        .limit(20)
        .all()
    )

    results = []
    for prog in progress_rows:
        issue = db.query(Issue).filter(Issue.id == prog.issue_id).first()
        if issue and not issue.missing:
            results.append({
                "id": issue.id,
                "series": issue.series,
                "number": issue.number,
                "cover_path": f"/api/cover/{issue.id}",
                "current_page": prog.current_page,
                "page_count": issue.page_count,
                "last_read_at": prog.last_read_at.isoformat() if prog.last_read_at else None,
            })

    return results


# ---------------------------------------------------------------------------
# GET /api/browse/writers
# ---------------------------------------------------------------------------

def _browse_people(role: str, db: Session) -> list[dict]:
    """Deduped people credited in `role`, with series counts (Tier 4 Item 3 —
    was grouped by raw CSV blob before; one comma-joined multi-name string
    used to show up as a single dropdown option)."""
    rows = (
        db.query(Person.id, Person.name, func.count(func.distinct(Issue.series)).label("series_count"))
        .join(IssueCredit, IssueCredit.person_id == Person.id)
        .join(Issue, Issue.id == IssueCredit.issue_id)
        .filter(IssueCredit.role == role, Issue.missing == False)
        .group_by(Person.id, Person.name)
        .order_by(Person.name)
        .all()
    )
    return [{"person_id": r.id, "name": r.name, "series_count": r.series_count} for r in rows]


@router.get("/browse/writers")
def browse_writers(db: Session = Depends(get_db)):
    """Distinct writers (deduped people, Tier 4 Item 3) with series counts."""
    return _browse_people("writer", db)


# ---------------------------------------------------------------------------
# GET /api/browse/artists
# ---------------------------------------------------------------------------

@router.get("/browse/artists")
def browse_artists(db: Session = Depends(get_db)):
    """Distinct artists/pencillers (deduped people, Tier 4 Item 3) with series counts."""
    return _browse_people("penciller", db)


# ---------------------------------------------------------------------------
# GET /api/people/fuzzy-match — editor save-time warn-on-save (Tier 4 Item 3)
# ---------------------------------------------------------------------------

@router.get("/people/fuzzy-match")
def people_fuzzy_match(
    name: str = Query(..., min_length=1),
    threshold: float = Query(0.82),
    db: Session = Depends(get_db),
):
    """
    Closest existing Person to `name`, for the editor's non-blocking save-time
    warning — same fuzzy-match approach as the one-time migration's candidate-
    duplicate detection (backend/migrate_people.py, now removed). Returns null
    if `name` already matches an existing person exactly (nothing to warn
    about) or nothing is close enough.
    """
    typed = name.strip()
    if not typed:
        return {"closest_match": None}

    best = None
    best_ratio = 0.0
    for person_id, person_name in db.query(Person.id, Person.name).all():
        if person_name == typed:
            return {"closest_match": None}
        ratio = difflib.SequenceMatcher(None, typed.lower(), person_name.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best = (person_id, person_name)

    if best and best_ratio >= threshold:
        return {"closest_match": {"person_id": best[0], "name": best[1], "similarity": round(best_ratio, 3)}}
    return {"closest_match": None}


# ---------------------------------------------------------------------------
# GET /api/browse/decades
# ---------------------------------------------------------------------------

@router.get("/browse/decades")
def browse_decades(db: Session = Depends(get_db)):
    """Distinct decades (e.g. 1970, 1980 … current) with issue counts."""
    years = (
        db.query(Issue.year, func.count(Issue.id).label("issue_count"))
        .filter(Issue.missing == False, Issue.year != None)
        .group_by(Issue.year)
        .all()
    )
    decade_map: dict[int, int] = {}
    for row in years:
        decade = (row.year // 10) * 10
        decade_map[decade] = decade_map.get(decade, 0) + row.issue_count

    return [
        {"decade": d, "issue_count": c}
        for d, c in sorted(decade_map.items())
    ]


# ---------------------------------------------------------------------------
# GET /api/browse/years
# ---------------------------------------------------------------------------

@router.get("/browse/years")
def browse_years(db: Session = Depends(get_db)):
    """
    Distinct years with issue counts — the web UI's own Year filter dropdown
    derives this client-side from /api/library, but HOME_STRIPS_SPEC.md's
    field-based strips need a server-side source the same way the other 8
    filter dimensions already have one.
    """
    rows = (
        db.query(Issue.year, func.count(Issue.id).label("issue_count"))
        .filter(Issue.missing == False, Issue.year != None)
        .group_by(Issue.year)
        .order_by(Issue.year.desc())
        .all()
    )
    return [{"year": r.year, "issue_count": r.issue_count} for r in rows]


# ---------------------------------------------------------------------------
# GET /api/browse/ratings
# ---------------------------------------------------------------------------

@router.get("/browse/ratings")
def browse_ratings(db: Session = Depends(get_db)):
    """Distinct age_rating values with issue counts."""
    rows = (
        db.query(Issue.age_rating, func.count(Issue.id).label("issue_count"))
        .filter(Issue.missing == False, Issue.age_rating != None, Issue.age_rating != "")
        .group_by(Issue.age_rating)
        .order_by(Issue.age_rating)
        .all()
    )
    return [{"rating": r.age_rating, "issue_count": r.issue_count} for r in rows]


# ---------------------------------------------------------------------------
# GET /api/reading/unread
# ---------------------------------------------------------------------------

@router.get("/reading/unread")
def reading_unread(
    group: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """All unread issues, newest first by year then id."""
    query = db.query(Issue).filter(Issue.missing == False)
    if group:
        query = query.filter(Issue.format_group == group)

    all_issues = query.order_by(Issue.year.desc(), Issue.id.desc()).all()

    # Exclude issues that have a progress row with status != unread
    read_ids = {
        p.issue_id
        for p in db.query(ReadingProgress)
        .filter(ReadingProgress.status != "unread")
        .all()
    }

    results = []
    for issue in all_issues:
        if issue.id not in read_ids:
            results.append({
                "id": issue.id,
                "series": issue.series,
                "number": issue.number,
                "year": issue.year,
                "cover_path": f"/api/cover/{issue.id}",
                "format_group": issue.format_group,
            })

    return results
