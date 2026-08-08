# Shared PyInstaller freeze step for both the .deb (build.sh) and the shell
# installer (install.sh). Sourced, not executed directly - expects PKG_DIR,
# REPO_ROOT, BUILD_ROOT, PYI_DIST, PYI_WORK already set by the caller.
#
# Build venv uses --system-site-packages + PYTHONNOUSERSITE=1 - NOT a fully
# isolated venv, and NOT include-system-site-packages=true on its own.
# Both matter:
#
# - PyInstaller's static analysis needs `gi` (PyGObject) importable at
#   freeze time to bundle pystray's AppIndicator backend at all - without
#   it, the frozen tray silently falls back to the menu-less X11 backend
#   (BUG-040's original symptom: icon renders, every click is a no-op).
#   `gi` lives in the system's dist-packages (apt: python3-gi), which
#   --system-site-packages exposes.
# - But a plain --system-site-packages venv (equivalently,
#   include-system-site-packages=true in pyvenv.cfg, the actual BUG-040 fix
#   applied to the dev venv) also enables Python's user site-packages
#   (~/.local/lib/pythonX/site-packages) - and on this laptop that happens
#   to hold an unrelated ML project's install (torch/nvidia/scipy/pandas/
#   psycopg2/asyncpg). PyInstaller's static analysis follows real
#   dependencies' optional/guarded import branches (scipy's optional torch
#   backend, sqlalchemy's psycopg2/asyncpg dialect hook) straight into that
#   pollution, bundling gigabytes of it in (this is BUG-041 - blew the .deb
#   up to 2.4GB). PYTHONNOUSERSITE=1 disables the user-site directory
#   specifically, independent of --system-site-packages, so torch et al.
#   stay invisible while `gi` (system, not user, site-packages) stays
#   visible. Confirmed empirically before wiring this in: a
#   --system-site-packages venv with PYTHONNOUSERSITE=1 set imports `gi`
#   fine and raises ModuleNotFoundError for `torch`, with no ~/.local path
#   in sys.path at all.
export PYTHONNOUSERSITE=1

# PyInstaller's pystray hook (collect_submodules) actually imports pystray
# during analysis to see which backend it picks - and pystray's own
# import-time backend probe needs a live X DISPLAY to succeed at all
# (otherwise it raises Xlib.error.DisplayNameError and the hook silently
# gives up, which can leave the wrong/no backend bundled). A normal
# interactive terminal on minty's desktop already has DISPLAY set; this
# only matters when freezing headlessly (e.g. over SSH) with none set.
# Confirmed: with DISPLAY=:0 (this laptop's real session), pystray imports
# successfully and resolves to pystray._appindicator, the correct backend.
export DISPLAY="${DISPLAY:-:0}"

BUILD_VENV="$BUILD_ROOT/build-venv"
echo "--- Prepare build venv (system site-packages for gi, user site-packages disabled) ---"
rm -rf "$BUILD_VENV"
python3 -m venv --system-site-packages "$BUILD_VENV"
"$BUILD_VENV/bin/pip" install --no-cache-dir --upgrade pip >/dev/null
"$BUILD_VENV/bin/pip" install --no-cache-dir -r "$REPO_ROOT/requirements.txt" pyinstaller
VENV_PYINSTALLER="$BUILD_VENV/bin/pyinstaller"

echo "--- PyInstaller freeze (server) ---"
"$VENV_PYINSTALLER" --noconfirm --distpath "$PYI_DIST" --workpath "$PYI_WORK" \
    "$PKG_DIR/digib00age-server.spec"

echo "--- PyInstaller freeze (tray) ---"
"$VENV_PYINSTALLER" --noconfirm --distpath "$PYI_DIST" --workpath "$PYI_WORK" \
    "$PKG_DIR/digib00age-tray.spec"
