"""
filename_sort_log.py — audit log for the Sort by Filename Processing Tool
(§11.5). Thin wrapper over tool_logs.py's shared append-only/1MB-cap writer,
same shape as convert_log.py. `[AUTO]`-prefix support included now even
though automation isn't wired yet — cheap to add, matches convention.
"""

from __future__ import annotations

from datetime import datetime

from backend import tool_logs

FILENAME = "filename_sort_log.md"


def append_entry(filename: str, folder_name: str, error: str | None = None, auto: bool = False) -> None:
    prefix = "[AUTO] " if auto else ""
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")

    if error:
        line = f"{ts} — {prefix}{filename} → FAILED: {error}"
    else:
        line = f"{ts} — {prefix}{filename} → {folder_name}\\{filename} [OK]"

    tool_logs.append_line(FILENAME, line)
