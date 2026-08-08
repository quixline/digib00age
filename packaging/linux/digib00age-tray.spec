# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the digib00age tray app. gi/PyGObject (AppIndicator) is
# deliberately excluded from the freeze and resolved from the system's own
# python3-gi at runtime instead — see the sys.path shim near the top of
# tray_app.py and DECISIONS.md "Linux .deb release" / BUG-040. The system
# libs it needs are declared as .deb Depends:, not bundled here.
#
# Build (from repo root):
#   venv/bin/pyinstaller --noconfirm --distpath dev/distros/deb-build/pyinstaller-out/dist \
#       --workpath dev/distros/deb-build/pyinstaller-out/build \
#       packaging/linux/digib00age-tray.spec

import os

REPO_ROOT = os.path.dirname(os.path.dirname(SPECPATH))  # packaging/linux/ -> repo root
SRC = os.path.join(REPO_ROOT, "src")

datas = [
    # The only frontend asset tray_app.py itself touches (FAVICON_PATH) —
    # not the whole frontend/ tree, that's the server binary's job.
    (os.path.join(SRC, "frontend", "images", "favicon.png"), os.path.join("frontend", "images")),
]

hiddenimports = [
    "pystray",
    "PIL",
]

a = Analysis(
    [os.path.join(SRC, "tray", "tray_app.py")],
    pathex=[SRC, REPO_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["gi"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="digib00age-tray",
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
    name="digib00age-tray",
)
