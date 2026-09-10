"""
filename_sort.py — Sort by Filename Processing Tool core logic
(ADMIN_SPEC.md §11.5). Ported from the standalone
`create-folders-from-file.py` script: for every CBZ/CBR file directly inside
a folder, move it into a new subfolder named after its own basename with the
extension stripped and the issue-number token (e.g. '#1') removed, leaving
title + bracketed year — 'Shellshock #1 (2026).cbz' -> 'Shellshock (2026)\\
Shellshock #1 (2026).cbz'. The moved file itself keeps its original
filename; only the folder name is cleaned. Anything else in the folder —
other file types, existing subfolders — is left untouched. Pure function,
no router/logging concerns.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from typing import Optional

_SORTABLE_EXTENSIONS = {".cbz", ".cbr"}
_ISSUE_NUMBER_PATTERN = re.compile(r'\s*#\d+(?:\.\d+)?\s*')


@dataclass
class FilenameSortFileResult:
    filename: str
    folder_name: str
    success: bool
    error: Optional[str] = None


@dataclass
class FilenameSortResult:
    success: bool
    files: list[FilenameSortFileResult] = field(default_factory=list)
    error: Optional[str] = None  # top-level failure (folder not found/unreachable) — no files were attempted


def _clean_folder_name(stem: str) -> str:
    """
    Strip the issue-number token (e.g. '#1', '#005', '#12.1') from a
    filename stem, leaving the title and any bracketed year —
    'Shellshock #1 (2026)' -> 'Shellshock (2026)'. Only removes that one
    token; everything else in the name (extra qualifiers, subtitles) is
    left as-is.
    """
    return _collapse_whitespace(_ISSUE_NUMBER_PATTERN.sub(' ', stem))


def _collapse_whitespace(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def _conflicting_existing_entry(target_folder: str, folder_name: str) -> Optional[str]:
    """
    None if `target_folder` doesn't exist yet, or exists but only contains
    entries whose own cleaned basename matches `folder_name` (a same-title/
    year CBZ+CBR pair, another issue of the same series, or a previous run's
    own output) — otherwise the name of the first unrelated entry found, so
    the caller can fail that one file with a clear reason instead of
    dropping it into a folder that already holds something else.
    """
    if not os.path.isdir(target_folder):
        return None
    for entry in os.listdir(target_folder):
        if _clean_folder_name(os.path.splitext(entry)[0]) != folder_name:
            return entry
    return None


def sort_by_filename(folder: str) -> FilenameSortResult:
    """
    Moves each CBZ/CBR file found directly inside `folder` (no recursion) into
    a sibling subfolder named after its own basename with the issue-number
    token stripped (see module docstring) — title + bracketed year only.
    Multiple issues of the same title/year (e.g. 'Batman #1 (2023).cbz',
    'Batman #2 (2023).cbz', ...) all land in the same folder, matching how a
    multi-issue series is already organised elsewhere in the library (one
    folder per series, every issue a loose file inside it, not one folder
    per issue) — not treated as a conflict. A file is skipped, individually,
    when its target folder already exists and holds a file that isn't one of
    its own cleaned-name siblings, or when the exact destination path is
    already occupied (§11.5 collision rules) — every other file in the batch
    is still attempted.
    """
    if not os.path.isdir(folder):
        return FilenameSortResult(success=False, error="Folder not found")

    try:
        entries = sorted(
            name for name in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, name))
        )
    except OSError as exc:
        return FilenameSortResult(success=False, error=str(exc))

    candidates = [
        name for name in entries
        if os.path.splitext(name)[1].lower() in _SORTABLE_EXTENSIONS
    ]

    results: list[FilenameSortFileResult] = []
    for filename in candidates:
        source_path = os.path.join(folder, filename)
        folder_name = _clean_folder_name(os.path.splitext(filename)[0])
        target_folder = os.path.join(folder, folder_name)
        destination_path = os.path.join(target_folder, filename)

        try:
            conflict = _conflicting_existing_entry(target_folder, folder_name)
            if conflict:
                raise FileExistsError(f"'{folder_name}' already contains an unrelated file: '{conflict}'")
            if os.path.exists(destination_path):
                raise FileExistsError(f"'{filename}' already exists in '{folder_name}'")
            os.makedirs(target_folder, exist_ok=True)
            shutil.move(source_path, destination_path)
            results.append(FilenameSortFileResult(filename=filename, folder_name=folder_name, success=True))
        except Exception as exc:
            results.append(FilenameSortFileResult(filename=filename, folder_name=folder_name, success=False, error=str(exc)))

    return FilenameSortResult(success=True, files=results)
