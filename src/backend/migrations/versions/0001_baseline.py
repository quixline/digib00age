"""Baseline — schema as of Alembic adoption.

Consolidates everything Base.metadata.create_all() plus the three ad hoc
ALTER-TABLE functions in backend/database.py built up since 2026-06-21:
_add_missing_issue_columns(), _drop_legacy_credit_columns(),
_add_missing_custom_tab_columns() (all now removed from init_db(), superseded
by this revision). See DECISIONS.md "Adopted Alembic for schema migrations"
for the history.

Written defensively, same guarded pattern as the functions it replaces, so
it's safe to run against either state:
  - A brand-new empty DB: every table is missing below, so step 1 creates
    all 7 tables straight from Base.metadata — byte-identical to what
    create_all() would have built, by construction (it IS create_all(),
    scoped to the missing tables), rather than a hand-transcribed copy of
    models.py that could silently drift from it over time.
  - An already-fully-migrated DB (e.g. quixy's real install, which has
    lived through every one of those ad hoc ALTERs already): every table
    exists and every column reconciliation in steps 2-3 finds its target
    state already in place, so it no-ops. DECISIONS.md documents the
    recommended `alembic stamp head` one-time step for exactly this case,
    which skips running this guard logic at all — this defensive write-up
    is the fallback if that step is ever missed, not the primary path.

_PERF_INDEXES and _seed_default_home_strips() (database.py) are deliberately
NOT part of this migration — both are already cheap and idempotent
(CREATE INDEX IF NOT EXISTS / insert-only-if-missing), and init_db() keeps
running them after the migration step, unchanged.
"""
from __future__ import annotations

import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from backend.models import Base

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_MANAGED_TABLES = (
    "issues", "issue_genres", "people", "issue_credits",
    "reading_progress", "custom_tabs", "home_strips",
)


def _table_names(bind) -> set[str]:
    return {
        row[0] for row in
        bind.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
    }


def _column_names(bind, table: str) -> set[str]:
    return {row[1] for row in bind.execute(sa.text(f"PRAGMA table_info({table})"))}


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = _table_names(bind)

    # 1. Tables that don't exist yet (fresh install) — build them straight
    #    from the current ORM metadata, in FK-safe order (create_all() sorts
    #    by dependency regardless of list order).
    missing = [name for name in _MANAGED_TABLES if name not in existing_tables]
    if missing:
        Base.metadata.create_all(
            bind=bind,
            tables=[Base.metadata.tables[name] for name in missing],
        )

    # 2. issues — reconcile columns on a pre-existing table exactly like
    #    _add_missing_issue_columns()/_drop_legacy_credit_columns() did.
    #    Skipped if "issues" was just created above — a fresh table from
    #    current metadata already has every column in its final shape.
    if "issues" in existing_tables:
        cols = _column_names(bind, "issues")

        if "favorites" not in cols:
            op.add_column("issues", sa.Column(
                "favorites", sa.Boolean(), nullable=False, server_default=sa.false(),
            ))
        if "personal_rating" not in cols:
            op.add_column("issues", sa.Column("personal_rating", sa.Integer(), nullable=True))
        if "container_format" not in cols:
            op.add_column("issues", sa.Column("container_format", sa.Text(), nullable=True))
            # Backfill every already-scanned row from its file_path extension —
            # not just new ones (SPEC.md §7, v2.4 Item 5/11).
            op.execute(
                "UPDATE issues SET container_format = "
                "CASE WHEN lower(file_path) LIKE '%.cbr' THEN 'cbr' ELSE 'cbz' END"
            )
        if "flagged_for_review" not in cols:
            op.add_column("issues", sa.Column(
                "flagged_for_review", sa.Boolean(), nullable=False, server_default=sa.false(),
            ))
        if "file_size" not in cols:
            op.add_column("issues", sa.Column("file_size", sa.Integer(), nullable=True))
            # Backfill from disk so the next scan doesn't treat every
            # already-scanned row as "changed" (BUG-013 fix).
            rows = bind.execute(sa.text("SELECT id, file_path FROM issues")).fetchall()
            for row in rows:
                try:
                    size = os.path.getsize(row.file_path)
                except OSError:
                    continue
                bind.execute(
                    sa.text("UPDATE issues SET file_size = :size WHERE id = :id"),
                    {"size": size, "id": row.id},
                )
        if "content_hash" not in cols:
            # No backfill here, unlike file_size above (BUG-029) — forward-only,
            # existing rows stay NULL until next inserted/updated by scanner.py.
            op.add_column("issues", sa.Column("content_hash", sa.Text(), nullable=True))
        if "queued_for_reading" not in cols:
            op.add_column("issues", sa.Column(
                "queued_for_reading", sa.Boolean(), nullable=False, server_default=sa.false(),
            ))

        # 2026-07-15: inker/colorist/letterer/cover_artist confirmed dead
        # (no reader anywhere in backend/frontend) and dropped. writer/
        # penciller are NOT included here — still power search/Group-by-
        # Writer/series-card display.
        cols = _column_names(bind, "issues")
        for legacy_col in ("inker", "colorist", "letterer", "cover_artist"):
            if legacy_col in cols:
                op.drop_column("issues", legacy_col)

    # 3. custom_tabs — reconcile columns exactly like
    #    _add_missing_custom_tab_columns() did. Same skip-if-fresh reasoning
    #    as step 2.
    if "custom_tabs" in existing_tables:
        cols = _column_names(bind, "custom_tabs")
        if "view_mode" not in cols:
            op.add_column("custom_tabs", sa.Column(
                "view_mode", sa.Text(), nullable=False, server_default="flat",
            ))
        if "basis_type" not in cols:
            op.add_column("custom_tabs", sa.Column(
                "basis_type", sa.Text(), nullable=False, server_default="folder",
            ))
        if "field_value" not in cols:
            op.add_column("custom_tabs", sa.Column("field_value", sa.Text(), nullable=True))


def downgrade() -> None:
    raise NotImplementedError("Baseline has no downgrade — restore from a DB backup instead.")
