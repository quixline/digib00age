#!/bin/bash
# Dev-machine convenience: builds the sdist from this full checkout, stages
# it into a flat temp folder alongside the same files a real release zip
# ships (release-template/install.sh expects digib00age.desktop/favicon.png
# sitting next to it - true inside an assembled release, not inside this
# repo's own directory layout), then runs that folder's install.sh. Not the
# distributed path itself - see make_release.sh for the small zip end users
# download without a repo.
#
# Run from anywhere; paths are resolved relative to this script's location.
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"       # packaging/linux/
REPO_ROOT="$(cd "$PKG_DIR/../.." && pwd)"

echo "=== Build sdist ==="
cd "$REPO_ROOT"
rm -rf dist
python3 -m build --sdist

SDIST="$(ls "$REPO_ROOT"/dist/digib00age-*.tar.gz | head -n1)"
echo "Built: $SDIST"

echo "=== Stage install folder ==="
STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGE_DIR"' EXIT
cp "$SDIST" "$STAGE_DIR/"
cp "$PKG_DIR/digib00age.desktop" "$STAGE_DIR/"
cp "$REPO_ROOT/src/frontend/images/favicon.png" "$STAGE_DIR/"
cp "$PKG_DIR/release-template/install.sh" "$STAGE_DIR/"
cp "$PKG_DIR/release-template/preflight-runtime.sh" "$STAGE_DIR/"
chmod +x "$STAGE_DIR/install.sh"

echo
exec "$STAGE_DIR/install.sh"
