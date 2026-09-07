#!/usr/bin/env bash
# digib00age - one-line install (Linux, Docker Engine + compose plugin already
# installed). No git, no source checkout, no build - pulls a pre-built image from
# the self-hosted registry on quixy and starts it.
#
#   curl -fsSL http://digib00age.tech/setup.sh -o setup.sh && less setup.sh && bash setup.sh
#
# (Fetch and read it before running it, same as any curl-piped installer.)
#
# See packaging/docker/README.txt for the full walkthrough, including the
# windy-only build/publish path this pulls from (publish.ps1).
set -euo pipefail

REGISTRY_HOST="digib00age.tech:5000"
INSTALL_SITE="http://digib00age.tech"
INSTALL_DIR="${1:-./digib00age}"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker not found on PATH - install Docker Engine first, then re-run this script." >&2
    exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
    echo "docker compose (v2 plugin) not found - install it, then re-run this script." >&2
    exit 1
fi

# One-time: trust the LAN-only, plain-HTTP registry. Docker refuses to pull from a
# non-HTTPS registry unless it's explicitly allow-listed.
DAEMON_JSON="/etc/docker/daemon.json"
if ! sudo test -f "$DAEMON_JSON" || ! sudo grep -q "$REGISTRY_HOST" "$DAEMON_JSON" 2>/dev/null; then
    echo "Adding $REGISTRY_HOST to $DAEMON_JSON's insecure-registries ..."
    sudo mkdir -p "$(dirname "$DAEMON_JSON")"
    sudo python3 - "$DAEMON_JSON" "$REGISTRY_HOST" <<'PYEOF'
import json, sys

path, host = sys.argv[1], sys.argv[2]
try:
    with open(path) as f:
        cfg = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    cfg = {}

regs = cfg.get("insecure-registries", [])
if host not in regs:
    regs.append(host)
cfg["insecure-registries"] = regs

with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
PYEOF
    echo "Restarting docker service ..."
    sudo systemctl restart docker
fi

echo "Setting up $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR/config" "$INSTALL_DIR/data"
curl -fsSL "$INSTALL_SITE/docker-compose.yml" -o "$INSTALL_DIR/docker-compose.yml"

cd "$INSTALL_DIR"
echo "Pulling image ..."
docker compose pull
echo "Starting digib00age ..."
docker compose up -d

HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo ""
echo "digib00age is starting - open http://${HOST_IP:-<this-host>}:9800 once the container is up (docker compose logs -f to watch)."
