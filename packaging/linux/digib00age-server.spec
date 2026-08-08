# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the digib00age reader/backend server, frozen separately
# from the tray app (digib00age-tray.spec) since sys.executable breaks as a
# way to relaunch "start_server.py" once the tray itself is frozen — see
# DECISIONS.md "Linux .deb release" / "Windows MSI installer".
#
# Build (from repo root):
#   venv/bin/pyinstaller --noconfirm --distpath dev/distros/deb-build/pyinstaller-out/dist \
#       --workpath dev/distros/deb-build/pyinstaller-out/build \
#       packaging/linux/digib00age-server.spec

import os
from PyInstaller.utils.hooks import copy_metadata

REPO_ROOT = os.path.dirname(os.path.dirname(SPECPATH))  # packaging/linux/ -> repo root
SRC = os.path.join(REPO_ROOT, "src")

datas = [
    (os.path.join(SRC, "frontend"), "frontend"),
    (os.path.join(SRC, "backend", "editor", "formats.json"), os.path.join("backend", "editor")),
    (os.path.join(SRC, "backend", "editor", "genres.json"), os.path.join("backend", "editor")),
    (os.path.join(SRC, "backend", "bin", "linux", "unrar"), os.path.join("backend", "bin", "linux")),
    (os.path.join(SRC, "backend", "bin", "linux", "LICENSE-unrar.txt"), os.path.join("backend", "bin", "linux")),
]
# comictalker's plugin discovery (comictalker/__init__.py) uses
# importlib.metadata.entry_points(group="comictagger.talker") at import time —
# needs the comictagger distribution's own metadata bundled, not just its .py
# files, or that lookup can fail/crash once frozen.
datas += copy_metadata("comictagger")

hiddenimports = [
    # start_server.py only ever references "backend.main:app" as a string for
    # uvicorn.run() to resolve dynamically — PyInstaller's static analysis
    # never sees that reference, so without this the whole backend.main
    # module (FastAPI app + all its routers) is silently left out of the
    # frozen build and the server fails to start at all.
    "backend.main",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "comicapi",
    "comictaggerlib",
    "comictaggerlib.issueidentifier",
    "comictaggerlib.resulttypes",
    "comictalker",
    "comictalker.talker_utils",
    "comictalker.talkers",
    "comictalker.talkers.comicvine",
    "fitz",
    "lxml.etree",
    "lxml._elementpath",
    "rarfile",
]

a = Analysis(
    [os.path.join(REPO_ROOT, "start_server.py")],
    pathex=[SRC, REPO_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="digib00age-server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="digib00age-server",
)
