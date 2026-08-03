"""
convert_images_log.py — audit log for Convert Images (§11.3.7). Thin wrapper
over tool_logs.py's shared append-only/1MB-cap writer. `[AUTO]`-prefixed
lines (§11.4.9) distinguish Processing Folder Automation runs from manual
ones.
"""

from __future__ import annotations

from datetime import datetime

from backend import tool_logs

FILENAME = "convert_images_log.md"


def append_entry(old_filename: str, new_filename: str, images_skipped: int = 0,
                  error: str | None = None, auto: bool = False) -> None:
    """
    Line format follows the unified backup model (§11.4.6): a clean success
    no longer keeps a `.bak` (auto-deleted), so — unlike §11.3.7's original
    doc sample, written before the Item 15 unification and not updated to
    match — a clean-success line carries no "(backed up to ...)" note. Only
    a success-with-warnings line does, since that's the only outcome that
    actually keeps one. Matches convert_log.py's (§11.2.6, already-correct)
    pattern for the same reason.
    """
    prefix = "[AUTO] " if auto else ""
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    same_name = old_filename == new_filename
    label = old_filename if same_name else f"{old_filename} → {new_filename}"

    if error:
        line = f"{ts} — {prefix}{old_filename} [FAILED] — {error}"
    elif images_skipped:
        line = f"{ts} — {prefix}{label} [OK, {images_skipped} images skipped] (backed up to {old_filename}.bak)"
    else:
        line = f"{ts} — {prefix}{label} [OK]"

    tool_logs.append_line(FILENAME, line)
