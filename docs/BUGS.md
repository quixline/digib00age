# ComicVault — Known Bugs Log

Tracks real, currently-open defects. Separate from `SPEC.md` (which is for
applied changes/decisions) and `EDITOR_SPEC.md` (which is for editor-integration
design). Add new entries at the top. **Fixed entries move out of this file** —
see `archive/bugs-fixed-archive.md` (split out 2026-06-29 to keep this file lean;
not version-scoped, since a bug found in one version can get fixed during a later
one).

---

## OPEN

### BUG-029 — Scanner has no rename/move detection; a renamed file creates a duplicate row and leaves the old one an orphaned "missing" entry forever

**Found:** 2026-07-18, during BUG-013's fix-verification session — surfaced by a
real pre-existing example already sitting in the dev DB: issue IDs 1-4
(`'68 Homefront`) still have `file_path` pointing at a bracket-style folder name
(`[2014]`) that was renamed to parentheses (`(2014)`) at some point, with
`missing` still `False` on all four rows. This is also the scenario BUG-025's
investigation traced back to "BUG-013's territory" before BUG-013 was split in
two on closeout (see `archive/bugs-fixed-archive.md`) — this entry is the
correct home for it going forward.

**Where:** `backend/scanner.py`'s `scan_single_file()` / `scan_library()` — the
only match key for "is this file already in the DB" is exact `Issue.file_path`
string equality (~line 479); no content hash, filename fallback, or move
detection anywhere.

**What happens:** Renaming or moving a file that's already scanned into the
library — a plain on-disk rename, or any tool that changes the path without
going through this app's own move-and-relink flow — makes the scanner treat
the new path as a brand-new issue on the next scan (fresh INSERT, new ID,
regenerated thumbnail, reading progress reset), while the old row's path is no
longer found on disk and just gets flagged `missing = True` — never deleted,
by design (`scanner.py` never runs DELETE outside `SCAN_EXCLUDE`-folder
cleanup). The orphaned row then sits there indefinitely unless someone
manually runs the admin-only `cleanup-missing` endpoint.

**Impact — low/medium:** doesn't corrupt data or crash anything, but silently
accumulates dead rows and duplicate issues over time on any manual
reorganization outside the app's own Move Series/Singles Folders tool, and
reading progress on the original row is stranded when this happens (same
failure shape as BUG-025, minus that bug's Stage-3 safeguard).

**Not fixed** — split out from BUG-013 2026-07-18 to keep that fix's scope to
the mtime/size check it actually addressed. A real fix likely means matching
by something more durable than exact path (content hash, or a lightweight
"did file_path X disappear and file_path Y appear with the same size/hash this
scan" heuristic) — candidate for a future scanner-accuracy pass, same family
BUG-013 was in.


