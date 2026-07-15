"""
archive_io.py — CBZ/CBR archive I/O for the editor core.

Ported from CAPT's utils/archive_xml_loader.py + utils/xml_archive_unpacker.py
(see v2_investigation_report.md). CBR support reinstated v2.4 Item 5/11
(EDITOR_SPEC.md Section 3.1/3.2) — read-only at the archive level; a rebuild
always produces a `.cbz`, never a `.cbr` (RAR creation needs a paid WinRAR
install, deliberately never a ComicVault dependency).
"""

import logging
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from backend import archive_formats

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")


def find_xml_in_archive(archive_path: str) -> list[str]:
    """Return the names of any .xml entries in the archive."""
    try:
        with archive_formats._opener(archive_path) as z:
            return [f for f in z.namelist() if f.lower().endswith(".xml")]
    except Exception as exc:
        logger.error("Error reading archive %s: %s", archive_path, exc)
        return []


def extract_xml_from_archive(archive_path: str, xml_filename: str) -> Optional[str]:
    """Return the decoded contents of one XML entry, or None on failure."""
    try:
        with archive_formats._opener(archive_path) as z:
            return z.read(xml_filename).decode("utf-8")
    except Exception as exc:
        logger.error(
            "Error extracting %s from %s: %s", xml_filename, archive_path, exc
        )
        return None


def get_archive_page_count(archive_path: str) -> int:
    """Count image entries in the archive (used to auto-populate PageCount)."""
    try:
        with archive_formats._opener(archive_path) as z:
            return sum(
                1 for f in z.namelist() if f.lower().endswith(IMAGE_EXTENSIONS)
            )
    except Exception as exc:
        logger.error("Error counting pages in %s: %s", archive_path, exc)
        return 0


def read_xml_and_page_count(archive_path: str) -> tuple[Optional[str], int]:
    """Combines find_xml_in_archive + extract_xml_from_archive + get_archive_page_count
    into a single archive open (was 3 separate opens/central-directory parses for one
    Basic Editor popup load — same redundant-reopen pattern PERFORMANCE.md findings
    #4/#5/#6 already fixed elsewhere, applied here)."""
    try:
        with archive_formats._opener(archive_path) as z:
            names = z.namelist()
            xml_files = [f for f in names if f.lower().endswith(".xml")]
            xml_content = z.read(xml_files[0]).decode("utf-8") if xml_files else None
            page_count = sum(1 for f in names if f.lower().endswith(IMAGE_EXTENSIONS))
            return xml_content, page_count
    except Exception as exc:
        logger.error("Error reading archive %s: %s", archive_path, exc)
        return None, 0


def flatten_and_zip(extract_dir: str, target_dir: str) -> str:
    """
    Flatten extract_dir (archive members may be nested; the rebuilt zip
    stores everything flat at the root, matching CAPT's existing behaviour)
    and zip it into a new staged archive inside target_dir. Does **not**
    move/replace anything — purely builds the staged file and returns its
    path, so callers with different replace semantics (an in-place editor
    rewrite vs. Convert Images' stage/validate/backup flow, §11.3.4) can
    share this step without also sharing what happens after it.

    Staged in target_dir (normally the same directory as the eventual
    destination), not the OS temp directory — a later `os.replace` is only
    atomic within a single filesystem, and the library commonly lives on a
    different drive than the OS temp dir.
    """
    flat_dir = tempfile.mkdtemp(prefix="cv_flatten_")
    try:
        for root, _dirs, files in os.walk(extract_dir):
            for name in files:
                shutil.copy2(os.path.join(root, name), os.path.join(flat_dir, name))

        staging_base = os.path.join(target_dir, f".cv_tmp_{uuid.uuid4().hex}")
        return shutil.make_archive(staging_base, "zip", flat_dir)
    finally:
        shutil.rmtree(flat_dir, ignore_errors=True)


def _rebuild_archive(extract_dir: str, archive_path: str) -> str:
    """
    Shared final stage of every editor archive rewrite (EDITOR_SPEC.md
    Section 3.2): flatten + zip (see flatten_and_zip), then replace the
    original file with it.

    **CBR source → CBZ output (EDITOR_SPEC.md Section 3.2, v2.4 Item 5/11).**
    The rebuild always produces a zip archive — when `archive_path` is a
    `.cbr`, the rebuilt zip is written to a sibling `.cbz` path instead of
    overwriting the `.cbr` in place, and the original `.cbr` is deleted only
    once the new `.cbz` is confirmed written. Returns the final path
    (unchanged for a `.cbz` source, the new sibling path for a `.cbr` one) —
    callers whose archive is tracked elsewhere (a DB row, a working-set dict)
    must update that tracking to the returned path.

    :raises FileExistsError: source is `.cbr` and a sibling `.cbz` already
        exists — no silent clobber, same guard principle used elsewhere.
    """
    is_cbr = archive_path.lower().endswith(".cbr")
    final_path = str(Path(archive_path).with_suffix(".cbz")) if is_cbr else archive_path

    if is_cbr and os.path.exists(final_path):
        raise FileExistsError(f"{final_path} already exists")

    staged_zip = flatten_and_zip(extract_dir, os.path.dirname(final_path))
    os.replace(staged_zip, final_path)

    if is_cbr:
        os.remove(archive_path)

    return final_path


def write_comicinfo_to_cbz(archive_path: str, xml_content: str) -> str:
    """
    Write ComicInfo.xml into an archive via full archive rebuild — extract,
    overwrite ComicInfo.xml, rebuild (see _rebuild_archive). No in-place
    patching.

    Returns the final archive path (see _rebuild_archive's CBR→CBZ note).

    :raises: on any I/O failure — callers are expected to handle/report it.
    """
    extract_dir = tempfile.mkdtemp(prefix="cv_editor_unpack_")
    try:
        with archive_formats._opener(archive_path) as archive:
            archive.extractall(extract_dir)

        with open(
            os.path.join(extract_dir, "ComicInfo.xml"), "w", encoding="utf-8"
        ) as f:
            f.write(xml_content)

        return _rebuild_archive(extract_dir, archive_path)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def keep_single_xml(archive_path: str, keep_filename: str) -> str:
    """
    Resolve a multi-ComicInfo.xml archive (EDITOR_SPEC.md Section 3.5, Full
    Editor only): delete every *.xml entry except keep_filename, renaming it
    to ComicInfo.xml if it wasn't already named that, then rebuild.

    Returns the final archive path (see _rebuild_archive's CBR→CBZ note).

    :raises: on any I/O failure, or if keep_filename isn't actually in the
        archive.
    """
    extract_dir = tempfile.mkdtemp(prefix="cv_editor_unpack_")
    try:
        with archive_formats._opener(archive_path) as archive:
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

        return _rebuild_archive(extract_dir, archive_path)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)
