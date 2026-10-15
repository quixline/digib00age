"""
ct_vendor_bootstrap.py — seeds comicapi's archiver/tag plugin registry
without relying on setuptools entry points.

comicapi.comicarchive.load_archive_plugins()/load_tag_plugins() normally
discover the Zip/Rar/7z/Folder archivers and the "cr" (ComicRack) tag
reader via importlib.metadata.entry_points(), reading them off the
"comictagger" pip distribution's registered entry points (comicapi.archiver
/ comicapi.tags groups) — confirmed 2026-10-15 by reading comicarchive.py
directly. Those entry points only exist while comictagger is pip-installed;
dropping that dependency per dev/docs/comictagger-vendoring-scope.md's
final cutover step would otherwise make ComicArchive silently find zero
archivers on every open, with no import-time error — this is on the
digib00age-exercised code path (ct_bridge.py already calls
ca.read_tags("cr")), not an unused CT feature.

Both loader functions accept a local_plugins parameter for exactly this
purpose, so the fix is new digib00age code calling that seam directly with
the real classes — no change to CT's own vendored logic. Both functions are
memoized (comicapi/comicarchive.py: `if archivers: return` / `if tags:
return`), so this must run before anything else constructs a ComicArchive;
import this module for its side effect before any ComicArchive(...) call —
ct_bridge.py does this at module-import time.
"""
from __future__ import annotations

from comicapi.archivers.folder import FolderArchiver
from comicapi.archivers.rar import RarArchiver
from comicapi.archivers.sevenzip import SevenZipArchiver
from comicapi.archivers.zip import ZipArchiver
from comicapi.comicarchive import load_archive_plugins, load_tag_plugins
from comicapi.tags.comicrack import ComicRack

load_archive_plugins(local_plugins=[ZipArchiver, RarArchiver, SevenZipArchiver, FolderArchiver])
load_tag_plugins(local_plugins=[ComicRack])
