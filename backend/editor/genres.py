"""
genres.py — loader/add/remove for the editable genre list.

Per EDITOR_SPEC.md Section 4.1: unlike AgeRating (constants.py), Genre is not
hardcoded — it's a flat JSON array, admin-editable via the Admin page (Tier 4
Item 1, comicvault-changes.md, 2026-06-20) or by editing genres.json directly.
Served fresh on every load rather than cached.
"""

from pathlib import Path

from backend.editor.editable_lists import add_value, load_list, remove_value

GENRES_PATH = Path(__file__).parent / "genres.json"


def load_genres() -> list[str]:
    """Read the current genre list from genres.json."""
    return load_list(GENRES_PATH)


def add_genre(name: str) -> list[str]:
    """Add a genre to genres.json. Raises ValueError on empty/duplicate name."""
    return add_value(GENRES_PATH, name)


def remove_genre(name: str) -> list[str]:
    """Remove a genre from genres.json. Raises ValueError if not found or it's the last one."""
    return remove_value(GENRES_PATH, name)
