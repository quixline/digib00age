# ComicVault — Known Bugs Log

Tracks real defects found during development, separate from `SPEC.md` (which is for
applied changes/decisions) and `EDITOR_SPEC.md` (which is for editor-integration design).
Add new entries at the top. Mark fixed entries with the date and what was changed.

---

## OPEN

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
defect class was already found and fixed twice in `comicvault-changes-2.1.md`'s
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
Related to `comicvault-changes-v2.3.md` Item 14 (header unification) — same
mechanism, worth sequencing together rather than fixing this in isolation again.

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

### BUG-010 — 2000 AD writer credit link doesn't filter the issue list

**Found:** 2026-06-23, inbox triage.

**Where:** Issue page for a 2000 AD-tagged issue (e.g. year 1979, issue #174) — clicking
a writer's series card (e.g. "2000 AD — writer in 1104 issues + 7 singles") opens the
full 2000 AD prog run, not a list filtered to issues credited to that writer.

**Impact:** The writer series card states correct totals (counts appear right) but the
click-through doesn't filter — it shows the full series, making the writer's credit
link functionally useless for browsing their specific contributions.

**Not fixed.**

---

### BUG-009 — Star rating doesn't clear to Unrated

**Found:** 2026-06-23, inbox triage.

**Where:** Issue page (`/issue/{id}`) star rating row.

**Impact:** Clicking an already-highlighted star (i.e. the current rating) should drop
the rating to Unrated (NULL). Currently it floors at 1 star — once any rating is set,
there's no way to return to Unrated via this interaction.

**Addendum, 2026-06-27 (inbox capture):** the multi-select toolbar's `✕` "Clear
rating" button (added 2026-06-26, Fix 2) already covers the bulk-selection case.
This bug is specifically about the single-issue page (`/issue/{id}`) star row,
where the desired fix is: clicking an already-highlighted star a second time clears
the rating to Unrated — same gesture, no separate control needed.

**Fixed, 2026-06-29.** `frontend/js/app.js`'s `buildRatingControl()` star click
handler now checks whether the clicked star's value already equals
`data.personal_rating`; if so it sends `rating: 0` instead of the star's value
(reusing the same `POST /api/progress/bulk/rate` endpoint the multi-select toolbar's
clear button already uses — that endpoint already accepted `0` as "clear", per its
existing `BulkRating` validator in `backend/routers/progress.py`, no backend change
needed). Verified directly against `/api/progress/bulk/rate` on a scratch-state real
issue (#1, originally unrated): rate→3 confirmed 3, then rate→0 (the same call the
new click handler now makes when re-clicking star 3) confirmed back to 0/null —
issue left in its original unrated state afterward.

---

### BUG-008 — Flutter app's 2000 AD tab calls endpoints removed in v2.2

## Edit 29/6/26 Tez; the fixed 2000 AD tab has been removed completely - Custom tabs
## This issue could be dead.

**Found:** 2026-06-22, flagged by the nightly doc scan.

**Where:** `flutter_app/lib/screens/two_thousand_ad_screen.dart` —
`TwoThousandAdTab` calls `GET /api/2000ad/years`; `TwoThousandAdYearScreen` calls
`GET /api/2000ad/year/{year}`. Both endpoints were removed in v2.2 (Part A,
`backend/routers/home.py`).

**Impact:** The Flutter app's 2000 AD tab would return 404 errors on those calls.
The web-side 2000 AD surface was removed intentionally and its behaviour generalised
into Folder View (Custom Tabs, `CUSTOM_TABS_SPEC.md` §9), but Flutter was explicitly
out of scope for v2.2 — the Flutter tab was not replaced, just left broken.

**Not fixed.** Flutter app development is on hold until web-side work is complete
(per `ROADMAP.md`). To be picked up as part of that Flutter work — fix would be
either removing the 2000 AD tab from the Flutter app, or adding a Folder View
equivalent for Flutter once the web Folder View is settled.

---

---

## FIXED

---

### BUG-007 — Basic Editor's multi-line textarea fields (Summary) round-trip with doubled line breaks on every save

## 

**Found:** 2026-06-21, incidentally — while verifying Tier 4 Item 3's editor fuzzy-
warn-on-save feature against a real issue (`2000AD #011 (1977)`), saving the form
(which submits every field, not just the one being tested) revealed that the
`Summary` field's blank lines double on every save: a single blank line between
paragraphs (`\n\n` in the original XML) becomes a doubled blank line (`\n\n\n\n`,
confirmed on-disk as literal `\r\r\n` sequences) after going through the Basic
Editor's save flow once. Re-saving again would presumably double it further each
time.

**Where:** `frontend/js/editor_basic.js` `onEditorSubmit()` (collects the `<textarea>`
value via `FormData`) → `backend/editor/field_merge.py` `build_xml_from_fields()`
(merges it into the XML). Not yet root-caused precisely — likely the browser's
textarea-to-FormData line-ending normalization (`\n` → `\r\n`) combined with
`field_merge.py` independently adding its own line separator when writing the
`<Summary>` tag, compounding on each save.

**Impact:** Any issue whose Summary is edited and saved through the Basic Editor
gets visually-doubled blank lines in its description, worsening on repeated saves.
Purely cosmetic (doesn't affect parsing — `_text()` still extracts the full string
correctly either way) but degrades readability over time. Pre-existing — unrelated
to Tier 4 Item 3, not introduced by it, just exposed by testing that happened to
touch a real issue. Not fixed in this session (out of scope for Item 3's no-ride-
alongs framing) — flagging per session convention.

**Fixed.** - Can't reproduce the double line issue. Tez; 29/6/26
(A future session should: confirm the exact mechanism (check whether
`field_merge.py` adds `\r\n` on top of an already-`\r\n`-converted textarea value),
then normalize line endings once, consistently, rather than compounding them.)

---

### BUG-011 — Admin "Scan Roots" Add button doesn't open file dialog

**Found:** 2026-06-23, inbox triage.

**Where:** Admin page — "Add" button under Scan Roots / Library Folders section.

**Impact:** Clicking "Add" should open a folder/file picker dialog so a new scan root
can be added. Currently does nothing. Admin page is otherwise functional; existing
scan roots still work.

**Fixed.** Not actually a Bug - Clicking Add after manually entering a new scan location Adds it to the list - misunderstanding of function not error in function; Tez 29/6/26

---

### BUG-012 — Library fails to initialise after changing theme in Admin, then navigating back

**Found:** 2026-06-23, manual test pass during v2.3 Item 3 (card behaviour additions).

**Where:** Library page (`/`), right after switching the Admin → Appearance theme
setting and navigating back to the library.

**Impact:** Library shows "Failed to initialise. Cannot read properties of null
(reading 'addEventListener')" with a Retry button, instead of loading normally.
`initLibrary()`'s catch block (`frontend/js/app.js`) is catching a `null.addEventListener`
call from one of `bindSurfaceNav()`/`bindFilterEvents()`/`bindSearchEvents()` — exactly
which element was null isn't confirmed yet. A hard refresh cleared it immediately, and
repeating the theme switch + back-navigation afterward did not reproduce it — so this
looks like a one-time/intermittent state issue (possibly browser back/forward-cache
restoring a stale DOM, or a race between the new theme anti-flash inline script and
the rest of page load), not a deterministic break in the new theme code itself.

**Fixed** — No issues found when changing theme; Tez 29/6/26

---

### BUG-003 — Dead duplicate route: `GET /api/reading/continue` defined twice

**Found:** 2026-06-19, while building the Home Strips feature (`HOME_STRIPS_SPEC.md`)
and tracing how "Continue Reading" was resolved before folding it into the unified
`GET /api/home/strips` endpoint.

**Where:** The route was defined in both `backend/routers/progress.py` (line ~219) and
`backend/routers/library.py` (line ~631) — identical path, same query intent, slightly
different implementation. `main.py` registers `library.router` before `progress.router`,
so `library.py`'s version always won; `progress.py`'s copy was unreachable dead code.

**Impact:** None — the live version (`library.py`) was correct throughout and is what
the Flutter app calls. Purely a maintenance hazard: a future edit to the dead copy
would have silently done nothing.

**Fixed:** 2026-06-27 — removed the unreachable duplicate (`get_continue_reading`) from
`backend/routers/progress.py`. `library.py`'s `reading_continue` remains the sole
implementation; no behaviour change since it was already winning registration order.

---

### BUG-006 — CSV-splitting helpers didn't dedupe a literal repeated name within one field

**Found:** 2026-06-21, while scratch-testing the Tier 4 Item 3 migration (Writer/
Artist entity dedup) against a copy of the real DB, before the real run.

**Where:** `backend/scanner.py`, `_split_csv()` (used by both `_genres()` and the
new `_credits()`/`_sync_credits()` added for Item 3).

**What happened:** Some real `ComicInfo.xml` Penciller/Inker fields contain a
literal repeated name, e.g. `"Chris Shehan, Maan House, Chris Shehan, Maan House"` —
175 issues affected (114 penciller + 61 inker) across the real library. Splitting
this CSV without deduplicating produced two identical entries, which crashed the new
Person/IssueCredit migration with a `UniqueConstraint` violation on
`(issue_id, person_id, role)` the moment it hit the first affected issue.

**Impact before the fix:** would have crashed `scan_single_file()`'s credit-sync on
any of these 175 issues going forward, not just the one-time migration — same
crash risk existed latently in `_sync_genres()`'s composite-PK insert for Genre,
just never triggered (zero real issues currently have a duplicated Genre value).

**Fix:** `_split_csv()` now deduplicates (order-preserving, via `dict.fromkeys`)
after stripping. Fixes both the credit-sync path and defensively covers Genre's
identical latent vulnerability. `backend/migrate_people.py`'s own independent
CSV-splitting (it doesn't go through `scanner._split_csv`, which operates on XML
elements, not arbitrary DB-stored strings) got the same fix applied separately,
including a second dedup pass *after* resolving through the merge-decision map,
since two different raw names can collide onto the same canonical name post-merge.

**Status:** Fixed in `scanner.py` and (separately) `migrate_people.py` before the
real migration ran. Verified by re-running the migration against the same 175
affected issues afterward with no errors.

---

### BUG-005 — New bulk progress endpoint swallowed by an existing route's path pattern

**Found:** 2026-06-21, while live-testing the new bulk endpoints for Tier 4 Item 2
(Multi-select + Favorites/Rating) against a scratch copy of the real DB, before the
frontend ever touched them.

**Where:** `backend/routers/progress.py` — the new `POST /api/progress/bulk/mark-read`
was registered *after* the existing `POST /api/progress/{issue_id}/mark-read`.

**What happened:** Both routes are two path segments after `/progress/`. Starlette
matches registered path templates in order and returns the first structural match
regardless of whether type conversion succeeds — `/progress/bulk/mark-read` matched
`/progress/{issue_id}/mark-read` first, with `issue_id` bound to the string `"bulk"`,
which failed `int` parsing and returned a 422 instead of ever reaching the new bulk
endpoint. Same collision applied to `bulk/mark-unread` against
`{issue_id}/mark-unread`. (`bulk/favorite`, `bulk/unfavorite`, `bulk/rate` were
unaffected — no existing route shares that suffix.)

**Fix:** Moved the new bulk route registrations (and their `BulkIssueIds`/`BulkRating`
request models) above the existing `/progress/{issue_id}/mark-read` /
`/mark-unread` routes in the same file, with a comment explaining why the ordering
matters. Re-verified both the new bulk routes and the pre-existing single-issue routes
work correctly via curl against the scratch server afterward.

**Status:** Fixed in `progress.py`. General hazard worth remembering for any future
route added under an existing `{param}/...` path: a new literal-segment route needs to
be registered *before* a parameterized route it could collide with, not just given a
different-looking name.

---

### BUG-004 — Tray app shows "Start ComicVault at login" ticked but server doesn't start on login; manual Start also fails

**Found:** 2026-06-19, first login after an OS restart following the prior session's
tray app changes (split Stop/Start, add Close, dark menu, login autostart toggle —
commit `6fc1840`). That session's testing was done but the OS restart + fresh login
happened afterward, outside the tested window.

**What happened:** Tray app started automatically at login as expected, and the
"Start ComicVault at login" menu item correctly showed as ticked. However the backend
server subprocess kept exiting immediately. Manually invoking Start from the tray menu
also failed — not a tray-app or autostart bug at all.

**Root cause — not in ComicVault's code.** `tray/reader_stdout.log` showed the actual
uvicorn error on every restart attempt:
`ERROR: [Errno 13] ... [winerror 10013] an attempt was made to access a socket in a
way forbidden by its access permissions` when binding `0.0.0.0:8000`.
`netsh interface ipv4 show excludedportrange protocol=tcp` confirmed port 8000 fell
inside a Windows TCP port-exclusion range (`7981–8080`) — `netstat` showed nothing
actually listening on 8000, i.e. Windows itself was refusing the bind, not a
competing process. `hns`/`vmms`(Hyper-V)/`WSL Service` were all running on this
machine; WSL2/Hyper-V's networking stack reserves blocks of TCP ports for NAT at
boot, and on this particular boot the reserved block happened to swallow port 8000.
This explains why manual Start also failed: it's an OS-level bind refusal, independent
of how the process is launched.

**Fix applied this session:** Restarted the `winnat` service (`net stop winnat` /
`net start winnat`) to force Windows to recompute its port-exclusion ranges. Confirmed
8000 was no longer excluded afterward, and the tray app's own health-check loop
(30s interval) picked this up on its next retry without any further action — log
shows `Reader server is up.` at 18:46:28, `netstat` confirmed `0.0.0.0:8000 LISTENING`,
and `GET /api/admin/stats` returned 200.

**Not a recurring code defect, but a recurring environmental risk:** any future
reboot can reproduce this if WSL2/Hyper-V's networking service happens to claim a
range overlapping port 8000 again. There is no permanent code-level fix being applied
in this session (would require either changing ComicVault's port to one outside
commonly-claimed ranges, or scripting a winnat restart into the startup sequence —
neither attempted here; flagging as a possible `ROADMAP.md` item rather than doing it
under this bug ticket).

**Status:** Resolved for this session by restarting `winnat`. Tray app and
`start_server.py` both behaved correctly throughout — no code changes were needed or
made.

---

### BUG-002 — Full Editor's Queue button stayed disabled for any file whose existing Genre/Format/AgeRating wasn't already enforced-valid

**Found:** 2026-06-18, during Tez's first manual test pass after the Full Editor build.

**Where:** `frontend/js/editor_full.js`, `updateValidityGate()` (now renamed
`updateActionButtonStates()`).

**What happened:** Queue (and Process All) were gated on the same Genre/Format/
AgeRating validity check as the Basic Editor's Save button. For any loaded file whose
current values didn't already pass (e.g. a genre like "Zombie" not in the enforced
list — the exact kind of file the pre-migration report exists to flag), Queue was
disabled immediately on focus, before Tez had a chance to fix anything. Reported as
"the Queue button is dead."

**Root cause:** `EDITOR_SPEC.md` Section 4.4 ("Existing-value mismatch behaviour") is
explicitly titled **Basic Editor only** — the hard validation gate was never meant to
apply to Full Editor. It got carried over by extension when building Full Editor's
form, which shares the same field markup/JS patterns as Basic Editor's popup.

**Fix:** Queue is now only gated on whether a file is focused; Process All only on
whether any files are loaded; Process Queue only on whether the queue is non-empty.
Validity enforcement for Full Editor happens server-side at process time only
(`backend/editor/validation.py`, already in place) — invalid fields are reported as
per-file errors without aborting the rest of the batch, matching the intended
workflow (queue first, fix fields, process after). The now-pointless
genre/format/agerating `change` listeners that only existed to re-run this check were
removed.

**Status:** Fixed in `editor_full.js`. Basic Editor's Save button is unaffected — its
gate is correctly scoped per Section 4.4.

---

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
