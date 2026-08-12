# Runtime-only pre-flight dependency check for the packaged Linux release
# (digib00age-linux-install.zip). Sourced by this folder's install.sh -
# ships inside the release zip, alongside the already-frozen binaries.
#
# Deliberately much smaller than packaging/linux/preflight-build.sh: the
# frozen binary bundles its own Python interpreter, so nothing Python-level
# (python3, python3-venv) is needed here at all - only the system GTK/
# AppIndicator libraries the frozen tray links against at launch. Confirmed
# against packaging/linux/debian/control's Depends: line, which lists these
# same three as the .deb's real runtime dependencies (and does NOT list
# python3 or python3-venv - those are build-time only).

_preflight_missing=""

for dep in python3-gi gir1.2-gtk-3.0; do
    dpkg -s "$dep" >/dev/null 2>&1 || _preflight_missing="$_preflight_missing $dep"
done
if ! dpkg -s libayatana-appindicator3-1 >/dev/null 2>&1 && ! dpkg -s libappindicator3-1 >/dev/null 2>&1; then
    _preflight_missing="$_preflight_missing libayatana-appindicator3-1"
fi

if [ -n "$_preflight_missing" ]; then
    echo "digib00age: missing required packages:$_preflight_missing" >&2
    echo "Install with: sudo apt install$_preflight_missing" >&2
    echo "Then re-run this script." >&2
    exit 1
fi

unset _preflight_missing
