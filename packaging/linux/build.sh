#!/bin/bash
# Build the digib00age .deb: PyInstaller-freeze both binaries, assemble the
# Debian package tree, build with dpkg-deb. Safe to re-run — each step wipes
# its own prior output first.
#
# This is the apt-managed path (fixed /opt/digib00age install, automatic
# Depends: resolution). For a user-chosen install directory instead, use
# install.sh, which shares this script's freeze.sh step but skips dpkg
# entirely.
#
# Run from anywhere; paths are resolved relative to this script's location.
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"       # packaging/linux/
REPO_ROOT="$(cd "$PKG_DIR/../.." && pwd)"

VERSION="1.0.0"
PKG_NAME="digib00age"
ARCH="amd64"

BUILD_ROOT="$REPO_ROOT/dev/distros/deb-build"
PYI_DIST="$BUILD_ROOT/pyinstaller-out/dist"
PYI_WORK="$BUILD_ROOT/pyinstaller-out/build"
DEB_TREE="$BUILD_ROOT/${PKG_NAME}_${VERSION}_${ARCH}"
OUT_DEB="$REPO_ROOT/dev/distros/${PKG_NAME}_${VERSION}_${ARCH}.deb"

echo "=== 1/3: Freeze both binaries ==="
source "$PKG_DIR/freeze.sh"

echo "=== 2/3: Assemble Debian package tree ==="
rm -rf "$DEB_TREE"
mkdir -p "$DEB_TREE/DEBIAN"
mkdir -p "$DEB_TREE/opt/$PKG_NAME"
mkdir -p "$DEB_TREE/usr/share/applications"
mkdir -p "$DEB_TREE/usr/share/icons/hicolor/128x128/apps"

# Merge (not nest) both --onedir outputs into one flat /opt/digib00age/ dir —
# _frozen_server_executable_path() (tray_app.py, shared with the future
# Windows build) expects the two executables as flat siblings in the same
# directory, not in separate subfolders. The trailing "/." makes cp merge
# each bundle's contents (including its own _internal/) into the shared
# destination rather than nesting a subdirectory; both bundles come from the
# same venv so overlapping _internal/ files are compatible duplicates.
cp -a "$PYI_DIST/digib00age-server/." "$DEB_TREE/opt/$PKG_NAME/"
cp -a "$PYI_DIST/digib00age-tray/." "$DEB_TREE/opt/$PKG_NAME/"
chmod +x "$DEB_TREE/opt/$PKG_NAME/digib00age-server"
chmod +x "$DEB_TREE/opt/$PKG_NAME/digib00age-tray"

cp "$PKG_DIR/digib00age.desktop" "$DEB_TREE/usr/share/applications/"
cp "$REPO_ROOT/src/frontend/images/favicon.png" \
    "$DEB_TREE/usr/share/icons/hicolor/128x128/apps/digib00age.png"

cp "$PKG_DIR/debian/control" "$DEB_TREE/DEBIAN/control"
cp "$PKG_DIR/debian/postinst" "$DEB_TREE/DEBIAN/postinst"
cp "$PKG_DIR/debian/postrm" "$DEB_TREE/DEBIAN/postrm"
chmod 755 "$DEB_TREE/DEBIAN/postinst" "$DEB_TREE/DEBIAN/postrm"

echo "=== 3/3: dpkg-deb build ==="
rm -f "$OUT_DEB"
# fakeroot/dpkg-deb use $TMPDIR (defaults to /tmp) for intermediate files —
# on a host where / is tight on space (as this one has been), that fails
# with ENOSPC even though the real output path below is on a roomy
# partition. Point TMPDIR at scratch space next to the rest of this build's
# output instead.
TMP_SCRATCH="$BUILD_ROOT/tmp"
mkdir -p "$TMP_SCRATCH"
TMPDIR="$TMP_SCRATCH" fakeroot dpkg-deb --build --root-owner-group "$DEB_TREE" "$OUT_DEB"
rm -rf "$TMP_SCRATCH"

echo
echo "Built: $OUT_DEB"
