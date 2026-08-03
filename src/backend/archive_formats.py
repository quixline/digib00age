"""
archive_formats.py — shared CBZ/CBR archive-reading dispatch (SPEC.md §6.1,
v2.4 Item 5/11). `.cbz` uses the stdlib `zipfile`; `.cbr` uses `rarfile`
(extraction-only — CBR is never written anywhere in digib00age, see
EDITOR_SPEC.md §3.2). Used by scanner.py, reader.py, and editor/archive_io.py
so the zipfile-vs-rarfile branch isn't triplicated.
"""

from __future__ import annotations

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


def _opener(file_path: str, container_format: Optional[str] = None):
    fmt = format_for_path(file_path, container_format)
    if fmt == "cbr":
        return rarfile.RarFile(file_path, "r")
    return zipfile.ZipFile(file_path, "r")


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
