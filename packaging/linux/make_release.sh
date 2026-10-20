#!/bin/bash
# Assembles a small, self-contained Linux release zip for end users - no
# repo, no build toolchain needed to install from it. Builds the sdist (the
# app's source, no compiled binaries - see DECISIONS.md "Linux packaging:
# PyInstaller -> sdist"), then copies it plus a lightweight installer and its
# runtime preflight check (release-template/) into a flat folder and zips
# it. This is the artifact to distribute; end users never see this script or
# the surrounding repo.
#
# Run from anywhere; paths are resolved relative to this script's location.
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"       # packaging/linux/
REPO_ROOT="$(cd "$PKG_DIR/../.." && pwd)"

PKG_NAME="digib00age"
ZIP_NAME="digib00age-linux-install.zip"

BUILD_ROOT="$REPO_ROOT/dev/distros/release-build"
RELEASE_DIR="$BUILD_ROOT/$PKG_NAME"
OUT_ZIP="$REPO_ROOT/dev/distros/$ZIP_NAME"

echo "=== 1/3: Build sdist ==="
cd "$REPO_ROOT"
rm -rf dist
python3 -m build --sdist
SDIST="$(ls "$REPO_ROOT"/dist/digib00age-*.tar.gz | head -n1)"
echo "Built: $SDIST"

echo "=== 2/3: Assemble release folder ==="
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

cp "$SDIST" "$RELEASE_DIR/"
cp "$PKG_DIR/digib00age.desktop" "$RELEASE_DIR/"
cp "$REPO_ROOT/src/frontend/images/icons/icon-512.png" "$RELEASE_DIR/favicon.png"
cp "$PKG_DIR/release-template/install.sh" "$RELEASE_DIR/"
cp "$PKG_DIR/release-template/preflight-runtime.sh" "$RELEASE_DIR/"
cp "$PKG_DIR/release-template/README.txt" "$RELEASE_DIR/"
chmod +x "$RELEASE_DIR/install.sh"

echo "=== 3/3: Zip release ==="
rm -f "$OUT_ZIP"
(cd "$BUILD_ROOT" && zip -rq "$OUT_ZIP" "$PKG_NAME")

echo
echo "Built: $OUT_ZIP"
echo "Unzip it anywhere and run ./$PKG_NAME/install.sh - no repo needed on the target machine."
