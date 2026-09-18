"""
path_utils.py — shared filtering helpers used by more than one router, so
every call site applies identical logic instead of near-duplicate copies.
normalize_path/is_under: folder-path normalization and prefix-matching
(custom tab + home strip folder validation/filtering — the separator-suffixed
boundary check means a folder "C:\\Comics\\Batman" won't match "C:\\Comics\\Batman2\\...").
matches_field: the 10 field-filter dimensions shared by the browse filter bar,
Custom Tabs, and HOME_STRIPS_SPEC.md's field-based strips.
title_sort_key: the leading-article-ignoring sort key shared by every
library-listing sort site and library_move.py's shelf-filing bucket.
"""

import os
import re

from backend.models import Issue

_LEADING_QUOTE_RE = re.compile(r"^['\"]")
_LEADING_ARTICLE_RE = re.compile(r"^(the|a|an)\s+", re.IGNORECASE)


def normalize_path(path: str) -> str:
    return os.path.normpath(os.path.abspath(path))


def title_sort_key(name: str) -> str:
    """Case-insensitive sort key ignoring a leading quote and a leading
    The/A/An article — matches library_move.py's _alpha_bucket() shelf-filing
    convention, so 'A Dream' sorts under 'D', not 'A'."""
    stripped = _LEADING_ARTICLE_RE.sub("", _LEADING_QUOTE_RE.sub("", name or ""))
    return stripped.lower()


def is_under(child: str, parent: str) -> bool:
    """True if `child` is `parent` itself or a path beneath it."""
    c = normalize_path(child).lower()
    p = normalize_path(parent).lower()
    return c == p or c.startswith(p + os.sep)


def matches_field(issue: Issue, field_name: str, field_value: str) -> bool:
    """
    One of: genre, publisher, writer, artist, format, decade, year, rating, bw,
    reading_queue.
    writer/artist: field_value is a Person.id (Tier 4 Item 3) — resolved against
    the issue_credits junction, not the old raw-CSV columns.
    reading_queue: field_value is unused — queued_for_reading is a single
    per-issue boolean, so picking the field is the entire filter.
    """
    if field_name == "genre":
        return any(g.genre_name == field_value for g in issue.genres)
    if field_name == "publisher":
        return issue.publisher == field_value
    if field_name == "writer":
        return any(c.role == "writer" and c.person_id == int(field_value) for c in issue.credits)
    if field_name == "artist":
        return any(c.role == "penciller" and c.person_id == int(field_value) for c in issue.credits)
    if field_name == "format":
        return issue.format == field_value
    if field_name == "rating":
        return issue.age_rating == field_value
    if field_name == "year":
        return str(issue.year) == str(field_value)
    if field_name == "decade":
        return bool(issue.year) and (int(issue.year) // 10) * 10 == int(field_value)
    if field_name == "bw":
        return issue.black_and_white == (field_value == "yes")
    if field_name == "reading_queue":
        return issue.queued_for_reading
    return False


def cover_url(issue: Issue) -> str:
    """
    /api/cover/{id} URL with a version stamp from Issue.date_modified, so the
    URL itself changes when a rescan detects the archive changed — lets the
    browser cache covers aggressively (BUGS.md, cover-refresh-delay,
    2026-07-16) without ever serving a stale one after an edit. Second-level
    granularity matches scanner.py's own unchanged-file tolerance.
    """
    if issue.date_modified:
        return f"/api/cover/{issue.id}?v={issue.date_modified.strftime('%Y%m%d%H%M%S')}"
    return f"/api/cover/{issue.id}"


def matches_search(issue: Issue, q: str) -> bool:
    """
    Free-text match across the same fields as GET /api/search (series, title,
    writer, characters, story_arc, publisher) — used to scope GET /library and
    GET /series/{id} to matching issues *before* grouping by series, so a
    series-level result's issue_count/issues only ever reflects the issues
    that actually matched (BUG-010: a series with one matching issue out of
    many must not surface/expand as if every issue in it matched).
    """
    pattern = q.lower()
    fields = [issue.series, issue.title, issue.writer, issue.characters, issue.story_arc, issue.publisher]
    return any(f and pattern in f.lower() for f in fields)
