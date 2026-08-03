"""
rename_log.py — audit log for the File Rename Tool (§12.1.7). Thin wrapper
over tool_logs.py's shared append-only/1MB-cap writer.
"""

from __future__ import annotations

from datetime import datetime

from backend import tool_logs

FILENAME = "rename_log.md"


def append_entry(old_filename: str, new_filename: str) -> None:
    line = f"{datetime.now().strftime('%d/%m/%Y %H:%M')} — {old_filename} → {new_filename}"
    tool_logs.append_line(FILENAME, line)
