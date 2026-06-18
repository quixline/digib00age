# ComicVault — Known Bugs Log

Tracks real defects found during development, separate from `SPEC.md` (which is for
applied changes/decisions) and `EDITOR_SPEC.md` (which is for editor-integration design).
Add new entries at the top. Mark fixed entries with the date and what was changed.

---

## OPEN

(none currently)

---

## FIXED

### BUG-001 — Scanner skips thumbnail generation for unchanged-mtime files, even if the thumbnail file is missing

**Found:** 2026-06-18, during V2 migration setup.

**Where:** `backend/scanner.py`, incremental scan logic (~line 419), "skip if unchanged"
branch based on `date_modified` comparison against the DB.

**What happens:** The scanner only generates a thumbnail on the new-file or
updated-file branches. If a file's `date_modified` in the DB already matches its
on-disk mtime, the scanner skips it entirely — including thumbnail generation — even
if no thumbnail file actually exists on disk for that issue.

**How it surfaced:** V2 was set up from a copied database (`comicvault.db` copy) but
without copying `thumbnails/` (deliberately, since thumbnails are gitignored and
assumed regenerable). Every file's `date_modified` in the copied DB still matched disk
mtime, so the scan treated all 5,429 files as "skipped" and none of them got a
thumbnail — `thumbnails/` was left at 0 files despite a full scan reporting 0 errors.

**Why it matters beyond this one case:** This isn't specific to the migration. Any
future scenario where the DB is restored/copied without its thumbnails — backup
restore, disk recovery, fresh deploy from a DB dump — will hit the same silent gap.
The scan reports success (0 new, 0 updated, 0 errors) with no indication that cover
art is missing.

**Proper fix (applied 2026-06-18):** The skip-if-unchanged branch in `scan_single_file`
now checks whether the expected thumbnail file (`{issue.id}.jpg`) exists on disk before
skipping. If missing, it calls `_generate_thumbnail` and updates `cover_path` even
though the DB row's metadata is otherwise unchanged — the file still counts as
"skipped" in scan stats, it just no longer silently leaves a missing thumbnail behind.

Applied to **V2 only** (`comicvault_v2/backend/scanner.py`). V1's `scanner.py` is
unmodified — V1 is being kept as-is and is not being changed going forward.

**Workaround applied for V2's existing data (does not by itself fix the bug):** Cleared
`date_modified` for all rows in `comicvault_v2.db` only (V1 untouched), then re-ran the
scan so every file was treated as updated and thumbnails generated. This got V2's
existing copied DB into a correct state; the scanner fix above is what prevents the
same gap from recurring on any future DB copy/restore.

**Verification:** Deleted one issue's thumbnail file manually, ran a scan — confirmed
only that issue regenerated its thumbnail while the rest of the library (5,428 other
issues, unchanged, thumbnails present) was still skipped quickly. Full-library scan
timing was unaffected by the fix (~5 seconds for all 5,429 files, matching pre-fix
skip-path timing).

**Status:** Fixed in V2. V1 retains the original (unfixed) logic by design.
