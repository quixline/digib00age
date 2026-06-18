"""
ComicVault — Editor (Basic) Router
GET /api/editor/genres    Editable genre list — shared by Basic and Full editor UIs
"""

from fastapi import APIRouter

from backend.editor.genres import load_genres

router = APIRouter(tags=["editor"])


@router.get("/editor/genres")
def get_genres():
    """Current genre list, read fresh from genres.json on every call (no caching) —
    EDITOR_SPEC.md Section 4.1, Tez edits the file directly."""
    return load_genres()
