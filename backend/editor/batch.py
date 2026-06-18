"""
batch.py — increment-number logic and per-file processing orchestration for
the editor core.

Ported from CAPT's utils/xml_worker.py. Increment-number is Full Editor only
(EDITOR_SPEC.md Section 3.4) — sequential, no collision guardrail, confirmed
acceptable since this only ever runs against files not yet in ComicVault's
database.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from backend.editor.archive_io import write_comicinfo_to_cbz
from backend.editor.field_merge import build_xml_from_fields

logger = logging.getLogger(__name__)


def apply_increment(field_values_list: list[dict], start_issue_no: int) -> None:
    """
    Set "Number" sequentially across field_values_list in place, starting at
    start_issue_no and incrementing by 1 per file in list order.
    """
    for idx, field_values in enumerate(field_values_list):
        field_values["Number"] = str(start_issue_no + idx)


@dataclass
class BatchItem:
    archive_path: str
    field_values: dict
    original_xml_content: Optional[str] = None


@dataclass
class BatchResult:
    processed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.errors


def process_files(items: list[BatchItem]) -> BatchResult:
    """
    Apply field-merge + archive rewrite to each item in order. A failure on
    one file is recorded and the batch continues rather than aborting.
    """
    result = BatchResult()
    for item in items:
        try:
            xml_content = build_xml_from_fields(
                item.field_values, item.original_xml_content
            )
            write_comicinfo_to_cbz(item.archive_path, xml_content)
            result.processed += 1
        except Exception as exc:
            logger.error("Error processing %s: %s", item.archive_path, exc)
            result.errors.append(f"{item.archive_path}: {exc}")
    return result
