"""
database.py — DB connection, session factory, and table creation.
Import get_db() in routers for dependency injection.
Call init_db() once at startup.
"""

import os

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.config import DB_PATH
from backend.models import Base, HomeStrip


def _get_engine():
    db_url = f"sqlite:///{DB_PATH}"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},  # needed for FastAPI threading
        echo=False,                                   # set True to log all SQL
    )
    # Enable WAL mode for better concurrent read/write performance
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = _get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def checkpoint_wal() -> None:
    """
    Forces a full WAL checkpoint and truncates digib00age.db-wal to zero length,
    folding any pending writes into the main .db file. Must run against the live
    engine before any shutil.copy2() of db_path — otherwise a leftover -wal
    sidecar sits next to the copied file and SQLite replays its pending frames
    back into it the next time the DB is opened, silently undoing whatever the
    copy was meant to capture or restore (BUG-016).
    """
    with engine.connect() as conn:
        conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
        conn.commit()


_PERF_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_issues_date_added   ON issues (date_added DESC)",
    "CREATE INDEX IF NOT EXISTS ix_issues_missing_fmt  ON issues (missing, format_group)",
    "CREATE INDEX IF NOT EXISTS ix_issues_series        ON issues (series)",
    "CREATE INDEX IF NOT EXISTS ix_issues_year          ON issues (year)",
    "CREATE INDEX IF NOT EXISTS ix_rp_status            ON reading_progress (status)",
    "CREATE INDEX IF NOT EXISTS ix_custom_tabs_visible  ON custom_tabs (visible, created_at)",
    "CREATE INDEX IF NOT EXISTS ix_home_strips_position ON home_strips (position)",
    "CREATE INDEX IF NOT EXISTS ix_issue_credits_person ON issue_credits (person_id)",
    "CREATE INDEX IF NOT EXISTS ix_issue_credits_issue  ON issue_credits (issue_id)",
    "CREATE INDEX IF NOT EXISTS ix_issue_credits_role   ON issue_credits (role)",
]

# Seeded once, per HOME_STRIPS_SPEC.md Section 2 — name is also the lookup key
# `home.py` uses to dispatch each builtin row to its existing strip logic.
_DEFAULT_HOME_STRIPS = ["Continue Reading", "Recently Added", "Random Unread", "Random Genre"]


def _seed_default_home_strips():
    with SessionLocal() as session:
        if session.query(HomeStrip).filter(HomeStrip.is_default == True).first():  # noqa: E712
            return
        for position, name in enumerate(_DEFAULT_HOME_STRIPS):
            session.add(HomeStrip(
                is_default=True,
                name=name,
                basis_type="builtin",
                visible=True,
                position=position,
            ))
        session.commit()


def _run_alembic_upgrade() -> None:
    """Versioned schema migrations (src/backend/migrations/), replacing the
    _add_missing_*/_drop_legacy_* functions above — see DECISIONS.md "Adopted
    Alembic for schema migrations". script_location is passed explicitly
    (not read from alembic.ini, which is dev-ergonomics-only and not shipped
    with any real install) so this works unmodified across every runtime
    layout (dev, frozen Windows, Docker, pip/XDG)."""
    from alembic.command import upgrade
    from alembic.config import Config

    from backend.config import BACKEND_DIR

    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{DB_PATH}")
    upgrade(cfg, "head")


def init_db():
    """Create/migrate the schema, then ensure performance indexes and default
    rows exist. Tests take a fast path that skips Alembic entirely (see
    DIGIB00AGE_SKIP_ALEMBIC in dev/tests/conftest.py) — safe because tests
    always drop_all() immediately before calling this, so there's never
    column drift for Alembic to reconcile; it's equivalent to create_all()
    for a bare table set."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if os.environ.get("DIGIB00AGE_SKIP_ALEMBIC"):
        Base.metadata.create_all(bind=engine)
    else:
        _run_alembic_upgrade()
    with engine.connect() as conn:
        for ddl in _PERF_INDEXES:
            conn.execute(text(ddl))
        conn.commit()
    _seed_default_home_strips()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a DB session per request, always closes it.

    Usage in a router:
        @router.get("/something")
        def handler(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
