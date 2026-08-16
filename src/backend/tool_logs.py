"""
tool_logs.py — shared append-only log writer for the Processing Tools
(Rename §12.1.7, Convert Archives §12.2.6, Convert Images §12.3.7). Parallel
to scan_logs.py's pattern, but with an independent, fixed 1MB cap — these
logs are NOT governed by the configurable Log Size Limit setting (§8), which
stays scoped to the four scan logs only.
"""

from __future__ import annotations

from backend.config import REPO_ROOT

LOGS_DIR = REPO_ROOT / "logs"

MAX_BYTES = 1 * 1024 * 1024  # fixed 1MB cap, independent of log_size_limit_mb


def append_line(filename: str, line: str) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    path = LOGS_DIR / filename
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    _truncate_if_oversized(path)


def _truncate_if_oversized(path) -> None:
    if path.stat().st_size <= MAX_BYTES:
        return
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    drop_count = max(1, len(lines) // 10)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines[drop_count:])
