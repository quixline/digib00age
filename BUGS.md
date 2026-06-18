# ComicVault — Known Bugs Log

Tracks real defects found during development, separate from `SPEC.md` (which is for
applied changes/decisions) and `EDITOR_SPEC.md` (which is for editor-integration design).
Add new entries at the top. Mark fixed entries with the date and what was changed.

---

## OPEN

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

**Proper fix (not yet applied):** The skip-if-unchanged branch should also check
whether the expected thumbnail file exists on disk, not rely on `date_modified` alone.
If the thumbnail is missing, generate it even when the DB row is otherwise unchanged.

**Workaround applied for V2 (does not fix the bug):** Cleared `date_modified` for all
rows in `comicvault_v2.db` only (V1 untouched), then re-ran the scan so every file was
treated as updated and thumbnails generated. This is a one-off fix for the copied DB,
not a fix to `scanner.py` — the underlying logic flaw remains and will recur the next
time a DB is restored/copied without thumbnails.

**Status:** Workaround applied to `comicvault_v2.db`. Scanner logic itself still needs
the proper fix — candidate for EDITOR_SPEC.md build phase or a dedicated small fix
pass, not blocking current work.

---

## FIXED

(none yet)
