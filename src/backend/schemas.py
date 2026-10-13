"""
backend/schemas.py — shared Pydantic response schemas, reused across
multiple endpoints. Router-specific, single-use response shapes stay
inline in their own router file instead, matching the existing convention
for request-body models (admin_auth.py, progress.py, sync.py).

Added 2026-10-13 adopting response_model typing — see DECISIONS.md
"Lightweight typed API contracts: response_model + JSDoc, not codegen".
Phase 1 (library.py) only; coverage grows router-by-router in later
sessions, not retrofitted everywhere at once. GET /library and
GET /series/{issue_id} are deliberately NOT covered yet — both have
genuinely bespoke, branch-dependent shapes that deserve their own
dedicated pass rather than being forced into this one.
"""
from __future__ import annotations

from pydantic import BaseModel


class PersonCredit(BaseModel):
    person_id: int
    name: str


class IssueOut(BaseModel):
    """Exact shape of library.py's _issue_to_dict() — used standalone for
    Folder View's file list (TabFolderOut.files) and as the base for
    IssueDetailOut/IssueWithFolderOut below."""
    id: int
    series: str
    volume: int | None
    number: str | None
    title: str | None
    year: int | None
    month: int | None
    publisher: str | None
    format: str | None
    format_group: str | None
    summary: str | None
    story_arc: str | None
    story_arc_number: int | None
    writer: str | None
    penciller: str | None
    writers: list[PersonCredit]
    pencillers: list[PersonCredit]
    characters: str | None
    teams: str | None
    locations: str | None
    age_rating: str | None
    language: str | None
    black_and_white: bool
    manga: str
    favorites: bool
    flagged_for_review: bool
    queued_for_reading: bool
    personal_rating: int | None
    page_count: int | None
    count: int | None
    genres: list[str]
    cover_path: str
    metadata_source: str | None
    missing: bool
    date_added: str | None
    read_status: str
    current_page: int
    last_read_at: str | None


class IssueDetailOut(IssueOut):
    """GET /issue/{issue_id} — IssueOut plus prev/next series navigation."""
    next_issue_id: int | None
    prev_issue_id: int | None


class IssueWithFolderOut(IssueOut):
    """Folder View search results — IssueOut plus the issue's folder path
    relative to the tab's root."""
    relative_folder: str


class FolderEntryOut(BaseModel):
    name: str
    issue_count: int
    cover_path: str | None
    has_favorite: bool
    has_flagged_review: bool
    year_min: int | None
    year_max: int | None


class TabFolderOut(BaseModel):
    """GET /library/tab/{tab_id}/folder"""
    tab_id: int
    path: str
    folders: list[FolderEntryOut]
    files: list[IssueOut]


class TabFolderMarkReadOut(BaseModel):
    """POST /library/tab/{tab_id}/folder/mark-read"""
    updated: list[int]


class TabSearchOut(BaseModel):
    """GET /library/tab/{tab_id}/search"""
    tab_id: int
    query: str
    count: int
    results: list[IssueWithFolderOut]


class SearchResultOut(BaseModel):
    id: int
    series: str
    number: str | None
    title: str | None
    year: int | None
    publisher: str | None
    format_group: str | None
    cover_path: str
    read_status: str


class SearchOut(BaseModel):
    """GET /search"""
    query: str
    count: int
    results: list[SearchResultOut]


class PublisherCount(BaseModel):
    publisher: str
    series_count: int


class GenreCount(BaseModel):
    genre: str
    issue_count: int


class StoryArcCount(BaseModel):
    story_arc: str
    issue_count: int


class FormatCount(BaseModel):
    format: str
    issue_count: int


class DecadeCount(BaseModel):
    decade: int
    issue_count: int


class YearCount(BaseModel):
    year: int
    issue_count: int


class RatingCount(BaseModel):
    rating: str
    issue_count: int


class PersonCount(BaseModel):
    person_id: int
    name: str
    series_count: int


class ContinueReadingOut(BaseModel):
    """GET /reading/continue"""
    id: int
    series: str
    number: str | None
    cover_path: str
    current_page: int
    page_count: int | None
    last_read_at: str | None


class UnreadIssueOut(BaseModel):
    """GET /reading/unread"""
    id: int
    series: str
    number: str | None
    year: int | None
    cover_path: str
    format_group: str | None


class SeriesCardOut(BaseModel):
    """GET /library — one entry per series (or, for a partially-queued
    reading-queue tab, one entry per queued issue card instead — see
    get_library()). The two branches are identical except `number`, which
    only the per-issue branch sets; `link_as_issue` is the real
    discriminator the frontend uses (app.js buildCoverCard()), not the
    presence of this field — confirmed its only frontend read is a
    truthy-check (`if (s.number) ...`), so treating it as always-optional
    is a verified no-op for the branch that omits it. NOT the same shape
    as IssueOut — `writers`/`artists` here are plain `list[str]` (raw
    aggregated values), not `list[PersonCredit]`."""
    series: str
    title: str | None
    number: str | None = None
    issue_count: int
    unread_count: int
    read_count: int
    reading_count: int
    cover_issue_id: int
    cover_path: str
    publisher: str | None
    year: int | None
    format_group: str | None
    page_count: int | None
    current_page: int
    summary: str | None
    genres: list[str]
    writers: list[str]
    artists: list[str]
    formats: list[str]
    age_ratings: list[str]
    has_bw: bool
    series_anchor_id: int
    favorites: bool
    flagged_for_review: bool
    queued_for_reading: bool
    personal_rating: int | None
    link_as_issue: bool


class SeriesIssueOut(BaseModel):
    """GET /series/{issue_id}'s issue list items — a distinct, smaller
    shape from IssueOut (no writers/pencillers credit lists, no
    metadata_source, no next/prev navigation)."""
    id: int
    number: str | None
    title: str | None
    year: int | None
    cover_path: str
    story_arc: str | None
    story_arc_number: int | None
    format: str | None
    black_and_white: bool
    publisher: str | None
    writer: str | None
    age_rating: str | None
    missing: bool
    read_status: str
    current_page: int
    page_count: int | None
    summary: str | None
    genres: list[str]
    favorites: bool
    flagged_for_review: bool
    queued_for_reading: bool
    personal_rating: int | None


class SeriesDetailOut(BaseModel):
    """GET /series/{issue_id}"""
    series: str
    publisher: str | None
    year: int | None
    format_group: str | None
    cover_path: str | None
    genres: list[str]
    issue_count: int
    issues: list[SeriesIssueOut]
    filtered_field: str | None
    filtered_value: str | None
    filtered_query: str | None
    total_issue_count: int


class FuzzyMatchResult(BaseModel):
    person_id: int
    name: str
    similarity: float


class FuzzyMatchOut(BaseModel):
    """GET /people/fuzzy-match"""
    closest_match: FuzzyMatchResult | None
