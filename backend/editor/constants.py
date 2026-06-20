"""
constants.py — locked, hardcoded dropdown lists for the editor core.

Per EDITOR_SPEC.md Section 4.3: AgeRating is fully enforced, select-only, with
no editing mechanism — this list is not meant to change. Format was the same
until Tier 4 Item 1 (comicvault-changes.md, 2026-06-20) made it an editable
list too (backend/editor/formats.json, formats.py) — see EDITOR_SPEC.md
Section 4.2 deviation note. Genre has always been editable (genres.json).
"""

AGE_RATING_OPTIONS = [
    "Everyone",
    "Early Childhood",
    "Everyone 10+",
    "PG",
    "Adult",
    "Teen",
    "Teen+",
    "Mature",
]
