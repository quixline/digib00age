#!/bin/bash
cd "$(dirname "$0")"
PYTHON="venv/bin/python3"
if [ ! -x "$PYTHON" ]; then
    echo "error: $PYTHON not found. Create the venv first:" >&2
    echo "  python3 -m venv venv --system-site-packages" >&2
    echo "  venv/bin/pip install -r requirements.txt" >&2
    echo "See README.md 'Linux hosts, tray app' for required apt packages." >&2
    exit 1
fi
mkdir -p dev/logs
nohup "$PYTHON" src/tray/tray_app.py >> dev/logs/start.log 2>&1 &
disown
