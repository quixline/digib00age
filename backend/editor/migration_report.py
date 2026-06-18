"""
migration_report.py — Pre-Migration Data-Hygiene Report (EDITOR_SPEC.md Section 7).

One-time report listing every issue whose current Genre, Format, or AgeRating
value doesn't match the newly-enforced lists (Section 4). Run as a script —
writes a CSV that's sortable/filterable in any spreadsheet tool. Issues
flagged "missing" (no value at all) are distinguished from issues flagged
"invalid" (a value present, but not one of the enforced options), since
those are different kinds of cleanup work for Tez to triage.

Usage (from the project root):
    python -m backend.editor.migration_report
"""

import csv
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from backend.editor.constants import FORMAT_OPTIONS, AGE_RATING_OPTIONS
from backend.editor.genres import load_genres
from backend.models import Issue


def generate_report(db: Session) -> list[dict]:
    """
    Return one row per (issue, field) mismatch — an issue with two bad
    fields produces two rows. Excludes issues flagged missing (file no
    longer on disk — nothing to edit).
    """
    enforced_genres = set(load_genres())
    enforced_formats = set(FORMAT_OPTIONS)
    enforced_ratings = set(AGE_RATING_OPTIONS)

    rows = []
    issues = db.query(Issue).filter(Issue.missing == False).all()  # noqa: E712

    for issue in issues:
        if not issue.format:
            rows.append(_row(issue, "Format", "", "missing"))
        elif issue.format not in enforced_formats:
            rows.append(_row(issue, "Format", issue.format, "invalid"))

        if not issue.age_rating:
            rows.append(_row(issue, "AgeRating", "", "missing"))
        elif issue.age_rating not in enforced_ratings:
            rows.append(_row(issue, "AgeRating", issue.age_rating, "invalid"))

        genre_names = [g.genre_name for g in issue.genres]
        if not genre_names:
            rows.append(_row(issue, "Genre", "", "missing"))
        else:
            for name in genre_names:
                if name not in enforced_genres:
                    rows.append(_row(issue, "Genre", name, "invalid"))

    return rows


def _row(issue: Issue, field: str, value: str, status: str) -> dict:
    return {
        "issue_id": issue.id,
        "series": issue.series,
        "file_path": issue.file_path,
        "field": field,
        "current_value": value,
        "status": status,
    }


def write_csv(rows: list[dict], out_path: Path) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["issue_id", "series", "file_path", "field", "current_value", "status"]
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    from backend.database import SessionLocal

    db = SessionLocal()
    try:
        rows = generate_report(db)
    finally:
        db.close()

    out_path = Path(__file__).resolve().parents[2] / "pre_migration_report.csv"
    write_csv(rows, out_path)

    by_field = {}
    for row in rows:
        by_field[row["field"]] = by_field.get(row["field"], 0) + 1

    print(f"{len(rows)} mismatched (issue, field) rows written to {out_path}")
    for field, count in sorted(by_field.items()):
        print(f"  {field}: {count}")
    sys.exit(0)
