"""
start_server.py — Start the digib00age reader server.

Run from the project root:
    python start_server.py

Checks config and paths, initialises the database, then launches the
FastAPI server on the port set in config.json (default: 9424).
The process stays alive — Ctrl+C to stop.
"""

import os
import sys

# Make backend importable as a package — it lives under src/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from backend.config import (
    READER_PORT,
    DB_PATH, LIBRARY_ROOT, THUMBNAIL_DIR, THUMBNAIL_SIZE,
    is_library_configured,
)
from backend.database import init_db


def _sep(title=""):
    width = 60
    if title:
        print(f"\n{'=' * 4} {title} {'=' * max(1, width - len(title) - 6)}")
    else:
        print("=" * width)


def main():
    _sep("digib00age")

    _sep("Config")
    print(f"  library_root   : {LIBRARY_ROOT}")
    print(f"  db_path        : {DB_PATH}")
    print(f"  thumbnail_dir  : {THUMBNAIL_DIR}")
    print(f"  thumbnail_size : {THUMBNAIL_SIZE}px wide")
    print(f"  reader_port    : {READER_PORT}")

    # Verify library root — not fatal; the app boots regardless and the
    # library can be configured from /admin (Library Folders) afterward.
    if not is_library_configured():
        print(f"\n  [!] Library location not configured yet.")
        print(f"     Go to http://localhost:{READER_PORT}/admin to set it.")
    else:
        print("\n  [OK] library_root found")

    # Verify / create thumbnail dir
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    print("  [OK] thumbnail_dir ready")

    # Initialise DB (creates tables if they don't exist yet)
    _sep("Database")
    init_db()
    print(f"  [OK] Database ready at {DB_PATH}")

    # Launch server
    _sep("Server")
    print(f"  Starting on http://0.0.0.0:{READER_PORT}")
    print(f"  Library UI  ->  http://localhost:{READER_PORT}/")
    print(f"  API docs    ->  http://localhost:{READER_PORT}/docs")
    print("  Press Ctrl+C to stop.\n")

    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=READER_PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
