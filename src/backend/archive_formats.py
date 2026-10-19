"""
archive_formats.py — shared CBZ/CBR archive-reading dispatch (SPEC.md §6.1,
v2.4 Item 5/11). `.cbz` uses the stdlib `zipfile`; `.cbr` uses `rarfile`
(extraction-only — CBR is never written anywhere in digib00age, see
EDITOR_SPEC.md §3.2). Used by scanner.py, reader.py, and editor/archive_io.py
so the zipfile-vs-rarfile branch isn't triplicated.
"""

from __future__ import annotations

import sys
import time
import zipfile
from pathlib import Path
from typing import Optional

import rarfile


def format_for_path(file_path: str, container_format: Optional[str] = None) -> str:
    """Returns 'cbr' or 'cbz'. Prefers the DB-recorded container_format (avoids
    re-checking the extension on every call); falls back to the file
    extension for files not yet in the DB (e.g. Full Editor pre-library
    intake)."""
    if container_format in ("cbz", "cbr"):
        return container_format
    return "cbr" if Path(file_path).suffix.lower() == ".cbr" else "cbz"


# BUG-033 cause 1 (Windows-only): an os.replace() swapping a file at a path
# a reader is simultaneously opening (editor/archive_io.py's _rebuild_archive
# swapping the archive itself; scanner.py's _generate_thumbnail swapping the
# thumbnail) isn't guaranteed atomic against a concurrent open-for-read on
# Windows the way it is on POSIX, so the reader can momentarily hit
# PermissionError mid-swap. Confirmed Windows-only (0 occurrences across
# 5,066 reads on Linux vs. reproduced on every Windows run, STRESS_TEST.md
# §4) and the race window is sub-millisecond to low-ms at the OS level, so a
# short retry absorbs it without masking a genuinely locked/in-use file.
_OPEN_RETRY_ATTEMPTS = 5
_OPEN_RETRY_DELAY_S = 0.05


def retry_on_windows_replace_race(open_fn):
    """Windows-only: retry `open_fn()` a few times with a short backoff if it
    raises PermissionError, absorbing BUG-033 cause 1 (see comment above).
    A no-op wrapper on POSIX, and on the first successful attempt either way.
    Shared by every call site that opens a file another thread might be
    `os.replace()`-ing concurrently — this module's own `_opener` below, and
    reader.py's thumbnail read."""
    if sys.platform != "win32":
        return open_fn()

    for attempt in range(_OPEN_RETRY_ATTEMPTS):
        try:
            return open_fn()
        except PermissionError:
            if attempt == _OPEN_RETRY_ATTEMPTS - 1:
                raise
            time.sleep(_OPEN_RETRY_DELAY_S)


def _opener(file_path: str, container_format: Optional[str] = None):
    fmt = format_for_path(file_path, container_format)
    opener_cls = rarfile.RarFile if fmt == "cbr" else zipfile.ZipFile
    return retry_on_windows_replace_race(lambda: opener_cls(file_path, "r"))


def archive_namelist(file_path: str, container_format: Optional[str] = None) -> list[str]:
    with _opener(file_path, container_format) as archive:
        return archive.namelist()


def is_macos_junk_entry(name: str) -> bool:
    """True for macOS AppleDouble sidecar entries (`._foo.jpg`) and
    `__MACOSX/` folder entries (BUGS.md BUG-028) — junk left behind by
    archives that were ever touched on a Mac, not real comic pages."""
    return (
        Path(name).name.startswith(".")
        or name.startswith("__MACOSX/")
        or "/__MACOSX/" in name
    )


def archive_read_bytes(file_path: str, entry_name: str, container_format: Optional[str] = None) -> bytes:
    with _opener(file_path, container_format) as archive:
        return archive.read(entry_name)


# Exceptions callers should treat as "bad/corrupt archive" for either format —
# fail soft (flag/skip), same as the existing zipfile.BadZipFile handling.
BAD_ARCHIVE_EXCEPTIONS = (zipfile.BadZipFile, rarfile.BadRarFile, rarfile.NotRarFile)

# Exceptions for "entry name not found in an otherwise-valid archive" —
# zipfile raises KeyError, rarfile raises its own NoRarEntry.
ENTRY_NOT_FOUND_EXCEPTIONS = (KeyError, rarfile.NoRarEntry)
