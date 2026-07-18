# ComicVault — Known Bugs Log

Tracks real, currently-open defects. Separate from `SPEC.md` (which is for
applied changes/decisions) and `EDITOR_SPEC.md` (which is for editor-integration
design). Add new entries at the top. **Fixed entries move out of this file** —
see `archive/bugs-fixed-archive.md` (split out 2026-06-29 to keep this file lean;
not version-scoped, since a bug found in one version can get fixed during a later
one).

---

## OPEN

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

---

### BUG-025 — Series move updates the files on disk but not the DB rows pointing at them

**Found:** 2026-07-18, performance re-baseline session (pre-flight).

**Where:** Series move tool (`logs/series_move_log.md` writer); `issues.file_path`,
`custom_tabs.folder_path`.

**What happens:** Moving a series relocates the archives and logs the move as
`[OK]`, but never updates the DB rows referencing the old location. After the
2000 AD move on 2026-07-18 (12:49–13:21), all **2,484** `2000 AD` rows still
had `file_path` under `L:\Comic Archives\20000AD\2000AD Progs - 1977-2026\`,
a directory that no longer existed. A random 400-issue sample found **177 dead
paths (44%), all 2000 AD** — meaning every 2000 AD issue was unopenable until a
rescan. The Folder View custom tab (`custom_tabs.folder_path`) was left
pointing at the same dead path.

**Why a rescan doesn't quietly fix it:** `scanner.scan_single_file()` identifies
an existing row solely by exact path match
(`filter(Issue.file_path == file_path)`) — there's no hash, filename fallback,
or move detection anywhere in `scanner.py`. Files at the new path take the
INSERT branch as brand-new issues, while `scan_library()`'s post-walk sweep
flags the old rows `missing=True` (it only *deletes* rows under `SCAN_EXCLUDE`
folders). A plain rescan after a move therefore yields duplicate issues plus a
matching set of dead rows, with reading progress stranded on the dead ones —
which is what forced the full wipe-and-rebuild in this session.

**Impact — high:** silent, total breakage of a moved series until someone
notices and rebuilds. Scales with how much gets moved at once.

**Related:** BUG-013 (scanner change-detection blind spot — same
identity-by-path-and-mtime assumption).

---

### BUG-016 — Restore Database: restore completes but does not revert DB to backup state

**Found:** 2026-06-28, manual test pass (Items 10–13).

**Where:** Admin page — Restore Database control (`ADMIN_SPEC.md` §9.2),
`backend/routers/admin.py` `POST /admin/restore-database`.

**What happens:** The restore flow appears to complete — confirm dialog fires, the
pre-restore safety snapshot is taken, and the server restarts — but after the restart
the DB is still in the pre-restore (current) state, not the backup state. Test
procedure: backed up the DB with only the 2000 AD custom tab in place; then added a
new 'testdb' custom tab and changed the read status on one issue; then restored the
backup. After the server restarted, the testdb tab and read-status change both
persisted — the DB was not reverted to the backed-up state.

**Note:** The restore code path was not live-exercised during the build session (the
auto-mode classifier declined a live Restore click as a destructive action against the
real DB, per the `progress.md` Item 12 entry). The code was verified by reading
against the existing `/admin/backup` pattern it mirrors. The live test is the first
real exercise of the full copy-and-restart sequence.

**Root cause confirmed 2026-06-28**, by reading `backend/database.py` and
`backend/routers/admin.py` directly — it's the WAL theory, not the path-mismatch
alternative (`db_path` resolves identically in both `restore_database()` and
`run_database_backup()`, ruled out). `database.py` enables
`PRAGMA journal_mode=WAL` on every connection. In WAL mode, recent writes land in a
separate `comicvault.db-wal` sidecar file, not the main `.db` file, until SQLite
checkpoints them. `restore_database()` only does `shutil.copy2(source, db_path)` —
it copies the backup over the main file but never touches the existing `-wal`/`-shm`
files sitting next to it. Sequence: backup taken → testdb tab created + read status
changed (written into the live `-wal` file, not yet checkpointed) → restore copies
the *old* backup over the main file, but the pre-restore `-wal` file is left in
place, still holding those two writes → server restarts → SQLite opens the DB,
finds the existing `-wal` file, and replays its pending writes straight back into
the just-restored main file — silently reintroducing exactly what the restore was
meant to undo. Not a race condition; the `-wal` file is simply never cleared.

**Same mechanism likely also affects backups themselves, not just restores
(unconfirmed):** `run_database_backup()` also does a plain `shutil.copy2` with no
checkpoint step first. SQLite auto-checkpoints periodically, so a backup usually
catches everything in practice — but there's no guarantee a very recent write has
been checkpointed out of the WAL at the exact moment a backup runs. Worth checking
once the restore fix below is in, since the same checkpoint fix would cover both.

**Impact — high:** Restore Database is the safety net for Clear Database and any
other destructive action, and it does not work at all if there's been any activity
since the backup was taken. It fails silently — no error, a normal "Database
restored, restarting" response — nothing in the UI suggests anything went wrong.
Until fixed, treat Restore Database as unreliable for anything beyond the most
trivial case (a backup taken seconds after server startup with zero activity since).

**Recommended fix:** before copying the backup over `db_path` in
`restore_database()`, force a checkpoint and clear the existing WAL state — either
`PRAGMA wal_checkpoint(TRUNCATE)` on the live connection followed by deleting any
remaining `db_path.with_suffix('.db-wal')`/`-shm` files, or simply delete those two
sidecar files outright once the process has been told to exit (`_schedule_delayed_exit()`
already tears it down immediately after). Apply the same checkpoint step to
`run_database_backup()` if the backup-side risk above is confirmed.

**Not fixed.**

---

### BUG-013 — Scanner doesn't detect a same-mtime, different-size file change

**Found:** 2026-06-24, v2.3 Item 7 build session (confirming ADMIN_SPEC.md §8's
open TODO about "changed" file semantics before building the scan log cards).

**Where:** `backend/scanner.py`'s `scan_single_file()` — the unchanged-file skip
check (~lines 475-487) compares only the file's mtime against
`Issue.date_modified`, with a 1-second tolerance. A CBZ re-saved/re-compressed
with the same content but a preserved or coincidentally-identical mtime (and a
different file size) will be silently skipped — `scan_progress`/the new
`changed_files_log.md` will never see it as "updated".

**Impact:** Low — this requires a tool that rewrites a CBZ without touching its
mtime, which is unusual but possible (e.g. some batch re-compression tools
preserve timestamps by default). Confirmed by direct code reading, not by
reproducing the actual scenario live.

**Not fixed** — out of scope for Item 7 (which only needed to document, not fix,
the scanner's actual "changed" semantics before building the log format around
them). A real fix would mean comparing file size (or a cheap hash) in addition
to mtime — flagged here as a candidate for a future scanner-accuracy pass.
