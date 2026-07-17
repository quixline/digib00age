# ComicVault — V1 Project Specification

> **How to use this document**
> Paste this entire file into any AI coding session (Claude, Copilot, etc.) before writing any code.
> It contains every decision made during the planning phase. Do not deviate from these decisions
> without noting the change at the bottom of this file.
>
> **⚠️ READ THIS FIRST — Section 20 (V1.1 UI/UX Revisions).**
> Phases 1–3 are built against Sections 1–19. After live testing, a round of UI/UX
> changes and new features was agreed. These are captured in **Section 20**, which is the
> authoritative source for the next build round (Phases 4 & 6 and the Flutter app).
> Where Section 20 modifies an earlier section, Section 20 wins. The original sections are
> kept intact for context — do not treat them as the final word where Section 20 overrides them.

---

## 1. Project Overview

> **Visible brand name (added 2026-07-07, v2.6 Item 1 Phase A):** the web UI's
> displayed product name is now **digib00age** (header logo, page titles,
> favicon) — see `docs/v2.6/comicvault-changes-v2.6.md` Item 1. **ComicVault**
> remains the repo/internal/codebase name throughout this doc, the DB, API
> routes, `config.json`, and the tray app — nothing below changes meaning, this
> note just explains why the running app's UI no longer literally says
> "ComicVault" anywhere.

**ComicVault** is a personal, local comic book server for a single user on a home network.
It serves a collection of up to 10,000 CBZ files with rich metadata from embedded ComicInfo.xml files.

| Property | Value |
|---|---|
| Host OS | Windows 10/11 |
| Access | Single user, home network (desktop + Android tablet) |
| Backend language | Python 3.11+ |
| Database | SQLite |
| Collection size | Up to 10,000 issues |
| File format | CBZ only (all files confirmed converted) |
| Metadata source | ComicInfo.xml embedded inside each CBZ |
| Reader app | Flutter (Android + Windows, single codebase) |

---

## 2. Architecture — Split Application

Two independent servers sharing one SQLite database. One system tray app manages both.
A Flutter app (Android + Windows) connects to the reader server over the home network.

```
ComicVault Tray App  (pystray, starts on Windows login)
        |
        |--- Reader Server   FastAPI + Uvicorn   localhost:8000   (home network accessible)
        |--- Editor Server   Flask (existing)    localhost:8001   (localhost only)
                |
                └── Shared:  L:\Comic Archives\   (CBZ files)
                             backend\comicvault.db (SQLite)
                             backend\thumbnails\   (generated covers)

Flutter App  (installed on Android tablet + Windows PC)
        |
        └── Connects to:  http://<host-pc-ip>:8000/api   (home network)
                          Local CBZ files on device       (travel / offline)
```

### Why split
- Editor already exists in Flask — no rewrite risk
- Reader crash does not affect editor and vice versa
- Editor is localhost-only (not exposed to home network)
- One `start.bat` / tray app launches both processes

### Sync between apps
When the editor saves a ComicInfo.xml back into a CBZ, it calls:
```
POST http://localhost:8000/api/scan/file?path=<file_path>
```
The reader rescans that single file and updates the DB immediately.

---

## 3. System Tray App

**File:** `tray/tray_app.py`
**Library:** `pystray` + `Pillow` (+ `pywin32` for the autostart shortcut, 2026-06-19)

> **Status (2026-06-19):** this section now reflects the live build. See the change
> log for the 2026-06-17 deviations (menu instead of a popup window, no separate
> editor subprocess) and the 2026-06-19 menu redesign below.

### Behaviour
- No window on startup — sits silently in system tray
- Either click opens a native right-click-style context menu (not a custom popup
  window — see 2026-06-17 change log entry) with:
  - **Open Library** → `webbrowser.open("http://localhost:8000")`
  - **Admin** → `webbrowser.open("http://localhost:8000/admin")`
  - **Metadata Editor** → `webbrowser.open("http://localhost:8000/editor")` (same
    FastAPI app, no separate process/port — see `EDITOR_SPEC.md` Section 2)
  - **Start ComicVault at login** (checkable) → creates/removes the Windows Startup
    shortcut; checked state reflects whether the shortcut currently exists
  - **Stop Server** → stops the reader subprocess only; the tray app keeps running
  - **Start Server** → restarts the reader subprocess; no-op if already running
  - **Close** → stops the reader subprocess, then exits the tray app
- Status (starting/running/stopped) is shown only via the tray icon's coloured dot
  (yellow/green/red) — not via menu text, to avoid corrupting the native menu's
  command-ID → callback mapping (see 2026-06-17 change log entry)
- **Icon base glyph (updated 2026-07-13):** the coloured dot sits over the
  digib00age favicon mark (`frontend/images/favicon.png`), not the original
  purple book glyph — see `DECISIONS.md` "Tray icon base glyph". Visual only;
  the tray app's process/menu/log name stays "ComicVault" per Section 1.
- Context menu follows Windows' own "Apps use dark mode" setting (2026-06-19) — it
  cannot force dark independent of that OS setting
- Health check every 30 seconds — restarts the reader if it has died, unless it was
  stopped deliberately via "Stop Server"/"Close"

### Startup sequence
1. Launch FastAPI reader as a subprocess on port 8000
2. Sit in tray, show green status once the port responds

---

## 4. Configuration

**File:** `config.json` (project root)
**Rule:** Paths are NEVER hardcoded anywhere in the codebase. Always read from config.

```json
{
  "library_root": "L:\\Comic Archives",
  "series_folder": "Series",
  "singles_folder": "Singles",
  "reader_port": 8000,
  "editor_port": 8001,
  "thumbnail_size": 300,
  "thumbnail_dir": "backend/thumbnails",
  "db_path": "backend/comicvault.db",
  "autostart_scan": false
}
```

If the drive letter changes (e.g. after HDD replacement), only `library_root` needs updating.
Next rescan re-links all file paths. Reading progress is preserved.

---

## 5. Folder Structure on Disk

### Root
```
L:\Comic Archives\
```

### Series (multiple CBZ files per folder)
```
L:\Comic Archives\
  #\Series\'68 Homefront (2024)\'68 Homefront #1 (2014).cbz
                                 '68 Homefront #2 (2014).cbz
                                 '68 Homefront #3 (2014).cbz
  C\Series\Criminal Volume 1\Criminal Vol 1 #1.cbz
           Criminal Volume 2\Criminal Vol 2 #1.cbz
           Cyberpunk 2077 - Blackout (2022)\Cyberpunk 2077 - Blackout #1.cbz
           Cyberpunk 2077 - Kickdown (2025)\Cyberpunk 2077 - Kickdown #1.cbz
```

### Singles (exactly one CBZ per folder, each title in its own folder)
```
L:\Comic Archives\
  #\Singles\The 13th Artifact (2016)\The 13th Artifact #1 (2016).cbz
  A\Singles\Another Single (2019)\Another Single #1 (2019).cbz
```

### Folder structure rules
| Rule | Detail |
|---|---|
| Alpha index folders (`#\`, `A\`, `B\`) | Navigation only — never stored in DB, transparent to scanner |
| `Series\` in path | Sets `format_group = "Series"` |
| `Singles\` in path | Sets `format_group = "Singles"` |
| Series CBZ files | Sit directly in the series folder — no sub-folders |
| Singles CBZ files | One CBZ per folder — always |
| CBR files | Supported alongside CBZ since v2.4 Item 5 (2026-06-30) — same folder rules apply, scanner treats `.cbz`/`.cbr` identically for folder-structure purposes. Was previously "none" in V1; see §6.1 |

---

## 6. Scanner Rules

**File:** `backend/scanner.py`

### How it works
- Uses `os.walk()` from each configured root folder
- Matches files ending in `.cbz` or `.cbr` (case-insensitive) — CBR support added
  v2.4 Item 5, see §6.1 below
- Opens each archive as a zip (`.cbz`) or RAR (`.cbr`) archive accordingly
- Finds `ComicInfo.xml` anywhere in the archive, any folder depth (fixed BUG-018,
  2026-07-02 — previously only matched a root-level entry; now uses the same
  `find_xml_in_archive()`/`extract_xml_from_archive()` helpers the Basic/Full
  Editors already used, `backend/editor/archive_io.py`)
- Parses XML → writes to DB

### 6.1 CBR support (scoped v2.4 Item 5, 2026-06-30 — built and manually tested
v2.4 Item 11, 2026-07-01)

CBR files are scanned, thumbnailed, and served identically to CBZ — the only
difference is which library opens the archive. `.cbz` uses Python's built-in
`zipfile`; `.cbr` uses `rarfile` (extraction-only — already a proven dependency via
CAPT's converter, `arc_conv_cb_proc.py`/`arc_conv_helpers.py`, no new library
introduced). Requires an `unrar`-compatible extraction backend (UnRAR.dll or
unrar.exe) present on the host — **confirmed present and resolvable** on the
dev machine (`C:\Program Files\WinRAR\unrar.exe`, on PATH, `rarfile.UNRAR_TOOL`
resolves it with no explicit override needed) as the first build sub-step, before
any CBR-dependent code was written. Shared dispatch lives in
`backend/archive_formats.py` (`archive_namelist()`/`archive_read_bytes()`), used
by `scanner.py`, `reader.py`, and `backend/editor/archive_io.py` so the
zipfile-vs-rarfile branch isn't repeated three times.

**CBR is read-only at the archive level — ComicVault (scanner, editor, any
future tool) never writes a `.cbr` file.** RAR archive *creation* requires a paid
WinRAR install (CAPT's `create_rar_archive()` shells out to a `rar` CLI tool and
errors if missing) — not viable as an app dependency, especially given the
possible-public-release direction. See `EDITOR_SPEC.md` §3.1/3.2 for what this
means for the metadata editor (short version: editing a CBR's metadata rebuilds it
as `.cbz` on save, the original `.cbr` is deleted once the new file is verified
written) and `DECISIONS.md` for the full rationale, including why this reverses
`EDITOR_SPEC.md`'s original "library is all-CBZ, CBR support dropped" decision.

**Damaged/CRC-error archives:** unlike CAPT's converter (which has a tolerant
extraction path, `ignore_crc_errors`), the scanner fails soft on a damaged
CBR — flag/skip the file rather than crashing the whole scan pass, same
`zipfile.BadZipFile` fallback-to-filename-metadata path already used for a bad
CBZ, extended to `rarfile`'s equivalent exceptions
(`archive_formats.BAD_ARCHIVE_EXCEPTIONS`). Verified: a truncated/corrupt CBR
scans in with `metadata_source="filename"` and the scan completes normally
(no crash, no error count) — same "can't fully trust this row" spirit as the
`missing = True` pattern for files that vanish from disk.

**Flutter local/offline mode is a known, accepted gap.** The Flutter app's
`archive` package (server-mode page-serving is unaffected — it calls the REST API,
which is already format-agnostic from the client's side) has no RAR support, so a
`.cbr` copied to a device for offline/travel reading won't open locally. Not
addressed by v2.4 Item 5; flagged for whoever revisits Mobile Reader work
(`ROADMAP.md` "Paused indefinitely").

### Incremental rescan (never full rebuild)
| Case | Action |
|---|---|
| File in folder, not in DB | INSERT new row |
| File in DB, `date_modified` changed | Re-parse XML, UPDATE row |
| File in DB, not found on disk | Flag as `missing = True` — do NOT delete |
| File unchanged | Skip |

### Cover / thumbnail generation
- Open CBZ, sort image filenames alphabetically, take the first image
- Resize to `thumbnail_size` px wide (from config) using Pillow
- Save as `backend/thumbnails/{issue_id}.jpg`
- Series cover = cover of the lowest-numbered issue in the series

### Fallback if ComicInfo.xml is missing or corrupt
Parse filename using pattern: `Series Name #Number (Year).cbz`
- Everything before `#` → series name
- Digits after `#` → issue number
- 4-digit number in parentheses → year
- Set `metadata_source = "filename"` (vs `"xml"`) so admin can identify these

### Format group detection
Determined from folder path, not from XML Format field:
```python
if "Singles" in file_path:
    format_group = "Singles"
elif "Series" in file_path:
    format_group = "Series"
```

---

## 7. Database Schema

**File:** `backend/comicvault.db` (SQLite)
**ORM:** SQLAlchemy

### `issues` table

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | |
| `series` | TEXT NOT NULL | From `<Series>` — grouping key |
| `volume` | INTEGER | Nullable |
| `number` | TEXT | Store as string — "1", "Annual", "½", NULL for singles |
| `title` | TEXT | Same as series in this collection (always kept in sync) |
| `year` | INTEGER | Cover year |
| `month` | INTEGER | Nullable |
| `publisher` | TEXT | |
| `format` | TEXT | Raw value: "One Shot", "Annual", "TPB", "Series", "Limited Series" etc. |
| `format_group` | TEXT | Computed: "Series" or "Singles" |
| `summary` | TEXT | Plot description |
| `story_arc` | TEXT | Nullable |
| `story_arc_number` | INTEGER | Nullable — position within arc for reading order |
| `writer` | TEXT | Raw CSV e.g. "Dan Abnett, Ian Edginton". Kept 2026-07-15 (see §21 change log) — still powers search/Group-by-Writer/series-card display, not yet migrated to `people`/`issue_credits` |
| `penciller` | TEXT | Raw CSV. Same status as `writer` above ("Artist" in the UI) |
| `characters` | TEXT | Raw CSV |
| `teams` | TEXT | Raw CSV |
| `locations` | TEXT | Raw CSV |
| `age_rating` | TEXT | |
| `language` | TEXT | Full word e.g. "English" — check both `<Language>` and `<LanguageISO>` tags |
| `black_and_white` | BOOLEAN DEFAULT FALSE | True only if `<BlackAndWhite>on</BlackAndWhite>` — empty/absent = False |
| `manga` | TEXT DEFAULT 'No' | "No" / "Yes" / "YesAndRightToLeft" — drives reader page direction |
| `page_count` | INTEGER | From XML — verify against actual image count in CBZ |
| `count` | INTEGER | Total issues in series if known |
| `file_path` | TEXT NOT NULL UNIQUE | Full absolute path to CBZ/CBR file |
| `container_format` | TEXT | `"cbz"` or `"cbr"` — scoped v2.4 Item 5 (2026-06-30), **built v2.4 Item 11 (2026-07-01)**. Distinct from `format` above, which holds ComicInfo's `<Format>` value ("One Shot"/"TPB"/etc.) and drives the existing Format filter dropdown — do not conflate the two. Derived from file extension at scan time; not user-editable. Drives which extraction backend (`zipfile`/`rarfile`) the scanner/reader use for a given row without re-checking the extension every call. Column + backfill (`_add_missing_issue_columns()`, `database.py`) verified against a scratch DB: existing rows backfilled from `file_path`'s extension, new CBR rows populate correctly on scan. Not currently exposed via the `/api/issue`/`/api/library` response JSON — nothing reads it client-side yet. |
| `cover_path` | TEXT | Path to generated thumbnail |
| `metadata_source` | TEXT | "xml" or "filename" |
| `missing` | BOOLEAN DEFAULT FALSE | True if file no longer found on disk |
| `date_added` | DATETIME | When first scanned |
| `date_modified` | DATETIME | File system modified date — used to detect changes |
| `favorites` | BOOLEAN DEFAULT FALSE | User-set, independent of file metadata. Added Tier 4 Item 2 (2026-06-21) — `create_all()` doesn't add columns to an already-existing table, so `database.py`'s `init_db()` runs a one-time manual `ALTER TABLE` for this and `personal_rating` (see §21 change log) |
| `personal_rating` | INTEGER | 1–5, NULL = not rated. Same Tier 4 Item 2 addition as `favorites` |

### `issue_genres` table (junction)

| Column | Type | Notes |
|---|---|---|
| `issue_id` | INTEGER FK → issues.id | |
| `genre_name` | TEXT | One row per genre per issue e.g. "Sci-Fi", "Action", "Adventure" |

Genres are split from the CSV on import. Filter queries use JOIN, not LIKE.
Genre values are consistent because the editor uses a dropdown menu — no normalisation needed.

### `people` / `issue_credits` tables (Tier 4 Item 3, 2026-06-21)

| Table | Column | Type | Notes |
|---|---|---|---|
| `people` | `id` | INTEGER PRIMARY KEY | |
| `people` | `name` | TEXT UNIQUE | Canonical display name |
| `people` | `created_at` | DATETIME | |
| `issue_credits` | `id` | INTEGER PRIMARY KEY | |
| `issue_credits` | `issue_id` | INTEGER FK → issues.id | |
| `issue_credits` | `person_id` | INTEGER FK → people.id | |
| `issue_credits` | `role` | TEXT | writer / penciller / inker / colorist / letterer / cover_artist |

One shared junction table with a `role` column, not 6 per-role tables — see
`DECISIONS.md`. Replaces `Issue.writer`/`penciller`/`inker`/`colorist`/`letterer`/
`cover_artist` as the source of truth for filtering/display once the frontend work
(Session C, not yet built) lands; those 6 raw CSV columns are kept on `Issue` for now
as a rollback safety net (`DECISIONS.md`), written by the scanner but no longer read.
Backed by a one-time migration across the real library — 3,738 distinct individual
names found after splitting the raw CSV fields, 35 confirmed duplicates merged via
human review (76 candidates surfaced, 41 correctly kept as separate people). Full
account in `progress.md` "Session — 2026-06-21: Tier 4 Item 3".

### `reading_progress` table

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | |
| `issue_id` | INTEGER FK → issues.id UNIQUE | |
| `status` | TEXT | "unread" / "reading" / "read" |
| `current_page` | INTEGER | Last page viewed (0-indexed) |
| `last_read_at` | DATETIME | For "continue reading" sort |

**Mobile sync (v2.5 Item 3):** one canonical row per issue, unchanged by sync — no
device concept or history log was added to this table. `POST /sync/progress` (§10)
reconciles offline-captured tablet progress against this same table using
last-write-wins: the client's captured `updated_at` is compared against `last_read_at`;
whichever is newer is authoritative (a missing row or an exact tie goes to the
incoming client write). See `mobile-server-sync-scope.md` for the product scope.

---

## 8. Fields Dropped from DB

These ComicInfo.xml fields are intentionally not stored:

| Field | Reason |
|---|---|
| `IncrementNumber` | Editor-only field, not needed in reader |
| `UseFirstYear` | Editor behaviour flag |
| `Notes` | Always "Modified with CAPT" — tool metadata |
| `ScanInformation` | Always empty |
| `ApplySummary` / `ApplyWriter` / `ApplyPenciller` | CAPT editor flags |
| `Editor` (credit) | Not meaningful for browsing |
| `Review` | Internal tool field |

---

## 9. XML Parsing Rules

| Rule | Detail |
|---|---|
| Empty self-closing tags | `<Number />` → treat as `None`, same as absent tag |
| `BlackAndWhite` | Only `True` if text content is exactly `"on"` — empty tag = `False` |
| `Language` vs `LanguageISO` | Check both tag names, store whichever is present |
| Multi-value fields | Split CSV on `", "` — store raw string in issues table, split into `issue_genres` for genre only |
| `Series` = `Title` | Always the same in this collection — use `series` for all display |
| Missing XML | Fall back to filename parsing, set `metadata_source = "filename"` |
| CAPT flags | Ignore `IncrementNumber`, `UseFirstYear`, `ApplySummary` etc. |

---

## 10. REST API

**Framework:** FastAPI
**Base URL:** `http://localhost:8000/api`
**Files:** `backend/routers/library.py`, `reader.py`, `progress.py`, `admin.py`, `sync.py`

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/library` | All series with cover, issue count, unread count |
| GET | `/library?group=Series` | Filter by format_group |
| GET | `/library?group=Singles` | Filter by format_group |
| GET | `/series/{id}` | Series detail + all issues with read status |
| GET | `/issue/{id}` | Full issue metadata |
| GET | `/issue/{id}/pages` | List of page image URLs in order |
| GET | `/page/{issue_id}/{page_number}` | Serve single page image from CBZ |
| GET | `/cover/{issue_id}` | Serve cover thumbnail |
| GET | `/issue/{id}/download` | Serve the whole CBZ/CBR file (Flutter offline download, v2.5 Item 3) |
| GET | `/search?q=` | Search across series, title, writer, characters, story_arc |
| GET | `/browse/publishers` | Publisher list with series counts |
| GET | `/browse/genres` | Genre list (SELECT DISTINCT from issue_genres) |
| GET | `/browse/arcs` | Story arc list with issue counts |
| GET | `/browse/formats` | All Format values with counts (for format badge filtering) |
| GET | `/reading/continue` | Issues with status="reading", sorted by last_read_at |
| GET | `/reading/unread` | All unread issues, newest first |
| POST | `/progress/{issue_id}` | Update status + current_page |
| POST | `/sync/progress` | Batch-reconcile offline tablet progress, last-write-wins by timestamp (v2.5 Item 3) |
| POST | `/scan` | Trigger full library rescan |
| POST | `/scan/file?path=` | Rescan single file (called by editor after save) |
| GET | `/scan/status` | Scan progress for UI progress bar |
| GET | `/admin/stats` | Series count, issue count, singles count, read count |
| POST | `/admin/backup` | Copy comicvault.db to dated backup file |

---

## 11. Web UI Pages

**Served by:** FastAPI static files
**Files:** `frontend/index.html`, `series.html`, `issue.html`, `admin.html`
**Responsive:** Yes — works on desktop browser and mobile (phone/tablet)
**Note:** The web UI covers browsing and issue detail. The reader is the Flutter app (Phase 5).
`reader.html` is NOT built. `issue.html` originally had a "Read" button deep-linking
into the Flutter app via `comicvault://read/{id}`; **removed 2026-07-09** (v2.6
UI tweak pass — see `DECISIONS.md`) since the custom URL scheme had no handler on a
plain desktop browser, so the button did nothing useful outside the Flutter app
itself. **Restored 2026-07-14 in a different form (v2.6 Item 6)** — the actual
gap (no Windows registration for the scheme) is now closed, so the Issue
Detail cover image itself links to `comicvault://read/{id}`; see §19 "Deep
link integration with web UI" for the full mechanism.

### Library home (`/`)
- Top strip: "Continue reading" — issues with status="reading"
- Two tabs or sections: **Series** | **Singles**
- Cover grid sorted alphabetically by series name
- Unread issue count badge on each cover
- Filter bar: Publisher / Genre / Year / Format (clicking a format badge filters to that value)
- Live search bar

### Series page (`/series/{id}`)
- Header: cover, series name, publisher, year, genre tags
- Issue list: number, title, read status icon
- "Mark all read" button
- Story arc grouping if `story_arc` is populated
- Each issue links to its detail page

### Issue detail (`/issue/{id}`)
- Cover image
- Series name, issue number, format badge
- B&W badge if `black_and_white = True`
- Summary text
- Credits block: writer, penciller, inker, colorist, letterer, cover artist
- Characters list, teams, story arc
- Age rating
- ~~**"Read" button** → deep-links to Flutter app via custom URL scheme: `comicvault://read/{id}`~~
  **Removed 2026-07-09.** **Restored 2026-07-14 as the cover image itself**
  (not a separate button) — see §11's note above, §19 "Deep link
  integration with web UI", and `DECISIONS.md`.
- Mark read / unread toggle

#### Admin page (/admin)
 
- Access: Gear/cog icon in the top-right of the primary header. In V1 this links directly to /admin with no login gate. Login/password protection is deferred to V2.
- Design: Follows the same design language as the main UI — dark theme, same fonts, same card style. Cards are centre-aligned and sized approximately 25% larger than cards elsewhere in the UI.
- Header: Same fixed top navigation header as all other pages, including the gear icon.
- Top action row — four buttons, spread across the row (not grouped together):
- Back — returns to the main library 
- User Guide — opens a stub page in a new tab (placeholder content only in V1; full guide is a future addition) 
- Backup Database — triggers POST /api/admin/backup, exports a dated copy of comicvault.db to a backup location 
- Password Reset — placeholder button, no function in V1 (password management deferred to V2) 
- Stats section — individual stat cards, one value per card:
 - Total Files (grand total of all issues in DB) 
 - Series count 
 - Singles count 
 - Total Read + overall percentage (e.g. "1,203 / 5,448 — 22%") 
 - Titles in progress (status = "reading") 
 
Scan section — individual stat cards plus one action card:
 - Last scan date/time 
 - Files found in last scan 
 - New files found in last scan 
 - Scan Now — button contained within its own card; triggers POST /api/scan; card expands inline to show a live progress bar and log output during the scan 
 
Library folders section:
 - Lists all configured scan root paths (default: one path from config.json) 
 - Multiple roots can be added and are each shown as their own entry 
 - Add folder — browse/select a drive\folder to add as a scan root 
 - Remove folder — remove a root from the scan list 
 - Exclude folders — per-root exclude list; paths entered here are skipped by the scanner (already supported in config.json via SCAN_EXCLUDE) 
 
 Pagination setting:
 - Global page-size selector: 50 / 100 / 200 / 500, default 50 
 - Set-and-forget — persists across sessions (stored in localStorage) 
 - Applies to all browse surfaces (Series, Singles, All, search results) 
 - Home page strips are exempt (fixed at 15 covers per strip) 
 
Advanced settings section:
 - Locked by default — a checkbox must be ticked to enable editing (unticked = all fields greyed out) 
 - Reader location — text field pre-populated from config.json; Browse/Change button to update. Saves to config.json. Has no functional effect in V1 — present for future use when an alternative reader can be configured. 
 - Open Editor — placeholder button, no link in V1. Planned for V2 as an integrated tab using the same base design. 
 - Save advanced settings button — writes any changed values back to config.json and restarts relevant services if needed

---

## 12. Project Folder Structure

```
cBook_Server/                    ← actual root folder name (spec uses comicvault/ but folder is cBook_Server/)
  backend/
    main.py              # FastAPI app entry point
    scanner.py           # Library walker + ComicInfo.xml parser
    models.py            # SQLAlchemy ORM models (issues, issue_genres, reading_progress)
    database.py          # DB connection, session, init
    routers/
      library.py         # GET /library, /series, /issue, /search, /browse
      reader.py          # GET /page, /cover, /issue/{id}/pages
      progress.py        # POST /progress
      admin.py           # GET /admin/stats, POST /scan, /scan/file, /admin/backup
    thumbnails/          # Generated cover images — gitignored
    comicvault.db        # SQLite database — gitignored, back up separately
  frontend/
    index.html           # Library home — BUILT (Phase 3)
    series.html          # Series detail page — BUILT (Phase 3)
    issue.html           # Issue detail page — Phase 4
    admin.html           # Admin page — Phase 6
    css/
      style.css          # BUILT (Phase 3)
    js/
      app.js             # Library + series JS — BUILT (Phase 3)
      admin.js           # Scan trigger, progress bar, stats — Phase 6
  flutter_app/
    lib/
      main.dart          # App entry point, routing
      screens/
        library_screen.dart    # Browse ComicVault collection
        series_screen.dart     # Series detail
        reader_screen.dart     # Comic reader (server + local)
        settings_screen.dart   # Server URL, preferences
      services/
        api_service.dart       # All calls to ComicVault REST API
        local_cbz_service.dart # Open and read local CBZ files
      models/
        issue.dart             # Issue data model
        series.dart            # Series data model
        reading_progress.dart  # Progress model
      widgets/
        comic_page_view.dart   # Page renderer (scroll + swipe modes)
        toolbar_overlay.dart   # Hide/show reading toolbar
  tray/
    tray_app.py          # pystray system tray app — launches both servers
  config.json            # All paths and settings — edit this, never hardcode
  requirements.txt
  start.bat              # Windows: launches tray app (which starts both servers)
  .gitignore
```

---

## 13. Python Dependencies

```
# requirements.txt
fastapi
uvicorn[standard]
sqlalchemy
pillow
pystray
watchdog
rarfile          # CBR extraction — added v2.4 Item 5 (2026-06-30), requires an
                 # unrar-compatible backend (UnRAR.dll/unrar.exe) on the host
```

Extraction-only — no archive-creation dependency. RAR archive creation needs a
paid WinRAR install and is deliberately never done by ComicVault (see §6.1);
editing a CBR's metadata rebuilds it as `.cbz` instead.
Flask is used by the existing editor app — managed separately.

---

## 14. Windows Startup

A shortcut named `ComicVault.lnk`, targeting `start.bat`, in the Windows Startup folder:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

`start.bat`:
```bat
@echo off
cd /d "%~dp0"
pythonw tray\tray_app.py
```

The tray app then launches the reader server as a subprocess and sits in the system tray.

**(2026-06-19) Self-service toggle:** the tray menu's checkable "Start ComicVault at
login" item creates/removes this shortcut directly — no manual creation needed
anymore. The shortcut's own existence on disk is the source of truth for whether the
checkbox shows checked; there's no separate config flag to fall out of sync.

---

## 15. Device Access

### Home network (primary use)
The Flutter app connects to the ComicVault server over the home network:
```
http://<host-pc-ip>:8000/api
```
The server IP is configured once in the Flutter app's Settings screen and stored locally on the device.

### Travel / offline use
The Flutter app can open local CBZ files stored on the device.
Local file progress is saved on the device only — not synced to the server.
The app detects whether the server is reachable on launch and switches modes automatically.

### Web UI (secondary, browser-based)
The web UI at `http://<host-pc-ip>:8000` remains available for browsing from any browser on the network.
The editor (port 8001) is localhost-only — not accessible from other devices by design.

---

## 16. Build Phases

| Phase | Scope | Key files | Status |
|---|---|---|---|
| **1** | Scanner + database | `config.py`, `models.py`, `database.py`, `scanner.py` | ✅ Complete |
| **2** | REST API | `main.py`, `routers/library.py`, `routers/reader.py`, `routers/progress.py` | ✅ Complete |
| **3** | Web library UI | `index.html`, `series.html`, `css/style.css`, `js/app.js` | ✅ Complete |
| **4** | Issue detail page | `frontend/issue.html` | ✅ Complete |
| **5** | Flutter app | `flutter_app/` — library browser + reader (Android + Windows) | ✅ Complete |
| **6** | Desktop tray app + admin | `tray/tray_app.py`, `start.bat`, `admin.html`, `js/admin.js` | ✅ Complete |

**Build order is strict.** Each phase must be tested before the next begins.

**Note on Phase 4:** `issue.html` is a web page — quick to build, completes the web UI browsing flow.
The Read button links out to the Flutter app via deep link rather than to a `reader.html`.

---

## 17. Key Decisions Log

| Decision | Choice | Reason |
|---|---|---|
| Framework | FastAPI | Async, fast, automatic docs, easy to learn |
| Database | SQLite | Sub-10k collection, single user, zero server setup |
| ORM | SQLAlchemy | Standard Python ORM, good migration path |
| Frontend | Vanilla JS | No build step, easy to understand and modify |
| Reader app | Flutter (Phase 5) | Single codebase for Android + Windows; proper native app feel on both |
| Reader on web | Not built | Flutter app handles all reading; no `reader.html` |
| Editor integration | Split app, shared DB | Editor already exists in Flask — no rewrite |
| Sync method | Webhook rescan endpoint | Instant sync, no polling |
| Genre storage | Junction table (`issue_genres`) | Clean JOIN filtering, consistent values from editor dropdown |
| Multi-value credits | Raw CSV string | No filtering needed, display-only split |
| Series grouping key | `Series` XML field | Consistent even if folder name varies |
| Format groups | Two: "Series" / "Singles" | Detected from folder path, not XML |
| CBR support | Full native support, read-only at archive level (v2.4 Item 5, 2026-06-30) | Public-release direction + large mixed CBZ/CBR collections (>100k issues for some users) make bulk-conversion-before-use unviable. Never written — RAR creation needs paid WinRAR; editing rebuilds as CBZ instead. Originally "None in V1" — see `DECISIONS.md` and §6.1 |
| Autostart method | Startup folder shortcut (V1) | Simple, no install needed |
| Path storage | `config.json` only | HDD-failure resilient, one edit to re-point |
| Missing files | Flag, don't delete | Protects against temporary disconnects |
| Rescan strategy | Incremental | Never wipes DB — reading progress preserved |
| Manga page direction | Driven by `manga` XML field | "YesAndRightToLeft" reverses reader nav |

---

## 18. Real Collection Examples Confirmed

These folder/file patterns are confirmed present in the collection and must all work:

```
'68 Homefront (2024)\  → series with multiple issues
Criminal Volume 1\     → series — volume in folder name, own series entry
Criminal Volume 2\     → separate series entry — NOT merged with Volume 1
Cyberpunk 2077 - Kickdown (2025)\   → dash-subtitle series
Cyberpunk 2077 - Blackout (2022)\   → separate series from above
The 13th Artifact (2016)\           → single, own folder, one CBZ
```

2000 AD confirmed as anthology format: five writers, five pencillers in one issue.
All credit fields store raw CSV — never split for filtering.

---

## 19. Flutter App Specification

**Technology:** Flutter (Dart)
**Platforms:** Android (tablet primary), Windows (desktop)
**Single codebase** — one Flutter project builds both platform targets.

### Source modes

| Mode | When active | Data source |
|---|---|---|
| Server mode | ComicVault server reachable on home network | REST API at `http://<ip>:8000/api` |
| Local mode | Server unreachable (travel) | CBZ files stored on device |

App detects server availability on launch and when resuming from background.
User can also switch manually in Settings.

### Screens

> **Superseded 2026-07-13.** This subsection describes the pre-redesign
> tab-based navigation (Library screen with Series/Singles tabs, Series
> screen). The Mobile UI Redesign (v2.6 Item 4) replaced this with a
> persistent nav rail + Home/Browse/Series Detail/Issue Detail screens,
> matching the web UI's own redesign (Item 1) — see
> `docs/v2.6/comicvault-changes-v2.6.md` Item 4 and `docs/v2.6/progress.md`
> for the current authoritative design. One real behaviour change worth
> flagging here specifically: tapping an issue no longer opens the Reader
> directly — it opens a new Issue Detail screen first (cover, credits,
> rating, a "Start Reading" button), matching the web UI's existing
> Issue Detail page. Left the text below as historical context rather than
> deleting it, same convention as §20.9's 2000 AD section note.

**Library screen**
- Mirrors the web UI: Series / Singles tabs, cover grid, unread badges
- Filter by publisher, genre, year
- Live search
- "Continue reading" strip at top
- Tapping a series opens the Series screen

**Series screen**
- Cover, title, publisher, year, genre tags
- Issue list with read/unread status
- Story arc grouping if populated
- "Mark all read" button
- Tapping an issue opens the Reader screen directly

**Reader screen**
- Two reading modes, switchable via toolbar:
  - **Scroll mode** — continuous vertical scroll (default)
  - **Page mode** — single page, swipe left/right or tap edges to advance
- Portrait and landscape both supported — layout adapts on rotation
- Toolbar overlaid at top and bottom:
  - Hides automatically after 3 seconds of inactivity
  - Reappears on single tap anywhere on the page
  - Top bar: back button, issue title, page counter (e.g. "12 / 32")
  - Bottom bar: reading mode toggle, fit-width / fit-height toggle, page scrubber slider
- Manga mode: if `manga = "YesAndRightToLeft"`, page mode reverses swipe direction
- Progress saved to server on every page turn in Page mode (POST
  `/api/progress/{id}`); Scroll mode has no native page-turn event, so
  progress is estimated from scroll position instead and saved to the same
  endpoint whenever that estimate's page number changes (fixed 2026-07-17,
  BUG-024 — previously Scroll mode, the default, never saved progress at
  all)
- Reopening an issue resumes the saved page in both modes — Scroll mode's
  resume is a scroll-fraction estimate, not pixel-exact
- Auto-marks issue as "read" when last page is reached
- "Next issue" prompt on completion

**Settings screen**
- Server URL field (e.g. `http://192.168.1.10:8000`) — stored locally on device
- Connection test button
- Default reading mode preference (scroll / page)
- App version

### Local file support (travel / offline)

> **Android-only, confirmed 2026-07-14 (v2.6 Item 5 — Windows Desktop
> Reader).** The file picker described below uses a native Android
> `MethodChannel` with no Windows-side implementation. Windows desktop is
> expected to be on the same LAN as the server, so local-file picking is
> hidden there rather than given a Windows-native picker — server mode only
> on that platform. The "Downloaded" offline section (separate from this —
> issues downloaded in-app via server mode, see Mobile ↔ Server Sync) is
> unaffected on Windows, since it doesn't go through this picker.

- File picker to open a CBZ from device storage
- Same reader experience as server mode
- Progress saved locally on device (SQLite), not synced to server
- Recently opened local files listed on Library screen when in local mode

### Deep link integration with web UI
**Web-UI trigger restored 2026-07-14 (v2.6 Item 6), Windows only.** The
"Read" button removed 2026-07-09 (`DECISIONS.md`, `BUGS.md` BUG-021 at the
time, since closed) is back in a different form — `issue.html`'s cover image itself is
now a link to `comicvault://read/{issue_id}` — because the actual gap
(nothing on Windows had ever registered a handler for the scheme) is now
closed, not because the Flutter app's own parsing of the scheme ever
needed fixing:
```
comicvault://read/{issue_id}
```
The Flutter app registers this custom URL scheme on both Android and
Windows, and always correctly handles it once registered/received.
Android's registration is via `AndroidManifest.xml`'s intent-filter,
present since V1. **Windows registration is now a deliberate, explicit
step** — not automatic — via a "Register as this PC's comic reader" button
in the Flutter app's Settings screen
(`flutter_app/lib/services/protocol_handler_service.dart`, writing
`HKEY_CURRENT_USER\Software\Classes\comicvault`). If the reader isn't
already running, clicking the cover launches it straight into that issue
(cold start). If it's already running, the existing window is brought to
the front and navigated there instead of a second process spawning
(`flutter_app/windows/runner/main.cpp`'s `SendAppLinkToInstance()`).

**Inherent limitation, not solved:** a custom URI scheme only works when
the browser and the registered reader are on the same Windows PC — this
was the same same-machine-only caveat flagged when the feature was first
scoped and parked (`ROADMAP.md`).

### Progress sync
- Server mode: all progress written back to ComicVault DB via REST API in real time
- Local mode: progress stored in local app database
- No automatic sync of local progress to server (V1)

### Flutter dependencies (pubspec.yaml)
```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.0.0              # REST API calls
  archive: ^3.4.0           # CBZ (zip) file reading
  sqflite: ^2.3.0           # Local progress storage (Android)
  drift: ^2.0.0             # Local progress storage (Windows)
  path_provider: ^2.1.0     # App storage paths
  file_picker: ^6.0.0       # Open local CBZ files
  shared_preferences: ^2.2.0 # Settings storage
  app_links: ^6.0.0         # Deep link handling (comicvault:// scheme)
  cached_network_image: ^3.3.0 # Cover image caching
```

---

## 20. V1.1 UI/UX Revisions (Post-Phase-3 Testing)

> **Status:** Agreed during planning, not yet built. Drives the next build round.
> **Scope:** Web UI and Flutter app share most of these changes (noted where they differ).
> Where this section conflicts with Sections 1–19, **this section is authoritative.**

### 20.1 Navigation Model — Browse Surfaces

Four top-level browse surfaces replace the current Series/Singles tab pair:

| Surface | Shows | Count displayed |
|---|---|---|
| **Home** | Curated strips (see 20.4) | — |
| **Series** | Series only (one card per series) | Total series count |
| **Singles** | Singles only (one card per single) | Total singles count |
| **All** | Series + Singles combined, one card each | Total **individual comics** (grand total) |

- **All** combines series and singles as single cards (one card per series, one per single — NOT exploded into individual issues). This exists so filters can cut across both pools at once (e.g. "all Horror, wherever it lives").
- A dedicated **2000 AD** surface also exists — see 20.9.

### 20.2 Filtering, Status & Sort — Three-Layer Model

Filtering and searching are the same activity (both narrow what's shown). They operate **inline** on whatever surface is active — results stay as cover cards in the current view. **No separate web search page.** (The Flutter app keeps its own search page — see 20.10.)

The model has three layers that stack:

1. **Tab** (All / Series / Singles / 2000 AD) — picks the *pool*
2. **Status** (Read / Reading / Unread) — narrows by read state
3. **Dropdown filters** — narrow by content

**Filter dropdowns:** Genre, Publisher, Writer, **Artist**, **Format**, Decade, Year, Rating, B&W
- **Artist** = the `penciller` field, displayed under the friendlier label "Artist". Data unchanged; label only.
- **Format** is a NEW dropdown (resolves the deferred Format filter from the 2026-06-12 change log). It also serves as an inspection tool — opening it reveals every `format` value actually present in the DB.
- **Decade** and **Year** are independent alternatives (pick a wide decade OR a precise year — not nested). Decade range runs 1900s → current decade, the "present" end calculated so it never goes stale. Year values read from `<Year>`.
- **B&W** options: Yes / No / (default All). Every other dropdown's first item after its title is **"All"** (acts as a reset).

**All filter menus are populated live from the database** — never from a fixed list — so dead/empty entries are structurally impossible. (See 20.11 for the genre data issue this addresses.)

**Sort:** a **Newest ↔ Recent toggle** (not a filter). Default sort is by title; the toggle flips to date sorting:
- **Newest** = by cover `year` (publication age)
- **Recent** = by `date_added` (when added to library)

**Group by:** a separate control from filtering. Filtering *narrows*; Group-by *clusters under headings*. Options: Title (#, A–Z), Year, Genre, Writer, Artist, Publisher. **Multi-select and stacking** supported (e.g. filter Horror + 2020, then group survivors by Writer → Alan Moore's titles cluster under his name). Group-by does not apply on the Home page (already grouped).

### 20.3 Count Wording

- Every browse surface shows a **bare total number** — no word after it (no "Series"/"Titles").
- Series → total series; Singles → total singles; **All → total individual comics** (library grand total).
- The number reflects the whole set, not the page (pagination means on-screen card count never matches anyway).
- The **All total intentionally doubles as a DB-vs-folders integrity check** — if it doesn't match the CBZ file count on disk, a file failed to scan. This is intended behaviour, not a bug — do not "fix" it to match visible cards.
- Display the number slightly **larger** than current.

### 20.4 Home Page (NEW)

A genuine home page, separate from the browse surfaces, made of **horizontal cover strips**. Five strips, in order:

1. **Random (Unread)** — a random unstarted comic (any single, or first issue of an unstarted series). Refreshes each visit.
2. **Recently Added** — most recently imported. Always current.
3. **Random Genre** — a genre picked at random; heading shows the plain genre name (e.g. "Horror"). Refreshes once per session.
4. **Random Single** — a random single. Refreshes each visit.
5. **Random Series** — a random series. Refreshes each visit.

- Each strip: **15 covers max**, then stops. Heading is **clickable** → opens a full page listing everything that qualifies.
- Cover info under each follows the active grid/list view.
- **Deferred to a later edition:** strips editable / reorderable / addable; admin control for random-refresh timing.

### 20.5 Grid & List Views

A **list/grid toggle** applies on all browse surfaces (Home, Series, Singles, All, search results).

**Grid view** (revised info under each cover): **Title, Year, and # of issues (series) / page count (singles)**. Publisher removed from grid.

**List view**: one title per row — thumbnail left, then title, year, genres, publisher, first writer only (if multiple), and as much description as fits the row (truncated). List-view thumbnail sized to allow ~3 lines of text beside it. **Two-column layout as of 2026-07-17** (`docs/v2.6/progress.md` "List View redesign") — rows lay out in 2 columns by default (50px gap between columns, 10px top padding per row), collapsing to a single column below ~1100px window width. Each genre in the row is its own link into the fieldview genre filter (`?surface=fieldview&field=genre&value=...`), not plain text.

**Card consistency (prerequisite):** web and Flutter cards currently differ (web has a border + larger gaps; app has neither). **Align card design across both before applying read-state colours**, so colour reads identically on each.

**Read-state card colours** (both views):
- **Unread** → no change (default background)
- **Part read** → amber, 50% opacity
- **Fully read** → green, 50% opacity
- No red.
- In **list view**, the state colour is carried as a border/background around the thumbnail.
- **List-view text emphasis, as of 2026-07-17:** background tint colours above are shared with Grid View, but List View intentionally inverts *text* emphasis — read/part-read rows render with muted, lighter-weight text and unread rows render bold/high-contrast, so the eye is drawn to what's unread rather than what's already read. Grid View's text styling is unchanged (still brighter/bolder on read/part-read). See `docs/v2.6/progress.md` "List View redesign".

**Progress indicator (part-read only):**
- **Grid** → thin progress bar overlaid on the cover
- **List** → "75% Read" text
- Not shown on unread or fully-read cards.

### 20.6 Series Detail Page (`/series/{id}`)

- **Full-cover backdrop:** the first-issue cover fills the header background at **20–30% opacity**, with slight blur, a dark semi-transparent tone overlay (so bright covers don't harm text legibility), and an extra gradual fade at the bottom. Layer order: image → blur → dark tone overlay → bottom gradient → text.
- **Header contents:** back button, mark-all-read button, title. Header ≈15% of a 10" tablet screen.
- **Below header:** Publisher · Year, then genre tags, then # Issues, then the issue list.
- **Issue list follows the grid/list view** (same cards, read-state colours, progress indicators) — including page count, reading progress, and per-issue description.
- **Paginated** (added v2.6 Item 3, 2026-07-13) — same page-size setting and page-number control as Browse (20.13); a large series (e.g. 2000 AD, 2,483 issues) no longer renders its whole issue list in one page load.
- **No Series Overview field** in V1 — per-issue descriptions cover the need. (A series-level overview would require new XML + DB + editor fields; deferred to a possible later version.)

### 20.7 Story Arc Grouping

- Changed from **always-on** to **off by default.** Surfaced as an option within the Group-by control (20.2).
- Default series view = **flat issue list in numerical order**, no grouping.
- Arc grouping available on demand for series where it helps.
- **Reason:** with grouping always on, a series like 2000 AD (only 105 of 2,483 progs carry a `<StoryArc>`) had its 105 arc'd issues floated above the 2,378 ungrouped ones, scrambling the apparent order (#555–607, #660–711, then #1–#2483). Flat numerical order is the correct default.
- **Code task:** confirm issue sort order is correct numerically with grouping off.

### 20.8 Issue Detail Page (`/issue/{id}`) — Phase 4

Replaces the credits/fields list in Section 11. **Trim to "subtract not add"** — the page currently pulls more than wanted.

**Display these fields** (where present): Series/Title, Number, Year, Genre, Format, B&W badge, AgeRating, Count, Writer, **Penciller (shown as "Artist")**, Publisher, PageCount, StoryArc, **Language**, Summary.

**Drop from display (but KEEP stored in DB):** Characters, Teams, Locations, Inker, Colorist, Letterer, Cover Artist.
- Rationale: hiding not deleting costs nothing, matches the "enable everything, prune the view" approach, and keeps options open for a public version where someone may want character/team data.

**Wording fix (front-end only):** age rating shows as "**Rated: PG**" / "**Rated: MA15+**" (not "PG rated").

**Confirmed:** Penciller = Artist; **Inker is dropped** (not "Artist"). Language is **added** to the issue-page display (it is already a DB column but was not being shown).

**Toolbar:** the fixed top menu (20.2) appears on all pages **except** `/issue/{id}`.

### 20.9 2000 AD Section (NEW) — REMOVED 2026-06-22, see CUSTOM_TABS_SPEC.md §9

> **Superseded.** This hardcoded section was removed in v2.2, exactly as
> anticipated by this section's own "removable later if the app ever goes
> public" note below. Its useful behaviour (browse-by-folder, organised by
> year) was generalised into Folder View, a new `view_mode` any Custom Tab
> can use — see `CUSTOM_TABS_SPEC.md` §9 for the current authoritative
> design, and its Change Log for the build record. Left the text below as
> historical context for the original design rather than deleting it.

A dedicated **hard-coded** top-level tab for the 2000 AD progs (~2,483 issues, ~half the collection). Removable later if the app ever goes public.

- **No HDD folder changes** — the scanner walks the existing `2000AD\2000AD Progs…\YYYY\` structure correctly (all progs scan with correct number and year).
- **Built from `series = '2000 AD'` grouped by `year`** — independent of `format_group` (which currently lands on "Series" via the path-default fallback, not a matched rule).
- **Two-level design:**
  - **Level 1 — year grid:** ~50 bespoke cards (1977 → current year). Each card: large **YYYY**, first-prog thumbnail, issue range (read from data; partial years display honestly).
  - **Level 2 — year detail:** clicking a year opens a **standard series-style issue list** for that year's ~52 progs, reusing the Series page design (20.6).
- **Arc grouping toggle** lives on the year-detail page only (not the year grid), off by default per 20.7.

### 20.10 Reader (Flutter App)

Refinements to the existing working reader (Section 19) — nothing here is broken, these are improvements.

- **Mode toggle (scroll/page):** already works both ways but is too small/hidden — make it **bigger and more visible** in the toolbar.
- **Tap zones (page mode only):** screen splits **25% left / 50% middle / 25% right.** Tap right edge → next page; tap left edge → previous page. Scroll mode unchanged (stays pure swipe).
- **Single tap (middle):** shows/hides the toolbar AND briefly flashes the navigation arrows.
- **Double tap:** toggles zoom between **fit-whole-page** (default) and **fit-to-width** (auto-snap, removes the need to manually pinch to width on rotating to landscape). Pinch zoom remains available on top.
- **Arrows = visual hints only**, not buttons. They signpost where the tap zones are, direction-matched to mode (up/down in scroll, left/right in page), appear briefly on a middle tap or a tap-zone tap, then fade once scrolling/turning begins.

### 20.11 Data-Hygiene & Code Tasks (Not Build Features)

Recorded so they aren't mistaken for code changes:

**User data tasks (Tez):**
- **Genre cleanup:** every genre has ≥1 title, but a handful of files carry old genre values predating the CAPT editor's dropdown. Compare the vault's genre menu against the editor dropdown, find the odd ones, re-edit those files' XML. (Menus are built live from data, so this is purely a data-quality task.)
- **XML consistency pass:** some files were added before full editing was established, a few were missed, and ComicTagger/ComicVine over-tagging may remain. The issue page mirrors data quality — it improves automatically as the data is cleaned.
- **Format value confirmation:** use the new Format dropdown (20.2) to see all `format` values present, to confirm the singles-routing rule (20.12).

**Code investigation tasks:**
- **`format_group` rule:** currently relies on a path-default fallback for paths containing neither `Series\` nor `Singles\` (e.g. 2000 AD). Replace the silent fallback with a deliberate rule.
- **Issue sort order** with arc grouping off (20.7).

### 20.12 Singles Routing Fix

- **Bug:** clicking a single currently routes to `/series/{id}` (wrapping a lone title in series furniture). It should go straight to `/issue/{id}`.
- **Grouping itself is correct** — series/singles split fine; only the click destination for singles is wrong.
- **Rule (provisional, pending Format-value confirmation per 20.11):** `<Format>` of `Series` or `Limited Series` → series page; everything else → `/issue/{id}`; **folder as fallback** where Format is blank.

### 20.13 Other Recorded Items

- **Search-page back button (bug):** the Flutter search page currently exits the app when there are no results, with no way back. Add a back control.
- **Settings/Admin icon:** add to the toolbar alongside admin-page development (Phase 6).
- **Pagination:** page-size control lives on the **admin page** (not the browse toolbar). Options 50 / 100 / 200 / 500, default 50, global, set-and-forget (persists). Standard page-number navigation (1, 2, 3… with forward/back) on browse pages **and the Series Detail issue list** (20.6, added v2.6 Item 3). **Home strips exempt** (fixed at 15). Admin can be opened in its own tab for a quick change.

### 20.14 Deferred to V2 (Noted, Not Built)

> Corrected 2026-06-20 (doc-map cleanup session): two items below were built and
> removed from this list — generalised custom tabs shipped as `CUSTOM_TABS_SPEC.md`
> (2026-06-19), and home-page strips shipped as `HOME_STRIPS_SPEC.md` (2026-06-19).
> See `CHANGELOG.md` / `progress.md` for build logs, `ROADMAP.md` for what's still
> actually deferred.

> **Corrected 2026-07-15:** the three remaining items below (multiple scan
> locations, series-level overview field, Advanced Search page) were all
> ruled out, not built — see `ROADMAP.md`'s "Resolved" section for the
> rationale on each. Nothing currently deferred under this heading.

### 20.15 Multi-select Scope Boundary (Tier 4 Item 2, 2026-06-21; expanded 2026-06-23)

Long-press-to-select and the bulk Read/Unread/Favorite/Rate toolbar (`comicvault-
changes.md` Tier 4 Item 2) attach to:

- Singles surface cards, and Singles-type cards on the All surface (`buildCoverCard()`,
  gated on `format_group === 'Singles'`) — map 1:1 to a single issue.
- Series-detail issue rows (`buildIssueRow()`) — map 1:1 to a single issue.
- Folder View flat file cards (`buildFolderFileCard()` — was `buildAdProgCard()`'s
  2000 AD prog cards until v2.2 generalised it; see `CUSTOM_TABS_SPEC.md` §9) — map
  1:1 to a single issue.
- **Series-aggregate cards** (Series surface, series-type cards on All) — map to every
  issue in that series. A bulk action against a selected series card expands to the
  series' full issue-id list server-side (`resolveBulkIssueIds()`, via the same
  `/series/{id}` endpoint the series-detail page uses) before calling the existing
  bulk endpoints, so "Mark Read"/"Mark Unread"/"Favorite"/rate apply to every issue in
  the series — the same meaning the existing series-detail "Mark all read" button has
  always had. Originally excluded on the reasoning that a bulk action's meaning across
  many issues would be ambiguous; superseded 2026-06-23 (`DECISIONS.md`) after Tez
  found issue-only selection too limiting in practice.

Any future surface or card type added to a browse view still needs to make this call
explicitly — don't assume multi-select should "just work" on a new card type without
deciding what a bulk action means for it first (1:1 passthrough, or an expansion like
Series cards', or genuinely excluded).

Favorites has **no dedicated browse surface yet** — a favorite badge renders on
eligible cards/rows when set, and the issue detail page shows favorite state + a 1–5
star rating, but there's no "Favorites" tab. See `ROADMAP.md` for that as a deferred
follow-up.

### 20.17 Card Behaviour Additions (2026-06-23, built 2026-06-23)

The following card and theme behaviours apply to the web UI and, where
relevant, the Flutter app — built and verified on the web UI; Flutter app
parity not yet done.

**Favourite star (grid and list cards):** the favourite badge rendered in the top-left
corner of cards increases in size by 5px and gains a 1px solid black border, for
improved visibility against light or busy cover images.

**Issue page star rating row** (`/issue/{id}`): the existing 1–5 star rating row has
excessive left/right padding relative to the button row below it. Fix by increasing
star size and reducing inter-star spacing so the row fills the same width as the
button row. Net result: same star count, less blank margin either side.

**Favourited card border:** any card where `favorites = true` gets a thin gold border
around its entire card outline, regardless of read state. This is in addition to the
existing tri-state amber/green/none read-state gradient (§20.5) — not a replacement
for it. Both decorations coexist: a favourited-and-fully-read card shows the green
gradient plus a gold border.

**Dark/Light theme:** the app auto-matches the Windows system theme (dark/light) by
default. A manual override toggle in Settings allows forcing light or dark,
independent of the OS setting. (The tray app's context menu already follows Windows'
\"Apps use dark mode\" setting — see §3/change log — this is the separate in-app theme
for the web UI itself.)

---

### 20.18 Card Icon/Badge Refresh & Personal-Rating Pill (2026-07-11, built 2026-07-11)

Cosmetic pass, `INBOX.md` triage — supersedes some of §20.17's badge detail above,
which stays for history rather than being rewritten in place.

**Favourite badge:** the top-left badge is now a red heart (`♥`, `#e02424`) on a
white circular background, replacing the gold star on a dark translucent
background. Size and 1px black border unchanged from §20.17. Explicit equal
width/height (20×20px, flex-centred) — needed because the heart glyph's own
metrics aren't square like the star's were, which stretched the `border-radius:
50%` circle into an egg shape when sized by content+padding alone (caught by
Tez from a live screenshot, fixed same session).

**Unread badge:** the top-right pill's text is now white, replacing black, for
better contrast against the blue background.

**Personal-rating pill (new):** grid cards for a rated issue (`personal_rating`
1–5) show a small pill in the bottom-right corner of the cover — background/border
match the existing bottom-toolbar rating pill (`.selection-rate`) — containing a
vertical stack of gold stars, one per rating point, growing upward from the
bottom. Hidden entirely when unrated. Series-aggregate cards show the cover
issue's own rating, same aggregation precedent as the existing favourite-badge
`any()` logic. Web UI only (grid/card views); not shown on the flat issue-list row
or Home Strip cards.

**Card-selected indicator:** the small circle at the bottom-left of a selected
card (hover-reveal, §Multi-select) now shows a gold checkmark on a dark grey
background, replacing the plain blue filled dot.

**Admin stat cards — uniform borderless baseline:** every `.stat-card` (the
Library Stats row plus all six Library Scan cards, `ADMIN_SPEC.md` §3–4) now
has a transparent 1px border rather than the visible grey `var(--border)` —
first pass only stripped it from three of the six Scan cards (Scan Now, Last
Scan, Changed Files), leaving an inconsistent mix; corrected same session to
apply uniformly. `#scanNowCard`'s previously-distinct default white border is
also gone, so it now matches the rest at rest. The functional status borders
(green while a scan is running, green on a card whose log has unviewed
entries — §8) are unchanged and still show, since they only override
`border-color`, not `border-style`.

### 20.19 Multi-Cover Cloud-Field Library-Page Background (2026-07-13, built 2026-07-13; corrected same day — full content-area width + reduced blue cast; reworked 2026-07-15 — multi-cover cloud field replacing the single top-right-masked cover)

`INBOX.md` triage. Home, Browse (All/Singles/Series), and every custom
tab (flat or Folder View) render inside `.app-content`, so one shared
background layer (`#pageBg`, `frontend/index.html`) covers every one of
these surfaces.

- **Cover source:** up to 4 *distinct* covers picked at random from
  whatever's actually shown on the active surface, never the whole
  library — Home draws from the union of all currently-loaded strip items,
  Browse/flat custom tabs draw from `getFilteredLibrary()`'s current
  surface pool, Folder View draws from the current directory's own
  folders+files. A custom tab like 2000 AD only ever shows 2000 AD covers,
  by construction (the pool passed in is already scoped server-side to
  that tab/folder). A surface with fewer than 4 covers gets fewer blobs —
  never padded with repeats.
- **Timing:** picked once per surface-entry (`renderBrowse()`/`loadHome()`/
  `renderFolderView()`), not on every filter tweak or pagination click, so
  it stays stable while browsing within a surface instead of flickering.
- **Geometry (container, unchanged since 2026-07-13):** `#pageBg` is
  `position: fixed`, pinned to the real viewport rather than scrolling with
  page content — `top: var(--header-h)`, `left: var(--sidebar-w)` (tracks
  the sidebar's collapsed width too), so it fills the whole visible content
  area next to the sidebar. (Historical note: the 2026-07-13 first cut
  clipped this to the then-centered 1440px `.container` column, corrected
  same day; `.container` itself dropped its 1440px cap entirely on
  2026-07-15 — see the site-wide full-width layout change — making that
  distinction moot going forward.)
- **Reworked 2026-07-15 — multiple blobs instead of one masked image:** the
  original single-cover version, anchored to a top-right radial mask fading
  out at ~70% of its radius, "didn't cover enough" per Tez — most of the
  content area stayed flat. `setPageBackground()` (`frontend/js/app.js`) now
  appends up to 4 `<img class="page-bg-blob">` elements to `#pageBg`, each:
  - A soft-masked circle (`radial-gradient(circle at center, #000 0%,
    transparent 68%)`), so it reads as a cloud rather than a rectangle.
  - Positioned via inline `--x`/`--y` custom props, seeded from one of four
    shuffled quadrant anchors (~22/26, ~80/22, ~30/76, ~74/70 in %) plus
    ±10% random jitter, and scaled via `--s` (0.9–1.4× random) — so blobs
    reliably spread across the whole area (zoned randomness) while still
    varying every surface-entry.
  - `opacity: var(--pagebg-blob-opacity)` (0.32) so overlapping blobs build
    up into a denser field where they meet; `filter: blur(var(--pagebg-blur))
    saturate(0.9)` (30px blur) — colour is let through more than the
    original (`saturate(0.6) sepia(0.15)` grey-mute dropped) since the
    point of the effect is "colourful blurred clouds," confirmed with Tez.
  - `--pagebg-blur` and `--pagebg-blob-opacity` are `:root` tokens, tunable
    without touching the rule itself.
- **Why real covers, not a generated gradient:** considered during this
  rework — see `DECISIONS.md`.
- **Where:** `frontend/index.html` (`.page-bg` markup, now an empty
  container populated by JS), `frontend/css/style.css` (`.page-bg`,
  `.page-bg-blob`, the `--pagebg-*` tokens, and the `position: relative;
  z-index: 1` elevation on `#homeView`/`#browseView`/`#folderView`/
  `.menu-bar`), `frontend/js/app.js` (`setPageBackground()`,
  `shufflePageBg()`, `PAGE_BG_BLOBS`/`PAGE_BG_ANCHORS`, plus its three call
  sites, unchanged).

---

### 20.16 Writer/Artist Click-Through (Tier 4 Item 3, 2026-06-21)

`/issue/{id}`'s Writer/Artist credits are clickable links to
`/?surface=fieldview&field=writer&value=<person_id>` (or `field=artist`) — reusing
the `fieldview` surface built for Home Strips rather than a new mechanism. The
target page is an ordinary filtered `GET /api/library?field=...&value=...` call;
`matches_field()` resolves `writer`/`artist` against `Person.id` via the
`issue_credits` junction (`backend/path_utils.py`).

New endpoint: `GET /api/people/fuzzy-match?name=<typed>` — closest existing `Person`
to a typed name (`difflib`-based), used by the metadata editor's non-blocking save-
time warning for Writer/Penciller. Returns `null` if the typed name already matches
exactly or nothing is close enough; never blocks a save either way.

`_issue_to_dict()` (`backend/routers/library.py`) gained `writers`/`pencillers`
arrays (`[{person_id, name}, ...]`) alongside the existing raw `writer`/`penciller`
strings, feeding the click-through links. `/browse/writers`/`/browse/artists` now
group by deduped `Person` (`{person_id, name, series_count}`) instead of the raw
CSV blob — also fixes a real, separate consumer: the admin Home Strips builder's
field-value picker (`frontend/js/admin.js`), which previously stored whatever raw
string it fetched verbatim as `HomeStrip.field_value`.

The Writer/Artist filter `<select>` dropdowns are removed from the browse filter
bar entirely (`frontend/index.html`, `app.js`) — replaced by the click-through
above, per the backlog's "search + click-through, not a dropdown" ask. The "Group
by Writer" option in the unrelated Grouping menu still uses the old raw-CSV
per-series aggregate (untouched, out of scope for this item).

---

### 20.20 Card Redesign — Grid, Home Strips, Folder View (2026-07-15, built 2026-07-15)

Scoped in Claude Design (`D:\workshop\Claude Design\new card design`), then heavily
fine-tuned live with Tez across many rounds. Supersedes the read-state/favourite/
badge visual detail in §20.5, §20.17, and §20.18 for the three surfaces below — those
sections stay for history rather than being rewritten in place, same convention as
§20.9/§20.18's own superseding notes.

**Applies to:** the main library grid (`buildCoverCard()` — Browse/Series/Singles/
All/Custom-Tabs-flat/search/fieldview), Home Page Strips (`buildStripCard()` — every
strip type, since they share one builder), and Folder View's flat file cards
(`buildFolderFileCard()`). Issue Detail's cover (`buildIssueDetail()`) got the same
border/progress treatment, not the rest of the card layout (title/genre/rating stay
in that page's own existing layout).

**Explicitly NOT applied:** Folder View's subfolder tiles (`buildFolderCard()` — an
aggregate across many issues, no single genre/rating/progress concept), Series
Detail's issue-list rows (`buildIssueRow()` — a horizontal row, not a portrait
tile), and list view (separate design pass, not yet scheduled).

**Card frame:** one uniform border on every card — `box-shadow: 0 0 5px 1px
rgba(255,255,255,0.45)` (45% white, 1px, soft blur) plus a drop shadow. No
read-state or favourite colour on the border anymore (a departure from §20.5's
read-state gradient and §20.17's gold favourite border) — those signals moved
elsewhere, see below. Multi-select's "selected" state still turns the border gold;
that's a distinct, temporary UI state, unrelated to favourite. The cover sits inset
from the border in a small matte gap, with its own rounded corners.

**Info block:** title (wraps up to 2 lines), then two meta rows — year + genre
ribbon, and issue/page count + rating stars — anchored to the bottom of the card
(not directly under the title) so they align across a grid row regardless of how
many lines the title takes.

**Genre ribbon (new):** first genre (`genres[0]`), off-white text on a neutral dark
fill, with the read-state colour carried only in a 2px bottom border — blue for
unread, green for reading or fully read. This is now the sole place read-state
colour shows on these cards.

**Favourite badge:** heart icon (unchanged glyph/position) on a `rgba(255,255,255,
0.6)` circle, no border — supersedes §20.17/§20.18's black-border/gold-ring
favourite treatment for these three surfaces. No separate card-level ring.

**Flag-for-review badge:** a real inline SVG flag icon (same stroke style as the
sidebar nav — `stroke="currentColor"`, stroke-width 2, rounded caps/joins),
replacing the old emoji tag. Circle background matches the favourite badge. No red
border on flagged cards.

**Progress bar:** an inset floating pill (`.card-progress-track`/`.card-progress-
fill`), not flush with the cover edge. Singles/individual-issue cards use the
issue's own real `current_page/page_count`; Series-aggregate cards still use
`read_count/issue_count`. (`current_page` was added to `/api/library`'s response,
and `genres`/`personal_rating`/`favorites`/`flagged_for_review` were added to
`/api/home/strips`' `_issue_card()` serializer — both pure additive fields, no new
queries.)

**Rating stars:** a horizontal row in the info block (moved off the cover image,
where §20.18's rating pill used to sit).

**Spacing:** main grid and Folder View grids both use a 19px gap between cards (was
14px). Home Strip cards are widened to `max(var(--card-min), 160px)` — a deliberate
choice over shrinking the badge sizing to fit the old narrower strip width, since
Tez wanted the same full-size treatment there, not a scaled-down variant — with a
matching 19px gap. Home Strip cards deliberately did **not** gain multi-select
(no select-dot) — strips have never supported selection, and adding it would be a
functional change beyond this item's visual scope.

**Theme:** dark-only, fixed regardless of the site's light/dark theme setting — the
card looks the same either way, unlike the rest of the UI.

**Where:** `frontend/js/app.js` (`buildCoverCard()`, `buildStripCard()`,
`buildFolderFileCard()`, `buildIssueDetail()`, plus new helpers `buildRatingRow()`
and `buildFlagBadge()`), `frontend/css/style.css` (`.cover-card--redesign` and
everything scoped under it — deliberately never the bare `.cover-card`/
`.cover-img-wrap`/`.cover-info` selectors, so Series Detail rows and list view stay
untouched), `backend/routers/library.py` (`current_page` addition), `backend/
routers/home.py` (`_issue_card()` field additions).

---

## 21. Change Log

> Record any deviations from this spec here with date and reason.

| Date | Change | Reason |
|---|---|---|
| 2026-06-12 | `backend/config.py` — added module-level constants (`DB_PATH`, `LIBRARY_ROOT`, `THUMBNAIL_DIR`, `THUMBNAIL_SIZE`, `SERIES_FOLDER`, `SINGLES_FOLDER`, `SCAN_EXCLUDE`) derived from `config.json` at import time | Phase 1 code referenced these as `config.DB_PATH` etc. but `config.py` only exposed `get_config()`. Added constants so the module API matches what `scanner.py` and `database.py` expect. |
| 2026-06-12 | `backend/database.py` — changed `from config import DB_PATH` → `from backend.config import DB_PATH` and `from models import Base` → `from backend.models import Base` | Bare module imports worked when running scripts directly from the `backend/` directory but broke when running as a package via `uvicorn backend.main:app`. All imports must use the `backend.` prefix. |
| 2026-06-12 | `backend/scanner.py` — changed `import config` → `from backend import config` and `from models import ...` → `from backend.models import ...` | Same reason as above — bare imports incompatible with package execution. |
| 2026-06-12 | Phase 3 filter bar — **Format filter not implemented**. Spec lists Publisher / Genre / Year / Format; only the first three were built. | The `GET /api/library` response does not include a per-series `format` value (only `format_group` = Series/Singles, which is already covered by the tabs). Filtering by format type (e.g. "Limited Series", "TPB") at the series level requires either a backend change to expose it in the library response, or a different UI approach. Deferred to a future phase. |
| 2026-06-12 | **Reader moved from web to Flutter app.** `reader.html` will NOT be built. Phase 4 is now `issue.html` only. Phase 5 is the Flutter app (Android + Windows) covering library browser + reader. Original Phase 4 (web reader) and Phase 5 (Electron) are replaced entirely. | User requires a proper installed app on Android tablet (primary reading device) and Windows PC. Flutter provides a single codebase for both platforms with native app feel, installed icon, full-screen reading, and local CBZ support for travel use. A web reader would not meet the installed-app requirement on Android. |
| 2026-06-14 | **Section 20 added — V1.1 UI/UX revision round.** Captures a full set of UI/UX changes and new features agreed after live testing of Phases 1–3: four browse surfaces incl. combined All; three-layer filter/status/sort model; Format + Artist filters; new Home page (5 strips); list view + grid tweaks; amber/green read-state colours + progress indicators; richer series page; story-arc grouping off by default; trimmed issue page (Phase 4); dedicated 2000 AD year-grid section; reader tap-zones/double-tap-zoom/signpost-arrows; pagination on admin page. Section 20 is authoritative where it overrides their predecessors. | Real-world testing surfaced the gap between the V1 browsing model and how the collection is actually used — particularly cross-pool filtering, the 2000 AD scale problem, and read-state visibility. Resolves the deferred Format filter from the 2026-06-12 entry. |
| 2026-06-14 | **Format filter — now scheduled** (was deferred 2026-06-12). Added as a live dropdown built from DB `format` values; also used as an inspection tool. | The combined All surface and cross-pool filtering make a per-value Format filter worthwhile; building menus live from the DB removes the original blocker. |
| 2026-06-15 | **Section 20 build round — Phase 4 complete; web UI overhaul complete.** Full implementation of Section 20 changes across frontend and backend. Details below. | Section 20 was the agreed next build round following Phase 3 live testing. |
| 2026-06-15 | **Issue detail page (Section 20.8) — trimmed and fixed.** Removed Characters, Teams, Locations, Inker, Colorist, Letterer, Cover Artist from display (all kept in DB). Renamed "Penciller" → "Artist". Fixed age rating wording to "Rated: X". Added series total-count to issue number badge ("#3 of 6"). Singles now back-link to `/` (Library), not `/series/{id}`. Series nav link at bottom of issue page also routes correctly per format_group. | Section 20.8 spec. Removes clutter; the hidden fields remain in the DB for any future public version. |
| 2026-06-15 | **New backend router: `backend/routers/home.py`.** Adds `GET /api/home/strips` (5 curated cover strips — Random Unread, Recently Added, Random Genre, Random Single, Random Series — 15 covers each) and `GET /api/2000ad/years` / `GET /api/2000ad/year/{year}` for the 2000 AD year-grid section. | Section 20.4 (home strips) and Section 20.9 (2000 AD year grid). |
| 2026-06-15 | **Extended browse endpoints added to `backend/routers/library.py`**: `GET /api/browse/writers`, `/browse/artists`, `/browse/decades`, `/browse/ratings`. | Required for the new filter dropdowns (Section 20.2). |
| 2026-06-15 | **`GET /api/library` response extended** — now includes `read_count`, `reading_count`, `writers`, `artists`, `formats`, `age_ratings`, `has_bw` per series entry. | Enables accurate client-side filtering by all nine filter dimensions without additional round-trips. |
| 2026-06-15 | **`frontend/index.html` rebuilt** — five surface tabs (Home / Series / Singles / All / 2000 AD); browse-controls row (bare count, sort toggle, group-by, grid/list toggle); filter bar with status pills (All / Unread / Reading / Read) and nine dropdown filters (Genre, Publisher, Writer, Artist, Format, Decade, Year, Rating, B&W); inline search in header (browse surfaces only). | Section 20.1–20.3, 20.2 filter model. |
| 2026-06-15 | **`frontend/js/app.js` — library section rewritten.** Surface switching, home page strips, continue reading, full three-layer filter/sort/group logic, read-state colour classification per series, singles card routing to `/issue/{id}`, 2000 AD year grid + year-detail view, arc grouping off by default on series pages. `buildIssueDetail()` updated per Section 20.8. | Section 20 — entire web UI overhaul. |
| 2026-06-15 | **`frontend/css/style.css` — new styles added.** Surface nav; browse-controls row; status pills; read-state card colours (amber 50% for part-read, green 50% for fully-read); part-read progress bar overlay on cover image; grid/list view toggle (list mode); group headings; home strips; 2000 AD year cards and year-detail heading; series backdrop header (blurred cover at 25% opacity + dark overlay + bottom gradient fade). | Section 20.5 (read-state colours + views), 20.6 (series backdrop), 20.9 (2000 AD cards). |
| 2026-06-15 | **`frontend/series.html` simplified** — removed hard-coded back-nav; back button now built inside `buildSeriesHeader()` in JS alongside the backdrop. | Series header now built entirely by JS to support the dynamic backdrop layer. |
| 2026-06-15 | **Singles routing fix (Section 20.12) applied** — `buildCoverCard()` routes `format_group === 'Singles'` cards to `/issue/{id}` instead of `/series/{id}`. | Section 20.12 bug fix. |
| 2026-06-17 | **Admin page V1 complete.** All admin features implemented and tested: stats, scan section (progress bar, changed-files counter, missing-records cleanup), library folders (add/remove roots and excludes), pagination preference, advanced settings. Admin V1 milestone closed. | Phase 6 complete. |
| 2026-06-17 | **Flutter app — navigation updated to 4 tabs (Section 20.1 / 20.9).** `library_screen.dart` updated: `TabController(length: 4)`; tabs are Series, Singles, All, 2000 AD. `all` tab loads `getLibrary()` with no group filter. 2000 AD tab is a standalone `TwoThousandAdTab` widget (not a filtered cover grid). | Matches web UI navigation; resolves Windows EXE also still showing old 2-tab layout. |
| 2026-06-17 | **Flutter 2000 AD tab — year-grid + year-detail (Section 20.9).** New file `flutter_app/lib/screens/two_thousand_ad_screen.dart`: `TwoThousandAdTab` (fetches `GET /api/2000ad/years`, renders fixed cover grid of year cards; `AutomaticKeepAliveClientMixin` preserves state on tab switch); `TwoThousandAdYearScreen` (fetches `GET /api/2000ad/year/{year}`, renders `SliverAppBar` with first-prog backdrop + flat `_ProgTile` list; tapping a prog opens reader). `api_service.dart` extended with `get2000adYears()` and `get2000adYear(int year)`. Backend endpoints unchanged (already in `home.py`). | Section 20.9 — mirrors the web UI's two-level 2000 AD section. Tested on Lenovo TB128FU (Android 13) and Windows EXE. |
| 2026-06-17 | **Android release manifest fix.** Created `flutter_app/android/app/src/release/AndroidManifest.xml` explicitly declaring `INTERNET` and `ACCESS_NETWORK_STATE` permissions. Prevents manifest merger from silently dropping network permissions in release builds (was the root cause of previous server connection failures in release APK). | The main manifest already had these permissions, but the explicit release overlay guarantees they survive the Gradle merge step. |
| 2026-06-17 | **Next phase: tray app (pystray).** See SPEC.md Sections 3 and 14 for full spec. Start in a new session. | Admin V1 complete; all prior phases done. |
| 2026-06-17 | **Tray app built (Phase 6 cont'd) — deviates from Section 3 in two ways.** (1) No Flask editor process exists in this repo, so the tray app does **not** launch/manage an editor subprocess — the "Metadata Editor" menu item just opens `http://localhost:8001`, same as before. (2) The spec's "left-click opens a small popup window" is implemented as a single pystray context menu (shown on either click) with Open Library, Admin, Metadata Editor, and Stop ComicVault — simpler and more robust on Windows than a custom Tkinter popup, same functionality. | User decision (this session): editor app isn't part of this codebase, defer auto-launching it. Menu-based actions chosen over a custom popup window for reliability with pystray's Windows backend. |
| 2026-06-17 | **Bug found and fixed: clicking "Admin" in the tray menu sometimes opened Home instead.** Root cause: pystray's Windows backend bakes the menu into one native `HMENU` handle and only rebuilds it when `icon.update_menu()` runs; `tray_app.py` was calling that on a 2-second timer to refresh a live "Reader: Running/Starting/Stopped" label. If that timer fired while the user had the context menu open (most likely right after launch, during the starting→running transition), `DestroyMenu()` ran on the currently-tracked native menu mid-display, corrupting the command-ID → callback mapping Windows used to dispatch the click. Fixed by dropping the live status text from the menu entirely — status is now conveyed only via the tray icon's coloured dot (swapping `icon.icon` doesn't touch the menu handle, so it carries no such risk) — and the menu's first label is now a static "ComicVault" item. `icon.update_menu()` is no longer called after startup. | User reported the bug after live use. Root-caused by reading pystray's `_win32.py` source (`_on_notify`, `_update_menu`, `_create_menu`) rather than guessing. |
| 2026-06-17 | **Bug found and fixed during live testing: reader subprocess crashed (exit code 1) when launched under `pythonw`.** `start_server.py`'s `print()` calls fail because a console-less parent's child inherits `sys.stdout = None`. Fixed in `tray/tray_app.py` by redirecting the reader subprocess's stdout/stderr to `tray/reader_stdout.log` instead of inheriting. | Found via end-to-end test: worked fine under `python` (console) but failed under `pythonw` (the mode actually used for normal/startup operation), so the bug would have only surfaced after a real reboot. |
| 2026-06-17 | **Windows Startup shortcut created** at `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ComicVault.lnk`, targeting `start.bat`. Tray app now auto-launches on login per Section 14. | Completes Phase 6. |
| 2026-06-17 | **ComicVault V1 build and testing complete.** All six phases (Section 16) built and live-tested end-to-end: scanner against the real collection, REST API via the web UI/Flutter app/tray app, web UI from desktop and tablet browsers, the Flutter deep link, the Flutter app installed and used for reading on Windows and Android, and the tray app's auto-start, health-check restart, and stop behaviour all verified on real hardware. No open bugs remain from this build round. | Closes the V1 build round opened in Section 16. |
| 2026-06-18 | **This file (`SPEC.md`) now lives in `comicvault_v2`, a separate cloned repo** (`D:\workshop\comicvault_v2`, history carried over from this V1 repo, remote repointed to `quixline/comicvault_v2`). **This entry, and all entries below it, apply to V2 only — V1's own copy of this file and its `cBook_Server/backend/scanner.py` are unmodified.** Found and fixed BUG-001 during V2's migration setup: Section 6's incremental scan rule ("File unchanged | Skip") didn't account for a thumbnail file being missing on disk despite unchanged `date_modified` — relevant because V2 was set up from a **copy** of this DB without copying `thumbnails/` (per Section 6's "Cover / thumbnail generation" rule, assumed regenerable on next scan, which it wasn't, until fixed). Scanner's skip branch now also checks thumbnail existence before skipping. Full detail in `comicvault_v2/BUGS.md` and `progress.md`. | One-time V2 environment setup, prerequisite to `EDITOR_SPEC.md` build work. Recorded here because it's a real defect in the scanner logic this file documents (Section 6), not just a migration footnote. |
| 2026-06-18 | **V2 found completely unreachable after a reboot** — root-caused to two compounding issues, neither a deviation from this spec's content: (1) the machine's Windows Startup shortcut had never been repointed from the old V1 repo (`cBook_Server`) during the V2 migration, so a reboot launched V1 instead of V2; (2) `start_server.py` still imported `EDITOR_PORT` after the BUG-002 commit deleted it from `backend/config.py`, crashing the reader server with an `ImportError` on every startup since. Both fixed (commit `7e49d35`); full root-cause writeup in `progress.md`. | Recorded here as a pointer since it looked like a regression in this spec's startup/process behaviour (Sections 3, 14) before the real cause — an unrelated stale shortcut plus an incomplete dead-code cleanup — was found. |
| 2026-06-18 | **Home page surface tab order changed** (Section 20.1) — `frontend/index.html`'s nav now reads Home, All, Singles, Series, 2000 AD (previously Home, Series, Singles, All, 2000 AD). Order only; the four surfaces and their behaviour are unchanged. | Tez's preferred browsing order, requested directly during live use. |
| 2026-06-21 | **Tier 4 Item 3 — Writer/Artist entity dedup, backend + real migration.** New `people`/`issue_credits` tables (Section 7); `_sync_credits()` added to `scanner.py` mirroring `_sync_genres()`'s pattern, the only code path that writes Issue credit data for both scans and editor saves. Found and fixed a real defect (`_split_csv()` didn't dedupe a literal repeated name within one CSV field — 175 real issues affected; see `BUGS.md` BUG-006) before the real run. 76 candidate duplicate pairs detected and reviewed (35 merged, 41 kept separate); migration run for real against the live ~5,429-issue library, verified idempotent, original `issues` table confirmed fully intact. An incident occurred mid-session — the live running server picked up in-progress source edits on its own restart and wrote a handful of real rows before the planned real-DB checkpoint — full account in `progress.md`, resolved per Tez's decisions, no data loss. Frontend (dropdown removal, click-through UI, editor fuzzy warn-on-save) deferred to a future session. | `comicvault-changes.md` Tier 4 Item 3. |
| 2026-06-21 | **Tier 4 Item 3 — Session C (frontend), item now fully complete.** Writer/Artist credits on `/issue/{id}` are now clickable links (Section 20.16); Writer/Artist filter dropdowns removed; `matches_field()`/`/browse/writers`/`/browse/artists` resolve against `Person.id`; new `GET /api/people/fuzzy-match` powers a non-blocking editor save-time warning. Also fixed a real second consumer found while exploring the field-filter mechanism: the admin Home Strips builder's field-value picker (`admin.js`), which stored the raw fetched value verbatim — now separates display label from stored `person_id`. **Incident:** verifying the editor's save flow against a real issue (assumed-from-memory id that turned out, on the *current* scratch copy, to point at a different real file than intended — ids aren't stable across separate scratch copies, a lesson this session had already written down once and failed to re-apply) modified a real CBZ's `Writer` and `Summary` fields. Root-caused with a genuinely fake, disposable CBZ fixture (proving the actual code has no bug — the mistake was in test construction), then fully restored from the same-day pre-migration DB backup and verified field-by-field identical to it. New unrelated bug found as a side effect, not fixed: BUG-007, Basic Editor Summary field line-break doubling on every save. Full account in `progress.md` and `DECISIONS.md`. | `comicvault-changes.md` Tier 4 Item 3. |
| 2026-06-21 | **Tier 4 Item 2 — Multi-select + Favorites/Rating built.** `issues` table gained `favorites`/`personal_rating` (Section 7). Found that `create_all()` doesn't add columns to an already-existing table (only new tables) — added a one-time manual `ALTER TABLE` step to `database.py`'s `init_db()`, verified against a scratch copy of the real ~5,500-row DB before relying on it (see `DECISIONS.md`). New bulk endpoints in `progress.py`: `POST /api/progress/bulk/{mark-read,mark-unread,favorite,unfavorite,rate}`, all accepting `{issue_ids: [...]}` (plus `rating` for `/rate`). Registered *before* the existing `/progress/{issue_id}/mark-read` route — Starlette matches path templates in registration order, and `/progress/bulk/mark-read` would otherwise have matched `{issue_id}/mark-read` first with `issue_id="bulk"`, 422ing (caught live during this session's own endpoint testing). Frontend: long-press (Pointer Events, ~500ms) enters selection mode, short taps add more; a floating bottom toolbar drives the bulk actions. Scope boundary documented in Section 20.15. Issue detail page also got standalone favorite-toggle + star-rating controls (reuse the same bulk endpoints with a 1-item id list — no separate single-issue endpoints). | `comicvault-changes.md` Tier 4 Item 2. |
| 2026-06-19 | **Tray app menu redesign** (Section 3) — "Stop ComicVault" (stopped the reader and exited the tray app together) split into three actions: **Stop Server** (reader only, tray keeps running), **Start Server** (restarts it, no-op if already running), and **Close** (stops the reader, then exits — the old combined behaviour, renamed). A new `manually_stopped` flag in `tray_app.py` stops the existing 30s health-check loop from auto-restarting a server that was stopped on purpose. Also added: a checkable **Start ComicVault at login** menu item (Section 14 — creates/removes the Startup shortcut directly, no more manual one-time setup), and dark-menu support following Windows' own theme setting (new `pywin32` dependency for the shortcut, small `ctypes`/`uxtheme` call for the theme — both additive, no architecture change). | Tez wanted independent start/stop of the reader without relaunching the whole tray app, plus self-service autostart management. |
| 2026-06-19 | **Corrected understanding of the 2026-06-17 menu-corruption bug fix**, found while verifying the new checkable autostart item was safe to add: `icon.update_menu()` is not "never called after startup" as the original fix's comment claimed — pystray wraps every menu item's callback in its own `update_menu()` call already (verified by reading `pystray/_base.py`/`_win32.py` directly), and this has always fired safely after every click since it runs on the message-pump thread only after the native popup has already closed. The actual bug came specifically from a **background thread** calling `update_menu()` on a timer, racing with the menu being open concurrently. `tray_app.py`'s `build_menu()` comment corrected accordingly. | Needed to confirm the new checkable item wouldn't reintroduce the original bug before relying on it; the original fix's own description of its mechanism turned out to be broader than necessary. |
| 2026-06-23 | **Section 20.17 added** — card behaviour additions: favourite star size +5px with 1px black border; issue-page star rating row padding fix; favourited card thin gold border (coexists with read-state gradient); dark/light theme auto-matches Windows system theme with manual override in Settings. Not yet built. | Inbox triage session 2026-06-23. |
| 2026-06-23 | Section 20.17 built. Theme override control lives in Admin → Appearance, a new ungated section (not inside the existing Advanced Settings unlock) since it's a plain preference, not a destructive or technical setting. | v2.3 build plan Item 3. |
| 2026-06-22 | **Section 20.9's hardcoded 2000 AD section removed (v2.2)**, exactly as anticipated by that section's own "removable later if the app ever goes public" note. Its behaviour is generalised into Folder View, a new `view_mode` on Custom Tabs — see `CUSTOM_TABS_SPEC.md` §9 (current authoritative design) and `comicvault-changes-v2.2.md` (build record). Section 20.15's multi-select scope bullet updated: `buildAdProgCard()` → `buildFolderFileCard()`. | `comicvault-changes-v2.2.md` Part A — 2000 AD's bespoke view was always meant to come out before the app went public; this was the planned removal, not a regression. |
| 2026-06-30 | **CBR support added (v2.4 Item 5), reversing V1's "all files confirmed CBZ" assumption.** Scanner (§6/§6.1) now matches `.cbr` alongside `.cbz`, opening via `rarfile` instead of `zipfile`. New `issues.container_format` column (§7) distinguishes container type from the unrelated ComicInfo `format` field. `rarfile` added to dependencies (§13), extraction-only — CBR is never written by any part of ComicVault; RAR creation needs a paid WinRAR install, so editing a CBR's metadata rebuilds it as `.cbz` instead (see `EDITOR_SPEC.md` §3.1/3.2/§2/§9 for the corresponding reversal there). Driven by a shift toward a possible public release — forcing users with large mixed CBZ/CBR collections (some >100,000 issues) to bulk-convert before their library is browsable was judged unviable. PDF and EPUB, originally scoped alongside CBR in the same v2.4 item, were dropped — PDF is handled by CAPT's existing convert-to-CBZ tool instead (v2.4 Item 6) rather than native scanner support; EPUB was dropped entirely as structurally incompatible with the page-indexed reading model and not a confirmed need. Full rationale in `DECISIONS.md`, build item in `v2.4/comicvault-changes-v2.4.md` Item 5/11. | v2.4 Item 5, eng-reviewed and scoped 2026-06-30. |
| 2026-07-02 | **§6 corrected — scanner finds `ComicInfo.xml` at any folder depth, not just the archive root (BUG-018 fix).** `_parse_cbz()` now reuses `find_xml_in_archive()`/`extract_xml_from_archive()` (`backend/editor/archive_io.py`), the same helpers the Basic/Full Editors already used — previously only the scanner's initial read was folder-blind; editors and the flatten-on-save rebuild path were already correct. No rebuild-at-scan-time added (would risk real delay across ~5,500 archives); flattening still only happens naturally on first edit-save, unchanged. | `BUGS.md`/`archive/bugs-fixed-archive.md` BUG-018 — found 2026-06-30 scoping v2.4 Item 8, fixed off-cycle 2026-07-02 after v2.4's close (never tied to a numbered version item). |
| 2026-07-15 | **§7 `issues` table — 4 of 6 legacy raw-CSV credit columns dropped:** `inker`/`colorist`/`letterer`/`cover_artist` (confirmed dead, no reader anywhere in backend/frontend) removed via a new idempotent `_drop_legacy_credit_columns()` migration in `database.py`. `writer`/`penciller` deliberately kept — traced every usage first and found they still power live search, "Group by Writer", and the series-card meta line, not yet migrated onto `people`/`issue_credits`. **§20.14 also trimmed** — Advanced Search page and Multiple scan locations/series-overview-field entries removed, both ruled out by Tez (see `ROADMAP.md` "Resolved" section for rationale). | `ROADMAP.md` "Resolved" · `DECISIONS.md` — verified against a scratch DB copy before touching the real one; Tez manually confirmed the real app afterward. |
| 2026-07-15 | **Section 20.20 added — card redesign (grid, Home Strips, Folder View).** New card border/genre-ribbon/favourite-badge/flag-badge/progress-pill treatment, scoped via a new `.cover-card--redesign` CSS modifier class so Series Detail rows and list view are untouched. Home Strip cards widened to fit the same full-size badges rather than a scaled-down variant. Supersedes the read-state/favourite/badge visual detail in §20.5, §20.17, §20.18 for the three affected surfaces. | Ad-hoc request, applying a Claude Design mockup then heavily fine-tuned live with Tez — see `v2.6/progress.md` and `DECISIONS.md`. |
