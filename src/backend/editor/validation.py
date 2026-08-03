"""
validation.py — enforced-field validation shared by Basic and Full editors.

EDITOR_SPEC.md Section 4.4: Genre/Format/AgeRating must each resolve to
enforced values before a save can proceed. The popup/toolbox UIs also gate
Save client-side, so this should rarely fire in normal use — it's the
server-side source of truth.
"""

from backend.editor.constants import AGE_RATING_OPTIONS
from backend.editor.formats import load_formats
from backend.editor.genres import load_genres


def validate_enforced_fields(field_values: dict) -> list[str]:
    errors = []

    genre_value = (field_values.get("Genre") or "").strip()
    genre_names = [g.strip() for g in genre_value.split(",") if g.strip()]
    enforced_genres = set(load_genres())
    if not genre_names:
        errors.append("Genre: at least one value is required")
    else:
        for name in genre_names:
            if name not in enforced_genres:
                errors.append(f"Genre: '{name}' is not in the enforced list")

    format_value = (field_values.get("Format") or "").strip()
    if format_value not in load_formats():
        errors.append(f"Format: '{format_value or '(blank)'}' is not in the enforced list")

    rating_value = (field_values.get("AgeRating") or "").strip()
    if rating_value not in AGE_RATING_OPTIONS:
        errors.append(f"AgeRating: '{rating_value or '(blank)'}' is not in the enforced list")

    return errors
