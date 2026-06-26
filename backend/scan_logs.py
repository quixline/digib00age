"""
ComicVault — Scan log files (ADMIN_SPEC.md §4 / §8)

Persistent, on-disk record of scan results — separate from scanner.py's
in-memory ScanProgress.log, which is ephemeral (reset every scan, capped at
500 lines) and not meant to survive past the live progress bar.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from backend.config import PROJECT_ROOT, get_config

LOGS_DIR = PROJECT_ROOT / "logs"

_FILENAMES = {
    "last_scan": "last_scan_log.md",
    "changed_files": "changed_files_log.md",
    "new_files": "new_files_log.md",
    "missing": "missing_log.md",
}


def log_path(log_name: str) -> Path:
    return LOGS_DIR / _FILENAMES[log_name]


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


def read_log(log_name: str, max_lines: int = 1000) -> tuple[str, bool]:
    path = log_path(log_name)
    if not path.exists():
        return "", False
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[-max_lines:]), True
