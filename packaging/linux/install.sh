#!/bin/bash
# Self-contained Linux installer for digib00age: freezes both binaries, then
# prompts for an install directory (any writable path/drive) instead of
# dpkg's hardcoded /opt/digib00age. Default distribution mechanism for Linux
# going forward - see DECISIONS.md "Installer: user-selectable install
# directory" for why plain dpkg can't do this (a .deb's file paths are fixed
# at build time; there's no MSI-style directory-picker dialog for dpkg).
# build.sh (the .deb path) is kept as a secondary/reference option, not
# deleted - both share this repo's freeze.sh step.
#
# Unlike a .deb, apt won't auto-install this app's system dependencies
# (python3, python3-venv, python3-gi, GTK, AppIndicator) - preflight-build.sh
# checks for all of them up front, before anything else runs, and exits
# with an `apt install` instruction if anything is missing. Installing them
# is left to the user (sudo, run by hand) - see preflight-build.sh.
#
# This script builds+installs directly from a full checkout - a dev-machine
# convenience, not the distributed path. For a small zip end users can
# download without the repo or a build toolchain, see make_release.sh.
#
# Run from anywhere; paths are resolved relative to this script's location.
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"       # packaging/linux/
REPO_ROOT="$(cd "$PKG_DIR/../.." && pwd)"

PKG_NAME="digib00age"

BUILD_ROOT="$REPO_ROOT/dev/distros/install-build"
PYI_DIST="$BUILD_ROOT/pyinstaller-out/dist"
PYI_WORK="$BUILD_ROOT/pyinstaller-out/build"

echo "=== Checking prerequisites ==="
source "$PKG_DIR/preflight-build.sh"

echo "=== 1/3: Freeze both binaries ==="
source "$PKG_DIR/freeze.sh"

echo "=== 2/3: Choose install directory ==="
# Default lives under ~/.local/opt/ (per-user mirror of the system /opt/
# convention), deliberately NOT ~/.local/share/digib00age - that's the app's
# own XDG *data* directory (config.py's _xdg_data_dir(): db + thumbnails),
# and uninstall.sh below does an rm -rf on whatever directory is chosen here.
# Installing the binaries into the data directory would make an uninstall
# wipe the user's comic-library database and thumbnails along with the app.
DEFAULT_DIR="$HOME/.local/opt/$PKG_NAME"
XDG_DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/$PKG_NAME"

read -r -p "Install directory [$DEFAULT_DIR]: " TARGET_DIR
TARGET_DIR="${TARGET_DIR:-$DEFAULT_DIR}"
TARGET_DIR="$(python3 -c "import os,sys; print(os.path.abspath(os.path.expanduser(sys.argv[1])))" "$TARGET_DIR")"

if [ "$TARGET_DIR" = "$(python3 -c "import os,sys; print(os.path.abspath(sys.argv[1]))" "$XDG_DATA_DIR")" ]; then
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

echo "=== 3/3: Install files ==="
cp -a "$PYI_DIST/digib00age-server/." "$TARGET_DIR/"
cp -a "$PYI_DIST/digib00age-tray/." "$TARGET_DIR/"
chmod +x "$TARGET_DIR/digib00age-server" "$TARGET_DIR/digib00age-tray"

mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/128x128/apps"
sed "s|^Exec=.*|Exec=$TARGET_DIR/digib00age-tray|" "$PKG_DIR/digib00age.desktop" \
    > "$HOME/.local/share/applications/digib00age.desktop"
cp "$REPO_ROOT/src/frontend/images/favicon.png" \
    "$HOME/.local/share/icons/hicolor/128x128/apps/digib00age.png"

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
echo "Launch: $TARGET_DIR/digib00age-tray  (or from your applications menu)"
echo "Uninstall: $TARGET_DIR/uninstall.sh"
