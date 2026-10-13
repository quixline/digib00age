"""
backend.cli — digib00age-server entry point (pyproject.toml [project.scripts]).

Checks config and paths, initialises the database, then launches the
FastAPI server on the port set in config.json (default: 9800).
The process stays alive — Ctrl+C to stop.

Also runnable via the dev-convenience `start_server.py` at the repo root.
"""

import argparse
import os

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


def _stamp_head() -> None:
    """One-time upgrade step for an install that already has the full
    current schema from years of the old ad hoc migration functions (e.g.
    quixy's live DB) — tells Alembic "already at baseline" without running
    0001_baseline's DDL. See DECISIONS.md "Adopted Alembic for schema
    migrations". Back up the DB before running this."""
    from alembic.command import stamp
    from alembic.config import Config

    from backend.config import BACKEND_DIR

    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{DB_PATH}")
    stamp(cfg, "head")
    print(f"  [OK] Stamped {DB_PATH} as already at the Alembic baseline.")


def main():
    parser = argparse.ArgumentParser(prog="digib00age-server")
    parser.add_argument(
        "--stamp-head", action="store_true",
        help="One-time: mark an existing, already-current-schema DB as "
             "migrated to Alembic's baseline, then exit without starting "
             "the server. Back up the DB first.",
    )
    args = parser.parse_args()
    if args.stamp_head:
        _stamp_head()
        return

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
