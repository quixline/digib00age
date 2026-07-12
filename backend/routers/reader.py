"""
ComicVault — Reader Router
GET /api/issue/{id}/pages     Ordered list of page image URLs
GET /api/page/{id}/{n}        Serve one page image from inside the CBZ
GET /api/cover/{id}           Serve the pre-generated cover thumbnail
GET /api/issue/{id}/download  Serve the whole CBZ/CBR file (mobile offline download)
"""

from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, FileResponse
from sqlalchemy.orm import Session

from backend import archive_formats
from backend.database import get_db
from backend.models import Issue
from backend.config import get_config

router = APIRouter(tags=["reader"])

# Image extensions we treat as comic pages
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_page_list_cache: dict[str, tuple[tuple[float, int], list[str]]] = {}


def _sorted_pages(archive_path: str) -> list[str]:
    """
    Return filenames inside the CBZ/CBR that look like images, sorted
    alphabetically. This is the canonical page order — same logic as the
    scanner uses for covers.

    Cached in-process per archive_path, keyed on (mtime, size) so a changed
    file on disk (rescan/replace) invalidates automatically — avoids
    re-parsing the ZIP central directory on every page request
    (PERFORMANCE.md findings #4/#5).
    """
    try:
        stat = os.stat(archive_path)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Cannot read archive: {exc}")

    cache_key = (stat.st_mtime, stat.st_size)
    cached = _page_list_cache.get(archive_path)
    if cached and cached[0] == cache_key:
        return cached[1]

    try:
        names = [
            n for n in archive_formats.archive_namelist(archive_path)
            if Path(n).suffix.lower() in IMAGE_EXTENSIONS
            and not Path(n).name.startswith(".")  # skip hidden files
        ]
        pages = sorted(names)
    except (*archive_formats.BAD_ARCHIVE_EXCEPTIONS, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f"Cannot read archive: {exc}")

    _page_list_cache[archive_path] = (cache_key, pages)
    return pages


def _mime_for(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }.get(ext, "image/jpeg")


# ---------------------------------------------------------------------------
# GET /api/issue/{id}/pages
# ---------------------------------------------------------------------------

@router.get("/issue/{issue_id}/pages")
def get_pages(issue_id: int, db: Session = Depends(get_db)):
    """
    Returns an ordered list of page URLs for the reader to load one by one.
    The reader uses these URLs to fetch each page via /api/page/{id}/{n}.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if issue.missing:
        raise HTTPException(status_code=404, detail="File is marked missing on disk")

    pages = _sorted_pages(issue.file_path)
    page_urls = [f"/api/page/{issue_id}/{n}" for n in range(len(pages))]

    return {
        "issue_id": issue_id,
        "page_count": len(pages),
        "manga": issue.manga,
        "pages": page_urls,
    }


# ---------------------------------------------------------------------------
# GET /api/page/{issue_id}/{page_number}
# ---------------------------------------------------------------------------

@router.get("/page/{issue_id}/{page_number}")
def get_page(issue_id: int, page_number: int, db: Session = Depends(get_db)):
    """
    Extract and serve a single page image from inside the CBZ.
    page_number is 0-indexed.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if issue.missing:
        raise HTTPException(status_code=404, detail="File is marked missing on disk")

    pages = _sorted_pages(issue.file_path)

    if page_number < 0 or page_number >= len(pages):
        raise HTTPException(
            status_code=404,
            detail=f"Page {page_number} out of range (0–{len(pages) - 1})"
        )

    target = pages[page_number]
    mime = _mime_for(target)

    try:
        data = archive_formats.archive_read_bytes(issue.file_path, target)
    except (*archive_formats.BAD_ARCHIVE_EXCEPTIONS, *archive_formats.ENTRY_NOT_FOUND_EXCEPTIONS) as exc:
        raise HTTPException(status_code=500, detail=f"Cannot read page: {exc}")

    return Response(content=data, media_type=mime)


# ---------------------------------------------------------------------------
# GET /api/cover/{issue_id}
# ---------------------------------------------------------------------------

@router.get("/cover/{issue_id}")
def get_cover(issue_id: int, db: Session = Depends(get_db)):
    """
    Serve the pre-generated thumbnail for an issue.
    Falls back to extracting the first page directly if no thumbnail exists.
    """
    config = get_config()
    thumb_dir = Path(config["thumbnail_dir"])

    # Resolve relative paths from project root
    if not thumb_dir.is_absolute():
        from backend.config import PROJECT_ROOT
        thumb_dir = PROJECT_ROOT / thumb_dir

    thumb_path = thumb_dir / f"{issue_id}.jpg"

    if thumb_path.exists():
        return FileResponse(str(thumb_path), media_type="image/jpeg")

    # Fallback — extract first page from CBZ on the fly
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue or issue.missing:
        raise HTTPException(status_code=404, detail="Cover not found")

    pages = _sorted_pages(issue.file_path)
    if not pages:
        raise HTTPException(status_code=404, detail="No pages found in CBZ")

    target = pages[0]
    mime = _mime_for(target)

    try:
        data = archive_formats.archive_read_bytes(issue.file_path, target)
    except (*archive_formats.BAD_ARCHIVE_EXCEPTIONS, *archive_formats.ENTRY_NOT_FOUND_EXCEPTIONS) as exc:
        raise HTTPException(status_code=500, detail=f"Cannot read cover page: {exc}")

    return Response(content=data, media_type=mime)


# ---------------------------------------------------------------------------
# GET /api/issue/{issue_id}/download
# ---------------------------------------------------------------------------

@router.get("/issue/{issue_id}/download")
def download_issue(issue_id: int, db: Session = Depends(get_db)):
    """
    Serve the whole CBZ/CBR file for offline download by the Flutter app —
    the only whole-archive endpoint in the API (everything else above serves
    one page at a time). v2.5 Item 3 (mobile reading-state sync).
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if issue.missing:
        raise HTTPException(status_code=404, detail="File is marked missing on disk")

    path = Path(issue.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    ext = path.suffix.lower()  # trust the real file, not container_format
    label = f"{issue.series} {issue.number}" if issue.number else issue.series
    filename = f"{label}{ext}".replace("/", "-")

    return FileResponse(
        str(path),
        media_type="application/vnd.comicbook+zip" if ext == ".cbz" else "application/x-cbr",
        filename=filename,  # FastAPI/Starlette sets Content-Disposition + escaping
    )
