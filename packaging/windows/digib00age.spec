# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the Windows MSI build (DECISIONS.md "Windows MSI
installer"). Freezes two --onedir executables that share one dist/ folder:

  digib00age-tray.exe    (src: tray/tray_app.py)   - windowed, no console
  digib00age-server.exe  (src: start_server.py)     - console kept on for
                                                       this first build, for
                                                       easier crash triage

They share a single COLLECT() call (not two separate builds) so both exes
land flat in the same dist/digib00age/ folder, next to a shared _internal/
support dir - this matches tray_app.py's _frozen_server_executable_path(),
which assumes the server exe sits directly beside the tray exe.

Source is a "pre-build" staging mirror of src/ (backend/frontend/tray
flattened out of src/, plus the repo-root LICENSE/README/requirements.txt/
start.bat/start_server.py/config.json), not src/ directly. Locally this
defaults to dev/distros/app-windows-pre-build-v1/ (gitignored, hand-synced by
Tez before a local rebuild - unaffected by this spec's own move into
packaging/windows/, since the default is computed from the repo root, not
from this file's location). CI (.github/workflows/windows-build.yml)
generates a fresh staging copy each run and points here via the
DIGIB00AGE_STAGING env var instead, since dev/ doesn't exist in a clean
checkout.
"""

import os
import sys

from PyInstaller.utils.hooks import collect_submodules

REPO_ROOT = os.path.normpath(os.path.join(SPECPATH, "..", ".."))
STAGING = os.environ.get(
    "DIGIB00AGE_STAGING",
    os.path.join(REPO_ROOT, "dev", "distros", "app-windows-pre-build-v1"),
)
ICON = os.path.join(SPECPATH, "digib00age.ico")

# collect_submodules() below does a real Python import at spec-eval time
# (separate from Analysis's own static scan), so "backend" needs to be
# resolvable here too.
sys.path.insert(0, STAGING)

# Mirror backend/__init__.py's own sys.path trick here, at spec-eval time -
# Analysis statically resolves ct_bridge.py's bare `import comicapi` etc.
# against whatever's on sys.path *right now* (it does not execute
# backend/__init__.py's runtime logic). Without this, Analysis finds the
# pip-installed comicapi/comictalker/comictaggerlib on site-packages instead
# of the vendored copy, bundles THAT under the bare top-level names, and the
# frozen EXE's FrozenImporter satisfies `import comicapi` straight out of the
# PYZ before ever consulting sys.path - so backend/__init__.py's runtime
# sys.path.insert becomes dead code once frozen, silently shipping the pip
# source instead of the vendored one. See dev/docs/comictagger-vendoring-scope.md.
sys.path.insert(0, os.path.join(STAGING, "backend", "vendor"))

datas_common = [
    (os.path.join(STAGING, "frontend"), "frontend"),
    (os.path.join(STAGING, "backend", "bin", "windows", "unrar.exe"), os.path.join("backend", "bin", "windows")),
    (os.path.join(STAGING, "backend", "editor", "formats.json"), os.path.join("backend", "editor")),
    (os.path.join(STAGING, "backend", "editor", "genres.json"), os.path.join("backend", "editor")),
    # Explicit, not left to the pip-installed comictagger distribution's own
    # hook-comicapi.py (collect_data_files("comicapi.data")) - that hook only
    # exists while comictagger is still pip-installed (entry-point-registered
    # hook discovery), and goes away the moment Step 5 drops it. Source from
    # the vendored copy directly so this survives that cutover unchanged.
    (os.path.join(STAGING, "backend", "vendor", "comicapi", "data", "publishers.json"), os.path.join("comicapi", "data")),
    # Alembic's ScriptDirectory scans versions/ on the filesystem at runtime —
    # it does NOT import them as a normal Python package walk, so PyInstaller's
    # static Analysis scan never sees 0001_baseline.py unless shipped as raw
    # data, same as the two editor JSONs above (see DECISIONS.md "Adopted
    # Alembic for schema migrations").
    (os.path.join(STAGING, "backend", "migrations"), os.path.join("backend", "migrations")),
    (os.path.join(STAGING, "config.json"), "."),
]

# uvicorn resolves its event-loop/protocol implementations dynamically
# (uvicorn.loops.auto etc. import-probe at runtime) - PyInstaller's static
# import scan can miss these. comictagger's comictalker plugin discovery is
# the other likely gap; add hiddenimports here as the first build surfaces
# ModuleNotFoundError for them (see plan Phase 4 note on expected iteration).
hiddenimports_common = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    # start_server.py only references "backend.main:app" as a string inside
    # uvicorn.run() - PyInstaller's static scan can't see that, so
    # backend.main (and everything it imports - all the routers) never got
    # bundled without this. collect_submodules is a safety net for the rest
    # of the backend/ package (routers/, editor/) in case anything else is
    # only reached dynamically.
    "backend.main",
] + collect_submodules("backend")

a_tray = Analysis(
    [os.path.join(STAGING, "tray", "tray_app.py")],
    pathex=[STAGING],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

a_server = Analysis(
    [os.path.join(STAGING, "start_server.py")],
    pathex=[STAGING],
    binaries=[],
    datas=datas_common,
    hiddenimports=hiddenimports_common,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz_tray = PYZ(a_tray.pure, a_tray.zipped_data)
pyz_server = PYZ(a_server.pure, a_server.zipped_data)

# Default PyInstaller 6.x nests support files under _internal/, but
# config.py's/tray_app.py's frozen branches assume backend/, frontend/, and
# config.json sit flat next to the exes (matching
# _frozen_server_executable_path()'s sibling-exe assumption) - flatten back
# to the pre-6.0 layout instead of teaching the Python code about an
# _internal indirection. This is an EXE()-level setting, not COLLECT().
_FLAT = {"contents_directory": "."}

exe_tray = EXE(
    pyz_tray,
    a_tray.scripts,
    [],
    exclude_binaries=True,
    name="digib00age-tray",
    icon=ICON,
    console=False,
    **_FLAT,
)

exe_server = EXE(
    pyz_server,
    a_server.scripts,
    [],
    exclude_binaries=True,
    name="digib00age-server",
    icon=ICON,
    console=True,
    **_FLAT,
)

coll = COLLECT(
    exe_tray,
    a_tray.binaries,
    a_tray.zipfiles,
    a_tray.datas,
    exe_server,
    a_server.binaries,
    a_server.zipfiles,
    a_server.datas,
    strip=False,
    upx=False,
    name="digib00age",
)
