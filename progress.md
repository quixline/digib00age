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

