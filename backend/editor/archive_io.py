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


def _rebuild_archive(extract_dir: str, archive_path: str) -> None:
    """
    Shared final stage of every archive rewrite (EDITOR_SPEC.md Section 3.2):
    flatten extract_dir (archive members may be nested; the rebuilt zip
    stores everything flat at the root, matching CAPT's existing behaviour),
    rebuild a new zip, and replace the original file with it.

    The rebuilt zip is staged in the *same directory* as the original file
    before the final replace, not in the OS temp directory — `os.replace` is
    only atomic within a single filesystem, and the library lives on a
    different drive (L:) than the OS temp dir (C:).
    """
    flat_dir = tempfile.mkdtemp(prefix="cv_editor_flat_")
    try:
        for root, _dirs, files in os.walk(extract_dir):
            for name in files:
                shutil.copy2(os.path.join(root, name), os.path.join(flat_dir, name))

        target_dir = os.path.dirname(archive_path)
        staging_base = os.path.join(target_dir, f".cv_editor_tmp_{uuid.uuid4().hex}")
        staged_zip = shutil.make_archive(staging_base, "zip", flat_dir)
        os.replace(staged_zip, archive_path)
    finally:
        shutil.rmtree(flat_dir, ignore_errors=True)


def write_comicinfo_to_cbz(archive_path: str, xml_content: str) -> None:
    """
    Write ComicInfo.xml into a CBZ via full archive rebuild — extract,
    overwrite ComicInfo.xml, rebuild (see _rebuild_archive). No in-place
    patching.

    :raises: on any I/O failure — callers are expected to handle/report it.
    """
    extract_dir = tempfile.mkdtemp(prefix="cv_editor_unpack_")
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            archive.extractall(extract_dir)

        with open(
            os.path.join(extract_dir, "ComicInfo.xml"), "w", encoding="utf-8"
        ) as f:
            f.write(xml_content)

        _rebuild_archive(extract_dir, archive_path)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def keep_single_xml(archive_path: str, keep_filename: str) -> None:
    """
    Resolve a multi-ComicInfo.xml archive (EDITOR_SPEC.md Section 3.5, Full
    Editor only): delete every *.xml entry except keep_filename, renaming it
    to ComicInfo.xml if it wasn't already named that, then rebuild.

    :raises: on any I/O failure, or if keep_filename isn't actually in the
        archive.
    """
    extract_dir = tempfile.mkdtemp(prefix="cv_editor_unpack_")
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            archive.extractall(extract_dir)

        keep_path = os.path.join(extract_dir, keep_filename)
        if not os.path.isfile(keep_path):
            raise FileNotFoundError(f"{keep_filename} not found in archive")

        target_path = os.path.join(extract_dir, "ComicInfo.xml")
        if os.path.normcase(keep_path) != os.path.normcase(target_path):
            shutil.move(keep_path, target_path)

        for name in os.listdir(extract_dir):
            candidate = os.path.join(extract_dir, name)
            if (
                name.lower().endswith(".xml")
                and os.path.normcase(candidate) != os.path.normcase(target_path)
            ):
                os.remove(candidate)

        _rebuild_archive(extract_dir, archive_path)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)
