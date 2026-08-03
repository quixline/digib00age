"""
formats.py — loader/add/remove for the editable format list.

Per comicvault-changes.md Tier 4 Item 1 (2026-06-20): Format is no longer a
locked constant (EDITOR_SPEC.md Section 4.2, deviation logged there) — it's
now a flat JSON array, same mechanism as Genre (genres.py), admin-editable via
the Admin page. Served fresh on every load rather than cached.
"""

from pathlib import Path

from backend.editor.editable_lists import add_value, load_list, remove_value

FORMATS_PATH = Path(__file__).parent / "formats.json"


def load_formats() -> list[str]:
    """Read the current format list from formats.json."""
    return load_list(FORMATS_PATH)


def add_format(name: str) -> list[str]:
    """Add a format to formats.json. Raises ValueError on empty/duplicate name."""
    return add_value(FORMATS_PATH, name)


def remove_format(name: str) -> list[str]:
    """Remove a format from formats.json. Raises ValueError if not found or it's the last one."""
    return remove_value(FORMATS_PATH, name)
