"""
rename_tool.py — File Rename Tool core logic (ADMIN_SPEC.md / admin-spec-
section-12-processing-tools.md §12.1). Ported from CAPT's
utils/filename_parser.py + utils/rename_u.py, with the three parser bugs
found and fixed during the 2026-07-01 re-scope (§12.1.3 Change Log) and the
output format changed to the format decided there — these are pure
functions, no PyQt/file-system dependency.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Filename parsing — parse_comic_filename()
# ---------------------------------------------------------------------------

_QUALIFIERS_TO_REMOVE = [
    r'\bTPB\b', r'\bLQ\b', r'\bHQ\b', r'\bGN\b', r'\bHC\b',
    r'\bSC\b', r'\bOMNIBUS\b', r'\bDELUXE\b', r'\bANNIVERSARY\b',
]

_ISSUE_PATTERN = re.compile(r'(?:v|V|#|prog\s*|vol\s*|Vol\s*)[ ._-]*(\d+)')
_ISSUE_STRIP_PATTERN = re.compile(r'(?:v|V|#|prog\s*|vol\s*|Vol\s*)[ ._-]*\d+')
_TRAILING_NUMBER_PATTERN = re.compile(r'^(.*?)\s+(\d+)$')


def _collapse_whitespace(s: str) -> str:
    """Collapse runs of whitespace and strip dangling leading/trailing
    dashes left behind by a token/bracket removal — fixes the
    'Conan the Barbarian  - Twisting Loyalties' double-space/dangling-dash
    artifact (§12.1.3 re-scope, bug #3). Called after every removal step,
    not just once at the end."""
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'^-\s*', '', s)
    s = re.sub(r'\s*-\s*$', '', s)
    return s.strip()


def _strip_leading_zeros(issue_num: str) -> str:
    """Only strip leading zeros when the result wouldn't be empty — fixes
    the '000' -> '' zero-issue bug (§12.1.3 re-scope, bug #2), which was
    indistinguishable from 'no issue found'."""
    stripped = issue_num.lstrip('0')
    return stripped if stripped else issue_num


def _extract_year(s: str) -> str:
    """Dynamically-computed validity ceiling, not a hardcoded year — fixes
    the 'present_year = 2025' bug (§12.1.3 re-scope, bug #1), which silently
    rejected every 2026-dated file (64% of the periodical sample) and
    cascaded into series/issue extraction failing too."""
    present_year = datetime.now().year

    bracket_years = re.findall(r'[\(\[\{](\d{4})[\)\]\}]', s)
    for y in bracket_years:
        yr = int(y)
        if 1900 <= yr <= present_year:
            return str(yr)

    date_matches = re.findall(r'[\(\[\{](\d{1,2})[-/](\d{1,2})[-/](\d{2})[\)\]\}]', s)
    for _day, _month, year_2digit in date_matches:
        yr = int(year_2digit)
        if 0 <= yr <= 99:
            full_year = 1900 + yr if yr >= 50 else 2000 + yr
            if 1900 <= full_year <= present_year:
                return str(full_year)

    bracket_2digit = re.findall(r'[\(\[\{](\d{2})[\)\]\}]', s)
    for y in bracket_2digit:
        yr = int(y)
        if 0 <= yr <= 99:
            full_year = 1900 + yr if yr >= 50 else 2000 + yr
            if 1900 <= full_year <= present_year:
                return str(full_year)

    for y in re.findall(r'(?<![A-Za-z0-9])\d{4}(?![A-Za-z0-9])', s):
        yr = int(y)
        if 1900 <= yr <= present_year:
            return str(yr)

    return ''


def _clean_series(s: str, year: str) -> str:
    def bracket_iter(string_):
        return re.finditer(r'[\(\[\{]([^\)\]\}]*)[\)\]\}]', string_)

    for m in bracket_iter(s):
        content = m.group(1).strip()
        if content == year:
            s = s.replace(m.group(0), '')
        elif re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', content):
            s = s.replace(m.group(0), '')
        elif re.search(r'[A-Za-z]', content):
            s = s.replace(m.group(0), '')
        s = _collapse_whitespace(s)
    return _collapse_whitespace(s)


def parse_comic_filename(filename: str) -> dict:
    """
    Parse a comic archive filename to extract metadata fields. Format-
    agnostic — operates on the filename string only (§12.1.1).

    Returns: {'series': str, 'issue_num': str, 'issue_title': str, 'year': str}
    No auto-splitting of Series and Title (§12.1.3, confirmed by design) —
    issue_title is always '', a manual entry via the edit panel.
    """
    name = re.sub(r'\.[^.]+$', '', filename)

    for qualifier in _QUALIFIERS_TO_REMOVE:
        name = re.sub(qualifier, '', name, flags=re.IGNORECASE)
    name = _collapse_whitespace(name)

    year = _extract_year(name)
    series_name = _clean_series(name, year)

    issue_num = ''
    issue_match = _ISSUE_PATTERN.search(series_name)
    if issue_match:
        issue_num = _strip_leading_zeros(issue_match.group(1))
        series = _collapse_whitespace(_ISSUE_STRIP_PATTERN.sub('', series_name))
    else:
        match = _TRAILING_NUMBER_PATTERN.match(series_name)
        if match:
            series = _collapse_whitespace(match.group(1))
            issue_num = _strip_leading_zeros(match.group(2))
        else:
            series = series_name

    return {
        'series': series,
        'issue_num': issue_num,
        'issue_title': '',
        'year': year,
    }


# ---------------------------------------------------------------------------
# Filename building
# ---------------------------------------------------------------------------

def apply_title_style(text: str, style: str = 'title') -> str:
    if style == 'title':
        return text.title()
    if style == 'upper':
        return text.upper()
    if style == 'lower':
        return text.lower()
    return text


def build_filename(series: str, issue_title: str, issue_num: str, year: str, ext: str) -> str:
    """
    'Series #Issue - Title (Year)', the format decided 2026-07-19 (replacing
    the original 2026-07-01 re-scope's 'Series - Title #Issue (Year)') so
    Issue sits right after Series instead of after Title. The dash+Title
    segment is present only when Title is non-empty; #Issue and (Year) are
    each included independently of the other, same as before.
    """
    parts = []
    if series:
        parts.append(series)
    if issue_num:
        parts.append(f"#{issue_num}")
    if issue_title:
        parts.append(f"- {issue_title}")
    if year:
        parts.append(f"({year})")
    return " ".join(parts) + ext


def preview_renames(file_list: list[str], rename_data: dict, batch_options: dict) -> list[str]:
    """
    Generate preview filenames for every file in file_list.
    rename_data: {'series', 'issue_num', 'issue_title', 'year'} — the values
        to apply (caller has already resolved File/All checkbox precedence
        per-file before calling this for a single file, or applies the same
        values to every file for a batch/"All" call).
    batch_options: {'auto_increment': bool, 'title_style': 'title'|'upper'|'lower'|None}
    """
    previews = []
    original_issue_num = (rename_data.get('issue_num') or '').strip()
    num_start = int(original_issue_num) if batch_options.get('auto_increment') and original_issue_num else None

    for idx, file_path in enumerate(file_list):
        ext = Path(file_path).suffix

        series = (rename_data.get('series') or '').strip()
        issue_num = (rename_data.get('issue_num') or '').strip()
        issue_title = (rename_data.get('issue_title') or '').strip()
        year = (rename_data.get('year') or '').strip()

        if batch_options.get('auto_increment') and num_start is not None:
            issue_num = str(num_start + idx)

        style = batch_options.get('title_style')
        if style:
            if series:
                series = apply_title_style(series, style)
            if issue_title:
                issue_title = apply_title_style(issue_title, style)

        previews.append(build_filename(series, issue_title, issue_num, year, ext))
    return previews
