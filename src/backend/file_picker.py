"""
file_picker.py — shared in-app folder-tree picker backend, used by every
Processing Tool (Rename §12.1, Convert Archives §12.2, Convert Images §12.3,
Processing Folder Automation §12.4). Unlike the Editor's/Custom Tabs' pickers,
this one is not scoped to library_root — it lists any directory the server
process can reach, with a drive-letter listing as the Up-navigation terminus
past a drive's root. Each tool's router applies its own extension/content
filter on top of the plain file list this returns.
"""

from __future__ import annotations

import os
import platform
import string


def list_directory(path: str) -> dict:
    """Files + folders directly inside `path`, unfiltered, no recursion."""
    if not os.path.isdir(path):
        raise FileNotFoundError(path)

    folders: list[dict] = []
    files: list[dict] = []
    try:
        for name in sorted(os.listdir(path), key=str.lower):
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                folders.append({"name": name, "path": full_path})
            elif os.path.isfile(full_path):
                files.append({"name": name, "path": full_path})
    except (OSError, PermissionError) as exc:
        raise PermissionError(str(exc))

    return {"path": path, "folders": folders, "files": files}


def list_drives() -> list[dict]:
    """Root-level listing — the Up-navigation terminus past a drive's/root's
    top (mirrors the Editor picker's Home/Up pattern, extended: Up climbs all
    the way to this list rather than stopping at a fixed root). Windows has
    multiple drive letters to enumerate; POSIX has a single filesystem root."""
    if platform.system() == "Windows":
        drives = []
        for letter in string.ascii_uppercase:
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                drives.append({"name": f"{letter}:", "path": drive_path})
        return drives
    return [{"name": "/", "path": "/"}]
