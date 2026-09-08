"""
archive_convert.py — Convert Archives core logic (ADMIN_SPEC.md §11.2).
Ported from CAPT's arc_conv_cb_proc.py / arc_conv_pdf_proc.py /
arc_conv_helpers.py / arc_convert_util.py. Only CBR->CBZ and PDF->CBZ are
ported — CAPT's CBZ->CBR/CBZ->PDF directions are dropped entirely (RAR
creation needs a paid WinRAR install, never a digib00age dependency).

`convert_archive_file()` is a plain, router-independent callable — Processing
Folder Automation (§11.4, v2.4 Item 16) invokes it directly, not through the
admin UI's HTTP layer.
"""

from __future__ import annotations

import os
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import rarfile

from backend import archive_formats, attention_log, backup_model

# Print-scan-grade sharpness — replaces CAPT's hardcoded Matrix(1, 1) (72 DPI).
# Isolated constant: adjusting DPI later needs no other code/schema changes.
PDF_RENDER_DPI = 300

_SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}


@dataclass
class ConvertResult:
    success: bool
    pages_skipped: int = 0
    error: Optional[str] = None
    critical: bool = False


def detect_archive_format(path: str) -> Optional[str]:
    """Content-based detection, ported unchanged from arc_convert_util.py —
    filenames/extensions are never trusted on their own for CBZ/CBR (a
    `.pdf` suffix is still trusted, matching CAPT's original behaviour)."""
    p = Path(path)
    try:
        if p.suffix.lower() == ".pdf":
            return "PDF"
        if zipfile.is_zipfile(path):
            return "CBZ"
        if rarfile.is_rarfile(path):
            return "CBR"
    except OSError:
        pass
    return None


def _extract_rar_tolerant(rar_path: str, extract_path: Path) -> tuple[list, list, list]:
    """Ported from arc_conv_helpers.py's extract_rar_archive(ignore_crc_errors=True)."""
    extracted_files, failed_files, crc_errors = [], [], []
    with rarfile.RarFile(rar_path, "r") as rf:
        for name in rf.namelist():
            try:
                rf.extract(name, str(extract_path))
                extracted_files.append(name)
            except rarfile.BadRarFile as exc:
                error_str = str(exc).upper()
                if "CRC" in error_str or "CHECKSUM" in error_str:
                    crc_errors.append(name)
                    potential = extract_path / name
                    if potential.exists() and potential.stat().st_size > 0:
                        extracted_files.append(name)
                    else:
                        failed_files.append(name)
                else:
                    failed_files.append(name)
            except Exception:
                failed_files.append(name)
    return extracted_files, failed_files, crc_errors


def _convert_cbr(source_path: str, staged_path: str) -> tuple[int, int]:
    """CBR -> CBZ. Returns (pages_skipped, expected_entry_count)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        _extracted, _failed, crc_errors = _extract_rar_tolerant(source_path, temp_path)
        pages_skipped = len(crc_errors)

        # Drop macOS AppleDouble sidecars (BUGS.md BUG-028) — never real page
        # content; don't let CBR->CBZ conversion carry them into the library.
        all_files = [
            f for f in temp_path.rglob("*")
            if f.is_file() and not archive_formats.is_macos_junk_entry(f.name)
        ]
        with zipfile.ZipFile(staged_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in all_files:
                zf.write(f, f.relative_to(temp_path))

        return pages_skipped, len(all_files)


def _convert_pdf(source_path: str, staged_path: str) -> tuple[int, int]:
    """PDF -> CBZ, one PNG page per PDF page. Returns
    (pages_skipped, expected_entry_count) — PDF rendering has no per-page
    tolerant-failure mode (fitz renders a page or the whole doc errors), so
    pages_skipped is always 0."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        doc = fitz.open(source_path)
        try:
            matrix = fitz.Matrix(PDF_RENDER_DPI / 72, PDF_RENDER_DPI / 72)
            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=matrix)
                pix.save(str(temp_path / f"page_{i + 1:03d}.png"))
            page_count = doc.page_count
        finally:
            doc.close()

        with zipfile.ZipFile(staged_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(temp_path.glob("*.png")):
                zf.write(f, f.name)

        return 0, page_count


def _validate(staged_path: str, expected_count: int) -> bool:
    try:
        with zipfile.ZipFile(staged_path, "r") as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
        return len(names) >= expected_count > 0
    except Exception:
        return False


def convert_archive_file(source_path: str, from_format: str) -> ConvertResult:
    """
    from_format: 'cbr' or 'pdf'. Converts to a sibling `.cbz` via the unified
    backup model (backend/backup_model.py) — stage, validate (opens as a
    valid archive, entry count matches expected, accounting for any
    pages_skipped), clean success auto-deletes the `.bak`, warnings keep it
    permanently, failure discards the staged file and leaves the original
    completely untouched.
    """
    source = Path(source_path)

    if backup_model.bak_already_exists(str(source)):
        return ConvertResult(success=False, error="Backup file already exists")

    target_path = source.with_suffix(".cbz")
    staged_path = str(target_path) + ".staging"

    try:
        if from_format == "cbr":
            pages_skipped, expected_count = _convert_cbr(str(source), staged_path)
        elif from_format == "pdf":
            pages_skipped, expected_count = _convert_pdf(str(source), staged_path)
        else:
            return ConvertResult(success=False, error=f"Unsupported from_format: {from_format}")
    except Exception as exc:
        # source is untouched at this point — only the never-committed
        # staged_path might exist (e.g. the zip write failed partway
        # through _convert_cbr's loop) — don't leave it behind.
        try:
            os.remove(staged_path)
        except OSError:
            pass
        return ConvertResult(success=False, error=str(exc))

    outcome, _bak, detail = backup_model.stage_validate_and_replace(
        str(source),
        staged_path,
        str(target_path),
        lambda p: _validate(p, expected_count),
        has_warnings=pages_skipped > 0,
    )

    if outcome == "critical_failure":
        attention_log.add(
            kind="convert_archives",
            message=detail,
            original_path=str(source),
            bak_path=_bak,
            target_path=str(target_path),
        )
        return ConvertResult(success=False, error=detail, critical=True)

    if outcome == "failure":
        return ConvertResult(success=False, error=detail or "Converted archive failed validation")

    return ConvertResult(success=True, pages_skipped=pages_skipped)
