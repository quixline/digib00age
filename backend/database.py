"""
database.py — DB connection, session factory, and table creation.
Import get_db() in routers for dependency injection.
Call init_db() once at startup.
"""

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


def _add_missing_issue_columns():
    """
    create_all() only creates missing *tables* — it never adds columns to a
    table that already exists. New additive Issue columns need a manual
    ALTER TABLE here, run once per missing column (idempotent).
    """
    with engine.connect() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(issues)"))}
        if "favorites" not in cols:
            conn.execute(text("ALTER TABLE issues ADD COLUMN favorites BOOLEAN NOT NULL DEFAULT 0"))
        if "personal_rating" not in cols:
            conn.execute(text("ALTER TABLE issues ADD COLUMN personal_rating INTEGER"))
        if "container_format" not in cols:
            conn.execute(text("ALTER TABLE issues ADD COLUMN container_format TEXT"))
            # Backfill every already-scanned row from its file_path extension —
            # not just new ones (SPEC.md §7, v2.4 Item 5/11).
            conn.execute(text(
                "UPDATE issues SET container_format = "
                "CASE WHEN lower(file_path) LIKE '%.cbr' THEN 'cbr' ELSE 'cbz' END"
            ))
        conn.commit()


def _drop_legacy_credit_columns():
    """
    2026-07-15: inker/colorist/letterer/cover_artist confirmed dead (no
    reader anywhere in backend/frontend — see DECISIONS.md) and dropped.
    writer/penciller are NOT included here — still power search/Group-by-
    Writer/series-card display, deliberately left in place. Idempotent, same
    guarded-ALTER-TABLE pattern as _add_missing_issue_columns(). Requires
    SQLite 3.35+ (2021) for DROP COLUMN support.
    """
    with engine.connect() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(issues)"))}
        for col in ("inker", "colorist", "letterer", "cover_artist"):
            if col in cols:
                conn.execute(text(f"ALTER TABLE issues DROP COLUMN {col}"))
        conn.commit()


def _add_missing_custom_tab_columns():
    """
    create_all() only creates missing *tables* — it never adds columns to a
    table that already exists. The additive CustomTab.view_mode/basis_type
    columns need a manual ALTER TABLE here, run once each (idempotent).
    """
    with engine.connect() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(custom_tabs)"))}
        if "view_mode" not in cols:
            conn.execute(text("ALTER TABLE custom_tabs ADD COLUMN view_mode TEXT NOT NULL DEFAULT 'flat'"))
        if "basis_type" not in cols:
            conn.execute(text("ALTER TABLE custom_tabs ADD COLUMN basis_type TEXT NOT NULL DEFAULT 'folder'"))
        conn.commit()


def init_db():
    """Create all tables and performance indexes if they don't already exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _add_missing_issue_columns()
    _drop_legacy_credit_columns()
    _add_missing_custom_tab_columns()
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
