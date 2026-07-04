"""
ct_autotag_log.py — audit log for CT Auto-Tag (ADMIN_SPEC.md §11.4.9). Thin
wrapper over tool_logs.py's shared append-only/1MB-cap writer, mirroring
convert_log.py/convert_images_log.py's pattern.

Unlike those two logs, every line here always carries the [AUTO] prefix — CT
Auto-Tag only ever runs as part of Processing Folder Automation, never as a
standalone admin-UI tool. Manual matches (Full Editor's Search Online) are an
interactive, one-file-at-a-time action and are never logged here.
"""

from __future__ import annotations

from datetime import datetime

from backend import tool_logs

FILENAME = "ct_autotag_log.md"


def append_entry(
    filename: str,
    confidence: str,
    tags_written: bool,
    series: str | None,
    issue: str | None,
    year: str | None,
    error: str | None = None,
) -> None:
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")

    if error:
        line = f"{ts} — [AUTO] {filename} [error: {error}]"
    elif confidence == "no_match":
        line = f"{ts} — [AUTO] {filename} [skipped: no match]"
    elif confidence == "low_confidence" and not tags_written:
        line = f"{ts} — [AUTO] {filename} [skipped: low confidence, Save on Low Confidence off]"
    elif confidence == "low_confidence":
        line = f'{ts} — [AUTO] {filename} [tagged: low confidence, NeedsReview set] "{series}" #{issue} ({year})'
    else:
        line = f'{ts} — [AUTO] {filename} [tagged: confident] "{series}" #{issue} ({year})'

    tool_logs.append_line(FILENAME, line)
