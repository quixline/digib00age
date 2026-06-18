"""
constants.py — locked, hardcoded dropdown lists for the editor core.

Per EDITOR_SPEC.md Sections 4.2/4.3: Format and AgeRating are fully enforced,
select-only dropdowns with no editing mechanism — unlike Genre (genres.json),
these lists are not meant to change.
"""

FORMAT_OPTIONS = [
    "Graphic Novel",
    "Series",
    "One Shot",
    "Anthology",
    "Art Book",
    "Limited Series",
    "Special",
    "Trade Paper Back",
    "Annual",
    "Other",
]

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
