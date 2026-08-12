#!/bin/bash
# digib00age installer. Self-contained - run this from inside the unzipped
# release folder. No repo, no build toolchain, no Python needed - the two
# binaries alongside this script are already fully built; this script only
# copies files into place and sets up a menu launcher.
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_NAME="digib00age"

echo "=== Checking prerequisites ==="
source "$PKG_DIR/preflight-runtime.sh"

echo "=== Choose install directory ==="
# Default lives under ~/.local/opt/ (per-user mirror of the system /opt/
# convention), deliberately NOT ~/.local/share/digib00age - that's the app's
# own XDG *data* directory (db + thumbnails), and uninstall.sh below does an
# rm -rf on whatever directory is chosen here. Installing the binaries into
# the data directory would make an uninstall wipe the user's comic-library
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

echo "=== Install files ==="
cp -a "$PKG_DIR/digib00age-server" "$PKG_DIR/digib00age-tray" "$PKG_DIR/_internal" "$TARGET_DIR/"
chmod +x "$TARGET_DIR/digib00age-server" "$TARGET_DIR/digib00age-tray"

mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/128x128/apps"
sed "s|^Exec=.*|Exec=$TARGET_DIR/digib00age-tray|" "$PKG_DIR/digib00age.desktop" \
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
echo "Launch: $TARGET_DIR/digib00age-tray  (or from your applications menu)"
echo "Uninstall: $TARGET_DIR/uninstall.sh"
