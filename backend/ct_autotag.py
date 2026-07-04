"""
ct_autotag.py — CT Auto-Tag stage core logic (ADMIN_SPEC.md §11.4.3/§11.4.4).
Plain, router-independent callable — invoked directly by
processing_folder.py's run_pipeline(), same pattern as
archive_convert.py's convert_archive_file()/image_convert.py's
convert_images_in_archive().

No backup-model involvement (§11.4.4: "Backup model does not apply") — this
stage only adds/rewrites XML inside the existing archive via the editor
core's rebuild path, no separate output file, no .bak to manage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend import ct_bridge
from backend.editor.archive_io import extract_xml_from_archive, find_xml_in_archive, write_comicinfo_to_cbz
from backend.editor.field_merge import build_xml_from_fields


@dataclass
class CTAutoTagResult:
    success: bool
    confidence: str  # "confident" | "low_confidence" | "no_match"
    tags_written: bool
    series: Optional[str] = None
    issue: Optional[str] = None
    year: Optional[str] = None
    error: Optional[str] = None
    # write_comicinfo_to_cbz() rebuilds a .cbr source as a sibling .cbz (same
    # mechanism every other editor save path already uses, EDITOR_SPEC.md
    # §3.2) — final_path carries the post-write path so the caller can log
    # the correct filename when a container-format change happened.
    final_path: Optional[str] = None


def ct_autotag_file(archive_path: str, api_key: str, save_low_confidence: bool = True) -> CTAutoTagResult:
    """
    Identifies a single file via ct_bridge.identify_file() and, for a
    confident or (if save_low_confidence) low-confidence match, writes the
    mapped fields into the archive's ComicInfo.xml. NeedsReview is set for
    low-confidence writes only (EDITOR_SPEC.md §9.2) — cleared on the file's
    next Editor save, not here.
    """
    try:
        result = ct_bridge.identify_file(archive_path)
    except Exception as exc:
        return CTAutoTagResult(success=False, confidence="no_match", tags_written=False, error=str(exc))

    if result.confidence == ct_bridge.ConfidenceLevel.NO_MATCH or not result.best_match:
        return CTAutoTagResult(success=True, confidence="no_match", tags_written=False)

    if result.confidence == ct_bridge.ConfidenceLevel.LOW_CONFIDENCE and not save_low_confidence:
        return CTAutoTagResult(success=True, confidence="low_confidence", tags_written=False)

    # result.best_match.md comes from IssueIdentifier's bulk candidate search
    # (ComicVine's lighter multi-issue endpoint), which does not carry
    # credits -- confirmed 2026-07-04 against a real file (Writer/Penciller/
    # Inker/etc. all silently empty). A follow-up single-issue fetch (the
    # same full-detail endpoint Search Online's confirm step already uses)
    # is required to get the complete metadata before mapping to fields.
    md = result.best_match.md
    if md.issue_id:
        try:
            md = ct_bridge.fetch_issue_metadata(md.issue_id)
        except Exception:
            pass  # fall back to the lighter candidate data rather than fail the whole match

    fields = ct_bridge.metadata_to_field_dict(md)
    if result.confidence == ct_bridge.ConfidenceLevel.LOW_CONFIDENCE:
        fields["NeedsReview"] = "true"

    try:
        xml_files = find_xml_in_archive(archive_path)
        original_xml = extract_xml_from_archive(archive_path, xml_files[0]) if xml_files else None
        xml_content = build_xml_from_fields(fields, original_xml)
        final_path = write_comicinfo_to_cbz(archive_path, xml_content)
    except Exception as exc:
        return CTAutoTagResult(success=False, confidence=result.confidence, tags_written=False, error=str(exc))

    return CTAutoTagResult(
        success=True,
        confidence=result.confidence,
        tags_written=True,
        series=fields.get("Series"),
        issue=fields.get("Number"),
        year=fields.get("Year"),
        final_path=final_path,
    )
