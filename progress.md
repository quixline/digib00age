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

