"""
editable_lists.py — shared read/add/remove logic for the editable, file-backed
enforced-field lists (Genre, Format — see genres.py / formats.py).

Each list is a flat JSON array of strings, read fresh on every call (no
caching) so admin edits take effect immediately with no server restart.
"""

import json
from pathlib import Path


def load_list(path: Path) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_list(path: Path, values: list[str]) -> None:
    # newline='' prevents Python's text-mode translation of '\n' to os.linesep
    # (CRLF on Windows), keeping the file's line endings consistent regardless
    # of platform or how it was first created.
    with open(path, "w", encoding="utf-8", newline="") as f:
        json.dump(values, f, indent=2, ensure_ascii=False)
        f.write("\n")


def add_value(path: Path, name: str) -> list[str]:
    name = (name or "").strip()
    if not name:
        raise ValueError("Value cannot be empty")

    values = load_list(path)
    if any(v.lower() == name.lower() for v in values):
        raise ValueError(f"'{name}' is already in the list")

    values.append(name)
    _save_list(path, values)
    return values


def remove_value(path: Path, name: str) -> list[str]:
    values = load_list(path)
    match = next((v for v in values if v.lower() == name.lower()), None)
    if match is None:
        raise ValueError(f"'{name}' is not in the list")
    if len(values) <= 1:
        raise ValueError("At least one value must remain in the list")

    values = [v for v in values if v != match]
    _save_list(path, values)
    return values
