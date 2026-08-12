#!/bin/bash
# Assembles a small, self-contained Linux release zip for end users - no
# repo, no build toolchain needed to install from it. Freezes both binaries
# (dev-only, needs the full repo + preflight-build.sh's toolchain), then
# copies the frozen output plus a lightweight installer and its runtime-only
# preflight check (release-template/) into a flat folder and zips it. This
# is the artifact to distribute; end users never see this script or the
# surrounding repo - see DECISIONS.md for why install.sh (freeze-on-the-
# user's-machine) isn't the distributed path anymore.
#
# Run from anywhere; paths are resolved relative to this script's location.
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"       # packaging/linux/
REPO_ROOT="$(cd "$PKG_DIR/../.." && pwd)"

PKG_NAME="digib00age"
ZIP_NAME="digib00age-linux-install.zip"

BUILD_ROOT="$REPO_ROOT/dev/distros/release-build"
PYI_DIST="$BUILD_ROOT/pyinstaller-out/dist"
PYI_WORK="$BUILD_ROOT/pyinstaller-out/build"
RELEASE_DIR="$BUILD_ROOT/$PKG_NAME"
OUT_ZIP="$REPO_ROOT/dev/distros/$ZIP_NAME"

echo "=== Checking build prerequisites ==="
source "$PKG_DIR/preflight-build.sh"

echo "=== 1/3: Freeze both binaries ==="
source "$PKG_DIR/freeze.sh"

echo "=== 2/3: Assemble release folder ==="
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

# Merge (not nest) both --onedir outputs into one flat dir - same pattern
# build.sh already uses. _frozen_server_executable_path() (tray_app.py)
# expects both executables as flat siblings, not in separate subfolders.
cp -a "$PYI_DIST/digib00age-server/." "$RELEASE_DIR/"
cp -a "$PYI_DIST/digib00age-tray/." "$RELEASE_DIR/"
chmod +x "$RELEASE_DIR/digib00age-server" "$RELEASE_DIR/digib00age-tray"

cp "$PKG_DIR/digib00age.desktop" "$RELEASE_DIR/"
cp "$REPO_ROOT/src/frontend/images/favicon.png" "$RELEASE_DIR/"
cp "$PKG_DIR/release-template/install.sh" "$RELEASE_DIR/"
cp "$PKG_DIR/release-template/preflight-runtime.sh" "$RELEASE_DIR/"
cp "$PKG_DIR/release-template/README.txt" "$RELEASE_DIR/"
chmod +x "$RELEASE_DIR/install.sh"

echo "=== 3/3: Zip release ==="
rm -f "$OUT_ZIP"
(cd "$BUILD_ROOT" && zip -rq "$OUT_ZIP" "$PKG_NAME")

echo
echo "Built: $OUT_ZIP"
echo "Unzip it anywhere and run ./$PKG_NAME/install.sh - no repo or build toolchain needed on the target machine."
