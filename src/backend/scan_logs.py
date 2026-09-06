"""
digib00age — Scan log files (ADMIN_SPEC.md §4 / §8)

Persistent, on-disk record of scan results — separate from scanner.py's
in-memory ScanProgress.log, which is ephemeral (reset every scan, capped at
500 lines) and not meant to survive past the live progress bar.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from backend.config import _logs_dir, get_config

LOGS_DIR = _logs_dir()

_FILENAMES = {
    "last_scan": "last_scan_log.md",
    "changed_files": "changed_files_log.md",
    "new_files": "new_files_log.md",
    "missing": "missing_log.md",
}

# Logs that accumulate 0+ lines per scan (as opposed to last_scan_log.md, which is
# always exactly one line per scan) get a marker line at the start of each scan run,
# so the most recent scan's entries can be sliced out without a per-line timestamp.
_MARKED_LOGS = ("changed_files", "new_files", "missing")
_SCAN_MARKER_PREFIX = "## Scan "


def log_path(log_name: str) -> Path:
    return LOGS_DIR / _FILENAMES[log_name]


def clear_all_logs() -> None:
    for name in _FILENAMES:
        path = log_path(name)
        if path.exists():
            path.unlink()


def append_log_line(log_name: str, line: str) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    path = log_path(log_name)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    _truncate_if_oversized(path)


def _truncate_if_oversized(path: Path) -> None:
    limit_mb = get_config().get("log_size_limit_mb", 5)
    limit_bytes = limit_mb * 1024 * 1024
    if path.stat().st_size <= limit_bytes:
        return
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    drop_count = max(1, len(lines) // 10)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines[drop_count:])


def write_scan_markers(started_at: datetime) -> None:
    """Called once at the start of each scan run, before any entries are appended,
    so read_recent_log() always has a boundary to slice the latest scan from —
    even a scan that finds zero changes still leaves a marker confirming it ran."""
    marker = f"{_SCAN_MARKER_PREFIX}— {started_at.strftime('%d/%m/%Y %H:%M')}"
    for log_name in _MARKED_LOGS:
        append_log_line(log_name, marker)


def append_last_scan_entry(started_at: datetime, finished_at: datetime) -> None:
    duration = finished_at - started_at
    total_seconds = int(duration.total_seconds())
    hh, rem = divmod(total_seconds, 3600)
    mm, ss = divmod(rem, 60)
    line = f"{started_at.strftime('%d/%m/%Y %H:%M')} — Duration: {hh:02d}:{mm:02d}:{ss:02d}"
    append_log_line("last_scan", line)


def append_changed_files_entry(filename: str, change_type: str = "metadata updated") -> None:
    append_log_line("changed_files", f"{filename} — {change_type}")


def append_new_files_entry(filename: str, location: str) -> None:
    append_log_line("new_files", f"{filename} — {location}")


def append_missing_entry(filename: str, last_known_path: str, date_missing: datetime) -> None:
    line = f"{filename} — {last_known_path} — {date_missing.strftime('%d/%m/%Y')}"
    append_log_line("missing", line)


def read_last_scan_timestamp() -> str | None:
    """Last line of the persistent last-scan log, surviving server restarts
    (unlike scanner.py's in-memory ScanProgress.finished_at)."""
    path = log_path("last_scan")
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines[-1] if lines else None


def read_recent_log(log_name: str) -> tuple[str, bool]:
    """Just the most recent scan's entries, not the full accumulated history —
    full history is still on disk and viewable via a text editor (View Logs Folder)."""
    path = log_path(log_name)
    if not path.exists():
        return "", False
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if log_name == "last_scan":
        return (lines[-1] if lines else ""), True

    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith(_SCAN_MARKER_PREFIX):
            return "".join(lines[i:]), True

    # No marker found — pre-existing log from before this feature shipped.
    # Fall back to full content rather than hiding history with no way to reach it.
    return "".join(lines), True
