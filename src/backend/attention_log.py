"""
attention_log.py — durable "needs manual attention" registry for the one
Processing Tools outcome that can't safely self-recover: backup_model.py's
"critical_failure" (the original was renamed to `.bak`, the converted file
couldn't be placed at its target, and restoring the original also failed).

Unlike the per-tool audit logs (convert_log.py etc — one line among
potentially hundreds in a single Processing Folder Automation run), entries
here persist until explicitly resolved and are surfaced as a standing banner
in the Admin UI, so a failure from an unattended scheduled run can't just
scroll past unnoticed in a large batch's results.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Optional

from backend.config import _logs_dir

FILENAME = "needs_attention.json"


def _path():
    logs_dir = _logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir / FILENAME


def _read() -> list[dict]:
    path = _path()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _write(entries: list[dict]) -> None:
    with open(_path(), "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def add(kind: str, message: str, original_path: str,
        bak_path: Optional[str] = None, target_path: Optional[str] = None) -> dict:
    """Record one needs-attention entry. `kind` identifies which tool hit
    it (e.g. "convert_archives", "convert_images") for display grouping."""
    entry = {
        "id": uuid.uuid4().hex,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "kind": kind,
        "message": message,
        "original_path": original_path,
        "bak_path": bak_path,
        "target_path": target_path,
    }
    entries = _read()
    entries.append(entry)
    _write(entries)
    return entry


def list_entries() -> list[dict]:
    return _read()


def count() -> int:
    return len(_read())


def resolve(entry_id: str) -> bool:
    entries = _read()
    remaining = [e for e in entries if e["id"] != entry_id]
    if len(remaining) == len(entries):
        return False
    _write(remaining)
    return True
