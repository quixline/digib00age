"""
genres.py — loader for the editable genre list.

Per EDITOR_SPEC.md Section 4.1: unlike Format/AgeRating (constants.py),
Genre is not hardcoded — it's a flat JSON array Tez can edit directly as the
library is worked through, served fresh on every load rather than cached.
"""

import json
from pathlib import Path

GENRES_PATH = Path(__file__).parent / "genres.json"


def load_genres() -> list[str]:
    """Read the current genre list from genres.json."""
    with open(GENRES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
