"""
path_utils.py — shared folder-path normalization and prefix-matching helpers.
Used by routers/admin.py (custom tab folder validation) and routers/library.py
(custom tab issue filtering) so both sites apply identical, correct logic —
in particular the separator-suffixed boundary check (a folder "C:\\Comics\\Batman"
must not match "C:\\Comics\\Batman2\\...").
"""

import os


def normalize_path(path: str) -> str:
    return os.path.normpath(os.path.abspath(path))


def is_under(child: str, parent: str) -> bool:
    """True if `child` is `parent` itself or a path beneath it."""
    c = normalize_path(child).lower()
    p = normalize_path(parent).lower()
    return c == p or c.startswith(p + os.sep)
