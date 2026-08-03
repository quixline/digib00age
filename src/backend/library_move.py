"""
library_move.py — Move Series Folders / Move Singles Folders Processing Tool
core logic (ADMIN_SPEC.md §11.7). Ported as two standalone scripts sharing
one core module. For every immediate subfolder of a chosen folder (e.g.
Processing\\Stage 3\\series or \\singles), moves it into its correct place in
the library structure — the final stage of processing before a library scan.

Pure function, no router/logging concerns — same pattern as filename_sort.py.

Also runnable directly from a terminal:
    python -m backend.library_move series  "L:\\...\\Processing\\Stage 3\\series"
    python -m backend.library_move singles "L:\\...\\Processing\\Stage 3\\singles"
"""

from __future__ import annotations

import difflib
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from typing import Optional

_LEADING_ARTICLE_RE = re.compile(r"^(the|a|an)\s+", re.IGNORECASE)

# Folders that already differ only by punctuation/case/year-suffix from an
# existing library folder get flagged as a near-miss rather than silently
# filed alongside it. Trailing "(YYYY)" / "[YYYY]" and non-alphanumeric
# characters are stripped before comparing.
_YEAR_SUFFIX_RE = re.compile(r"[\[\(]\s*\d{4}\s*[\]\)]\s*$")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")

_NEAR_MISS_THRESHOLD = 0.87


@dataclass
class LibraryMoveFolderResult:
    folder_name: str
    destination: str
    success: bool
    error: Optional[str] = None
    files_moved: int = 0
    files_failed: int = 0
    moved_paths: list[tuple[str, str]] = field(default_factory=list)
    db_sync_error: Optional[str] = None


@dataclass
class NearMissWarning:
    folder_name: str
    destination: str
    existing_match: str


@dataclass
class LibraryMoveResult:
    success: bool
    folders: list[LibraryMoveFolderResult] = field(default_factory=list)
    near_misses: list[NearMissWarning] = field(default_factory=list)
    error: Optional[str] = None  # top-level failure — no folders were attempted


def _alpha_bucket(folder_name: str) -> str:
    """
    Derive the alpha index folder ('#', 'A'..'Z') from a folder name.
    A leading 'The '/'A '/'An ' is stripped first (matches how the existing
    library is actually filed — 'The 13th Artifact' -> '#', 'A Taste for
    Blood' -> 'T'), then the next character decides: A-Z -> that letter,
    anything else (digit, apostrophe, punctuation) -> '#'.
    """
    stripped = _LEADING_ARTICLE_RE.sub("", folder_name).strip()
    first = stripped[0].upper() if stripped else ""
    return first if first.isalpha() and first in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else "#"


def _normalize_for_comparison(folder_name: str) -> str:
    """Loose form used only for near-miss detection — never affects where a
    folder actually gets filed."""
    no_year = _YEAR_SUFFIX_RE.sub("", folder_name)
    return _NON_ALNUM_RE.sub("", no_year.lower()).strip()


def _find_exact_duplicate(folder_name: str, candidates: list[tuple[str, str]]) -> Optional[tuple[str, str]]:
    """
    Returns the (name, full_path) of an existing folder that is the SAME
    title under different notation — e.g. an older 'Barbarella [1964]'
    against a new 'Barbarella (1964)' coming out of Processing. Anything
    that normalizes identically (same letters/digits once the year suffix
    and all punctuation are stripped, regardless of bracket style) is
    treated as a confident duplicate, not a maybe: the caller blocks the
    move entirely rather than just warning, since moving it would silently
    create a second copy of the same content under a different name.
    """
    norm_target = _normalize_for_comparison(folder_name)
    if not norm_target:
        return None
    for cand_name, cand_path in candidates:
        if cand_name == folder_name:
            continue
        if _normalize_for_comparison(cand_name) == norm_target:
            return cand_name, cand_path
    return None


def _find_near_miss(folder_name: str, candidates: list[tuple[str, str]]) -> Optional[tuple[str, str]]:
    """Returns the (name, full_path) of an existing folder that looks like a
    probable — but not certain — variant of `folder_name`, or None.
    Candidates already known to be an exact duplicate (see
    `_find_exact_duplicate`) are handled separately and blocked outright;
    this function is for the softer, still-worth-a-look case. Candidates are
    folders already known to live somewhere in the target format-group,
    library-wide (not just the computed destination's own alpha bucket) —
    this is what catches cases like 'The Complete Terminal City' filing
    under T while 'Terminal City' lives under C."""
    norm_target = _normalize_for_comparison(folder_name)
    if not norm_target:
        return None
    best_ratio = 0.0
    best_match: Optional[tuple[str, str]] = None
    for cand_name, cand_path in candidates:
        if cand_name == folder_name:
            continue
        norm_candidate = _normalize_for_comparison(cand_name)
        if not norm_candidate:
            continue

        # Straight similarity ratio catches near-identical names (typos,
        # punctuation drift). Containment catches the more common real case
        # — one name sitting inside another with an extra prefix/suffix
        # word, e.g. "Judge Dredd Megazine" inside "2000 AD - Judge Dredd
        # Megazines" — which a whole-string ratio scores too low on. A
        # minimum length guard keeps a short generic word from flagging
        # everything that happens to contain it.
        ratio = difflib.SequenceMatcher(None, norm_target, norm_candidate).ratio()
        shorter, longer = sorted((norm_target, norm_candidate), key=len)
        contained = len(shorter) >= 8 and shorter in longer
        score = 1.0 if contained else ratio

        if score > best_ratio:
            best_ratio = score
            best_match = (cand_name, cand_path)
    if best_match is not None and best_ratio >= _NEAR_MISS_THRESHOLD:
        return best_match
    return None


def _list_existing_folders(library_root: str, format_folder: str) -> list[tuple[str, str]]:
    """Every (folder_name, full_path) that currently exists under any alpha
    bucket for the given format group (e.g. all Series folders, library-
    wide) — used for exact-duplicate/near-miss comparison, not for filing."""
    entries: list[tuple[str, str]] = []
    if not os.path.isdir(library_root):
        return entries
    for alpha_entry in os.listdir(library_root):
        alpha_path = os.path.join(library_root, alpha_entry)
        if not os.path.isdir(alpha_path):
            continue
        group_path = os.path.join(alpha_path, format_folder)
        if not os.path.isdir(group_path):
            continue
        try:
            for name in os.listdir(group_path):
                full_path = os.path.join(group_path, name)
                if os.path.isdir(full_path):
                    entries.append((name, full_path))
        except OSError:
            continue
    return entries


_SORTABLE_EXTENSIONS = {".cbz", ".cbr"}


def _merge_into_existing(
    source_folder: str, target_folder: str
) -> tuple[int, int, Optional[str], list[tuple[str, str]]]:
    """
    Recursively merges every entry of `source_folder` into an existing
    `target_folder`. Returns (moved, failed, error, moved_pairs).

    Purely structural, no name-based inference: if an entry is a plain file,
    the ordinary per-file clash rule applies (destination path already
    occupied -> that file fails, everything else still attempted). If an
    entry is a folder and the destination already has a same-named folder,
    the merge recurses one level deeper into it rather than failing the
    whole subfolder outright — this is what lets a container-style series
    (e.g. one grouped into dated sub-folders, issues never sitting directly
    in the top folder) merge correctly, without the mover needing to know
    anything about that series by name. A folder entry with no matching
    destination folder is moved over as a new addition, same as a brand-new
    top-level series folder would be.

    Source folder (and any subfolder emptied by the recursion) is removed
    only if it ends up empty.

    `moved_pairs` records the exact (src, dst) of every unit actually moved
    on disk (a merge is not always a clean single-prefix rename — some
    entries can fail on a destination clash and stay put — so callers need
    the precise set of what moved, not just the source/target folders, to
    keep any downstream path rewriting correct).
    """
    moved = 0
    failed = 0
    moved_pairs: list[tuple[str, str]] = []
    try:
        entries = sorted(os.listdir(source_folder))
    except OSError as exc:
        return 0, 0, str(exc), moved_pairs

    for name in entries:
        src = os.path.join(source_folder, name)
        dst = os.path.join(target_folder, name)

        if os.path.isdir(src) and os.path.isdir(dst):
            sub_moved, sub_failed, sub_err, sub_pairs = _merge_into_existing(src, dst)
            if sub_err:
                failed += 1
                continue
            moved += sub_moved
            failed += sub_failed
            moved_pairs.extend(sub_pairs)
            continue

        if os.path.exists(dst):
            failed += 1
            continue
        try:
            shutil.move(src, dst)
            moved += 1
            moved_pairs.append((src, dst))
        except OSError:
            failed += 1

    try:
        if not os.listdir(source_folder):
            os.rmdir(source_folder)
    except OSError:
        pass

    return moved, failed, None, moved_pairs


def move_folders(folder: str, group: str) -> LibraryMoveResult:
    """
    Moves every immediate subfolder of `folder` into its correct place under
    `library_root`, per SPEC.md §5's Series/Singles structure.

    group: "series" or "singles" — determines the format-group subfolder
    used (config.json's series_folder/singles_folder) and the collision rule:
    Series merges into an existing destination (file-level clashes fail
    individually); Singles fails the whole folder if the destination already
    exists.
    """
    from backend.config import SERIES_FOLDER, SINGLES_FOLDER, get_library_root
    LIBRARY_ROOT = get_library_root()

    if group not in ("series", "singles"):
        return LibraryMoveResult(success=False, error=f"Unknown group: {group}")

    if not os.path.isdir(folder):
        return LibraryMoveResult(success=False, error="Folder not found")

    format_folder = SERIES_FOLDER if group == "series" else SINGLES_FOLDER

    try:
        subfolders = sorted(
            name for name in os.listdir(folder)
            if os.path.isdir(os.path.join(folder, name))
        )
    except OSError as exc:
        return LibraryMoveResult(success=False, error=str(exc))

    existing_folders = _list_existing_folders(LIBRARY_ROOT, format_folder)

    results: list[LibraryMoveFolderResult] = []
    near_misses: list[NearMissWarning] = []

    for folder_name in subfolders:
        source_path = os.path.join(folder, folder_name)
        alpha = _alpha_bucket(folder_name)
        target_folder = os.path.join(LIBRARY_ROOT, alpha, format_folder, folder_name)

        # Confident duplicate — same title, different notation (e.g. an
        # older 'Barbarella [1964]' vs a new 'Barbarella (1964)'). Blocked
        # outright rather than just warned about: moving it would silently
        # create a second copy of the same content under a different name.
        # Folder stays exactly where it is in Stage 3, logged as a failure.
        exact_dup = _find_exact_duplicate(folder_name, existing_folders)
        if exact_dup:
            _, dup_path = exact_dup
            results.append(LibraryMoveFolderResult(
                folder_name=folder_name,
                destination=target_folder,
                success=False,
                error=f"Looks like a duplicate of existing '{dup_path}' (differs only in "
                      f"punctuation/year-bracket style) — not moved, resolve manually",
            ))
            continue

        near_miss = _find_near_miss(folder_name, existing_folders)
        if near_miss:
            _, nm_path = near_miss
            near_misses.append(NearMissWarning(
                folder_name=folder_name,
                destination=target_folder,
                existing_match=nm_path,
            ))

        destination_exists = os.path.isdir(target_folder)

        if destination_exists and group == "singles":
            results.append(LibraryMoveFolderResult(
                folder_name=folder_name,
                destination=target_folder,
                success=False,
                error=f"Destination already exists: '{target_folder}'",
            ))
            continue

        try:
            if destination_exists:
                # Series merge — recursive, per-item independence, source
                # folder (and any subfolder it contains) only removed if it
                # ends up empty.
                moved, failed, err, moved_pairs = _merge_into_existing(source_path, target_folder)
                if err:
                    raise OSError(err)
                if failed and not moved:
                    raise FileExistsError(
                        f"All {failed} file(s) already exist in '{target_folder}'"
                    )
                results.append(LibraryMoveFolderResult(
                    folder_name=folder_name,
                    destination=target_folder,
                    success=True,
                    files_moved=moved,
                    files_failed=failed,
                    error=(f"{failed} file(s) skipped — already present" if failed else None),
                    moved_paths=moved_pairs,
                ))
            else:
                os.makedirs(os.path.dirname(target_folder), exist_ok=True)
                shutil.move(source_path, target_folder)
                file_count = sum(
                    1 for n in os.listdir(target_folder)
                    if os.path.splitext(n)[1].lower() in _SORTABLE_EXTENSIONS
                )
                results.append(LibraryMoveFolderResult(
                    folder_name=folder_name,
                    destination=target_folder,
                    success=True,
                    files_moved=file_count,
                    moved_paths=[(source_path, target_folder)],
                ))
        except Exception as exc:
            results.append(LibraryMoveFolderResult(
                folder_name=folder_name,
                destination=target_folder,
                success=False,
                error=str(exc),
            ))

    return LibraryMoveResult(success=True, folders=results, near_misses=near_misses)


def sync_moved_paths_to_db(db, result: LibraryMoveResult) -> dict[str, int]:
    """
    After a move_folders() run, rewrite the DB rows that referenced the old
    on-disk locations so they point at the new ones — BUG-025. Only ever
    touches folders that actually succeeded on disk (`folder.success` and a
    non-empty `moved_paths`); a folder that was blocked/failed keeps its
    original, still-correct paths untouched.

    Commits per folder, not once for the whole run, so a DB-sync failure on
    one folder can't roll back a different folder's already-correct update —
    and so a partially-successful run (some folders moved, some blocked)
    only ever syncs the folders that actually moved.

    Returns {folder_name: issues_updated_count} for the caller to fold into
    its result/log output. Imports are local so this module's top-level
    stays DB-free (the CLI entry point below has no DB access at all).
    """
    from backend.models import CustomTab, HomeStrip, Issue
    from backend.path_utils import is_under, normalize_path

    counts: dict[str, int] = {}

    for folder in result.folders:
        if not folder.success or not folder.moved_paths:
            continue

        try:
            issues_updated = 0
            for old_path, new_path in folder.moved_paths:
                old_n = normalize_path(old_path)
                new_n = normalize_path(new_path)

                for issue in db.query(Issue).all():
                    if is_under(issue.file_path, old_n):
                        issue.file_path = new_n + issue.file_path[len(old_n):]
                        issues_updated += 1

                for tab in db.query(CustomTab).all():
                    if tab.folder_path and is_under(tab.folder_path, old_n):
                        tab.folder_path = new_n + tab.folder_path[len(old_n):]

                for strip in db.query(HomeStrip).all():
                    if strip.folder_path and is_under(strip.folder_path, old_n):
                        strip.folder_path = new_n + strip.folder_path[len(old_n):]

            db.commit()
            counts[folder.folder_name] = issues_updated
        except Exception as exc:
            db.rollback()
            folder.db_sync_error = (
                f"moved on disk but DB sync failed: {exc} — run a rescan to reconcile"
            )

    return counts


def _main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] not in ("series", "singles"):
        print("Usage: python -m backend.library_move <series|singles> <folder>")
        raise SystemExit(1)

    group, folder = sys.argv[1], sys.argv[2]
    result = move_folders(folder, group)

    if result.error:
        print(f"FAILED: {result.error}")
        raise SystemExit(1)

    for f in result.folders:
        status = "OK" if f.success else "FAILED"
        detail = f" ({f.error})" if f.error else ""
        print(f"[{status}] {f.folder_name} -> {f.destination}{detail}")

    if result.near_misses:
        print("\nNear-miss warnings (not moved differently, just flagged):")
        for nm in result.near_misses:
            print(f"  '{nm.folder_name}' looks similar to existing '{nm.existing_match}'")

    moved = sum(1 for f in result.folders if f.success)
    print(f"\n{moved} of {len(result.folders)} folder(s) moved.")


if __name__ == "__main__":
    _main()
