#!/usr/bin/env bash
# digib00age - one-line install (Linux, Docker Engine + compose plugin already
# installed). No git, no source checkout, no build - pulls the pre-built public
# image from GitHub Container Registry and starts it.
#
#   curl -fsSL https://github.com/quixline/digib00age/releases/download/v1-beta/setup.sh -o setup.sh && less setup.sh && bash setup.sh
#
# (Fetch and read it before running it, same as any curl-piped installer.)
#
# See packaging/docker/README.txt for the full walkthrough, including the
# windy-only build/publish path this pulls from (publish.ps1). GHCR is real
# TLS - no insecure-registry trust step needed, unlike the old quixy-registry
# rehearsal this replaced.
set -euo pipefail

RELEASE_TAG="v1-beta"
COMPOSE_URL="https://github.com/quixline/digib00age/releases/download/${RELEASE_TAG}/docker-compose.yml"
INSTALL_DIR="${1:-./digib00age}"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker not found on PATH - install Docker Engine first, then re-run this script." >&2
    exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
    echo "docker compose (v2 plugin) not found - install it, then re-run this script." >&2
    exit 1
fi

echo "Setting up $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR/config" "$INSTALL_DIR/data"
curl -fsSL "$COMPOSE_URL" -o "$INSTALL_DIR/docker-compose.yml"

cd "$INSTALL_DIR"
echo "Pulling image ..."
docker compose pull
echo "Starting digib00age ..."
docker compose up -d

HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo ""
echo "digib00age is starting - open http://${HOST_IP:-<this-host>}:9800 once the container is up (docker compose logs -f to watch)."
