"""
digib00age — Config helper
Loads config.json once and provides a get_config() function.
All paths in the codebase come from here — nothing is ever hardcoded.
"""

from __future__ import annotations

import json
import os
import platform
import sys
from functools import lru_cache
from pathlib import Path

import rarfile

# backend/ lives under src/ — PROJECT_ROOT (= src/) is what the rest of the
# codebase's "backend/..."-relative paths (db_path, etc.) are joined against.
# config.json itself stays at the true repo root, one level above src/.
BACKEND_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent
REPO_ROOT = PROJECT_ROOT.parent

# A packaged (.deb) Linux install lands in /opt, which isn't user-writable —
# unlike the Windows per-user install (%LocalAppData%, already writable) or
# any dev/unfrozen run (writes next to the repo as always). Only this exact
# combination redirects config/db/thumbnails to XDG user paths; every other
# run — including minty's current unfrozen dev/manual testing — is
# unaffected. Mirrors the frozen-branch precedent in tray_app.py.
_IS_FROZEN_LINUX = getattr(sys, "frozen", False) and platform.system() == "Linux"


def _xdg_data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME", "~/.local/share")
    return Path(base).expanduser() / "digib00age"


def _xdg_config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME", "~/.config")
    return Path(base).expanduser() / "digib00age" / "config.json"


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


def _config_path() -> Path:
    return _xdg_config_path() if _IS_FROZEN_LINUX else REPO_ROOT / "config.json"


# The bare-minimum keys config.json ships with before any library is set up
# (see the "Reset config.json to a clean template" commit) — everything else
# (library_root(s), scan_exclude, backup_*, log_last_viewed, etc.) is added
# later by Admin UI / scan / library setup and is what a wipe clears back out.
_BASE_CONFIG_KEYS = ("reader_port", "thumbnail_size", "thumbnail_dir", "db_path")
_DEFAULT_CONFIG = {
    "reader_port": 9800,
    "thumbnail_size": 300,
    "thumbnail_dir": "backend/thumbnails",
    "db_path": "backend/digib00age.db",
}


@lru_cache(maxsize=1)
def get_config() -> dict:
    """Load and return config.json. Cached after first call."""
    config_path = _config_path()
    if _IS_FROZEN_LINUX and not config_path.exists():
        # First launch of a packaged .deb install — nothing ships a
        # config.json at the XDG path yet, so seed it with the same bare
        # template dev/Windows already start from.
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(_DEFAULT_CONFIG, f, indent=2)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict) -> dict:
    """Read-modify-write config.json with the given keys, then invalidate the cache."""
    config_path = _config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        current = json.load(f)
    current.update(data)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    get_config.cache_clear()
    return current


def reset_config() -> dict:
    """Rewrite config.json down to just _BASE_CONFIG_KEYS, dropping every key
    added since (library setup, scan, admin settings). Used by clear_database()
    so a DB wipe also puts config.json back to its pre-setup state."""
    config_path = _config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        current = json.load(f)
    minimal = {k: current[k] for k in _BASE_CONFIG_KEYS if k in current}
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(minimal, f, indent=2)
    get_config.cache_clear()
    return minimal


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    base = _xdg_data_dir() if _IS_FROZEN_LINUX else PROJECT_ROOT
    return base / p


# Module-level constants derived from config.json — used by scanner and database
_cfg = get_config()

DB_PATH        = _resolve(_cfg["db_path"])
LIBRARY_ROOT   = _cfg.get("library_root")
THUMBNAIL_DIR  = _resolve(_cfg["thumbnail_dir"])
THUMBNAIL_SIZE = int(_cfg.get("thumbnail_size", 300))
SERIES_FOLDER  = _cfg.get("series_folder", "Series")
SINGLES_FOLDER = _cfg.get("singles_folder", "Singles")
READER_PORT    = int(_cfg.get("reader_port", 9800))


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
