# Build-time-only pre-flight dependency check (BUG-044). Sourced by
# make_release.sh, install.sh, and build.sh - the dev/build-machine scripts
# that freeze the app from source. NOT used by the end-user release
# installer (packaging/linux/release-template/install.sh) - that one ships
# inside the release zip and only needs the three real runtime deps (see
# release-template/preflight-runtime.sh), never python3/venv/build-time gi.
#
# Matches freeze.sh's sourced convention, inherits the caller's
# `set -euo pipefail`. Debian/Ubuntu only (uses dpkg).
#
# Run this BEFORE any freeze/venv/directory/file work, and fail fast with
# every missing prerequisite collected into one message - not one at a time.

_preflight_missing=""

if ! command -v python3 >/dev/null 2>&1; then
    _preflight_missing="$_preflight_missing python3"
else
    # ensurepip is what `python3 -m venv` actually needs at runtime -
    # Debian/Ubuntu split it out of the base python3 package into
    # python3-venv. Testing the real capability (rather than guessing a
    # package name, which varies by Python minor version - e.g.
    # python3.12-venv) is more robust across releases.
    if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
        _preflight_missing="$_preflight_missing python3-venv"
    fi
fi

# python3-gi/gtk/appindicator are needed at FREEZE time too, not just
# runtime - PyInstaller's static analysis needs `gi` importable to bundle
# pystray's AppIndicator backend (see freeze.sh). Missing it doesn't error
# the freeze, it silently produces a menu-less tray (BUG-040).
for dep in python3-gi gir1.2-gtk-3.0; do
    dpkg -s "$dep" >/dev/null 2>&1 || _preflight_missing="$_preflight_missing $dep"
done
if ! dpkg -s libayatana-appindicator3-1 >/dev/null 2>&1 && ! dpkg -s libappindicator3-1 >/dev/null 2>&1; then
    _preflight_missing="$_preflight_missing libayatana-appindicator3-1"
fi

if [ -n "$_preflight_missing" ]; then
    echo "digib00age (build): missing required packages:$_preflight_missing" >&2
    echo "Install with: sudo apt install$_preflight_missing" >&2
    echo "Then re-run this script." >&2
    exit 1
fi

unset _preflight_missing
