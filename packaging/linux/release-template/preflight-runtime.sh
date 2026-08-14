# Runtime pre-flight dependency check for the packaged Linux release
# (the sdist + install.sh in this folder). Sourced by this folder's
# install.sh before it creates a venv and runs `pip install` - unlike the
# old PyInstaller-frozen release, `pip install` now runs on the end user's
# own machine (see DECISIONS.md "Linux packaging: PyInstaller -> sdist"),
# so it needs python3/venv present, and (confirmed empirically building this
# release - most target Python versions have prebuilt PyPI wheels for
# pymupdf/lxml, but not guaranteed for every version) a compiler + Python
# dev headers as a fallback in case a wheel isn't available for this
# specific Python. pystray's AppIndicator backend (PyGObject/gi) is *not*
# pip-installed at all - confirmed empirically pip warns "pystray does not
# provide the extra 'appindicator'" and installs nothing for it; it's always
# the system's apt-installed python3-gi, reached via install.sh's
# --system-site-packages venv - so no PyGObject build toolchain (pkg-config/
# girepository/cairo dev headers) is needed here, only the GTK/AppIndicator
# runtime libs below.

_preflight_missing=""

# python3 / python3-venv - install.sh creates a venv to install into.
if ! command -v python3 >/dev/null 2>&1; then
    _preflight_missing="$_preflight_missing python3"
elif ! python3 -c "import ensurepip" >/dev/null 2>&1; then
    _preflight_missing="$_preflight_missing python3-venv"
fi

# git - comictagger is pinned to a specific commit via a git+https:// direct
# reference (requirements.txt: PyPI's published release predates a
# comictalker plugin split this integration needs), not a PyPI release. Any
# `pip install` of a git+... reference shells out to a real `git` binary to
# clone it - there's no pure-pip fallback - so this is a genuine, unavoidable
# prerequisite, not optional.
if ! command -v git >/dev/null 2>&1; then
    _preflight_missing="$_preflight_missing git"
fi

# C compiler + Python dev headers - fallback for whenever pymupdf/lxml don't
# have a prebuilt wheel for this machine's exact Python version/arch and
# pip has to compile from source.
if ! command -v gcc >/dev/null 2>&1 && ! command -v cc >/dev/null 2>&1; then
    _preflight_missing="$_preflight_missing build-essential"
fi
if command -v python3 >/dev/null 2>&1 && ! python3 -c "
import sysconfig, os
inc = sysconfig.get_path('include')
assert inc and os.path.isfile(os.path.join(inc, 'Python.h'))
" >/dev/null 2>&1; then
    _preflight_missing="$_preflight_missing python3-dev"
fi

# GTK / AppIndicator runtime libs - unchanged from the frozen-binary era,
# still needed at pystray's backend-selection time regardless of how the
# app got onto disk. Reached via install.sh's --system-site-packages venv,
# not pip-installed.
for dep in python3-gi gir1.2-gtk-3.0; do
    dpkg -s "$dep" >/dev/null 2>&1 || _preflight_missing="$_preflight_missing $dep"
done
if dpkg -s libayatana-appindicator3-1 >/dev/null 2>&1; then
    _appindicator_typelib="gir1.2-ayatanaappindicator3-0.1"
elif dpkg -s libappindicator3-1 >/dev/null 2>&1; then
    _appindicator_typelib="gir1.2-appindicator3-0.1"
else
    _preflight_missing="$_preflight_missing libayatana-appindicator3-1"
    _appindicator_typelib="gir1.2-ayatanaappindicator3-0.1"
fi
# The typelib is a *separate* package from the .so above - confirmed
# empirically on a real target machine that having the shared library alone
# still fails inside pystray's own backend selection with
# `gi.require_version('AyatanaAppIndicator3', '0.1')` -> "Namespace ... not
# available", since GObject-Introspection needs the typelib file to resolve
# the namespace regardless of the .so being present.
dpkg -s "$_appindicator_typelib" >/dev/null 2>&1 || _preflight_missing="$_preflight_missing $_appindicator_typelib"
unset _appindicator_typelib

# python3-icu - comictagger requires pyicu, a C++ extension wrapping the
# ICU library with no portable prebuilt PyPI wheel. Building it from source
# needs pkg-config + libicu-dev *and* has to match the system's exact
# installed ICU version (fragile) - same shape of problem as PyGObject, and
# the same fix: use the system's apt-installed python3-icu (pre-built,
# version-matched to the system's libicu automatically), reached via
# install.sh's --system-site-packages venv rather than compiled by pip.
if ! dpkg -s python3-icu >/dev/null 2>&1; then
    _preflight_missing="$_preflight_missing python3-icu"
fi

if [ -n "$_preflight_missing" ]; then
    echo "digib00age: missing required packages:$_preflight_missing" >&2
    echo "Install with: sudo apt install$_preflight_missing" >&2
    echo "Then re-run this script." >&2
    exit 1
fi

unset _preflight_missing
