"""
path_utils.py — shared filtering helpers used by more than one router, so
every call site applies identical logic instead of near-duplicate copies.
normalize_path/is_under: folder-path normalization and prefix-matching
(custom tab + home strip folder validation/filtering — the separator-suffixed
boundary check means a folder "C:\\Comics\\Batman" won't match "C:\\Comics\\Batman2\\...").
matches_field: the 9 field-filter dimensions shared by the browse filter bar,
Custom Tabs, and HOME_STRIPS_SPEC.md's field-based strips.
"""

import os

from backend.models import Issue


def normalize_path(path: str) -> str:
    return os.path.normpath(os.path.abspath(path))


def is_under(child: str, parent: str) -> bool:
    """True if `child` is `parent` itself or a path beneath it."""
    c = normalize_path(child).lower()
    p = normalize_path(parent).lower()
    return c == p or c.startswith(p + os.sep)


def matches_field(issue: Issue, field_name: str, field_value: str) -> bool:
    """One of: genre, publisher, writer, artist, format, decade, year, rating, bw."""
    if field_name == "genre":
        return any(g.genre_name == field_value for g in issue.genres)
    if field_name == "publisher":
        return issue.publisher == field_value
    if field_name == "writer":
        return issue.writer == field_value
    if field_name == "artist":
        return issue.penciller == field_value
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
    return False
