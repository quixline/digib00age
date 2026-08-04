"""
digib00age — Config helper
Loads config.json once and provides a get_config() function.
All paths in the codebase come from here — nothing is ever hardcoded.
"""

from __future__ import annotations

import json
import os
import platform
from functools import lru_cache
from pathlib import Path

import rarfile

# backend/ lives under src/ — PROJECT_ROOT (= src/) is what the rest of the
# codebase's "backend/..."-relative paths (db_path, etc.) are joined against.
# config.json itself stays at the true repo root, one level above src/.
BACKEND_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent
REPO_ROOT = PROJECT_ROOT.parent


def _configure_unrar_tool() -> None:
    """Point rarfile at the bundled unrar binary (bin/windows or bin/linux)
    instead of requiring one on the host's PATH. Falls back to rarfile's
    default PATH lookup on any OS/arch the bundle doesn't cover (e.g. a dev
    machine that isn't Windows or x86_64 Linux) — same behaviour as before
    this existed."""
    system = platform.system()
    if system == "Windows":
        bundled = BACKEND_DIR / "bin" / "windows" / "unrar.exe"
    elif system == "Linux":
        bundled = BACKEND_DIR / "bin" / "linux" / "unrar"
    else:
        return
    if not bundled.exists():
        return
    if system == "Linux":
        # git doesn't reliably preserve the executable bit through a
        # Windows checkout/commit round-trip — enforce it at runtime.
        try:
            os.chmod(bundled, 0o755)
        except OSError:
            pass
    rarfile.UNRAR_TOOL = str(bundled)


_configure_unrar_tool()


@lru_cache(maxsize=1)
def get_config() -> dict:
    """Load and return config.json. Cached after first call."""
    config_path = REPO_ROOT / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict) -> dict:
    """Read-modify-write config.json with the given keys, then invalidate the cache."""
    config_path = REPO_ROOT / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        current = json.load(f)
    current.update(data)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    get_config.cache_clear()
    return current


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else PROJECT_ROOT / p


# Module-level constants derived from config.json — used by scanner and database
_cfg = get_config()

DB_PATH        = _resolve(_cfg["db_path"])
LIBRARY_ROOT   = _cfg.get("library_root")
THUMBNAIL_DIR  = _resolve(_cfg["thumbnail_dir"])
THUMBNAIL_SIZE = int(_cfg.get("thumbnail_size", 300))
SERIES_FOLDER  = _cfg.get("series_folder", "Series")
SINGLES_FOLDER = _cfg.get("singles_folder", "Singles")
READER_PORT    = int(_cfg.get("reader_port", 9424))


def get_library_root() -> str | None:
    """
    Return the current library_root, re-read fresh from config.json (not the
    frozen LIBRARY_ROOT constant above) so a path saved via the Admin UI
    takes effect immediately without restarting the server.
    """
    return get_config().get("library_root")


def get_scan_exclude() -> list[str]:
    """
    Return the current scan_exclude list, re-read fresh from config.json on
    every call (not cached at import time) so an exclusion added via the
    Admin UI takes effect on the very next scan without restarting the
    server — same reasoning as get_library_root() above.
    """
    return get_config().get("scan_exclude", [])


def is_library_configured() -> bool:
    """Return True if library_root is set and the path exists on disk."""
    root = get_library_root()
    return bool(root) and os.path.isdir(root)
