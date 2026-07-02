"""
scanner.py — Library walker, ComicInfo.xml parser, thumbnail generator.

Rules:
- Incremental only: INSERT new, UPDATE changed, FLAG missing — never DELETE
- Thumbnail generated on first scan, regenerated if file changes
- format_group detected from folder path ("Series" or "Singles"), never from XML
- Genres and the 6 credit roles (writer/penciller/inker/colorist/letterer/
  cover_artist) are split into junction tables (IssueGenre, IssueCredit) —
  credit rows resolve to a deduped Person entity (Tier 4 Item 3). The raw CSV
  Issue columns for credits are kept temporarily as a rollback safety net
  (see DECISIONS.md) but are no longer the source of truth once Session C lands.
- Characters/Teams/Locations remain raw CSV strings — not in scope for this dedup.
"""

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from PIL import Image
from sqlalchemy.orm import Session

from backend import archive_formats, config, scan_logs
from backend.editor.archive_io import extract_xml_from_archive, find_xml_in_archive
from backend.models import Issue, IssueCredit, IssueGenre, Person, ReadingProgress

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Progress tracking (used by /api/scan/status endpoint)
# ---------------------------------------------------------------------------

@dataclass
class ScanProgress:
    running: bool = False
    total: int = 0
    processed: int = 0
    new: int = 0
    updated: int = 0
    skipped: int = 0
    missing: int = 0
    errors: int = 0
    log: list[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    def add_log(self, msg: str):
        logger.info(msg)
        self.log.append(msg)
        # Keep log from growing unbounded
        if len(self.log) > 500:
            self.log = self.log[-500:]


# Module-level singleton — the API status endpoint reads this
scan_progress = ScanProgress()

# Tracks ALL metadata updates (editor rescans + full scan) since the last full
# scan completed. _since_scan_count accumulates continuously; at the end of
# each full scan it is snapshotted into _last_cycle_changes then reset to 0.
_since_scan_count: int = 0
_last_cycle_changes: int = 0


def get_changes_last_cycle() -> int:
    return _last_cycle_changes


# ---------------------------------------------------------------------------
# XML parsing helpers
# ---------------------------------------------------------------------------

def _text(element: Optional[ET.Element], tag: str) -> Optional[str]:
    """Return stripped text for a child tag, or None if absent/empty/self-closing."""
    if element is None:
        return None
    child = element.find(tag)
    if child is None:
        return None
    # A self-closing tag (<Number />) has text=None; an empty tag (<Number></Number>) has text=""
    if not child.text or not child.text.strip():
        return None
    return child.text.strip()


def _int(element: Optional[ET.Element], tag: str) -> Optional[int]:
    raw = _text(element, tag)
    if raw is None:
        return None
    try:
        return int(float(raw))  # handle "1.0" style strings
    except (ValueError, TypeError):
        return None


def _bool_on(element: Optional[ET.Element], tag: str) -> bool:
    """True only if the tag text is exactly 'on' (case-insensitive). Absent/empty = False."""
    raw = _text(element, tag)
    if raw is None:
        return False
    return raw.lower() == "on"


def _language(element: Optional[ET.Element]) -> Optional[str]:
    """Check <Language> first, then <LanguageISO> — store whichever is present."""
    return _text(element, "Language") or _text(element, "LanguageISO")


def _split_csv(element: Optional[ET.Element], tag: str) -> list[str]:
    """
    Split a CSV child tag into a list of stripped, non-empty, deduplicated
    strings (order preserved). Dedup matters because real ComicInfo.xml files
    in this library do contain a literal repeated name within one field (e.g.
    Penciller = "Chris Shehan, Maan House, Chris Shehan, Maan House", found in
    175 issues across Penciller/Inker) — without it, a junction-table insert
    keyed on (issue_id, value) hits a UniqueConstraint violation.
    """
    raw = _text(element, tag)
    if not raw:
        return []
    return list(dict.fromkeys(s.strip() for s in raw.split(",") if s.strip()))


def _genres(element: Optional[ET.Element]) -> list[str]:
    """Split <Genre> CSV into a list of stripped, non-empty strings."""
    return _split_csv(element, "Genre")


# Credit role -> ComicInfo.xml tag name, in the same order as the raw Issue columns
_CREDIT_TAGS = {
    "writer": "Writer",
    "penciller": "Penciller",
    "inker": "Inker",
    "colorist": "Colorist",
    "letterer": "Letterer",
    "cover_artist": "CoverArtist",
}


def _credits(element: Optional[ET.Element]) -> dict[str, list[str]]:
    """Split each of the 6 credit CSV tags into per-role lists of names."""
    return {role: _split_csv(element, tag) for role, tag in _CREDIT_TAGS.items()}


# ---------------------------------------------------------------------------
# Filename fallback parser
# ---------------------------------------------------------------------------

_FILENAME_RE = re.compile(
    r"^(?P<series>.+?)\s*#(?P<number>[\w½]+)\s*(?:\((?P<year>\d{4})\))?"
    r"(?:\s*.+)?\.(?:cbz|cbr)$",
    re.IGNORECASE,
)


def _parse_filename(filename: str) -> dict:
    """
    Extract metadata from filename when ComicInfo.xml is missing/corrupt.
    Pattern: Series Name #Number (Year).cbz
    Returns a dict of extracted fields; unrecognised fields are None.
    """
    m = _FILENAME_RE.match(filename)
    if not m:
        # Minimal fallback — just use the stem as series name
        stem = Path(filename).stem
        return {"series": stem, "number": None, "year": None}

    return {
        "series": m.group("series").strip(),
        "number": m.group("number"),
        "year": int(m.group("year")) if m.group("year") else None,
    }


# ---------------------------------------------------------------------------
# Format group detection
# ---------------------------------------------------------------------------

def _format_group(file_path: str) -> str:
    """Derive format_group from folder path. 'Singles' takes priority."""
    if config.SINGLES_FOLDER in file_path:
        return "Singles"
    if config.SERIES_FOLDER in file_path:
        return "Series"
    return "Series"  # safe default


# ---------------------------------------------------------------------------
# Thumbnail generation
# ---------------------------------------------------------------------------

def _generate_thumbnail(cbz_path: str, issue_id: int) -> Optional[str]:
    """
    Open the CBZ, find the first image alphabetically, resize to thumbnail_size wide,
    save as backend/thumbnails/{issue_id}.jpg.
    Returns the thumbnail path string, or None on failure.
    Never raises — a bad/corrupt image is logged and skipped.
    """
    config.THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
    thumb_path = config.THUMBNAIL_DIR / f"{issue_id}.jpg"

    # Tell Pillow to be lenient with truncated/corrupt images
    from PIL import ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    img = None
    try:
        with archive_formats._opener(cbz_path) as archive:
            image_files = sorted(
                name for name in archive.namelist()
                if name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))
                and "comicinfo" not in name.lower()
            )
            if not image_files:
                logger.warning("No images found in %s", cbz_path)
                return None

            # Try images in order until one succeeds — first may be corrupt
            for cover_name in image_files[:3]:
                try:
                    raw = archive.read(cover_name)
                    from io import BytesIO
                    img = Image.open(BytesIO(raw))
                    img.load()
                    break  # success
                except Exception as img_exc:
                    logger.warning("Cover image unreadable in %s (%s): %s",
                                   cbz_path, cover_name, img_exc)
                    img = None

        if img is None:
            logger.error("All cover attempts failed for %s", cbz_path)
            return None

        # Resize maintaining aspect ratio
        target_width = config.THUMBNAIL_SIZE
        w, h = img.size
        target_height = int(h * target_width / w) if w > 0 else target_width

        img = img.convert("RGB")  # ensure JPEG-safe colour mode
        img = img.resize((target_width, target_height), Image.LANCZOS)
        img.save(str(thumb_path), "JPEG", quality=85, optimize=True)
        return str(thumb_path)

    except archive_formats.BAD_ARCHIVE_EXCEPTIONS:
        logger.error("Thumbnail skipped — bad archive: %s", cbz_path)
        return None
    except Exception as exc:
        logger.error("Thumbnail failed for %s: %s", cbz_path, exc)
        return None


# ---------------------------------------------------------------------------
# Single-file scan (called for new files and changed files)
# ---------------------------------------------------------------------------

def _parse_cbz(file_path: str) -> tuple[dict, str]:
    """
    Open a CBZ or CBR and parse its ComicInfo.xml (SPEC.md §6.1 — CBR added
    v2.4 Item 5/11, scanner treats both identically except which extraction
    backend opens the archive).
    Returns (metadata_dict, metadata_source) where source is "xml" or "filename".
    """
    filename = Path(file_path).name
    metadata_source = "xml"
    root_el = None

    try:
        # ComicInfo.xml can be anywhere in the archive, not just the root
        # (BUG-018) — find_xml_in_archive()/extract_xml_from_archive() are
        # the same helpers the editors already use, matching by full path at
        # any folder depth. Filtered to names actually ending in
        # "comicinfo.xml" (case-insensitive) to keep today's semantics of
        # only trusting that exact filename, not any stray .xml sidecar.
        xml_names = [n for n in find_xml_in_archive(file_path)
                     if n.lower().endswith("comicinfo.xml")]
        if xml_names:
            xml_content = extract_xml_from_archive(file_path, xml_names[0])
            if xml_content is not None:
                root_el = ET.fromstring(xml_content)
            else:
                metadata_source = "filename"
        else:
            metadata_source = "filename"
    except ET.ParseError:
        logger.warning("Corrupt ComicInfo.xml in: %s", file_path)
        metadata_source = "filename"
    except Exception as exc:
        logger.error("Unexpected error reading %s: %s", file_path, exc)
        metadata_source = "filename"

    if metadata_source == "filename" or root_el is None:
        fallback = _parse_filename(filename)
        return {
            "series": fallback["series"],
            "volume": None,
            "number": fallback["number"],
            "title": fallback["series"],
            "year": fallback["year"],
            "month": None,
            "publisher": None,
            "format": None,
            "summary": None,
            "story_arc": None,
            "story_arc_number": None,
            "writer": None,
            "penciller": None,
            "inker": None,
            "colorist": None,
            "letterer": None,
            "cover_artist": None,
            "characters": None,
            "teams": None,
            "locations": None,
            "age_rating": None,
            "language": None,
            "black_and_white": False,
            "manga": "No",
            "page_count": None,
            "count": None,
            "genres": [],
            "credits": {role: [] for role in _CREDIT_TAGS},
        }, "filename"

    # --- Full XML parse ---
    # Verify actual image count vs XML page_count
    actual_page_count = None
    try:
        with archive_formats._opener(file_path) as archive:
            actual_page_count = sum(
                1 for n in archive.namelist()
                if n.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))
            )
    except Exception:
        pass

    xml_page_count = _int(root_el, "PageCount")
    page_count = actual_page_count if actual_page_count is not None else xml_page_count

    series = _text(root_el, "Series") or _parse_filename(filename)["series"]

    return {
        "series": series,
        "volume": _int(root_el, "Volume"),
        "number": _text(root_el, "Number"),
        "title": _text(root_el, "Title") or series,
        "year": _int(root_el, "Year"),
        "month": _int(root_el, "Month"),
        "publisher": _text(root_el, "Publisher"),
        "format": _text(root_el, "Format"),
        "summary": _text(root_el, "Summary"),
        "story_arc": _text(root_el, "StoryArc"),
        "story_arc_number": _int(root_el, "StoryArcNumber"),
        "writer": _text(root_el, "Writer"),
        "penciller": _text(root_el, "Penciller"),
        "inker": _text(root_el, "Inker"),
        "colorist": _text(root_el, "Colorist"),
        "letterer": _text(root_el, "Letterer"),
        "cover_artist": _text(root_el, "CoverArtist"),
        "characters": _text(root_el, "Characters"),
        "teams": _text(root_el, "Teams"),
        "locations": _text(root_el, "Locations"),
        "age_rating": _text(root_el, "AgeRating"),
        "language": _language(root_el),
        "black_and_white": _bool_on(root_el, "BlackAndWhite"),
        "manga": _text(root_el, "Manga") or "No",
        "page_count": page_count,
        "count": _int(root_el, "Count"),
        "genres": _genres(root_el),
        "credits": _credits(root_el),
    }, "xml"


def _apply_metadata(issue: Issue, meta: dict, source: str,
                    file_path: str, mtime: datetime):
    """Write parsed metadata dict into an Issue ORM object."""
    issue.series          = meta["series"]
    issue.volume          = meta["volume"]
    issue.number          = meta["number"]
    issue.title           = meta["title"]
    issue.year            = meta["year"]
    issue.month           = meta["month"]
    issue.publisher       = meta["publisher"]
    issue.format          = meta["format"]
    issue.format_group    = _format_group(file_path)
    issue.summary         = meta["summary"]
    issue.story_arc       = meta["story_arc"]
    issue.story_arc_number = meta["story_arc_number"]
    issue.writer          = meta["writer"]
    issue.penciller       = meta["penciller"]
    issue.inker           = meta["inker"]
    issue.colorist        = meta["colorist"]
    issue.letterer        = meta["letterer"]
    issue.cover_artist    = meta["cover_artist"]
    issue.characters      = meta["characters"]
    issue.teams           = meta["teams"]
    issue.locations       = meta["locations"]
    issue.age_rating      = meta["age_rating"]
    issue.language        = meta["language"]
    issue.black_and_white = meta["black_and_white"]
    issue.manga           = meta["manga"]
    issue.page_count      = meta["page_count"]
    issue.count           = meta["count"]
    issue.metadata_source = source
    issue.container_format = archive_formats.format_for_path(file_path)
    issue.date_modified   = mtime
    issue.missing         = False


def _sync_genres(db: Session, issue: Issue, genre_list: list[str]):
    """Replace the issue's genre rows with the current parsed list."""
    # Delete existing
    for g in list(issue.genres):
        db.delete(g)
    db.flush()
    # Insert new
    for genre_name in genre_list:
        db.add(IssueGenre(issue_id=issue.id, genre_name=genre_name))


def _sync_credits(db: Session, issue: Issue, credits: dict[str, list[str]]):
    """
    Replace the issue's credit rows with the current parsed lists (Tier 4 Item
    3) — same delete-then-reinsert shape as _sync_genres, except each name
    resolves to a stable Person row (get-or-create by exact name) instead of a
    denormalized string, since a person needs one id referenceable across all
    six roles.
    """
    for c in list(issue.credits):
        db.delete(c)
    db.flush()
    for role, names in credits.items():
        for name in names:
            person = db.query(Person).filter(Person.name == name).first()
            if person is None:
                person = Person(name=name)
                db.add(person)
                db.flush()
            db.add(IssueCredit(issue_id=issue.id, person_id=person.id, role=role))


def _ensure_progress(db: Session, issue: Issue):
    """Create a ReadingProgress row if one doesn't exist yet."""
    if issue.progress is None:
        db.add(ReadingProgress(issue_id=issue.id, status="unread", current_page=0))


# ---------------------------------------------------------------------------
# Scan a single file (also used by POST /api/scan/file)
# ---------------------------------------------------------------------------

def scan_single_file(file_path: str, db: Session, details: dict | None = None) -> str:
    """
    Scan or rescan one CBZ or CBR file.
    Returns one of: "new", "updated", "skipped", "error"

    `details`, if passed, is filled in with extra info the caller may want —
    currently just `change_type` for "updated" results (changed_files log,
    2.3-fixes.md Fix 8). Other callers don't need it and can omit it.
    """
    file_path = str(Path(file_path).resolve())

    try:
        mtime = datetime.utcfromtimestamp(os.path.getmtime(file_path))
    except FileNotFoundError:
        # File has disappeared since we started — flag it if it's in the DB
        issue = db.query(Issue).filter(Issue.file_path == file_path).first()
        if issue:
            issue.missing = True
            db.commit()
        return "error"
    except Exception as exc:
        logger.error("Cannot stat %s: %s", file_path, exc)
        return "error"

    existing = db.query(Issue).filter(Issue.file_path == file_path).first()

    # --- Skip if unchanged ---
    if existing and existing.date_modified:
        # Compare to the nearest second to avoid float precision issues
        if abs((existing.date_modified - mtime).total_seconds()) < 1:
            # Unchanged metadata doesn't guarantee the thumbnail file still
            # exists on disk (e.g. a DB restored/copied without thumbnails/) —
            # check and backfill it before skipping (BUG-001).
            thumb_path = config.THUMBNAIL_DIR / f"{existing.id}.jpg"
            if not thumb_path.exists():
                thumb = _generate_thumbnail(file_path, existing.id)
                if thumb:
                    existing.cover_path = thumb
                    db.commit()
            return "skipped"

    # --- Parse metadata ---
    try:
        meta, source = _parse_cbz(file_path)
    except Exception as exc:
        logger.error("Parse error for %s: %s", file_path, exc)
        return "error"

    global _since_scan_count

    if existing:
        # UPDATE
        if details is not None:
            old_page_count = existing.page_count
            new_page_count = meta["page_count"]
            details["change_type"] = (
                f"archive changed (pages: {old_page_count} → {new_page_count})"
                if new_page_count != old_page_count
                else "metadata updated"
            )
        _apply_metadata(existing, meta, source, file_path, mtime)
        db.flush()
        _sync_genres(db, existing, meta["genres"])
        _sync_credits(db, existing, meta["credits"])
        thumb = _generate_thumbnail(file_path, existing.id)
        if thumb:
            existing.cover_path = thumb
        db.commit()
        _since_scan_count += 1
        return "updated"
    else:
        # INSERT
        issue = Issue(file_path=file_path, date_added=datetime.utcnow())
        _apply_metadata(issue, meta, source, file_path, mtime)
        db.add(issue)
        db.flush()
        _sync_genres(db, issue, meta["genres"])
        _sync_credits(db, issue, meta["credits"])
        _ensure_progress(db, issue)
        thumb = _generate_thumbnail(file_path, issue.id)
        if thumb:
            issue.cover_path = thumb
        db.commit()
        _since_scan_count += 1
        return "new"


# ---------------------------------------------------------------------------
# Full library scan
# ---------------------------------------------------------------------------

def scan_library(db: Session):
    """
    Walk the entire library and incrementally update the DB.
    Updates the module-level scan_progress object throughout.
    Files in DB that are no longer on disk are flagged missing=True.
    """
    global scan_progress

    scan_progress = ScanProgress(running=True, started_at=datetime.utcnow())
    scan_progress.add_log("Scan started")

    library_root = config.LIBRARY_ROOT

    if not os.path.isdir(library_root):
        scan_progress.add_log(f"ERROR: library_root not found: {library_root}")
        scan_progress.running = False
        scan_progress.finished_at = datetime.utcnow()
        return

    # ---- Collect all CBZ paths on disk ----
    exclude = config.SCAN_EXCLUDE  # folder name fragments to skip e.g. ["Processing"]
    if exclude:
        scan_progress.add_log(f"Excluding folders: {exclude}")

    disk_paths: set[str] = set()
    for dirpath, dirs, filenames in os.walk(library_root):
        # Prune excluded directories in-place so os.walk doesn't descend into them
        if exclude:
            dirs[:] = [d for d in dirs if d not in exclude]

        # Also skip if any path component matches an exclusion (catches nested cases)
        path_parts = Path(dirpath).parts
        if exclude and any(part in exclude for part in path_parts):
            continue

        for fname in filenames:
            if fname.lower().endswith((".cbz", ".cbr")):
                full = str(Path(dirpath) / fname)
                disk_paths.add(full)

    scan_progress.total = len(disk_paths)
    scan_progress.add_log(f"Found {len(disk_paths)} CBZ/CBR files on disk")

    # ---- Process each file ----
    for file_path in sorted(disk_paths):
        details: dict = {}
        result = scan_single_file(file_path, db, details)
        scan_progress.processed += 1

        if result == "new":
            scan_progress.new += 1
            scan_progress.add_log(f"NEW: {Path(file_path).name}")
            scan_logs.append_new_files_entry(Path(file_path).name, str(Path(file_path).parent))
        elif result == "updated":
            scan_progress.updated += 1
            scan_progress.add_log(f"UPDATED: {Path(file_path).name}")
            scan_logs.append_changed_files_entry(
                Path(file_path).name, details.get("change_type", "metadata updated")
            )
        elif result == "skipped":
            scan_progress.skipped += 1
        elif result == "error":
            scan_progress.errors += 1
            scan_progress.add_log(f"ERROR: {Path(file_path).name}")

    # ---- Handle files in DB that are no longer on disk ----
    # Also silently delete any records whose path falls inside an excluded folder —
    # these were scanned before the exclusion was added and should be cleaned up.
    all_db_issues = db.query(Issue).filter(Issue.missing == False).all()  # noqa: E712
    for issue in all_db_issues:
        if issue.file_path in disk_paths:
            continue  # still on disk and in scope — fine

        # Check if this path lives inside an excluded folder
        path_parts = Path(issue.file_path).parts
        if exclude and any(part in exclude for part in path_parts):
            db.delete(issue)
            scan_progress.add_log(f"REMOVED (excluded folder): {Path(issue.file_path).name}")
            continue

        # Genuinely missing from disk
        issue.missing = True
        scan_progress.missing += 1
        scan_progress.add_log(f"MISSING: {Path(issue.file_path).name}")
        scan_logs.append_missing_entry(
            Path(issue.file_path).name, issue.file_path, datetime.utcnow()
        )

    db.commit()

    scan_progress.add_log(
        f"Scan complete — "
        f"new={scan_progress.new}, "
        f"updated={scan_progress.updated}, "
        f"skipped={scan_progress.skipped}, "
        f"missing={scan_progress.missing}, "
        f"errors={scan_progress.errors}"
    )
    scan_progress.running = False
    scan_progress.finished_at = datetime.utcnow()
    scan_logs.append_last_scan_entry(scan_progress.started_at, scan_progress.finished_at)

    # Snapshot the accumulated change count (includes editor rescans + this
    # scan's own detections), then reset for the next cycle.
    global _since_scan_count, _last_cycle_changes
    _last_cycle_changes = _since_scan_count
    _since_scan_count = 0
