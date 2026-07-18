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

---

### BUG-027 — No safe way to reset the DB: Clear Database can only be run against a live server

**Found:** 2026-07-18, performance re-baseline session (pre-flight).

**Where:** Admin page — Clear Database (`ADMIN_SPEC.md` §9), tray app
Stop/Start Server.

**What happens:** There is no supported sequence for wiping and rebuilding the
library. The safe-looking order — stop the server, then wipe — isn't available
to Tez in practice: stopping the reader server takes the Admin page down with
it, and Clear Database *is* an Admin page control, so stopping the server
removes the only means of triggering the wipe. The wipe therefore has to be
performed against a live server holding open connections to the DB it's
clearing. That worked this time (verified: all library tables at 0 rows,
`custom_tabs`/`home_strips` intact), but it's unverified as a general
guarantee, and it interacts badly with BUG-016's WAL findings — a 9MB
`-wal` sidecar was sitting next to the cleared DB immediately afterwards.

**Impact — medium:** the operation people reach for precisely when the DB is
already in a bad state is the one with no clean execution path. Also blocks
any workflow that needs a guaranteed-quiescent DB (a cold-start performance
baseline, a trustworthy backup, a schema migration).

**Scope — needs its own session.** Probable shape: a server-side reset that
quiesces writes, checkpoints/clears the WAL (shares the fix surface with
BUG-016), clears the tables, disposes derived data (BUG-026), and either
restarts itself cleanly or rescans — rather than leaving the caller to
sequence a stop/wipe/start dance that isn't actually sequenceable from the UI.

---

### BUG-026 — Clear Database only clears DB rows; derived data on disk is left orphaned

**Found:** 2026-07-18, performance re-baseline session.

**Where:** Admin page — Clear Database (`ADMIN_SPEC.md` §9),
`backend/routers/admin.py`; `backend/thumbnails/`.

**What happens:** Clearing the database empties the library tables but leaves
everything derived from them on disk. Measured immediately after a successful
clear (issues/credits/genres/people/reading_progress all at 0 rows):
**7,904 thumbnail files, 354MB, still present in `backend/thumbnails/`** — all
of them orphaned, since the next scan assigns fresh issue IDs that won't match
any existing `{id}.jpg`. The DB file itself also isn't reclaimed: 4,652 of
4,677 pages were freelist (~99.5% empty) and the file stayed at 19.2MB, since
nothing runs `VACUUM`.

**Contributing history:** the thumbnail count was already inflated *before*
this clear — 7,904 files against 5,424 issues, where the 2026-07-09
performance baseline recorded a near-exact 5,436-for-5,427. The ~2,480 excess
matches the 2000 AD series count, i.e. an earlier re-add of that series
regenerated thumbnails under new IDs and orphaned the previous set. So this
leaks on ordinary re-add paths too, not only on an explicit clear.

**Impact — medium:** unbounded disk growth across the exact operations meant
to reset state, and it makes "is thumbnail coverage healthy?" unanswerable by
counting files — a check the 2026-07-09 baseline relied on.

**Scope — needs its own session,** per Tez 2026-07-18: define what "wipe"
should actually cover (thumbnails certainly; also consider scan logs,
`log_last_viewed` config timestamps, `next_processing_run`), whether it's
opt-in or unconditional, and whether a `VACUUM` runs afterwards.

