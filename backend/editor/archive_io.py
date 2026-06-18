"""
archive_io.py — CBZ archive I/O for the editor core.

Ported from CAPT's utils/archive_xml_loader.py + utils/xml_archive_unpacker.py
(see v2_investigation_report.md). CBR support is dropped entirely per
EDITOR_SPEC.md Section 2 — the library is all-CBZ.
"""

import logging
import os
import shutil
import tempfile
import uuid
import zipfile
from typing import Optional

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")


def find_xml_in_archive(archive_path: str) -> list[str]:
    """Return the names of any .xml entries in the archive."""
    try:
        with zipfile.ZipFile(archive_path, "r") as z:
            return [f for f in z.namelist() if f.lower().endswith(".xml")]
    except Exception as exc:
        logger.error("Error reading archive %s: %s", archive_path, exc)
        return []


def extract_xml_from_archive(archive_path: str, xml_filename: str) -> Optional[str]:
    """Return the decoded contents of one XML entry, or None on failure."""
    try:
        with zipfile.ZipFile(archive_path, "r") as z:
            with z.open(xml_filename) as f:
                return f.read().decode("utf-8")
    except Exception as exc:
        logger.error(
            "Error extracting %s from %s: %s", xml_filename, archive_path, exc
        )
        return None


def get_archive_page_count(archive_path: str) -> int:
    """Count image entries in the archive (used to auto-populate PageCount)."""
    try:
        with zipfile.ZipFile(archive_path, "r") as z:
            return sum(
                1 for f in z.namelist() if f.lower().endswith(IMAGE_EXTENSIONS)
            )
    except Exception as exc:
        logger.error("Error counting pages in %s: %s", archive_path, exc)
        return 0


def write_comicinfo_to_cbz(archive_path: str, xml_content: str) -> None:
    """
    Write ComicInfo.xml into a CBZ via full archive rebuild (per
    EDITOR_SPEC.md Section 3.2 — no in-place patching):

    1. Extract the entire archive to a temp directory
    2. Overwrite ComicInfo.xml in that temp directory
    3. Flatten to a second temp directory (archive members may be nested;
       the rebuilt zip stores everything flat at the root, matching CAPT's
       existing behaviour)
    4. Rebuild a new zip from the flattened directory
    5. Replace the original file with the rebuilt one

    The rebuilt zip is staged in the *same directory* as the original file
    before the final replace, not in the OS temp directory — `os.replace` is
    only atomic within a single filesystem, and the library lives on a
    different drive (L:) than the OS temp dir (C:).

    :raises: on any I/O failure — callers are expected to handle/report it.
    """
    extract_dir = tempfile.mkdtemp(prefix="cv_editor_unpack_")
    flat_dir = tempfile.mkdtemp(prefix="cv_editor_flat_")
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            archive.extractall(extract_dir)

        with open(
            os.path.join(extract_dir, "ComicInfo.xml"), "w", encoding="utf-8"
        ) as f:
            f.write(xml_content)

        for root, _dirs, files in os.walk(extract_dir):
            for name in files:
                shutil.copy2(os.path.join(root, name), os.path.join(flat_dir, name))

        target_dir = os.path.dirname(archive_path)
        staging_base = os.path.join(target_dir, f".cv_editor_tmp_{uuid.uuid4().hex}")
        staged_zip = shutil.make_archive(staging_base, "zip", flat_dir)
        os.replace(staged_zip, archive_path)
    finally:
        for d in (extract_dir, flat_dir):
            shutil.rmtree(d, ignore_errors=True)
