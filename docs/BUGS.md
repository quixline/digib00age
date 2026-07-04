# ComicVault — Known Bugs Log

Tracks real, currently-open defects. Separate from `SPEC.md` (which is for
applied changes/decisions) and `EDITOR_SPEC.md` (which is for editor-integration
design). Add new entries at the top. **Fixed entries move out of this file** —
see `archive/bugs-fixed-archive.md` (split out 2026-06-29 to keep this file lean;
not version-scoped, since a bug found in one version can get fixed during a later
one).

---

## OPEN

### BUG-020 — Flutter app crashes when selecting a CBZ on the tablet

**Found:** 2026-07-04, OPDS/3rd-party-reader scoping session — Tez reported the
app has been in this state "a while," not caught earlier because all recent
attention was on server/web dev, not Flutter.

**Where:** Not yet diagnosed — likely `reader_screen.dart` / `comic_page_view.dart`
or the file-open path feeding them, but not confirmed against the code yet.

**What happens:** Selecting a CBZ on the Android tablet crashes the app. No stack
trace or repro steps captured yet beyond "select a CBZ, it crashes."

**Relationship to BUG-019 and BUG-008:** three separate-looking Flutter problems
surfaced in the same report (this crash, the now-fixed connection failure —
`archive/bugs-fixed-archive.md` — and the stale 2000 AD tab). Not assumed to
share a root cause — could be one underlying issue or three independent ones.
Needs its own diagnosis pass, not folded into BUG-019 by assumption. BUG-019's
fix didn't touch anything in the CBZ-open path, so this crash is still
unexplained and open on its own.

**Not fixed.** Full diagnosis and fix scoped as the next session's focus (see
`ROADMAP.md` and `docs/v2.5/progress.md`).

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

### BUG-015 — Genre field-view filter (`?surface=fieldview&field=genre&value=X`) has no UI way to clear, and survives back-navigation incorrectly

**Found:** 2026-06-27, inbox capture.

**Where:** Selecting a genre from an issue page correctly navigates to a filtered
field-view (`/?surface=fieldview&field=genre&value=Comedy`). From there:
- The Genre dropdown on that filtered view still shows "Genre" (not the active
  value "Comedy"), so it doesn't visibly reflect the active filter.
- Selecting a different tab changes the surface but leaves the genre filter and URL
  value untouched underneath.
- Selecting a different genre from the dropdown, then resetting via "Genre" in the
  dropdown, does visually reset the displayed list — but the URL itself still says
  `value=Comedy`.
- Because of that stale URL, opening an issue/series from the (visually reset) list
  and then pressing back restores the Comedy-filtered view, since back-navigation
  re-reads the (never-actually-cleared) URL.

**Impact:** No reliable way to fully clear a field-view genre filter via the UI once
set — dropdown state, displayed list, and URL state can all disagree with each
other simultaneously.

**Not fixed.**

---

### BUG-014 — Back-button regression: returns to Home instead of the originating tab

**Found:** 2026-06-27, inbox capture (3 repro cases reported across two separate
inbox lines).

**This is a long-running problem area, not a one-off.** Tez notes this `← Back`
behaviour "has been buggy from the start, various solutions" — the exact same
defect class was already found and fixed twice in `archive/comicvault-changes-2.1.md`'s
Tier 1 ("Back button inconsistency" — first fix 2026-06-21, a follow-up correction
2026-06-22 after the first fix turned out to miss Issue/Series detail pages). That
fix replaced hardcoded/guessed-destination back links with real `history.back()` +
a literal "Back" label.

**Root cause identified 2026-06-27 (confirmed by reading `app.js`/`issue.html`/
`series.html` directly, while scoping `comicvault-changes-v2.3.md` Item 14):** the
2026-06-21/22 fix is still in place and working as designed — `initIssue()`/
`initSeries()` both correctly call `window.history.back()`. The actual problem is
upstream: the four main surface tabs (Home/All/Singles/Series, `bindSurfaceNav()`)
never call `pushState` when switching — they only update a JS variable, so the URL
stays bare `/` no matter which tab is active. Folder View *already* solves this
correctly via `pushFolderViewUrl()` → `history.pushState()` on every drill-down
(explicitly documented in `app.js` as "a deliberate departure from the simpler
`history.back()`-only pattern used elsewhere") — that pattern was just never
extended to the four main tabs. Sequence: user on All (URL still `/`) → opens an
issue → real navigation pushes `/issue/123` onto history → Back → browser
correctly returns to the literal previous entry, bare `/` → page loads defaulting
to Home, since nothing in the URL says otherwise.

The `?from=all`/`?from=series`/`?from=singles` query params seen in the URLs below
are a red herring — still being attached when card links are built
(`buildCoverCard()` etc. in `app.js`), but already dead code: both detail pages'
back-links stopped reading `from=` when they switched to real `history.back()`.

**Recommended fix:** extend Folder View's existing `pushState` pattern to the four
main surface tabs (Home/All/Singles/Series), so the URL always reflects the active
tab. Once in place, the dead `from=` param construction can be removed as cleanup.
Related to `ROADMAP.md`'s "Blocked on Claude Design UI redesign exploration" entry
(header unification) — same mechanism, worth sequencing together rather than fixing
this in isolation again.

**Where — three repro cases, all landing on Home instead of the expected tab:**
- `/issue/{id}?from=all` (e.g. `/issue/2769?from=all`) — expected All
- `/series/{id}?from=series` (e.g. `/series/2589?from=series`) — expected Series
- `/issue/{id}?from=singles` (e.g. `/issue/5478?from=singles`) — expected Singles

**Impact:** Back navigation from any of these pages drops the user on Home instead
of the tab they actually came from, despite the URL explicitly carrying a `from=`
param that should make the correct destination unambiguous.

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

---

### BUG-008 — Flutter app's 2000 AD tab calls endpoints removed in v2.2

**Reactivated 2026-07-04:** Flutter dev is starting next session (mobile
connectivity fix, per `ROADMAP.md`), so the 2026-06-29 "ignore until Flutter dev
starts (if it starts)" note no longer applies. This is now in-scope. Not assumed
to be the cause of BUG-019/BUG-020 above — it's a known-broken tab calling
removed endpoints, a separate problem from a connection or CBZ-select crash —
but it needs fixing in the same pass since it touches the same screen set, and
the fix now has a real destination: Custom Tabs (`CUSTOM_TABS_SPEC.md` §9),
which didn't exist yet when this bug was first found.

**Found:** 2026-06-22, flagged by the nightly doc scan.

**Where:** `flutter_app/lib/screens/two_thousand_ad_screen.dart` —
`TwoThousandAdTab` calls `GET /api/2000ad/years`; `TwoThousandAdYearScreen` calls
`GET /api/2000ad/year/{year}`. Both endpoints were removed in v2.2 (Part A,
`backend/routers/home.py`).

**Impact:** The Flutter app's 2000 AD tab would return 404 errors on those calls.
The web-side 2000 AD surface was removed intentionally and its behaviour generalised
into Folder View (Custom Tabs, `CUSTOM_TABS_SPEC.md` §9), but Flutter was explicitly
out of scope for v2.2 — the Flutter tab was not replaced, just left broken.

**Not fixed.** Fix would be either removing the 2000 AD tab from the Flutter app,
or adding a Custom Tabs equivalent for Flutter now that the web-side feature is
built and settled — to be decided during next session's scoping pass, not here.
