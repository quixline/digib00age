"""
database.py — DB connection, session factory, and table creation.
Import get_db() in routers for dependency injection.
Call init_db() once at startup.
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.config import DB_PATH
from backend.models import Base


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
]


def init_db():
    """Create all tables and performance indexes if they don't already exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        for ddl in _PERF_INDEXES:
            conn.execute(text(ddl))
        conn.commit()


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
