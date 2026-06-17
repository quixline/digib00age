"""
ComicVault — Config helper
Loads config.json once and provides a get_config() function.
All paths in the codebase come from here — nothing is ever hardcoded.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

# Project root is one level up from backend/
BACKEND_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent


@lru_cache(maxsize=1)
def get_config() -> dict:
    """Load and return config.json. Cached after first call."""
    config_path = PROJECT_ROOT / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else PROJECT_ROOT / p


# Module-level constants derived from config.json — used by scanner and database
_cfg = get_config()

DB_PATH        = _resolve(_cfg["db_path"])
LIBRARY_ROOT   = _cfg["library_root"]
THUMBNAIL_DIR  = _resolve(_cfg["thumbnail_dir"])
THUMBNAIL_SIZE = int(_cfg.get("thumbnail_size", 300))
SERIES_FOLDER  = _cfg.get("series_folder", "Series")
SINGLES_FOLDER = _cfg.get("singles_folder", "Singles")
SCAN_EXCLUDE   = _cfg.get("scan_exclude", [])
READER_PORT    = int(_cfg.get("reader_port", 8000))
EDITOR_PORT    = int(_cfg.get("editor_port", 8001))
