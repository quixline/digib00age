#!/bin/bash
# digib00age installer. Self-contained - run this from inside the unzipped
# release folder. No repo needed - the sdist tarball alongside this script
# is the whole app; this script creates a venv, `pip install`s it (compiling
# any C extensions against *this* machine's Python - see DECISIONS.md
# "Linux packaging: PyInstaller -> sdist"), and sets up a menu launcher.
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_NAME="digib00age"

SDIST="${1:-$(ls "$PKG_DIR"/digib00age-*.tar.gz 2>/dev/null | head -n1)}"
if [ -z "$SDIST" ] || [ ! -f "$SDIST" ]; then
    echo "Error: couldn't find a digib00age-*.tar.gz sdist next to this script." >&2
    echo "Pass its path explicitly: ./install.sh /path/to/digib00age-<version>.tar.gz" >&2
    exit 1
fi

echo "=== Checking prerequisites ==="
source "$PKG_DIR/preflight-runtime.sh"

echo "=== Choose install directory ==="
# Default lives under ~/.local/opt/ (per-user mirror of the system /opt/
# convention), deliberately NOT ~/.local/share/digib00age - that's the app's
# own XDG *data* directory (db + thumbnails), and uninstall.sh below does an
# rm -rf on whatever directory is chosen here. Installing the venv into the
# data directory would make an uninstall wipe the user's comic-library
# database and thumbnails along with the app.
DEFAULT_DIR="$HOME/.local/opt/$PKG_NAME"
XDG_DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/$PKG_NAME"

read -r -p "Install directory [$DEFAULT_DIR]: " TARGET_DIR
TARGET_DIR="${TARGET_DIR:-$DEFAULT_DIR}"
TARGET_DIR="${TARGET_DIR/#\~/$HOME}"
# readlink -f canonicalizes without requiring the path to exist yet (unlike
# `cd && pwd`) - matches the abspath+expanduser behaviour the old
# freeze-on-install.sh used python3 for; no Python needed here at all.
TARGET_DIR="$(readlink -f -- "$TARGET_DIR")"

if [ "$TARGET_DIR" = "$(readlink -f -- "$XDG_DATA_DIR")" ]; then
    echo "Error: $TARGET_DIR is digib00age's own data directory (database/thumbnails)." >&2
    echo "Installing the app there would make uninstalling it delete your library data. Choose a different directory." >&2
    exit 1
fi

if [ -d "$TARGET_DIR" ] && [ -n "$(ls -A "$TARGET_DIR" 2>/dev/null)" ]; then
    read -r -p "$TARGET_DIR already exists and isn't empty. Overwrite its contents? [y/N] " CONFIRM
    case "$CONFIRM" in
        [yY]*) ;;
        *) echo "Aborted."; exit 1 ;;
    esac
fi
mkdir -p "$TARGET_DIR"
if [ ! -w "$TARGET_DIR" ]; then
    echo "Error: $TARGET_DIR is not writable. Re-run with sudo, or choose a directory you own." >&2
    exit 1
fi

echo "=== Create venv + install ==="
rm -rf "$TARGET_DIR/venv"
# --system-site-packages: pystray's AppIndicator/GTK backend imports the
# system's apt-installed python3-gi (PyGObject) at runtime - it is never
# pip-installed (pystray's "appindicator" extra is a no-op; pip warns
# "does not provide the extra" and installs nothing GTK-related). Without
# this flag the venv can't see it at all. Same choice the old PyInstaller
# build venv made for the same reason (see DECISIONS.md "Linux .deb release").
python3 -m venv --system-site-packages "$TARGET_DIR/venv"
"$TARGET_DIR/venv/bin/pip" install --upgrade pip wheel >/dev/null
"$TARGET_DIR/venv/bin/pip" install "$SDIST"

mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/128x128/apps"
sed "s|^Exec=.*|Exec=$TARGET_DIR/venv/bin/digib00age-tray|" "$PKG_DIR/digib00age.desktop" \
    > "$HOME/.local/share/applications/digib00age.desktop"
cp "$PKG_DIR/favicon.png" "$HOME/.local/share/icons/hicolor/128x128/apps/digib00age.png"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

cat > "$TARGET_DIR/uninstall.sh" <<UNINSTALL
#!/bin/bash
set -e
rm -f "$HOME/.local/share/applications/digib00age.desktop"
rm -f "$HOME/.local/share/icons/hicolor/128x128/apps/digib00age.png"
rm -rf "$TARGET_DIR"
echo "digib00age uninstalled. Your data (~/.local/share/digib00age, ~/.config/digib00age) was left untouched - remove it by hand for a full wipe."
UNINSTALL
chmod +x "$TARGET_DIR/uninstall.sh"

echo
echo "Installed to: $TARGET_DIR"
echo "Launch: $TARGET_DIR/venv/bin/digib00age-tray  (or from your applications menu)"
echo "Uninstall: $TARGET_DIR/uninstall.sh"
