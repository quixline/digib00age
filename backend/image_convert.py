"""
image_convert.py — Convert Images core logic (ADMIN_SPEC.md §11.3). Ported
from CAPT's utils/convert_images.py, but the flatten/rebuild step is
re-pointed at the Editor's shared `flatten_and_zip()`
(backend/editor/archive_io.py) rather than carrying CAPT's separate
implementation — a deliberate consolidation, not a coincidence (nested-folder
archives are a known prior problem, and two flatten implementations
drifting apart is exactly the kind of risk worth avoiding).

`convert_images_in_archive()` is a plain, router-independent callable —
Processing Folder Automation (§11.4, v2.4 Item 16) invokes it directly, not
through the admin UI's HTTP layer.
"""

from __future__ import annotations

import os
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image

from backend import archive_formats, backup_model
from backend.editor.archive_io import flatten_and_zip

CONVERT_EXTENSIONS = {".jpg", ".jpeg", ".tiff", ".gif", ".png", ".bmp"}


@dataclass
class ConvertImagesResult:
    success: bool
    images_skipped: int = 0
    error: Optional[str] = None


def _extract_all(source_path: str, extract_dir: str) -> list[str]:
    """Extract every entry from a CBZ or CBR (content-detected) into
    extract_dir. Returns the list of entry names."""
    names = archive_formats.archive_namelist(source_path)
    with archive_formats._opener(source_path) as archive:
        archive.extractall(extract_dir)
    return names


def _convert_images_in_dir(extract_dir: str, quality: int, lossless: bool) -> int:
    """Convert every supported raster image under extract_dir to WebP in
    place. Returns the count of images skipped due to per-image failure —
    a corrupted/unreadable image is left in its original format rather than
    aborting the whole archive (matches CAPT's existing fallback)."""
    images_skipped = 0
    for root, _dirs, files in os.walk(extract_dir):
        for name in files:
            ext = Path(name).suffix.lower()
            if ext not in CONVERT_EXTENSIONS:
                continue
            src_path = os.path.join(root, name)
            webp_path = os.path.splitext(src_path)[0] + ".webp"
            try:
                with Image.open(src_path) as im:
                    im.load()
                    if lossless:
                        im.save(webp_path, "WEBP", lossless=True)
                    else:
                        im.save(webp_path, "WEBP", quality=quality)
                os.remove(src_path)
            except Exception:
                images_skipped += 1
    return images_skipped


def _validate(staged_path: str, expected_count: int) -> bool:
    try:
        with zipfile.ZipFile(staged_path, "r") as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
        return len(names) >= expected_count > 0
    except Exception:
        return False


def convert_images_in_archive(archive_path: str, quality: int = 95, lossless: bool = False) -> ConvertImagesResult:
    """
    Converts supported raster images inside a CBZ or CBR to WebP and repacks
    the archive — CBR input always rebuilds as `.cbz` (§11.3.1, CBR is never
    written). Applies the unified backup model
    (backend/backup_model.py, shared with Convert Archives §11.2): stage,
    validate, clean success auto-deletes the `.bak`, warnings (>0 images
    skipped) keep it permanently, failure discards the staged file and
    leaves the original completely untouched.
    """
    source = Path(archive_path)

    if backup_model.bak_already_exists(str(source)):
        return ConvertImagesResult(success=False, error="Backup file already exists")

    target_path = source.with_suffix(".cbz")

    extract_dir = tempfile.mkdtemp(prefix="cv_convimg_")
    try:
        try:
            entry_names = _extract_all(str(source), extract_dir)
        except Exception as exc:
            return ConvertImagesResult(success=False, error=str(exc))

        expected_count = sum(1 for n in entry_names if not n.endswith("/"))
        images_skipped = _convert_images_in_dir(extract_dir, quality, lossless)

        try:
            staged_path = flatten_and_zip(extract_dir, str(target_path.parent))
        except Exception as exc:
            return ConvertImagesResult(success=False, error=str(exc))

        outcome, _bak = backup_model.stage_validate_and_replace(
            str(source),
            staged_path,
            str(target_path),
            lambda p: _validate(p, expected_count),
            has_warnings=images_skipped > 0,
        )

        if outcome == "failure":
            return ConvertImagesResult(success=False, error="Converted archive failed validation")

        return ConvertImagesResult(success=True, images_skipped=images_skipped)
    finally:
        import shutil
        shutil.rmtree(extract_dir, ignore_errors=True)
