"""
convert_log.py — audit log for Convert Archives (§11.2.6). Thin wrapper over
tool_logs.py's shared append-only/1MB-cap writer. `[AUTO]`-prefixed lines
(§11.4.9) distinguish Processing Folder Automation runs from manual ones —
the prefix is the caller's job (router for manual, processing_folder for
automated), keeping the conversion callable itself trigger-agnostic.
"""

from __future__ import annotations

from datetime import datetime

from backend import tool_logs

FILENAME = "convert_log.md"


def append_entry(old_filename: str, new_filename: str, pages_skipped: int = 0,
                  error: str | None = None, auto: bool = False) -> None:
    prefix = "[AUTO] " if auto else ""
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")

    if error:
        line = f"{ts} — {prefix}{old_filename} → FAILED: {error}"
    elif pages_skipped:
        line = (f"{ts} — {prefix}{old_filename} → {new_filename} "
                f"[OK, {pages_skipped} pages skipped] (backed up to {old_filename}.bak)")
    else:
        line = f"{ts} — {prefix}{old_filename} → {new_filename} [OK]"

    tool_logs.append_line(FILENAME, line)
