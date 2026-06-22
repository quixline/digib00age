# ComicVault — Build Progress Log

All development completed on 2026-06-12.

---

## Phase 1 — Scanner + Database

**Goal:** Walk the comic library, parse metadata, write to SQLite.

- Defined `config.json` as the single source of truth for all paths and ports. Nothing hardcoded anywhere.
- Built `backend/models.py` — SQLAlchemy ORM for `issues`, `issue_genres`, and `reading_progress` tables.
- Built `backend/database.py` — session management, `init_db()` to create tables on first run.
- Built `backend/scanner.py` — walks `L:\Comic Archives\` recursively, opens each CBZ as a zip, parses `ComicInfo.xml`, falls back to filename parsing if XML is absent or corrupt.
  - Incremental scan: INSERT new, UPDATE changed, flag missing — never deletes rows.
  - Generates cover thumbnails via Pillow (first image in CBZ, resized to configured width).
  - Format group (`Series` / `Singles`) detected from folder path, not XML.
- Fixed bare-import issues — all `backend/` modules must use `from backend.xxx import` when running under `uvicorn backend.main:app`.

---

## Phase 2 — REST API

**Goal:** Expose library data and file serving over HTTP.

- Built `backend/main.py` — FastAPI app with CORS open for home network access.
- Built `backend/routers/library.py` — `/api/library`, `/api/series/{id}`, `/api/issue/{id}`, `/api/search`, `/api/browse/*`.
- Built `backend/routers/reader.py` — `/api/page/{issue_id}/{page_number}` (extracts single page from CBZ on demand), `/api/cover/{issue_id}`, `/api/issue/{id}/pages`.
- Built `backend/routers/progress.py` — `POST /api/progress/{issue_id}`, mark-read, mark-unread endpoints.
- Built `backend/routers/admin.py` — `/api/admin/stats`, `/api/scan`, `/api/scan/file`, `/api/admin/backup`.
- Removed dead `/reader/{issue_id}` route that referenced a `reader.html` never built.

---

## Phase 3 — Web Library UI

**Goal:** Browser-based library browser accessible from any device on the home network.

- Built `frontend/index.html` — library home with Series/Singles tabs, cover grid, unread badges, continue-reading strip.
- Built `frontend/series.html` — series detail with issue list, story arc grouping, mark-all-read.
- Built `frontend/css/style.css` — dark theme, responsive grid.
- Built `frontend/js/app.js` — all library + series page JS.
- Publisher, Genre, and Year filters implemented. Format filter deferred (backend library response does not include per-series format value).

---

## Phase 4 — Issue Detail Page

**Goal:** Complete the web browsing flow and wire up the Flutter deep link.

- Built `frontend/issue.html` — cover, full metadata, credits block, story arc, characters.
- **Read button** fires `comicvault://read/{issue_id}` — opens directly in the Flutter app.
- Mark read / unread toggle calls `POST /api/progress/{id}`.

---

## Phase 5 — Flutter App (Android + Windows)

**Goal:** Native installed app for reading comics on Android tablet and Windows desktop.

### App architecture
- Single Flutter project (`flutter_app/`) builds both Android APK and Windows exe.
- Dark Material 3 theme throughout.
- Named routes: `/` LibraryScreen, `/series` SeriesScreen, `/reader` ReaderScreen, `/reader/local` LocalReaderScreen, `/settings` SettingsScreen.
- `SettingsService` (shared_preferences) stores server URL, reading mode preference, local progress.
- `ApiService` makes all REST calls; `LocalCbzService` handles on-device CBZ files via `file_selector`.

### Key screens built
- **LibraryScreen** — Series/Singles tabs, continue-reading strip with progress bars, publisher/genre filters, live search delegate, offline fallback.
- **SeriesScreen** — SliverAppBar with cover, story arc grouping, mark-all-read.
- **ReaderScreen** — immersive fullscreen, scroll mode (ListView) and page mode (PageView + InteractiveViewer zoom 1×–4×), toolbar auto-hides after 3 s, progress sync on every page turn, next-issue prompt on completion.
- **SettingsScreen** — server URL input, test connection button, reading mode toggle.

### Deep link integration
- Registered `comicvault://read/{id}` custom URL scheme via `app_links` package.
- Works when app is running (pushes `/reader` route) and when app is cold-started by the link.

### Windows build
- `flutter build windows --release` — exe at `flutter_app/build/windows/x64/runner/Release/comicvault.exe`.
- Confirmed working on Windows 10 desktop.

### Android APK
- `flutter build apk --release` — APK at `flutter_app/build/app/outputs/flutter-apk/app-release.apk` (51 MB).
- Installed on Lenovo M10 tablet via ADB.

---

## Phase 5 — Build Issues Resolved

A series of build problems were encountered and fixed during Flutter development:

| Issue | Fix |
|---|---|
| Flutter needs symlinks on Windows | Enabled Developer Mode in Windows Settings |
| `TabBarTheme` type error in Flutter 3.44 | Changed to `TabBarThemeData` |
| `file_picker` v1 embedding removed | Upgraded through versions 6 → 8 → 11 → switched to `file_selector: ^1.0.3` (Flutter-team package, no KGP issues) |
| Kotlin incremental compiler crash on cross-drive build (D: project, C: pub cache) | Added `kotlin.incremental=false` to `gradle.properties` |
| `compileSdk` 34 too low for plugin deps | Pinned `compileSdk = 36` in `build.gradle.kts` |
| Stale `GeneratedPluginRegistrant.java` checked into source (listed `sqflite` — never in pubspec) | Deleted file; Gradle regenerates correctly |
| `path` package not declared explicitly | Added `path: ^1.8.0` to pubspec |
| Miscellaneous analyzer lint errors (unused imports, `_` callback vars, curly braces) | Fixed all before each build attempt |

---

## Server Launcher — start_server.py

`test_phase1.py` was the original scanner diagnostic script. It was being launched to "start the server" but it ran the scanner and exited — uvicorn never ran.

Created `start_server.py` as the proper server entry point:
- Prints a config summary (library root, ports, DB path) on startup.
- Validates that `library_root` exists; exits with a clear error if not.
- Calls `init_db()` to ensure tables exist.
- Launches `uvicorn backend.main:app` and stays alive until Ctrl+C.
- All terminal output uses ASCII only — Windows `cp1252` terminal cannot render Unicode box-drawing characters (U+2500 series) which caused a crash on startup.

---

## Android Tablet Connectivity — Root Cause and Fix

**Symptom:** Flutter app on Lenovo M10 tablet failed to connect to the server at `192.168.0.151:8000`. Browser on the same tablet and curl from a laptop both reached the server successfully.

**Diagnosis:** Android 9+ (API 28+) enforces a cleartext HTTP policy for all apps. Browser apps have an exemption. The Flutter app (targeting API 36) was subject to the policy. All HTTP requests silently failed without any user-visible error — the app fell through to offline mode.

**Fixes applied:**

1. `android/app/src/main/AndroidManifest.xml` — added `android:usesCleartextTraffic="true"` to the `<application>` element. Confirmed present in the built APK via `aapt dump xmltree` (`0xffffffff`).

2. `lib/services/settings_service.dart` — added `_normalise()` helper. Users entering `192.168.0.151:8000` without the `http://` scheme caused silent failures (Uri.parse treats it as a path, not a host). `_normalise()` prepends `http://` if no scheme is detected, and trims trailing slashes.

**Verified working:** ADB logcat on the Lenovo M10 shows:
```
CV_DEBUG checkConnection -> http://192.168.0.151:8000/api/admin/stats
CV_DEBUG checkConnection <- 200
```
Library loads from server on tablet. Debug prints removed; release APK built and deployed.

---

## Current State (2026-06-12)

| Component | Status |
|---|---|
| Backend (FastAPI reader server) | Running via `python start_server.py` |
| Web UI (browser library) | Working — accessible from any device on home network |
| Flutter Windows | Built and running on desktop PC |
| Flutter Android | Built and running on Lenovo M10 tablet |
| Android tablet connectivity | Confirmed working — HTTP 200 from server |
| Phase 6 (tray app + admin page) | Not started |

---

## Phase 6 — Tray App + Admin (Complete)

**Admin page** — see SPEC.md change log 2026-06-17 for full feature list (stats, scan section, library folders, pagination, advanced settings). Tested and closed out.

**Tray app** (`tray/tray_app.py`) — pystray-based, built and live-tested 2026-06-17:
- Launches the reader server (`start_server.py`) as a subprocess on startup.
- Health-check thread every 30s; restarts the reader if the process has died. Verified end-to-end: killed the reader process directly, confirmed the tray app detected the exit and relaunched it within one health-check cycle.
- Tray icon colour reflects status (green/yellow/red dot) via a dynamically generated PIL image.
- Context menu (either click, since pystray's Windows backend doesn't support a separate custom popup reliably): Open Library, Admin, Metadata Editor (opens `http://localhost:8001` — does not manage that process, since no Flask editor exists in this repo), Stop ComicVault. Status (starting/running/stopped) is shown only via the tray icon's coloured dot, not menu text — see bug note below.
- Stop gracefully terminates the reader subprocess and confirmed the port is released immediately — verified directly by calling the stop function in isolation.
- **Bug fixed (pythonw crash):** reader subprocess crashed under `pythonw` (no console) because `start_server.py`'s `print()` calls hit `sys.stdout = None` in the child. Fixed by redirecting the child's stdout/stderr to `tray/reader_stdout.log`.
- **Bug fixed (wrong menu action firing):** clicking "Admin" sometimes opened Home instead. Caused by a periodic `icon.update_menu()` call (refreshing a live status label) racing with the user having the context menu open — pystray's Windows backend destroys and rebuilds one native menu handle on `update_menu()`, and doing that mid-display corrupted the command-ID → callback dispatch. Fixed by dropping the live status text from the menu (status is icon-dot-only now) and never calling `update_menu()` after startup.
- `start.bat` — `pythonw tray\tray_app.py`, used by both manual launch and the Windows Startup shortcut.
- Windows Startup shortcut created at `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ComicVault.lnk` → `start.bat`. Confirmed via `WScript.Shell` that target/working-dir resolve correctly.

**Deviations from original spec** (logged in SPEC.md change log 2026-06-17): no editor subprocess management (editor isn't part of this repo); status/actions via tray context menu instead of a custom Tkinter popup window.

ComicVault V1 build (Phases 1–6) is now complete.

---

## V1 — Build and Testing Complete (2026-06-17)

All six phases are built and have been live-tested end-to-end on real hardware (Windows desktop PC + Lenovo M10 Android tablet), not just unit-level:

| Area | Tested as |
|---|---|
| Scanner + DB (Phase 1) | Full library scan against real `L:\Comic Archives\` collection |
| REST API (Phase 2) | Exercised by web UI, Flutter app, and tray app in normal use |
| Web library UI (Phase 3) | Browsed from desktop browser and tablet browser on home network |
| Issue detail + deep link (Phase 4) | Read button confirmed opening Flutter app via `comicvault://read/{id}` |
| Flutter app — Windows + Android (Phase 5) | Built, installed, and used for actual reading sessions on both targets |
| Tray app + admin page (Phase 6) | Auto-start on login verified after reboot; health-check restart and stop verified by killing the reader process directly |

No open bugs or pending fixes remain from this build round. ComicVault V1 is closed.

---

## V2 — Migration Setup Complete (2026-06-18)

**Goal:** Stand up `comicvault_v2` as an independent clone of V1, ready for `EDITOR_SPEC.md`
build work, without touching V1 (`cBook_Server`) in any way.

- Cloned V1's git history (`f20fe67`, `4b405bf`) into `D:\workshop\comicvault_v2`, repointed
  `origin` to `https://github.com/quixline/comicvault_v2`, pushed both commits.
- Copied V1's database to `backend/comicvault_v2.db` (a separate file, never the live V1 DB).
  `config.json` created locally (gitignored, same as V1) pointing `db_path` at the copy;
  `library_root` intentionally left pointing at the real `L:\Comic Archives` — V2's editor
  work will operate on real files, only the database is sandboxed.
- Verified clean startup and a full library scan against the copy (5,429 issues, 0 errors).

**BUG-001 found and fixed during setup:** the scanner's incremental "skip if unchanged"
logic only generated thumbnails on the new/updated branches, so copying the DB without
`thumbnails/` (gitignored, assumed regenerable) left every issue's `date_modified`
matching disk and the scan silently skipped all 5,429 thumbnails — 0 generated despite
0 errors reported. Fixed in `comicvault_v2/backend/scanner.py` only (V1 unmodified): the
skip branch now checks whether the issue's thumbnail file actually exists on disk before
skipping, backfilling it if missing. Verified: deleting one thumbnail and rescanning
regenerates only that one while the rest of the library stays on the fast skip path
(~5 seconds for all 5,429 files, unchanged from pre-fix timing). Full writeup in `BUGS.md`.
Existing missing thumbnails for the copied DB were backfilled via a one-off standalone
script (not committed) rather than the documented `date_modified`-clear-and-rescan
approach, after that approach proved extremely slow against the real library — same end
result, much faster.

V2 is now ready for `EDITOR_SPEC.md` build work to begin.

---

## V2 — Editor Core Built (2026-06-18)

**Goal:** `EDITOR_SPEC.md` Section 10, build step 1 — port CAPT's editing logic into a
shared, FastAPI-independent `backend/editor/` package. No UI, no routers yet.

- `xml_parser.py` — `parse_comicinfo_xml()` (ported from CAPT, `ScanInformation` dropped
  per Section 4) and `parse_filename_for_comicinfo()`. The filename-fallback parser
  reuses the scanner's existing `_parse_filename()` rather than reimplementing it a
  third time (Section 3.1's explicit instruction), with a thin adapter remapping its
  lowercase keys to the tag-cased field names the editor uses.
- `archive_io.py` — CBZ-only read (`find_xml_in_archive`, `extract_xml_from_archive`,
  `get_archive_page_count`) and write (`write_comicinfo_to_cbz`, full extract → overwrite
  → flatten → rebuild → replace, no in-place patching, per Section 3.2). The rebuilt zip
  is staged in the *same directory* as the target file (not the OS temp dir) before the
  final `os.replace` — `library_root` is on a different drive (L:) than the OS temp dir,
  and `os.replace` is only atomic within one filesystem.
- `field_merge.py` — `build_xml_from_fields()`, ported from CAPT's
  `widgets/xml_editor.py`. Untouched tags preserved verbatim; empty string removes a tag;
  `None` leaves it alone.
- `batch.py` — `apply_increment()` (sequential numbering, no collision guardrail, by
  design per Section 3.4) and `process_files()` (per-file merge + write, collects
  per-file errors instead of aborting the batch).
- `constants.py` — locked `FORMAT_OPTIONS` (10) / `AGE_RATING_OPTIONS` (8).
- `genres.json` + `genres.py` — the editable 21-value starting genre list plus a loader
  that re-reads the file fresh each call (no caching), since Tez edits it directly.
- Added `lxml` to `requirements.txt` — required for the tolerant recovery-mode XML
  parsing Section 3.1 specifies; wasn't previously a ComicVault dependency.

**Verified** via a one-off test script (not committed): read path against a real library
file (no real file ever modified); filename-fallback parsing; full write-rebuild round
trip against a scratch copy confirming untouched tags survive, `BlackAndWhite` on/off
tag semantics match `SPEC.md` Section 9 exactly, page count is unchanged after rebuild,
and the original real file was untouched throughout; batch increment + multi-file
processing against two scratch copies. All checks passed.

**Not yet built:** pre-migration data-hygiene report, Basic Editor, Full Editor —
remaining build-order steps in `EDITOR_SPEC.md` Section 10.

---

## V2 — Editor Genres Endpoint Built (2026-06-18)

**Goal:** `EDITOR_SPEC.md` Section 10, build step 2 (remaining piece — `genres.json` and
`constants.py` were already done as part of the core in the previous step).

- New `backend/routers/editor_basic.py` — `GET /api/editor/genres`, returning the current
  contents of `genres.json` fresh on every call. Per Section 6.1, this endpoint formally
  belongs to the Basic Editor router; the rest of that router (`GET`/`POST
  /api/editor/{issue_id}`) is step 4, not yet built. Full Editor's UI will call this same
  endpoint rather than getting its own copy, so the two views can never drift out of sync.
- Registered in `backend/main.py` alongside the existing routers.

**Verified:** started the server, confirmed `GET /api/editor/genres` returns the 21-value
list, confirmed an existing endpoint (`/api/admin/stats`) still works (no regression),
checked the startup log was clean, then stopped the server and checkpointed the DB's WAL.

**Not yet built:** pre-migration data-hygiene report, the rest of the Basic Editor
(`GET`/`POST /api/editor/{issue_id}`), Full Editor.

---

## V2 — Pre-Migration Data-Hygiene Report Built (2026-06-18)

**Goal:** `EDITOR_SPEC.md` Section 10, build step 3 / Section 7.

- `backend/editor/migration_report.py` — `generate_report(db)` queries every non-missing
  issue and flags any `Genre`/`Format`/`AgeRating` value not in the enforced lists.
  Distinguishes **missing** (field has no value at all) from **invalid** (a value is
  present but doesn't match) — different cleanup work for Tez, so kept as separate
  statuses rather than one generic "mismatch" bucket. Genre is checked per individual
  genre value (an issue can have one bad genre among several good ones and only that
  one gets flagged). Run via `python -m backend.editor.migration_report`; writes
  `pre_migration_report.csv` (gitignored — a snapshot of current DB state, not source) to
  the project root with columns `issue_id, series, file_path, field, current_value,
  status`, sortable/filterable in any spreadsheet.

**Run against the real V2 DB:** 751 mismatched (issue, field) rows — Genre 447 (380
invalid / 67 missing), Format 177 (104 invalid / 73 missing), AgeRating 127 (44 invalid /
83 missing). Spot-checked: correctly catches real drift like `"Zombie"` (not in the
genre list, while a sibling `"Horror"` value on the same issue passes), `"One-Shot"` vs
the enforced `"One Shot"`, and `"MA15+"` vs the enforced `"Mature"`.

**Not yet built:** the rest of the Basic Editor (`GET`/`POST /api/editor/{issue_id}`),
Full Editor.

---

## V2 — Basic Editor Built (2026-06-18)

**Goal:** `EDITOR_SPEC.md` Section 10, build step 4 / Section 6 — the popup editor on
`/issue/{id}`, end to end (backend endpoints + the popup UI itself).

**Backend** (`backend/routers/editor_basic.py`):
- `GET /api/editor/{issue_id}` — reads the live XML from the file (not DB columns —
  the file is the source of truth), returns the editor's field set. `PageCount` is
  always the live archive image count, not whatever the XML says (Section 4).
- `POST /api/editor/{issue_id}` — server-side validation gate (Section 4.4: Genre/
  Format/AgeRating must resolve to enforced values, checked per individual genre so a
  single bad value among several good ones is caught precisely), then merge + rewrite
  via the Step 1 core, then `scan_single_file()` in-process — the same function the old
  `POST /api/scan/file` webhook called, just no longer over HTTP since editor and
  reader now share one process (Section 6.1).

**Frontend:**
- `frontend/editor_basic.html` — modal markup fragment (Main/More tabs, fields per
  Section 4 minus `ScanInformation` and minus Increment Number per 6.2), lazy-fetched
  and injected into the DOM on first open.
- `frontend/js/editor_basic.js` — `openEditorModal(issueId, onSaved)`. Genre renders as
  a checkbox grid (not a native multi-select) sourced from `GET /api/editor/genres`;
  Format/AgeRating render as `<select>` with a blank placeholder option, options
  hardcoded to mirror `constants.py` (these two are locked, no server round-trip
  needed). Save stays disabled until all three enforced fields have a valid selection,
  re-checked live on every change. An existing-but-invalid value (e.g. a genre no
  longer in the list) simply has no matching checkbox to pre-check — it's dropped
  silently rather than blocking unrelated valid fields, matching Section 4.4 exactly.
- Wired the **already-present** `Edit XML` button on `/issue/{id}` (`app.js`) — it had
  no handler before this; no new button needed, per Section 6.
- CSS added to `style.css` (reuses existing design tokens, no new ones introduced).

**Verified two ways:**
1. Backend, via a temporary DB row pointing at a scratch copy (never a real library
   file) — GET, POST-with-invalid-fields (422, all 3 expected errors), POST-with-valid
   fields (200, file rewritten, confirmed via re-GET), and confirmed the in-process
   rescan updated the DB row without any webhook. Row and scratch file deleted after.
2. Live in a browser (Playwright, installed to a scratch dir for this check, since no
   project run-skill or `chromium-cli` existed yet) against the real `/issue/1` page:
   opened the popup, confirmed Save started enabled (existing values already valid),
   confirmed all fields populated correctly on both tabs, screenshotted both tabs, no
   console errors, closed via the X without saving. No real file was touched by this
   pass — Save was deliberately never clicked.

**Not yet built:** Full Editor, tray app wiring.

---

## V2 — Full Editor Built (2026-06-18)

**Goal:** `EDITOR_SPEC.md` Section 10, build steps 5–6 — the three-column toolbox
(`/editor`, own page, never touches the DB) and wiring it up from the tray app and
Admin page. Built against the **revised** Section 5.1 (path-based file picker
reinstated — see the `EDITOR_SPEC.md` change-log entry from earlier this session).

**Shared core additions** (`backend/editor/`):
- `archive_io.py` refactored to share a `_rebuild_archive()` helper between writing
  ComicInfo.xml and the new `keep_single_xml()` (Section 3.5 — deletes every `*.xml`
  entry except the one Tez picks, renaming it to `ComicInfo.xml` if needed).
- `validation.py` — the Genre/Format/AgeRating enforcement gate, extracted out of
  `editor_basic.py` so Full Editor's batch processing can reuse the exact same rule
  per file rather than a second copy of the logic.

**Backend** (`backend/routers/editor_full.py`, all in-memory, single-session, never
touches the issues table):
- File picker — `GET browse`, `POST files/add`, `POST folders/add`, ported from
  CAPT's `web_server.py`, validated against `config.LIBRARY_ROOT` (fixes the
  investigation-flagged typo bug — old CAPT checked some routes against a
  `"L:\Comics Archives"` typo and others against the correct string inconsistently).
  `.cbr` is excluded entirely (CBZ-only allowlist).
- Working set (Loaded Files): list/remove/clear, `GET files/{id}/xml` (multi-XML
  detection — returns `multiple_xml: true` + parsed fields for every candidate when
  an archive has more than one), `POST files/{id}/resolve-xml` (pick one, delete the
  rest), `GET files/{id}/preview` + `GET files/{id}/page/{n}` (image viewer, mirrors
  the existing `/api/page/{issue_id}/{page_number}` pattern but reads a working-set
  path instead of a DB row).
- Queue: add/list/remove/clear, separate from the Loaded Files working set.
- `POST process` — `mode: "queue"` (each file's own captured fields; successes are
  removed from the queue, failures stay for retry) or `mode: "all"` (one shared field
  set applied to every file in `file_ids`, in caller-supplied order — respects
  drag-and-drop reorder). Both support `increment_enabled`/`start_issue_no`
  (sequential, no collision guardrail, per Section 3.4). Per-file validation failures
  are collected as errors rather than aborting the whole batch.
- New `/editor` page route in `main.py` serving `editor_full.html`.

**Frontend** (`editor_full.html` + `editor_full.js`, self-contained — no dependency
on `app.js`):
- Three-column layout matching the Admin page's card language (`admin-card`,
  `folder-row`-style horizontal rows) per Section 5.2: File Management + Queue,
  XML Editor (same Main/More fields as Basic Editor plus the Increment Number
  checkbox, which Basic omits), Image Viewer.
- Drag-and-drop reorder and arrow-key navigation on the Loaded Files list (unified
  focus mechanic — both ways of moving focus load the same file into the editor).
  Queue has neither, by design.
- Loaded/Queued count mismatch shown as a visible amber banner, not just two numbers.
- File picker as an in-page modal (tree view, breadcrumb, Select All/Deselect All,
  Add Selected Files/Folder) rather than CAPT's separate popup window — simpler
  given Full Editor is already its own page, same underlying interaction model.
- Multi-XML resolution as a side-by-side read-only comparison modal, one "Keep this
  one" button per candidate.
- Process Queue auto-disables when the queue is empty; Process All and the Queue
  button both gate on the same Genre/Format/AgeRating validity check as Basic Editor.

**Tray app + Admin page wiring:**
- `tray_app.py`'s `open_editor()` now opens `http://localhost:{READER_PORT}/editor`
  instead of the old `:8001` (`EDITOR_PORT` import removed, now fully unused —
  `editor_port` stays in `config.json` untouched per Section 8, just no longer read
  anywhere in code).
- Admin page's "Open Editor (V2)" placeholder (`disabled`, inside the locked Advanced
  Settings fieldset) replaced with a real `<a href="/editor" target="_blank">` link.
  Deliberately **not** form-gated by the Advanced Settings unlock checkbox — `<a>`
  tags aren't affected by a parent `<fieldset disabled>` the way `<button>` is, and
  that's the right behaviour here: opening the editor is a navigation action like
  "User Guide", not a setting change, so it shouldn't need the same unlock step.

**Verified** entirely against scratch copies staged in the real, scan-excluded
`Processing` folder (never touching Tez's actual in-progress files there, and never
touching real library files) — backend script covering folders/add, multi-XML
detection + resolution, Process Queue (validation rejection + success + queue
auto-empty), Process All with increment, per-file error isolation; then live in a
browser (Playwright) covering the picker modal end-to-end against the real
`Processing` folder listing (confirmed `.cbr` files correctly excluded), focusing a
file and seeing the cover load in the Image Viewer, both tabs, queueing, Process
Queue, Process All with increment (confirmed sequential numbering on disk after),
the multi-XML modal, keyboard navigation, zoom, drag-and-drop reorder, and the
Admin-page link opening `/editor` in a new tab. No console errors throughout. All
scratch files and folders deleted afterward; confirmed Tez's real `Processing`
folder contents untouched.

This closes out `EDITOR_SPEC.md`'s build order (Section 10) — CAPT is now fully
retired as a separate app.

---

## V2 — First Manual Test Pass Fixes (2026-06-18)

Tez ran the first hands-on test of both editors against the live server. Confirmed
working: tray app's Metadata Editor menu item, the Genre checkbox-grid design choice
(kept as built). Three small fixes from this pass:

- **BUG-002 fixed** — Full Editor's Queue/Process All buttons were incorrectly gated
  by the Basic-Editor-only validation rule (Section 4.4). See `BUGS.md`.
- **Admin page "Open Editor" moved** from inside the locked Advanced Settings
  fieldset to the top action row, alongside Back/User Guide/Backup Database/Password
  Reset — confirmed this is a navigation action, not a setting, so it shouldn't need
  the advanced-settings unlock step.
- **Dead code removed** — `EDITOR_PORT` constant in `backend/config.py` (only
  `tray_app.py` read it, already fixed to use `READER_PORT` + `/editor`). No change
  to `config.json` itself — `editor_port` stays in the file, just unread.

**Not yet tested:** Basic Editor remote access from a second device (Section 6.4).

Tez is continuing manual testing; further bugs/design changes will be logged as they
come up.

---

## V2 — Startup Failure Found and Fixed (2026-06-18)

**Symptom:** Tez reported that after closing a session and rebooting, the editor was
unreachable from a second device on the network (library still visible), and that it had
also stopped working on the PC itself, with the tray icon back to referencing port 8001.

**Two compounding root causes found:**
- The Windows Startup shortcut (`%APPDATA%\...\Startup\ComicVault.lnk`) had never been
  repointed during the V1→V2 migration — it still targeted `D:\workshop\cBook_Server\start.bat`.
  After the reboot it launched V1's tray app/server instead of V2's, explaining the
  `:8001` tray reference and the missing `/editor` route (V1 has no editor route at all).
- Independently, `start_server.py` still imported `EDITOR_PORT` from `backend/config.py`,
  which the BUG-002 commit (`5b1b11c`, previous entry above) had deleted as dead code
  without checking this remaining caller — so V2's reader server crashed with an
  `ImportError` on every single startup attempt since that commit, regardless of the
  shortcut issue.

**Fixed:** stopped the wrongly-running V1 processes, repointed the Startup shortcut to
`comicvault_v2\start.bat`, removed the stale `EDITOR_PORT` import/print from
`start_server.py` (commit `7e49d35`), and confirmed `/api/admin/stats` (returning
`comicvault_v2.db` as `db_path`) and `/editor` both return 200 after a clean restart.

---

## V2 — Full Editor / Basic Editor UI Polish (2026-06-18)

A round of small layout fixes from live use on both the desktop PC (primary editing
machine) and Tez's laptop (smaller screen). Committed as `cc772ba`.

**Full Editor (`editor_full.html`/`.js`, `style.css`):**
- Image Viewer column narrowed in two passes (`460px → 368px`) and the loaded page image
  capped at 80% of the frame width — both the card and the image now shrink together
  (an intermediate version capped only the inner frame/image while the card stayed
  full-width, which read as "the width is off" and was corrected).
- `.fe-layout` reworked so the XML Editor column is now the flexible (`1fr`) track, with
  File Management and Image Viewer as the two fixed-width tracks — needed once the Genre
  grid went to 5 columns and started horizontal-scrolling inside the old fixed-width
  Editor column.
- Genre grid (`#fe-genre-grid`) — 3 columns, then 5 columns.
- Increment Number checkbox relabelled "Increment #" and moved into the Issue
  Number/Year row (between them), via a new scoped `.fe-number-row` (auto-sized columns,
  packed left) replacing the shared 2-column `.editor-field-row` for just this row —
  fixes an oversized gap that appeared when the row still used `1fr` tracks sized for two
  wide fields now holding three narrow ones.
- Year field pushed to the row's right edge (`margin-left: auto`) once Increment # was
  sitting directly against it.
- Zoom in/out buttons split into their own `.fe-viewer-controls` row below Prev/Next.
- Increment #/B&W checkbox label font matched to the other field labels, scoped to
  `#feForm` only so Basic Editor's checkbox labels are unaffected.

**Basic Editor (`editor_basic.html`/`.js`, `style.css`):**
- Popup width increased (`520px → 720px`) to fit a multi-column genre grid without
  horizontal scroll.
- Genre grid (`#ed-genre-grid`) — 3 columns, then 4 columns once the wider popup was
  confirmed. `min-width: 0` + `overflow-wrap: anywhere` added on the genre items so
  longer names (e.g. "Non-Fiction") wrap inside their column instead of forcing the grid
  wider.
- B&W checkbox moved onto the same row as Format/Age Rating (after Age Rating), via a
  scoped `.ed-format-row`. Format/AgeRating `<select>` width capped at 150px then
  widened to 200px once Tez confirmed the cramped version was only an issue on the
  laptop's smaller screen — the desktop PC is the primary editing machine and has the
  room.
- "Black & White" label briefly shortened to "B&W" then reverted back to the full label
  once the row had room for it.

**Also found (not a real bug):** edits to `editor_basic.html` appeared not to take effect
in an already-open browser tab — caused by `editor_basic.js`'s `ensureEditorLoaded()`
caching the fetched HTML fragment in the `editorReady` promise for the life of the page.
A full page reload (not just reopening the popup) picks up markup changes.

**Web UI home nav (`index.html`):** surface tab order changed to Home, All, Singles,
Series, 2000 AD (previously Home, Series, Singles, All, 2000 AD).

---

## V2.1 — Custom Tabs Built (2026-06-19)

**Goal:** `CUSTOM_TABS_SPEC.md` — admin-managed, folder-scoped library tabs. First of
four planned v2.1 features (the other three — editable home strips, taskbar app
changes, mobile reader changes — remain untouched; `HOME_STRIPS_SPEC.md` is a planning
doc only, no code written for it).

This session picked up build steps 1–4 (backend: `custom_tabs` table/model, CRUD +
folder-validation endpoints in `routers/admin.py`, `tab_id` filtering on
`GET /api/library` in `routers/library.py`, `GET /api/nav/config` in `routers/home.py`,
shared `path_utils.py` prefix-matching helpers) that had already been written in an
earlier, interrupted session but never logged or finished. Completed steps 5–7:

**Frontend — home page nav + browse (`app.js`):**
- `loadCustomTabsNav()` fetches `/api/nav/config` on every library page load and
  appends a `.surface-btn` per visible tab after the fixed nav (Home, All, Singles,
  Series, 2000 AD), in `created_at` order — matching the nav bar's existing static
  order exactly since custom tabs are always last.
- `bindSurfaceNav()` switched from per-button listeners to event delegation on
  `.surface-nav`, since custom-tab buttons are injected after the initial bind.
- Tab surfaces (`data-surface="tab-{id}"`) reuse the existing Series/Singles/All
  browse pipeline wholesale, per spec 5.3: `getFilteredLibrary()` sources from a new
  `tabLibraryCache[id]` (fetched via `/api/library?tab_id={id}`, separate from the
  global `allLibrary` used for filter-dropdown options) and skips the format_group
  split — flat like All. Count display reuses All's "Titles / grand total of
  individual comics" rule for tab surfaces too.
- `?surface=tab-{id}` deep links (used by the existing singles/series back-link
  mechanism) work the same way `?surface=all` etc. already did.
- **Small enhancement beyond the spec's text:** the existing back-link label logic on
  `series.html`/`issue.html` only knew the four fixed surface names and fell back to
  generic "Library" for anything else — which would've made every custom-tab back
  link say "← Library" instead of the tab's name (navigation itself was never broken,
  just the label). Fixed by caching `tab-{id} → name` in `sessionStorage` from
  `loadCustomTabsNav()` and reading it as a fallback in both label lookups.

**Admin page (`admin.html`/`admin.js`):** new "Custom Tabs" subsection inside the
existing locked Advanced Settings fieldset (same unlock gating, native `<fieldset
disabled>` covers the new buttons/inputs automatically). Tab list shows name, path,
a Visible/Hidden toggle button, and Delete (browser `confirm()`, explicit that it only
removes the tab definition). Add form has a manual path input plus a "Browse…" button
opening a folder-only picker modal reusing the Full Editor's existing
`.editor-overlay`/`.editor-modal`/`.fe-picker-*` CSS classes against the new
`GET /api/admin/browse` endpoint (multi-root aware — shows a root-switcher row when
more than one `library_root` is configured, though only one is configured currently).
"Add Tab" disables at the 4-visible cap with an inline hint, per spec.

**Verified** end-to-end with Playwright (installed to a scratch temp dir, not
committed) against the live dev server and the real `comicvault_v2.db` (sandboxed,
never the live V1 DB — consistent with V2's existing testing convention):
- Backend via curl: create/list/patch/delete, the 409 cap at 5 visible tabs, a hidden
  tab freeing a slot, both folder-validation warnings (outside all roots / wraps an
  entire root), and 400 on a nonexistent folder.
- Browser: unlocking Advanced Settings reveals the section; add via the folder picker
  (breadcrumb navigation, click-to-descend, "Select This Folder"); hide/show toggle
  updates the row and the home nav immediately; cap-hint and disabled Add button at
  4 visible; clicking a tab in nav loads the correct folder-scoped subset (spot-checked
  counts against direct `/api/library?tab_id=` calls); opening an issue/series from a
  tab and navigating back returns to the tab with the correct label; delete removes
  the tab and nav entry with no file-system side effects. No console/page errors in
  any pass. All test tab rows deleted after each run — `custom_tabs` table confirmed
  empty at the end; WAL checkpointed into the main DB file before finishing.

This closes out `CUSTOM_TABS_SPEC.md`'s build order (Section 7). Next v2.1 feature is
`HOME_STRIPS_SPEC.md` (editable home page strips) — planning only so far, not started.

---

## V2.1 — Home Strips Built (2026-06-19)

**Goal:** `HOME_STRIPS_SPEC.md` — admin-editable home page strips (second of four
planned v2.1 features). Per `CLAUDE.md` (added this session — see its own change-log
note), V2.1 is no longer "paused"; this is the documented active focus.

**Backend:**
- `HomeStrip` model + `home_strips` table (`models.py`); seeded idempotently inside
  `init_db()` (`database.py`) with the 4 default rows (Continue Reading, Recently
  Added, Random Unread, Random Genre, `position` 0–3) — same no-formal-migration
  convention as the rest of this codebase.
- `backend/path_utils.py` gained `matches_field()` (the 9 filter dimensions — genre,
  publisher, writer, artist, format, decade, year, rating, bw), moved there from a
  one-off copy in `library.py` so `home.py` could share the exact same logic rather
  than a second copy of a 9-branch dispatcher — the one piece of this build judged
  risky enough to duplicate that it got pulled into the existing shared-helpers module
  instead.
- CRUD + bulk reorder endpoints in `admin.py` (`GET`/`POST`/`PATCH`/`DELETE
  /api/admin/home-strips`, `PATCH /api/admin/home-strips/reorder`), mirroring Custom
  Tabs' pattern closely: same default-row lockout (only `position` editable), same
  hard-delete-with-no-filesystem-effect, same cap pattern (5 non-default strips here
  vs. 4 visible tabs there). **Route-ordering gotcha caught before it shipped:** the
  static `/reorder` path was originally registered after the dynamic `/{strip_id}`
  route — FastAPI would have tried `int("reorder")` first and 422'd before ever
  reaching the reorder handler. Fixed by registering `/reorder` first.
- `GET /api/home/strips` (`home.py`) extended to resolve all three basis types in
  `position` order: `builtin` (existing per-strip logic, including Continue Reading's
  query, ported in rather than calling the standalone endpoint — see Change Log decision
  in `HOME_STRIPS_SPEC.md`), `field`, and `folder`. Continue Reading is pinned first
  whenever it has any matching issues, overriding stored `position` for every row, per
  spec 4.4 — verified by deliberately reordering it mid-list and confirming render order
  didn't move.
- New `GET /api/browse/years` endpoint — Year is one of the spec's 9 field dimensions
  but had no server-side value-list source before (the web UI only ever derived it
  client-side from the full library payload).
- `GET /api/library` gained generic `field`/`value` and `folder_path` query params
  (alongside the existing `tab_id`) so a home strip's "view all" link can be served by
  the same endpoint Custom Tabs already uses, rather than a new one.

**Frontend:**
- Continue Reading's dedicated `continueSection`/`continueStrip` markup and
  `renderContinueStrip()` removed from `index.html`/`app.js` — it now arrives as the
  first entry in the unified `/api/home/strips` response and renders through the same
  `buildHomeStrip()`/`buildStripCard()` path as every other strip (which already
  supported a progress bar for partially-read items, so this is a no-visible-regression
  removal, not just a refactor). Associated now-dead CSS (`.continue-section`,
  `.continue-card`, `.continue-info/-title/-sub`, `.progress-track/-fill`) removed too.
- Two new transient browse surfaces, `fieldview` and `folderview`
  (`?surface=fieldview&field=&value=` / `?surface=folderview&folder=`), opened only via
  a strip's clickable heading — not part of the persistent nav. Reuse the exact same
  filter/sort/grouping/pagination pipeline as Series/Singles/All/Custom-Tabs by sourcing
  `getFilteredLibrary()`'s pool from a new `viewLibraryCache`, fetched via the new
  `GET /api/library` params above. Added strips' headings render as real links
  (`stripViewAllHref()`); default strips' headings stay plain text — see
  `HOME_STRIPS_SPEC.md`'s Change Log for why that gap is deliberate, not an oversight.
- Admin page: new "Home Page Strips" subsection inside the same locked Advanced
  Settings fieldset as Custom Tabs. List shows up/down reorder arrows (per Tez's choice
  over drag-and-drop), a "Default" badge + no edit/delete controls for the 4 fixed rows,
  and for added rows a basis summary, Visible/Hidden toggle, and Delete (same `confirm()`
  wording convention as Custom Tabs). Add form: basis-type radio (Field/Folder), a field
  dropdown whose second "value" dropdown populates live from the matching `/browse/*`
  endpoint (B&W special-cased to a fixed Yes/No, no server round-trip), or the same
  shared folder-picker modal Custom Tabs uses — generalized to take a target input id
  (`openCtPicker(targetInputId)`) so both features' "Browse…" buttons could reuse one
  modal instead of two near-identical copies. Order mode (Random/Fixed + sort field)
  rounds out the form. "Add Strip" disables at the 5-strip cap with an inline hint.

**Verified** end-to-end with curl and a live Playwright browser session (scratch temp
dir, not committed) against the real `comicvault_v2.db` (sandboxed dev DB, same
convention as every prior session) — backend: full CRUD, the reorder route-ordering
fix (confirmed `/reorder` no longer 422s), the 409 cap at 6 non-default strips,
default-row lockout (name-change and delete both rejected with clear errors),
Continue Reading's pin-first behaviour surviving a deliberate position reorder.
Browser: admin add/reorder/hide/delete for both field- and folder-based strips
(including the shared picker modal), cap-hint and disabled Add button at 5, home page
rendering strips in order with the dynamic Random Genre title still working, clicking
an added strip's heading landing on the correct `fieldview`/`folderview` surface with
counts matching direct API calls (490 Titles / 190 Titles, spot-checked). No
console/page errors in any pass. All test rows deleted and `home_strips` positions
restored to 0–3 after — table confirmed back to exactly the 4 seeded defaults; WAL
checkpointed into the main DB file before finishing.

**Flagged, not fixed this session:** `BUG-003` (dead duplicate `GET /api/reading/continue`
route in `progress.py`, shadowed by `library.py`'s copy) — found while tracing Continue
Reading's query, logged in `BUGS.md`, out of scope for this build.

This closes out `HOME_STRIPS_SPEC.md`'s build order (Section 7). Remaining v2.1 work
(taskbar app changes, mobile reader changes) is tracked in `v2_1-main-new-features.md`
and not started.

---

## V2.1 — Tray App Menu Redesign (2026-06-19)

**Goal:** Taskbar app changes — the first of the two remaining items flagged above.
Split the old single "Stop ComicVault" action into independent server start/stop
controls, add a self-service autostart toggle, and a dark-themed menu.

**`tray/tray_app.py` changes:**
- New module-level `manually_stopped` flag (alongside the existing `state_lock`/
  `reader_process`/`reader_status`/`stop_event`). `health_check_loop()`'s auto-restart
  branch now checks it before restarting a dead reader process — without this, a
  deliberate "Stop Server" would get silently undone by the next 30s health-check tick.
- `stop_comicvault` (terminate reader + `icon.stop()`, both at once) replaced with four
  functions: `_terminate_reader_process()` (the shared terminate/10s-grace/kill logic),
  `stop_server()` (reader only, tray keeps running, sets `manually_stopped`),
  `start_server()` (no-ops if a live process already exists, otherwise clears the flag
  and relaunches — runs `wait_for_startup()` in a thread so the menu callback doesn't
  block the message-pump for up to 15s), and `close_app()` (stops the reader, then
  `icon.stop()` — the old combined behaviour, renamed).
- `is_autostart_enabled()`/`toggle_autostart()` — the checkable "Start ComicVault at
  login" item. Checked state is just `os.path.exists()` on the Startup shortcut path,
  no new config.json key. Toggling creates/removes the `.lnk` via `pywin32`
  (`win32com.client`, imported lazily inside the function so a missing `pywin32`
  degrades to a logged failure rather than crashing tray startup).
- `_enable_dark_menu_support()` — one `ctypes` call to the undocumented
  `SetPreferredAppMode` export (ordinal 135, `uxtheme.dll`), run once at the top of
  `main()` before any window/menu is created. Makes the native popup menu follow
  Windows' own dark/light personalization setting; can't force dark independent of it.
- `build_menu()` rebuilt: Open Library / Admin / Metadata Editor / separator / Start
  ComicVault at login (checkable) / separator / Stop Server / Start Server / Close.

**Investigated and corrected before relying on the checkable item being safe:** the
existing `build_menu()` comment claimed `icon.update_menu()` is "never called after
startup," citing the 2026-06-17 menu-corruption bug (a background-thread timer
rebuilding the native menu while it was open, corrupting the command-ID → callback
mapping so clicking "Admin" could fire "Open Library"). Reading the installed
`pystray` package directly (`_base.py`'s `_handler`, `_win32.py`'s `_create_menu`)
showed this claim was broader than the actual fix: pystray wraps **every** menu item
callback in its own `update_menu()` call already, and always has — it's safe because
it runs on the message-pump thread strictly after the native `TrackPopupMenuEx` popup
has already closed (a blocking call), so there's never a concurrently-open menu to
corrupt. The real, narrower rule from the 2026-06-17 fix: never call `update_menu()`
from a **background thread** (`health_check_loop`, `update_icon_loop`) — calling it via
a menu item's own click handler is exactly what was already happening for Open
Library/Admin/Editor the whole time. This means the checkable autostart item's
checkmark updates correctly with zero extra code. Comment in `build_menu()` corrected
to state the narrower rule. `SPEC.md`'s change log also updated with this finding.

**`requirements.txt`:** added `pywin32` (new dependency, for the autostart shortcut).

**Verified:**
- Module import + isolated function tests (no tray UI, no Playwright — this is a
  desktop Windows app): `is_autostart_enabled()` correctly read the real, pre-existing
  shortcut (confirmed `True`); `_enable_dark_menu_support()` ran without raising on
  this machine. `toggle_autostart()`'s create/remove logic tested against a throwaway
  temp path (not the real shortcut) — confirmed it creates a `.lnk` with the exact same
  `TargetPath`/`WorkingDirectory`/`WindowStyle` as the real, already-working shortcut,
  then removes it cleanly; confirmed the real shortcut was untouched throughout.
  `stop_server()` tested against a real spawned dummy subprocess — confirmed it
  terminates the process and sets `manually_stopped`/`reader_status` correctly; the
  `start_server()` no-op guard condition verified against a still-running dummy process.
- Full real launch: `python tray/tray_app.py` started cleanly end-to-end (real
  `start_reader()` spawning real `start_server.py`, port 8000 confirmed responding,
  `tray.log` showing the expected startup sequence, no traceback in console output).
  Manually killing the tray process without going through `close_app()` left the reader
  subprocess running (had to be killed separately) — confirms Windows does NOT clean up
  child processes when a parent exits, which is exactly why `close_app()` (and
  `stop_server()`) explicitly terminate the reader themselves rather than relying on
  process-tree cleanup.
- WAL checkpointed into the main DB file after testing.

**Not verifiable by me — needs a manual pass on the real machine** (clicking an actual
tray icon menu isn't something Playwright or any other tool here can drive): the
checkable item's visual checkmark updating immediately after a click, the dark-theme
appearance against both Windows light and dark mode, the 35-second health-check
non-restart window after a manual "Stop Server", and a reboot test of the new
self-service autostart toggle. Full manual checklist is in the approved plan file from
this session.

This closes the first of the two remaining v2.1 items. Mobile reader changes (tracked
in `v2_1-main-new-features.md`) are not started.

---

## Session — 2026-06-19: BUG-004, server failed to start after OS restart

**Goal:** Investigate why, on first login after the OS restart that followed the prior
tray-app session's testing, the server didn't start automatically (despite "Start
ComicVault at login" showing correctly ticked) and manual "Start Server" from the tray
menu also did nothing.

**Found:** Not a tray-app or autostart bug. `tray/reader_stdout.log` showed uvicorn
itself failing on every launch attempt with `[WinError 10013] an attempt was made to
access a socket in a way forbidden by its access permissions` when binding
`0.0.0.0:8000`. `netsh interface ipv4 show excludedportrange protocol=tcp` confirmed
port 8000 fell inside a Windows-reserved TCP exclusion range (`7981–8080`) at the time;
`netstat` showed no process actually holding 8000, i.e. Windows itself was refusing
the bind. `hns`, `vmms` (Hyper-V), and the WSL Service were all running on this
machine — this is the known behaviour where WSL2/Hyper-V's networking stack reserves
blocks of TCP ports for NAT at boot, and this particular boot's reserved block
happened to overlap port 8000.

**Fix applied:** Restarted the `winnat` service (`net stop winnat` / `net start
winnat`) to force Windows to recompute its exclusion ranges. Confirmed port 8000 was
no longer excluded afterward. No manual restart of the tray app or server was even
needed — the tray app's existing 30-second health-check loop picked the now-available
port up on its own next retry (`tray.log`: "Reader server is up." at 18:46:28).
Confirmed `netstat` showed `0.0.0.0:8000 LISTENING` and `GET /api/admin/stats`
returned `200`.

**No code changes made.** `tray_app.py` and `start_server.py` both behaved exactly as
designed throughout (correct retry/health-check behaviour is in fact what self-healed
this once the OS-level block cleared) — logged as BUG-004 in `BUGS.md` for the record,
since "manual Start also failing" is a legitimate first-impression of a code bug and
worth having the real (environmental) explanation on file. Flagged as a possible
future `ROADMAP.md` item: either move ComicVault off port 8000 to a range Windows
doesn't commonly reserve for Hyper-V/WSL NAT, or have `start.bat`/the tray app
proactively restart `winnat` before launching — neither done in this session, since
the immediate goal was just to get the server back up and find the real cause.

---

## Session — 2026-06-20: Tier 4 Item 1 — Genre/Format admin editor

**Goal:** First item in the new `comicvault-changes.md` build queue — make Format an
admin-editable, file-backed list alongside the existing Genre mechanism, and surface
add/remove for both in the Admin page. Reverses `EDITOR_SPEC.md` Section 4.2's
"Format = locked constant" decision.

**Found while planning:** the backlog's framing assumed Genre already had admin
add/remove UI — it didn't. `genres.json` existed and was served via `GET
/api/editor/genres`, but the only way to edit it was hand-editing the file; no Admin
page control existed. So this session built add/remove UI for **both** lists, not
just ported Format onto an existing Genre mechanism.

**Built:**
- `backend/editor/editable_lists.py` — shared load/add/remove logic for both lists
  (trim, case-insensitive duplicate check, blocks removing the last remaining value).
  `genres.py` and `formats.py` are now thin wrappers over this, keeping their existing
  public function names so nothing importing `load_genres()` had to change.
- `backend/editor/formats.json` + `formats.py` — new editable list, seeded with the
  original 10 `FORMAT_OPTIONS` values. `FORMAT_OPTIONS` removed from `constants.py`
  (only `AGE_RATING_OPTIONS` remains locked there); `validation.py` and the one-time
  `migration_report.py` script switched to call `load_formats()`.
- New endpoints in `editor_basic.py`: `POST/DELETE /api/editor/genres[/{name}]` and the
  same pair for `/api/editor/formats`. Mirrors the existing `GET` endpoints; removal of
  the last remaining value 400s with a clear message.
- Admin page: new "Genre List" / "Format List" subsections (`admin.html`/`admin.js`),
  mirroring the existing Custom Tabs list+add-form pattern. Each row shows the value's
  current issue count (from `/api/browse/genres`/`/formats`, already existing
  endpoints); deleting a value in use shows a confirm dialog stating the count; the
  Delete button is disabled outright when only one value remains (backend already
  blocks it — this just avoids a round-trip to be told no).
- `editor_basic.js`/`editor_full.js`: Format dropdown now fetches `/api/editor/formats`
  live instead of a hardcoded array, same pattern Genre already used.
- `EDITOR_SPEC.md` Sections 4.1/4.2 updated — 4.2 reframed from "locked, hardcoded" to
  "enforced, backend-served, editable list" with a dated deviation note; 4.1 updated to
  mention the new Admin-page add/remove endpoints alongside direct file editing.

**Bug caught during verification:** the shared save function originally opened
`genres.json`/`formats.json` in plain text mode, which on Windows silently translates
`\n` to `\r\n` on write — round-tripping a file through add+remove was rewriting every
line ending from LF to CRLF even though content was unchanged. Fixed by opening with
`newline=''` in `editable_lists.py`. Caught by diffing the file against a pre-test
backup after an add/remove cycle, byte-for-byte, not just by checking JSON content
matched.

**Verified:**
- Backend: exercised every new endpoint live against the running server — add,
  duplicate-rejected (400), delete (clean and confirm-dialog paths), last-item-blocked
  (400), confirmed via diff that `genres.json`/`formats.json` round-tripped
  byte-identical to a pre-test backup after every add+remove cycle.
- Admin UI: drove the live Admin page with a throwaway Playwright/Chromium instance
  (no existing Node tooling in this repo, so installed to a scratch temp dir, not the
  project) — added and deleted a throwaway value in both lists, confirmed toasts, zero
  console errors; triggered the confirm dialog on a real in-use genre ("Crime", 529
  issues) and dismissed it, confirming cancel leaves the list untouched.
- Editor: opened the Basic Editor on a real issue (id 4318), confirmed the Format
  `<select>` populated from the live endpoint and pre-selected the issue's existing
  value ("Graphic Novel"), closed without saving.
- Confirmed `genres.json` and `formats.json` are git-clean (no diff) after the session
  — only code/doc files changed. Scratch Playwright install and temp backups removed
  afterward.

**Not yet done:** Tier 5's manual Genre additions (Anthology, Comic, Omnibus) are now
unblocked by this but were intentionally left for Tez to do by hand through the new
Admin UI, per the backlog's own sequencing — not part of this session's scope.

---

## Session — 2026-06-20: Doc-map cleanup — create missing docs, fix stale ones

**Goal:** `CLAUDE.md` Section 2's doc map listed `CHANGELOG.md`, `DECISIONS.md`,
`INDEX.md`, `README.md`, `ROADMAP.md`, and `TESTING.md` as "to be created." In
practice `README.md` already existed but was stale (written for V1, before the editor
was integrated); the other five genuinely didn't exist. Create the five missing docs,
bring `README.md` current, and fix related staleness found while auditing the doc map.

**Found while auditing, beyond README.md:**
- `CUSTOM_TABS_SPEC.md` and `HOME_STRIPS_SPEC.md` both still had a status header
  reading "Planning complete. Not yet built," even though both shipped (commits
  `b37b494`, `b52771d`). Both also pointed to `v2_1-main-new-features.md` for
  taskbar/mobile-reader tracking — that file no longer exists; the tracking is in
  `comicvault-changes.md` now, which itself had two of the same dangling references.
- `SPEC.md` Section 20.14's "Deferred to V2" list still included Custom Tabs and Home
  Strips as not-built.
- `BUGS.md` had two `## FIXED` headings (a duplicate/misplaced one), with BUG-003 (an
  explicitly *not*-fixed bug) sitting under the first one. Confirmed with Tez: this
  was a filing mistake, not intentional — BUG-003 is genuinely open.

**Built:**
- `CHANGELOG.md` — newest-first one-line index into `progress.md`'s session headers.
- `DECISIONS.md` — rationale log for non-obvious calls (editor sync mechanism
  evolution, Format's locked→editable reversal, Home Strips' total-vs-visible cap,
  Genre/Format delete-confirm behaviour, and four V1-era architecture calls).
- `ROADMAP.md` — active build queue (Tier 4 items 2-3, Tiers 1-3/5), Mobile Reader
  (paused indefinitely), the corrected SPEC.md §20.14 list, the installer, and the two
  known issues (BUG-004 environmental risk, BUG-003 open bug).
- `INDEX.md` — one-page map: active/authoritative docs, the new reference docs, and a
  "historical only" bucket for the one-time migration/investigation docs.
- `TESTING.md` — standing verification runbook, codifying two patterns established
  this week: byte-for-byte diff-against-backup for file-writing changes (this is how
  the LF→CRLF bug got caught in the previous session), and scratch-Playwright-in-
  temp-dir for UI verification in a repo with no Node tooling checked in.
- `README.md` — full rewrite: removed the "separate metadata editor" claim (false
  since 2026-06-18), corrected run instructions to `start_server.py`, current V1/V2
  status, pointers to `INDEX.md` instead of duplicating content.

**Fixed:**
- `CUSTOM_TABS_SPEC.md` / `HOME_STRIPS_SPEC.md` status headers corrected to "Built and
  verified," dangling file reference repointed to `comicvault-changes.md`.
- `SPEC.md` §20.14 — removed the two now-built items, added a correction note pointing
  to `CHANGELOG.md`/`ROADMAP.md`.
- `comicvault-changes.md` — removed its own two dangling `v2_1-main-new-features.md`
  citations (the content was already inline; the file just doesn't exist).
- `BUGS.md` — split into `## OPEN` (BUG-003, moved here) and one `## FIXED` section
  (BUG-004, BUG-002, BUG-001) — removed the duplicate heading. No bug body text
  changed, confirmed by reading the full file after the edit.
- `CLAUDE.md` §2 — flipped the doc-map status column from "to be created" to "exists"
  for all six docs, per the file's own rule that drift should be corrected, not left
  silent.

**Verified:**
- `grep -rn "v2_1-main-new-features"` across all `.md` files — remaining hits are only
  explanatory ("now-removed...") or inside `progress.md`'s own historical entries
  (left untouched, since that log is append-only and was accurate at the time it was
  written). No live dangling references remain.
- Confirmed every doc path named in the new `INDEX.md` actually exists on disk.
- Re-read `BUGS.md` in full after editing to confirm both bugs' body text is
  byte-identical to before, only the headings moved.

**No app code changed this session** — documentation only.

---

## Session — 2026-06-20: Junction `docs/` to Google Drive for Claude Cowork access

**Goal:** Tez wants Claude Cowork (connected via Google Drive) to read and write
ComicVault's project docs directly for extra planning assistance. Most docs from the
session above got moved out of the git repo to a Drive-synced folder
(`C:\Users\tezdr\My Drive (quixlinedesign@gmail.com)\Dev_Folders\Workshop\comicvault_v2\
project_docs`) for this purpose, which broke git tracking for 13 files (`git status`
showed them as deleted from the working tree). Tez wanted git tracking and `git push`
restored without giving up Drive/Cowork access.

**Solution (supplied by Tez, technically verified before applying):** a Windows
directory junction at `D:\workshop\comicvault_v2\docs` pointing at the real Drive
folder. `mklink`/`New-Item -ItemType Junction` needs no admin elevation (only
symbolic links do); junctions work across drive letters for local NTFS folders, and
the Drive folder was confirmed to be a real local folder, not a virtual placeholder.
Git for Windows walks junctions transparently when scanning the working tree, so
`git add docs/` tracks the real file content normally — no symlink-blob special
casing. Because both paths point at the same physical files (not a copy), there's no
sync mechanism needed: an edit made through Drive shows up immediately as a normal
working-tree change in the repo.

**Verified before committing:**
- Created the junction, confirmed `docs/` lists the same 16 files as the Drive folder.
- Appended a throwaway line to `docs/TESTING.md` via the real Drive path directly,
  confirmed `git status` in the repo showed it as a working-tree change with zero
  delay — proved the core premise concretely, not just by reasoning about it. Reverted
  the test line and confirmed the file diffed byte-identical to the last commit
  afterward.
- Confirmed `git check-ignore` still correctly excludes the three historical files
  inside `docs/` (`V2_MIGRATION_SETUP.md`, `V2_FOLLOWUP_COMMIT_AND_SCANNER_FIX.md`,
  `pre_migration_report.csv`) — existing `.gitignore` patterns have no leading slash,
  so they match by basename at any depth, no `.gitignore` changes needed.
- `git add docs/` plus the old paths showed clean renames (`R`) for all 13 files, not
  unexpected delete+add pairs.

**Fixed:**
- `CLAUDE.md` §2 — added a note explaining the junction and why it exists, prefixed
  every doc-map table entry except `README.md` with `docs/`, updated the close-of-
  session checklist (§4) and doc-update-threshold (§5) prose references to match.
- `README.md` — same `docs/` prefix updates to its doc cross-references.
- Resolved a `CHANGELOG.md` duplication that emerged mid-session (briefly existed both
  at the repo root and in the Drive folder) — Tez deleted the root copy, so
  `docs/CHANGELOG.md` is the only copy going forward.

**Cleanup:** removed `location-change-soloution.txt` (Tez's scratch note proposing the
junction fix) from the repo root — content fully captured here and in `CLAUDE.md`.

**Not committed/pushed without separate confirmation** — per standing instruction,
even though this session continues straight from one where push was already approved;
this is a distinct, structurally significant change.

---

## Follow-up — Tray App Manual Verification (2026-06-20)

Tez confirmed that all items flagged as "needs a manual pass on the real machine" in the
"V2.1 — Tray App Menu Redesign (2026-06-19)" session entry were completed and passed with
no issues:

- Checkable "Start ComicVault at login" item: visual checkmark updates immediately on click.
- Dark-theme menu appearance: correct against both Windows light and dark mode.
- 35-second health-check non-restart window after a manual "Stop Server": confirmed.
- Reboot test of the self-service autostart toggle: confirmed.

No issues found. Tray app menu redesign is fully closed.

---

## Session — 2026-06-21: Tier 4 Item 2 — Multi-select + Favorites/Rating

**Goal:** Build `comicvault-changes.md` Tier 4 Item 2 — long-press a card to select it,
tap more cards to add to the selection, then bulk-apply Read/Unread, Add to Favorites,
or a 1–5 star Rating. New additive `favorites`/`personal_rating` Issue fields. Scope
confirmed with Tez before building: multi-select only on cards/rows that map 1:1 to a
single issue (Singles surface, Singles-type cards on All, series-detail issue rows,
2000 AD prog cards) — never on series-aggregate cards. Floating bottom toolbar for the
bulk actions. Issue detail page also gets its own standalone favorite-toggle + star
control, independent of multi-select.

**Schema risk found and fixed before writing any endpoint code:** the backlog doc's
"purely additive, no migration needed" assumption (based on the CustomTab/HomeStrip
precedent) doesn't hold here — those were whole new *tables*, and SQLAlchemy's
`create_all()` only creates missing tables, it never adds columns to a table that
already exists. Proved this empirically with a throwaway SQLite file before touching
real code (column absent from `PRAGMA table_info` both before and after `create_all()`
re-ran with the column added to the model). Fixed by adding `_add_missing_issue_columns()`
to `backend/database.py`'s `init_db()` — a one-time, idempotent `ALTER TABLE` per
missing column. Verified against a **scratch copy of the real ~5,500-row
`comicvault_v2.db`** (not just a synthetic test) — columns appeared correctly, default
values landed as expected (`favorites=0`, `personal_rating=NULL`), all 5,429 rows
intact, real file's mtime unchanged afterward.

**Backend (`backend/models.py`, `backend/routers/progress.py`, `backend/routers/library.py`,
`backend/routers/home.py`):**
- `Issue.favorites` (Boolean, default False) and `Issue.personal_rating` (Integer,
  nullable) added.
- Five new bulk endpoints in `progress.py`: `POST /api/progress/bulk/mark-read`,
  `bulk/mark-unread`, `bulk/favorite`, `bulk/unfavorite`, `bulk/rate` — all take
  `{issue_ids: [...]}` (`rate` also takes `rating`, Pydantic-validated 1–5). Missing/
  unknown ids are silently skipped rather than 404ing the whole batch (no ordering
  invariant to protect here, unlike `admin.py`'s home-strip reorder). Extracted
  `_get_or_create_progress()` out of the existing `update_progress()` so the bulk
  read/unread path doesn't duplicate the upsert-or-create logic.
- **Bug caught during this session's own endpoint testing, before it ever reached the
  frontend:** `POST /api/progress/bulk/mark-read` initially 422'd — Starlette matches
  path templates in registration order, and the pre-existing
  `/progress/{issue_id}/mark-read` route (registered first) matched `bulk/mark-read`
  too, with `issue_id="bulk"` failing int parsing. Fixed by moving the new bulk routes
  above the single-issue mark-read/mark-unread routes in the file. Re-verified by curl
  against the scratch server afterward — both the new bulk routes and the pre-existing
  single-issue routes work correctly.
- `favorites`/`personal_rating` added to all four response payloads that needed them:
  `_issue_to_dict()` (issue detail), `get_series()`'s inline dict (series detail page),
  `get_library()`'s inline dict (browse grid), and `home.py`'s `get_2000ad_year()`
  inline dict (2000 AD prog cards). `GET /api/search` was deliberately left alone —
  confirmed the web UI's search box filters client-side over already-loaded
  `/api/library` data and never calls that endpoint.

**Frontend (`frontend/js/app.js`, `frontend/css/style.css`):**
- `makeSelectable(element, issueId)` — shared long-press (Pointer Events,
  ~500ms threshold, cancels on >10px drag) + tap-to-add logic, attached to
  `buildCoverCard()` only when `format_group === 'Singles'`, and unconditionally to
  `buildIssueRow()` and `buildAdProgCard()`. A delegated capture-phase `click` listener
  suppresses navigation on selectable elements while selection mode is active (more
  reliable across browsers than relying on `pointerup`'s `preventDefault()` alone).
  `exitSelectionMode()` called defensively at the top of `switchSurface()`,
  `_renderBrowsePage()`, and `load2000ADYear()` so a re-rendered grid never holds
  stale selected-element references.
- Floating bottom toolbar built once via `ensureSelectionToolbar()` (vanilla DOM,
  matching the existing `el()` pattern) and appended to `document.body` — not static
  markup in `index.html`/`series.html`, since the same toolbar needs to work on both
  pages without duplicating HTML.
- Issue detail page: `buildFavoriteToggle()` + `buildRatingControl()` added next to
  the existing `buildStatusToggle()`, reusing the bulk endpoints with a 1-item
  `issue_ids` list rather than adding separate single-issue endpoints.
- Favorite badge on cards/rows is pure CSS (`.is-favorite::before { content: '★' }`)
  — no DOM node management needed. Personal rating has no card-level visual (per the
  confirmed scope — only the issue detail page shows the star rating).

**Verified** (per CLAUDE.md §6 — scratch DB, no real `Processing` folder touch):
installed `playwright` + Chromium one-off (not added to `requirements.txt` — a
dev-only verification tool, consistent with the project's previous ad-hoc Playwright
use noted in `TESTING.md`). Ran the actual FastAPI app against a scratch copy of the
real DB on a throwaway port, then a 25-check Playwright script covering: long-press →
toolbar appears → tap-to-add → bulk Mark Read → card state updates and backend
confirms via a follow-up `GET /api/issue/{id}`; the critical scope-boundary regression
— a **Series-aggregate card does not enter selection mode** on long-press and a plain
click still navigates normally; the same long-press/Cancel/Done flow on a series-
detail issue row and a 2000 AD prog card; standalone favorite-toggle + star-rating on
the issue detail page, both surviving a page reload; zero console/page errors
throughout. All 25 checks passed. Confirmed the real `comicvault_v2.db` was untouched
throughout (unchanged mtime, no new columns, 5,429 rows) and removed all scratch
artifacts (`scratch_test/` directory, including the scratch DB copy and verification
script) afterward.

**Docs updated:** this entry; `CHANGELOG.md`; `SPEC.md` §7 (schema) and new §20.15
(multi-select scope boundary, documented as a standing rule for future surface work,
plus the create_all/migration correction); `ROADMAP.md` (moved this item out of the
active queue, added the deferred Favorites browse surface as a named follow-up);
`DECISIONS.md` (the create_all column-migration correction, and bulk-endpoint-vs-
client-loop choice); `comicvault-changes.md` (Item 2 marked done).

---

## Session — 2026-06-21: Tier 4 Item 3 — Writer/Artist Entity Dedup (backend + real migration)

**Goal:** Tier 4 Item 3, the largest and explicitly highest-risk item in the backlog
— dedupe people into real entities (one "Alan Moore" row regardless of how many
issues credit him), replacing the raw-CSV writer/penciller/inker/colorist/letterer/
cover_artist Issue fields with a `people` + `issue_credits` junction-table design,
plus a one-time review/merge pass across the real ~5,429-issue library. Tez asked
for no ride-alongs and extra care, and the session was explicitly staged: Session A
(schema, scanner, migration script, candidate detection, review UI — scratch-only)
was meant to end with a checkpoint before anything touched the real DB, with Session
B (real run) requiring a separate go-ahead. In practice, after Tez finished
reviewing the candidates same-day, the two were collapsed into one sitting — see
below for why that was safe to do, and for a real incident in between that delayed it.

**Correction to the backlog doc, found before building:** "same pattern as the new
Genre links on `/issue/{id}`" doesn't apply — verified directly that pattern doesn't
exist yet (genre tags are still plain non-clickable spans, a separate not-yet-built
Tier 2 item). Not built as part of this session (no ride-alongs); Item 3's eventual
click-through UI will need its own mechanism.

**Real data sampled before designing anything** (read-only queries against the live
DB): 3,739 distinct individual names across all 6 credit roles after splitting the
raw CSV fields (which store *multiple* names per issue, e.g. "Al Ewing, Alan Grant,
Pat Mills" — exactly like Genre before it was split). Only 5 exact-normalization
collisions found — far cleaner than the backlog doc feared — which justified a
candidate-detection-and-review approach instead of a full manual pass over thousands
of names.

**Schema (`backend/models.py`):** one `Person` table (id, name unique, created_at) +
one shared `IssueCredit` junction table with a `role` column (not 6 per-role tables
mirroring `IssueGenre`'s pattern) — a person needs one stable id referenceable across
all 6 roles (someone can be writer on one issue, colorist on another), which a
6-table split would multiply migration/sync code six-fold for no benefit. Both new
tables; `create_all()` handles them with no manual `ALTER TABLE` needed (unlike Item
2's case of adding columns to an *existing* table). Old raw CSV columns kept for now
as a rollback safety net (decided with Tez) — to be dropped in a later session.

**Scanner integration (`backend/scanner.py`):** new `_sync_credits()` mirrors the
existing `_sync_genres()` delete-then-reinsert pattern, with get-or-create-by-
exact-name Person lookup. Generalized `_genres()`'s CSV-splitting into a shared
`_split_csv()` helper, reused for all 6 credit tags. Confirmed via direct code read
that `scan_single_file()` is the *only* place Issue credit data is ever written, for
both full scans and every single-issue editor save (editor routers never touch the
DB directly — they rewrite the CBZ's XML and call `scan_single_file()` in-process) —
so this one function is the only code path needing a change for ongoing correctness.

**Real bug found and fixed during scratch testing, before the real run:**
`_split_csv()`/`_sync_credits()` didn't dedupe a literal repeated name within one
CSV field. Real data has this — 175 issues (114 penciller + 61 inker) have a field
like `"Chris Shehan, Maan House, Chris Shehan, Maan House"` — which crashed the
migration on every one of them with a UniqueConstraint violation. Fixed by
deduplicating (order-preserving) at the CSV-split layer, which also defensively
covers Genre's identical latent vulnerability (zero real instances today, but the
same crash risk existed there too, just never triggered).

**Candidate-duplicate detection + review (one-time, throwaway tooling):**
`backend/migrate_people.py` ran two passes globally across all 6 roles combined —
exact-normalization (5 pairs) and a `difflib`-fuzzy pass bucketed by surname token
to avoid an O(n²) scan over 3,738 names — producing 76 candidate pairs. Reviewed via
a small standalone throwaway FastAPI app (`backend/people_review_app.py`, isolated
from the main app, never registered in `main.py`) showing each pair with issue-count/
role/sample-series context. **Result: 35 confirmed merges, 41 correctly kept
separate** — including a genuine deliberate-disambiguation pair the detection
correctly surfaced rather than auto-merging, `"Matt Smith (UK)"`/`"Matt Smith (US)"`.
Full merge list recorded below for the permanent record (the working JSON file was
scratch tooling, deleted after the real run):

Merges applied (other spelling → canonical): A.L. Kaplan→A. L. Kaplan, Ande Parks→
Andre Parks, Benito J. Cereno→Benito Cereno, Charles M. Schulz→Charles Schulz,
Christopher→Tom Christopher, Cynthia von Buhler→Cynthia Von Buhler, Devmayla
Pramanik→Dev Pramanik, George C. Romero→George A. Romero, H.P. Lovecraft→H. P.
Lovecraft, J. R. R. Tolkien→J R R Tolkien, J.M. DeMatteis→J.M DeMatteis, JD Faith→
J.D. Faith, Jake Lynch→Jay Lynch, Jed Alexander→J Alexander, Jim Alexander→J
Alexander, Joana Lafuente→Joana LaFuente, John K. Snyder III→John K Snyder III,
Jonathan Howard→John Howard, Joshua George→Josh George, Kel Mcdonald→Kel McDonald,
Kevin Laporte→Kevin LaPorte, Kristian Rossi→Christian Rossi, Mikaël Ross→Mikael
Ross, Patrricio Delpeche→Patricio Delpeche, Rob Harrington→Robert Harrington, Robin
Taylor→Rob Taylor, Shof Coker→Shofela Coker, Stewart Moore→Stuart Moore, Stéphane
Levallois→Stephane Levallois, Thomas J. Campbell→Thomas Campbell, Tiernan
Trevallion→Tiernen Trevallion, Tommi Parrish→Tom Parrish, VOFAN→Vofan, Wiliam Roy→
William Roy, Will Simpson→William Simpson.

**Incident during the build — full account, not minimized:** while editing
`backend/models.py`/`database.py`/`scanner.py` directly in the live working tree,
the live, continuously-running ComicVault reader server (managed by `tray_app.py`,
up since before this session) restarted at some point for an unrelated reason and
picked up the new code from disk, ran `init_db()` against the **real**
`comicvault_v2.db`, and a real editor save / rescan on 2 issues (`Harold and Purple
Crayon`, `Dishonored: The Dunwall Archives`) wrote 3 real `Person` rows and 4
`IssueCredit` rows via the new (at that point only scratch-tested) `_sync_credits()`
— directly breaking the explicit "Session A never touches the real DB" boundary
agreed with Tez. Root cause: the scratch-only isolation built into this session's
own test scripts (overriding `DB_PATH` before importing `backend.database`)
protected nothing about the *live, already-running* server, which reads shared
source files directly off disk independent of anything a session does. Caught via a
routine post-task mtime/table-existence check (not by the live app surfacing an
error) and reported to Tez immediately and in full, including admitting a permission-
system block on a follow-up read that I respected rather than working around.

**Resolution, per Tez's explicit decisions:** (1) leave the 7 stray rows as-is —
inert today, and the real migration's per-issue delete-then-reinsert would overwrite
the affected issues' credits anyway; (2) for the rest of this session, stop the live
server before touching shared source files, rather than the more involved option of
moving the work into an isolated git worktree; (3) since the merge review was already
done, collapse Session A/B into one sitting rather than deferring the real run.
`git stash` safely shelved the in-progress edits while Tez stopped the server via the
tray app, then the stash was restored once confirmed down (verified independently via
`Get-NetTCPConnection` before proceeding, not just taken on trust).

**Real run:** backed up `comicvault_v2.db` to a timestamped copy
(`comicvault_v2.backup_pre_people_migration_20260621_150534.db`, gitignored
alongside the main DB) immediately before running. Migration ran against the real DB
— 3,702 Person rows, 34,425 IssueCredit rows (one less Person / 3 fewer credits than
the scratch dry-run's 3,703/34,428, fully explained by the 2 issues legitimately
re-scanned during the incident window, after the scratch snapshot was taken — not a
migration bug, confirmed by checking `date_modified`). Spot-checked "John Wagner"
resolves to exactly one Person with exactly 1,547 writer credits, matching the live
substring count sampled before any code was written. Re-ran the migration a second
time against the real DB — identical counts, confirming idempotency for real, not
just on scratch. Confirmed `issues` table itself fully intact (5,429 rows, all 6 raw
credit columns still present, `PRAGMA integrity_check` → `ok`).

**Cleanup:** stopped the throwaway review-UI server, deleted `scratch_test/`,
`backend/migrate_people.py`, and `backend/people_review_app.py` (one-time tooling,
purpose complete, decisions captured here permanently). DB backup file kept
(gitignored, the actual rollback mechanism if ever needed).

**Remaining (a future session, not started):** frontend — remove the Writer/Artist
filter dropdowns, build the click-through UI on `/issue/{id}` (credited names become
links to a filtered issue list, reusing the existing `fieldview` surface plumbing),
update `matches_field()`/`/browse/writers`/`/browse/artists` to resolve against
`person_id` instead of raw string equality, and wire the editor's fuzzy warn-on-save
for Writer/Penciller. Dropping the old raw CSV columns is deferred further still,
until the frontend work has shipped and run for real with no issues found.

**Docs updated:** this entry; `CHANGELOG.md`; `comicvault-changes.md` (Item 3 marked
backend-done/frontend-remaining); `BUGS.md` (the `_split_csv` duplicate-name defect);
`DECISIONS.md` (junction-table shape, old-columns-kept-temporarily, the live-server-
isolation lesson).

---

## Session — 2026-06-21: Tier 4 Item 3 — Session C (frontend + editor warn-on-save)

**Goal:** finish Tier 4 Item 3 — the frontend half deferred from the backend+migration
session above. Server stopped before any shared source-file edits this time (per
the decision from the prior session's incident), restarted by Tez partway through to
spot-check, stopped again before resuming.

**Built:**
- `backend/path_utils.py` `matches_field()` — `writer`/`artist` now resolve against
  `Person.id` via `issue_credits`, not raw string equality against the old columns.
- `backend/routers/library.py` — `/browse/writers`/`/browse/artists` rewritten to
  group by deduped `Person` (fixes the exact bug Item 3 exists to solve: a 5-person
  comma-joined string no longer shows up as one dropdown option). `_issue_to_dict()`
  gained `writers`/`pencillers` arrays (`{person_id, name}` per credited person) for
  the new clickable links. New `GET /api/people/fuzzy-match` — closest existing
  `Person` to a typed name, `difflib`-based, same approach as the one-time
  migration's candidate-detection pass, for the editor's save-time warning.
- `frontend/js/app.js` `buildIssueDetail()` — Writer/Artist credits are now `<a>`
  links to `/?surface=fieldview&field=writer&value=<person_id>`, reusing the
  existing `fieldview` plumbing (built for Home Strips, repurposed here) rather than
  inventing new routing. Removed the `writerFilter`/`artistFilter` dropdowns and all
  their state/population/filtering/binding code; `frontend/index.html` had the two
  `<select>` elements removed. (Found and left alone: the backlog's referenced
  "Genre links on `/issue/{id}`" precedent doesn't actually exist yet — genre tags
  are still plain spans, a separate not-yet-built Tier 2 item — so this click-through
  is Item 3's own new mechanism, not a reuse of an existing one.)
- `frontend/js/admin.js` — found and fixed a real second consumer of
  `/browse/writers`/`/browse/artists` while exploring the field-filter mechanism:
  the Home Strips builder's field-value picker, which stores the picked value
  verbatim as `HomeStrip.field_value`. Since that value is now a `person_id`, not a
  display string, the picker (`HS_FIELD_ENDPOINTS`, `updateHsFieldValueOptions()`)
  needed a separate label-vs-stored-value split, and `hsBasisSummary()` needed a
  small lazy id→name cache so an admin-created Writer/Artist strip doesn't show a
  raw id in its summary line. Zero real strips use writer/artist today, so this is
  forward-looking correctness, not a live bug fix.
- `frontend/js/editor_basic.js` / `editor_full.js` — non-blocking save-time fuzzy
  warning for Writer/Penciller (Decision 3 from the backend session): typing a name
  close to but not exactly matching an existing `Person` shows a native `confirm()`
  ("Did you mean 'X'? You typed 'Y'.") before the save proceeds; either choice still
  saves, nothing is blocked.

**Verified (scratch DB + scratch server, port 8099, real server stopped throughout
code edits):** a 10-check Playwright pass covering clickable credit links, correct
fieldview filtering (John Wagner → exactly his 13 series), both dropdowns gone,
`/browse/writers` shape, zero console errors. Separately confirmed the admin Home
Strips picker shows names with `person_id` values underneath. All passed.

### Incident: a real production file was modified during editor-save testing

Verifying the editor's fuzzy-warn dialog meant actually clicking Save in the Basic
Editor — and that endpoint rewrites the real CBZ archive, not just the DB. The first
attempt used `/issue/89`, assuming (from memory of an *earlier* scratch copy several
hours earlier in this same session) that it was `2000AD #009`. It wasn't — ids are
not stable across different scratch-DB/migration runs, a lesson this session had
*already* learned and written down once, then failed to re-apply rigorously here.
Issue 89 in the *current* scratch copy was actually `2000AD #011 (1977).cbz`, a real
file on `L:\`. The save succeeded exactly as designed (no bug in the feature), so it
correctly rewrote that real file's `Writer` tag to the test value — and because the
Basic Editor's save submits the *entire* form, not just the field being tested, it
also rewrote `Summary`, incidentally exposing a separate, pre-existing, unrelated
defect (BUG-007 — multi-line textarea fields round-trip with doubled line breaks).

Checked the wrong filename ("#009") afterward and saw no change, wrongly concluding
the real file was safe. The actual safety check — re-querying issue 89's real
`file_path` in the current copy — wasn't done until directly asked to investigate
further by building a true fake-CBZ fixture (a disposable comic with its own
throwaway DB row, in `scratch_test/fake_library/`, never touching any real path).
That fake-fixture test reproduced the save cleanly and proved the actual code has no
bug whatsoever — confirming the entire incident was a test-construction mistake, not
a defect in anything built this session.

**Restoration, done with Tez's explicit go-ahead:** the original `Writer` value
(`"Gerry Finley-Day, John Wagner, Kelvin Gosnell, Roy Preston, Tom Tully"`) and
`Summary` value were both still intact in the morning's pre-migration DB backup
(`comicvault_v2.backup_pre_people_migration_20260621_150534.db` — neither field is
touched by the people migration itself). Restored via the app's own
`write_comicinfo_to_cbz()`, surgically replacing only the two affected tags in the
*current* on-disk XML (confirmed via a line-by-line diff before writing that nothing
else would change), then ran a normal rescan to resync the real DB. Verified
afterward with a full field-by-field comparison of the real DB's row against the
backup: **zero differences** (excluding `date_modified`, which legitimately reflects
the resync). `PRAGMA integrity_check` → `ok`, issue count still 5,429.

**Lesson, recorded in `DECISIONS.md`:** a "scratch DB" copy is only actually scratch-
safe for DB-only features. Every `Issue.file_path` inside any copy — scratch or
real — still points at the one physical file on disk. Any test that exercises a
file-*writing* endpoint needs a genuinely fake, disposable file with its own
throwaway DB row, never a real path borrowed from a copied DB. Also: re-derived
identities (ids) don't carry over between separate scratch copies — re-query, don't
remember.

**New bug found, not fixed (out of scope, pre-existing, unrelated to Item 3):**
BUG-007 — Basic Editor's Summary field (and likely any multi-line textarea field)
gains doubled blank lines on every save. Logged in `BUGS.md`, left open for a future
session.

**Cleanup:** scratch server stopped, `scratch_test/` (scratch DB copy, fake CBZ
fixture, verification scripts) removed entirely. The real-DB backup from the prior
session is kept — it's the actual rollback mechanism, not scratch tooling, and it's
exactly what made today's restoration possible with full confidence.

**Tier 4 Item 3 is now fully complete** — backend, one-time migration, and frontend
all shipped. Only the deferred cleanup (dropping the old raw CSV credit columns,
after a release cycle with no issues found) remains, tracked in `ROADMAP.md`.

**Docs updated:** this entry; `BUGS.md` (BUG-007); `DECISIONS.md` (the scratch-DB/
file_path lesson); `CHANGELOG.md`; `comicvault-changes.md` (Item 3 fully done);
`ROADMAP.md` (Item 3 removed from active queue, only the deferred column-drop
remains); `SPEC.md` (new endpoint + response shape documented).

---

## Session — 2026-06-21: Tier 1 — Back button inconsistency (fix)

Admin's Back link (`frontend/admin.html`/`admin.js`) previously hardcoded
`href="/"`, losing whatever surface the user actually came from. Fixed by giving
the link `id="adminBackLink"` and wiring `initAdminBackLink()`: the label is
derived from a `from` query param (Home/Series/Singles/All/2000 AD, or a custom
tab name pulled from `sessionStorage`'s `cv_custom_tab_names`), and the click
handler calls real `window.history.back()` instead of reconstructing a guessed
destination — so it's automatically correct for every current and future entry
point into Admin with no per-entry-point wiring.

Verified live: confirmed `/static/js/admin.js` served by the running app matches
the source on disk (the fix is live, not stale-cached), and the label/back
navigation behave correctly from multiple entry points (Home's gear icon, a
custom tab).

**Docs updated:** this entry; `comicvault-changes.md` (Tier 1 bullet removed);
`CHANGELOG.md`.

---

## Session — 2026-06-22: Tier 1 — Back button inconsistency (full fix)

The fix above only covered Admin. **Root cause of the gap: the session that did
this work was terminated by an error before it reached the Issue and Series
detail pages**, which had the exact same "guessed destination" problem — it
just went unnoticed at the time because the close-of-session checklist never
ran to catch it.

Confirmed by Tez via a real repro: from Home, clicking into a random genre's
issue (e.g. "To Drink and to Eat" #1) landed on the issue page, and Back showed
the series name and routed to `/series/{id}` — not back to Home, where the user
actually came from. Root cause in `app.js`:
- `initIssue()` hardcoded the back link to `/series/{id}` (named `Series`
  issues) or a `from`-param-guessed surface (`Singles`), never real history.
- `buildSeriesHeader()` did the same `from`-param guess, with no `history.back()`
  call at all — a plain anchor `href`.

Fixed both the same way as Admin: literal `← Back` label, click handler calls
`window.history.back()` when `window.history.length > 1`, falls back to `href="/"`
otherwise (Tez's choice — always Home on no-history, not the old guessed
destination). Admin's label was also simplified from the dynamic surface name to
plain `← Back`, so all three back links now look and behave identically.

Cleanup: the `from`-param label/destination logic this replaced — `LABELS`/
`_LABELS` objects, `customTabLabel()`, and the `cv_custom_tab_names`
`sessionStorage` cache that fed it — had no other callers once removed, so they
were deleted rather than left as dead code. The `from` query param itself is
still generated and threaded through some link hrefs elsewhere (e.g. home →
issue/series links); that plumbing is now inert for back-link purposes but
harmless, and wasn't chased further since it's outside this bug's scope.

Verified: confirmed via the running server that `/static/js/app.js` and
`/static/js/admin.js` no longer contain the removed label logic, and that
`/issue/1`'s served page carries the new `← Back` default text. Full interactive
click-through (Home → genre → issue → Back; series page Back; Admin Back; the
no-history direct-link case) needs a real browser to confirm end-to-end — no
browser automation tool was available this session, so that step is left for
Tez to confirm live.

**Docs updated:** this entry; `comicvault-changes.md` (Change Log correction
row added, superseding the 2026-06-21 row rather than rewriting it);
`CHANGELOG.md`.

---

## Session — 2026-06-22: Tier 1 — Back button inconsistency (2000 AD Years page)

Tez found a third instance: the 2000 AD Years page's "← All Years" button
(`adBackBtn` in `index.html`, click handler in `app.js`'s `load2000ADYear()`)
had the same inconsistent labeling as the other three before today's fix.

**Root cause of the miss is a process gap, not a search gap.** This button was
in the grep results during the earlier sweep — it just got silently judged out
of scope (it's a `<button>` toggling two `<div>`'s `hidden` state within the
same page load, not an `<a>` doing real page navigation) and that judgment call
was never surfaced to Tez to confirm or override.

**Fix:** label changed to `← Back` for visual/textual consistency with the
other three. **Behavior deliberately left unchanged** — selecting a year never
pushes a browser history entry (no URL change, pure client-side state), so
wiring this to `window.history.back()` would jump out of the 2000 AD tab
entirely (back to whatever page preceded it) rather than return to the year
grid. Tez confirmed: keep the existing toggle-based click handler, label-only
change. Confirmed live via the running server that `/` now serves `← Back` for
this button.

**Process note for future sweeps:** when grepping for a UI pattern across the
codebase, surface every match found to Tez with a one-line note on why each
either is or isn't in scope, rather than filtering silently — so a wrong
judgment call gets caught immediately instead of resurfacing as a separate bug
report later.

**Docs updated:** this entry; `comicvault-changes.md` (second Change Log
correction row); `CHANGELOG.md`.


---

## Session — 2026-06-22: Tier 1 — List view read-state text colour

Tez reported list view's read-state cards looked clashing/hard to read
compared to grid view. Took two misfires to land on the right spot:

1. First attempt edited `.status-btn.read` and `.issue-row` text colours in
   `style.css` — that's the series-detail issue-row markup (`buildIssueRow()`
   in `app.js`), not the All-tab list view Tez meant. Reverted in full once
   the mismatch was clear from a screenshot of `/series/15?from=series`.
2. Correct location: the All tab's list view is `buildCoverCard()` rendered
   inside `#coverGrid.list-view` (CSS at `style.css` ~line 317 onward, "List
   view override — spec 20.5"). Grid view's read/part-read cards already
   override `--text-3`'s dim grey to white for `.cover-title`,
   `.cover-count`, `.cover-year` (style.css ~line 464). The list-view-only
   fields — `.list-genres`, `.list-pub-writer`, `.list-summary` — were never
   added to that override block, so they stayed dim grey on the green/black
   read-state backgrounds while everything else went white/bold.

**Fix:** added `.list-genres` / `.list-pub-writer` / `.list-summary` to the
existing `state-read`/`state-part-read` text-colour override in `style.css`,
same `rgba(255, 255, 255, 0.82)` value already used for `.cover-count`/
`.cover-year`.

**Verified:** Tez confirmed live in-browser on the All tab, list view.

**Docs updated:** this entry; `CHANGELOG.md`; `comicvault-changes.md` (Tier 1
bullet removed, since it's now resolved).

---

## Session — 2026-06-22: Tier 2 — full batch

All 9 Tier 2 ride-along items built and verified live, one at a time, each
confirmed by Tez before moving to the next.

1. **Genre tags clickable on `/issue/{id}`.** Each tag now links to
   `/?surface=fieldview&field=genre&value=<genre>`, reusing the exact same
   fieldview plumbing the Tier 4 Item 3 Writer/Artist credit links already
   use (`field_name == "genre"` was already supported in `matches_field()`,
   `backend/path_utils.py` — no backend change needed). Series-detail page's
   own genre tags (`buildSeriesHeader()`) were deliberately left as plain
   spans — out of scope, the backlog item named `/issue/{id}` specifically.

2. **"Clear" filter button restyled.** Was a bare accent-coloured text link
   (`.filter-clear`, `style.css`) — now a proper bordered button matching the
   other filter controls. Click behaviour unchanged (`filterClear` handler
   untouched).

3. **"Format" added to the Grouping option menu.** New `<option value="format">`
   in `index.html`'s `#groupBySelect`; `renderGrouped()` in `app.js` groups by
   `s.formats[0]` the same way it already does for genre/writer.

4. **"Mark all read" added to the 2000 AD Year page.** New button
   (`#adMarkAllBtn`) next to the existing `← Back` in `#adYearDetail`'s nav
   row. New `markAllReadAdYear(issues, year)` function — marks every unread
   prog in the open year via the bulk progress endpoint, then re-fetches and
   re-renders the year (`load2000ADYear(year)`) so card states refresh from
   the server rather than hand-patching DOM classes. Verified against 2000 AD
   1977 (45 issues) — Tez confirmed leaving that test data marked read rather
   than reverting it.

5. **Admin pagination: 25 added as an option, 50 still default.** One new
   `<option value="25">` in `admin.html`'s `#pageSizeSelect` — `app.js`'s
   `pageSize` default and `admin.js`'s `initPagination()` fallback were
   already `'50'`, untouched.

6. **Admin "Save Advanced Settings" → "Save Location", moved onto the path's
   row.** Confirmed before renaming that this button only ever patches
   `library_root` (`saveAdvanced()`, `admin.js`) and that the fieldset around
   it contains nothing else — unlike Genre/Format (auto-save on every
   add/remove, no save button at all) and Custom Tabs/Library Folders/Exclude
   Patterns (also auto-save via immediate `patchConfig()` calls), this was
   the only setting still behind an explicit save action, and it only does
   one thing. Safe to rename. Tez additionally asked for the button to sit
   on the same line as the path input rather than below it — restructured
   `admin.html`'s field markup into `.admin-field-input-row` (input + button
   in a flex row, hint text below spanning full width).

7. **Admin: Scan Now card border — white when idle, green while scanning.**
   New `#scanNowCard` border rules in `style.css`; `is-scanning` class toggled
   in `admin.js`'s `showScanProgress()`, `updateScanUI()`, and the `doScan()`
   catch branch. Had to scope the CSS to the `#scanNowCard` id rather than
   the `.scan-now-card` class, since that class is shared with the Missing
   Records card. Verified with a real scan (5,429 files, 0 new/changed — i.e.
   genuinely read-only) — border was green mid-scan, reverted to white on
   completion.

8. **Admin: Clean Up card border — green when files are pending cleanup.**
   New `#missingRecordsCard.has-pending` rule; class added when
   `missingCount > 0` in `renderScanSection()`, removed in `doCleanup()` on
   success. Library currently has 0 missing records, so this was verified by
   adding the class via a one-off JS console call (not real data) rather than
   manufacturing missing files — reverts to normal on next page load.

9. **Admin: dashboard width now aligns with the header.** Root cause:
   `.admin-main { padding: 24px 0 60px; }` (style.css) used the 4-value
   shorthand, which zeroes left/right padding — overriding the inherited
   `.container { padding: 0 20px; }` rule and making Admin's content sit
   flush to the outer container edge while the header's content (logo, gear
   icon) stayed inset by the normal 20px. This wasn't caught by initially
   comparing `.container` bounding boxes (those matched exactly — the bug is
   inside the box, not the box itself); found once Tez pointed at the actual
   misaligned elements (logo vs Back button, gear vs Password Reset). Fixed
   by splitting the shorthand into `padding-top`/`padding-bottom` only.
   Verified: logo/Back button left edges and gear/Password-Reset right edges
   are now pixel-identical (`248.5` / `1648.5` respectively at the tested
   viewport).

**Process note:** browser-side verification kept hitting stale cached
`app.js`/`admin.js` in the Chrome MCP tab (heuristic HTTP caching — no
`Cache-Control` header is set on `/static/*`, so Chrome can serve a cached
script even on a fresh tab/navigation without revalidating). Worked around
per-check by re-fetching the script with `cache:'reload'` and `eval`-ing it
into the page; a real hard refresh (Ctrl+Shift+R) or full browser restart
fixes it for normal use. Not fixed at the server level this session (would
mean adding explicit `Cache-Control` headers to the static mount) — flagging
as a possible future `ROADMAP.md` item if it keeps causing confusion during
manual testing.

**Docs updated:** this entry; `CHANGELOG.md`; `comicvault-changes.md` (Tier 2
list cleared); `ROADMAP.md` (Tier 2 line updated to none-open).
