"""
singles_move_log.py — audit log for the Move Singles Folders Processing Tool
(§11.7). Thin wrapper over tool_logs.py's shared append-only/1MB-cap writer,
same shape as filename_sort_log.py. `[AUTO]`-prefix support included now
even though nothing calls it with auto=True yet — matches convention.
"""

from __future__ import annotations

from datetime import datetime

from backend import tool_logs

FILENAME = "singles_move_log.md"


def append_entry(
    folder_name: str,
    destination: str,
    error: str | None = None,
    auto: bool = False,
    issues_updated: int = 0,
    db_sync_error: str | None = None,
) -> None:
    prefix = "[AUTO] " if auto else ""
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")

    if error:
        line = f"{ts} — {prefix}{folder_name} → FAILED: {error}"
    elif db_sync_error:
        line = f"{ts} — {prefix}{folder_name} → {destination} [OK, DB SYNC FAILED — rescan and check logs]"
    else:
        suffix = f", {issues_updated} issue(s) re-pointed" if issues_updated else ""
        line = f"{ts} — {prefix}{folder_name} → {destination} [OK{suffix}]"

    tool_logs.append_line(FILENAME, line)
