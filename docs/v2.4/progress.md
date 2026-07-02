# ComicVault — Progress Log (v2.4)

Narrative build history for v2.4 — per-session detail, what was actually built,
verification notes. Append-only, written by Claude Code at the close of each
session. Full project history through v2.3's close lives in
`archive/v2.3/progress.md` — not duplicated here.

---

## Session — 2026-06-29: v2.4 Item 1 — restrict all admin access for remote users when Remote Administration is off

**Goal.** Close the gap flagged going in: today's gating only blocked remote
requests from the handful of endpoints explicitly decorated with
`is_local_request()` (Clear Database, Restore Database, the folder/file
dialogs, `/admin/restart`). Every other `/api/admin/*` and `/api/editor/*`
endpoint — stats, logs, cleanup-missing, backup, the folder-tree browse, the
scan trigger — was reachable from any LAN device whenever password protection
was off, which is the **default** state. So in practice most installs were
wide open remotely despite "Remote Administration" reading as off.

**What was found.** `require_admin_auth()` (`backend/auth.py`) no-op'd
entirely — including its remote-block check — whenever
`is_protection_enabled()` was false. The remote check only ever ran in the one
case (protection on, remote admin off) that already worked correctly. The
`/admin` and `/editor` page routes (`backend/main.py`) had no gating of any
kind — always served the HTML shell to anyone, local or remote.

**What changed.**
- `backend/auth.py` `require_admin_auth()` — moved the
  `is_local_request()` / `is_remote_admin_enabled()` check ahead of the
  protection-enabled early return, so it now applies unconditionally. This
  alone fixes every route already wired through the `_auth_gate` dependency
  in `main.py` (all of `admin.router`, `editor_basic.router`,
  `editor_full.router`) — not just the destructive actions.
- `backend/main.py` — `GET /admin` and `GET /editor` now run the same
  local-or-remote-admin-enabled check before serving the page, so a blocked
  remote request gets a 403 instead of a functional-looking HTML shell.
- `frontend/js/auth.js` `checkAuthStatus()` + `frontend/css/style.css` — the
  cog icon **stays in place** for a non-local session when Remote
  Administration is off (no layout shift to the Login/Logout button next to
  it), but gets a `.settings-btn--disabled` class: dimmed and
  `pointer-events: none`, so it's visibly inert rather than removed. First
  pass hid the icon outright with `hidden`, which both shifted the Login
  button left and didn't match the intended behaviour — corrected same
  session before doc close, per the manual-test-first rule this session
  added to `CLAUDE.md`/`working-rules.md`.

Local sessions (the owner, at `127.0.0.1`) are unaffected in every state —
this only closes the remote-access gap, V1 local behaviour is unchanged.

**Verified.** Unit-level check (`unittest.mock.patch` on
`is_protection_enabled` / `is_remote_admin_enabled`, scratch script, not
committed) against `require_admin_auth()` directly, covering all four
relevant (protection, remote_admin, local) combinations. **Manual test by
Tez: passed** (2026-06-29) — confirmed after the cog-icon correction above.
No real `config.json` or library data touched.

**Docs.** `ADMIN_SPEC.md` §7.2 updated to describe the broadened gate.
`meta/roadmap.html`'s Now lane updated — Item 1's card removed, remaining 13
cards renumbered 1–13 (those are display-order badges, not the `comicvault-
changes-v2.4.md` Item numbers, which never renumber — see
`meta/working-rules.md` "Version-qualified references").

---

## Session — 2026-06-29: v2.4 Item 2 — default server port → 9424

**Goal.** Resolve the recurring Windows port-exclusion conflict (`BUGS.md`
BUG-004) at the source by changing the default `reader_port` from `8000` to
`9424`, rather than relying on the existing user-configurable port field
(`ADMIN_SPEC.md` §7.3) only being discovered after a fresh install already
hits the conflict.

**What changed.**
- Default fallback (used when `reader_port` is missing from `config.json`):
  `backend/main.py`, `backend/config.py`, `backend/routers/admin.py`
  (`/admin/config` GET fallback) — `8000` → `9424`.
- `config.example.json` — template default for new installs.
- `config.json` (the real, live config) — updated directly to `9424`, since
  it had `reader_port` set explicitly and an explicit value shadows the code
  default; nothing would have changed on restart otherwise.
- Stale port mentions in comments/docs-adjacent text: `start_server.py`,
  `README.md`.
- Flutter app placeholder/default server URL (`api_service.dart`,
  `settings_service.dart`, `settings_screen.dart`) — example text only, no
  functional change, updated for consistency.
- **Not touched (scoping miss, caught during testing):** `tray/tray_app.py`'s
  "Open Library"/"Admin" menu links read `READER_PORT` from `config.json` at
  the tray app's own launch — they update automatically once the tray app is
  restarted, no code change needed there. Flagged here so it's not mistaken
  for an oversight next time this comes up.

**Verified — manual test by Tez: passed (2026-06-29).** Library reachable at
`http://localhost:9424` after restart.

**Found during testing, not a regression from this change:** stopping the
server from the tray menu did not actually terminate the old process — it kept
listening on 8000 with `config.json` still showing the new 9424 in memory-cache
for the *new* process the tray then started, leaving two live server instances
against the same `comicvault.db` simultaneously (confirmed via `netstat`/
`Get-Process`: PID 10520 on 8000, started before the edit; PID 15232 on 9424,
started after). Resolved by fully quitting and relaunching the tray app rather
than using its "stop" action alone. Documented as a standing caution in
`ADMIN_SPEC.md` §7.3 so it's not rediscovered the same way next port/config
change.

**Docs.** `ADMIN_SPEC.md` §7.3 updated (default value + the tray-app-restart
caution). `ROADMAP.md`'s "Resolved (kept for context)" port-8000 note tightened
to reflect the new default. `meta/roadmap.html`'s Now lane updated — Item 2's
card removed, remaining 12 cards renumbered 1–12.

---

## Session — 2026-06-29: v2.4 Item 3 — empty-results icon → logo image

**Goal.** Replace `<div class="empty-icon">📚</div>` on the no-matching-results
state ("No comics match these filters.") with the logo image at
`images/logo1.png`, per the item as scoped.

**What changed.**
- `images/logo1.png` was confirmed present but not web-reachable — the
  project-root `images/` folder isn't under any static mount (only `/static`
  → `frontend/` exists). Copied the file to `frontend/images/logo1.png`
  (the root copy is untouched) so it's served at `/static/images/logo1.png`
  through the existing mount, rather than adding a new one for a single file.
- `frontend/js/app.js` line ~906 — swapped the `📚` `empty-icon` div for
  `<img class="empty-logo" src="/static/images/logo1.png" alt="">` on the
  "No comics match these filters." state, as scoped.
- `frontend/css/style.css` — added `.empty-logo` alongside the existing
  `.empty-icon` (emoji) class rather than overloading one class for both.
  Went through two corrections from manual testing before settling:
  first pass used fixed `width`/`height` (56×56), which squashed the logo's
  non-square aspect ratio into a box; fixed by switching to
  `height: 56px; width: auto`. Centering also needed `display: block;
  margin: 0 auto` rather than relying on the parent's `text-align: center`,
  since an `<img>` doesn't center the same way inline text does.
- **Expanded beyond the item's original scope, at Tez's explicit call after
  seeing it work:** the same `.empty-icon` emoji pattern (`⚠️` and one more
  `📚`) appeared in 10 other empty/error states across `app.js` — home strips
  init failure, "No content yet.", server-unreachable, tab/view no-longer-
  available, folder-load failure, search failure, series-not-found,
  issue-not-found. All 10 were switched to the same `<img class="empty-logo">`
  markup for visual consistency, since the fix (file location, sizing,
  centering) was already proven working on the first one. See
  `DECISIONS.md` for the rationale entry — this is a judgment call (logo
  standing in for warning/error icons too, not just "no content") worth a
  paper trail since it wasn't in the original item text.

**Verified — manual test by Tez: passed (2026-06-29).** Confirmed across the
filtered-empty state and re-checked after both CSS corrections.

**Docs.** `DECISIONS.md` — new entry for the scope expansion. `meta/
roadmap.html`'s Now lane updated — Item 3's card removed, remaining 11 cards
renumbered 1–11.

---

## Session — 2026-07-01: CAPT-tooling cluster (Items 9, 10, 11, 12, 13, 16) — build session

**Scratch environment, used for every item below.** `config.json` was
temporarily swapped for a scratch copy pointing `library_root`/`db_path`/
`thumbnail_dir`/`backup_folder`/`reader_port` (9425) at
`C:\Users\tezdr\AppData\Local\Temp\claude\...\scratchpad\` — a handful of
synthetic CBZ fixtures, never `L:\Comic Archives` or the real
`backend/comicvault_v2.db`. The real `config.json` (and `logs/*.md`, which
`scan_logs.py` writes to a hardcoded repo-relative path regardless of the
active config) were backed up before the swap and restored exactly once this
whole build round closed out. Any per-item "verified against a scratch
library/DB" note below refers to this same environment, not a fresh one
per item.

## Session — 2026-07-01: v2.4 Item 9 — Favourites as a Custom Tab category

**Goal.** Build the design from `CUSTOM_TABS_SPEC.md` §10 (scoped 2026-06-30):
a library-wide Custom Tab showing every favourited issue regardless of folder,
plus the bundled BUG-017 fix (`BUGS.md`) in the same session since both touch
`get_library()`'s per-series aggregation.

**What changed.**
- `backend/models.py` / `backend/database.py` — new `CustomTab.basis_type`
  column (`'folder'`/`'favorites'`, default `'folder'`), added via the same
  idempotent `ALTER TABLE` pattern already used for `view_mode`.
- `backend/routers/admin.py` — `create_custom_tab()` gained a `basis_type`
  branch: `basis_type="favorites"` skips the name/folder_path requirement,
  server-assigns `name="Favourites"`/`folder_path=""`/`view_mode="flat"`, and
  is blocked (409) if a favourites tab already exists — server-side, not just
  the button-disable in the UI. `update_custom_tab()` rejects (400) any
  attempt to change `folder_path`, `basis_type`, or set `view_mode` off
  `"flat"` on a favourites-basis row, same protection style
  `HOME_STRIPS_SPEC.md` §4.3 uses for `is_default` rows.
- `backend/routers/library.py` — `get_library()` gained the `basis_type`
  branch from §10.3 (filters to `Issue.favorites` before the per-series
  groupby, same principle as BUG-010's fix); the three Folder View endpoints
  (`GET .../folder`, `POST .../folder/mark-read`, `GET .../search`) now 400 on
  a favourites-basis tab rather than evaluating against an empty
  `folder_path`.
- **BUG-017 fixed** in the same function: `"favorites": cover_issue.favorites`
  → `"favorites": any(i.favorites for i in issues)`, matching the existing
  `has_bw` aggregation two lines below. Favouriting a non-#1 issue in a series
  now correctly surfaces that series under the All-tab Favourites filter.
- `backend/routers/home.py` — `/api/nav/config` now includes `basis_type` per
  tab, so the frontend can tell a favourites tab apart from a folder tab
  without a second fetch.
- `frontend/admin.html` / `frontend/js/admin.js` — new "Add Favourites Tab"
  button next to "Add Tab" (disables once one exists or the 4-visible cap is
  hit); `makeCustomTabRow()` special-cases favourites rows (shows "Library-wide
  (Favourites)" instead of a path, view-mode selector disabled).
- `frontend/js/app.js` — new `tabBasisTypes` map + `isFavoritesTab()` helper
  (mirrors the existing `tabViewModes`/`isFolderViewTab()` pair). Favourites-
  specific empty-state text (§10.6). **Live-removal fix (§10.5) — went through
  one correction during manual testing:** the first pass re-ran
  `getFilteredLibrary()` + re-render after patching the `.favorites` flag, on
  the assumption that would re-exclude the item — this works for the All-tab
  `activeFavorites` filter (which re-evaluates `pool.filter(s => !!s.favorites)`
  on every render) but silently did nothing for the Favourites tab itself,
  since `tabLibraryCache[tabId]` was already scoped server-side at fetch time
  and nothing re-filters it client-side. Caught by testing the actual DOM
  output, not just reading the diff. Fixed by explicitly dropping the matching
  entry from any favourites-basis tab's cache on unfavourite, same best-effort
  tolerance the rest of this bulk-patch family already accepts (a reload
  reflects true server state).

**Verified — manual test, this session, against a scratch library/DB (never
`L:\Comic Archives`).** Favourited issue #2 of a 3-issue scratch series
(deliberately not #1); confirmed the series surfaced under both the new
Favourites tab and the existing All-tab Favourites filter (BUG-017); confirmed
un-favouriting live-removed the card from both surfaces without a reload;
confirmed the Favourites-specific empty-state text renders when nothing is
favourited; confirmed a second favourites tab is rejected (409) and direct
PATCH attempts against `folder_path`/`basis_type`/`view_mode` on the
favourites row are rejected (400); confirmed renaming the tab still works.
Real library/config untouched — see the session's scratch-environment note at
the top of this build round.

**Docs.** `CUSTOM_TABS_SPEC.md` §10 marked built. `BUGS.md` BUG-017 moved to
`archive/bugs-fixed-archive.md`.

---

## Session — 2026-07-01: v2.4 Item 10 — File Rename Tool

**Goal.** Build the File Rename Tool per `admin-spec-section-12-processing-
tools.md` §12.1 (re-scoped 2026-07-01), and — since this is the first
Processing Tool built — the shared in-app picker/log/backup infrastructure
the rest of the CAPT-tooling cluster (Items 12, 13, 16) will reuse rather than
duplicating a fourth and fifth time, per the cross-review finding at the start
of this build session.

**Shared infrastructure built this session:**
- `backend/file_picker.py` — `list_directory()` / `list_drives()`, no
  `library_root` restriction. Each tool's router mounts its own thin
  `browse`/`drives` wrapper with its own extension/content filter on top.
- `backend/tool_logs.py` — append-only log writer with a fixed 1MB cap,
  independent of the configurable Log Size Limit (§8). `rename_log.py` is a
  thin wrapper over it.
- `frontend/js/filePicker.js` — one configurable picker component (Home/Up
  with a "This PC" drive-letter listing as the Up terminus, single-folder or
  multi-file select modes), reusing the existing `.fe-picker-*` CSS classes
  from the Full Editor's picker. One shared overlay in `admin.html`
  (`#ptPickerOverlay`), reconfigured per `openFilePicker()` call — same
  pattern `admin.js`'s existing `#ctPickerOverlay` already uses for Custom
  Tabs + Home Strips.

**File Rename Tool:**
- `backend/rename_tool.py` — ported `parse_comic_filename()`/`build_filename()`
  from CAPT's `filename_parser.py`/`rename_u.py`, with the three bugs fixed
  per the 2026-07-01 re-scope (dynamic year ceiling instead of hardcoded
  `present_year = 2025`; zero-issue strings no longer stripped to empty;
  whitespace/dangling-dash collapsed after every token/bracket removal, not
  just once) and `build_filename()` rewritten to the decided
  `Series - Title #Issue (Year)` dash-joined format (CAPT's original was
  space-joined, different field order — not a straight port).
- `backend/routers/rename.py` — browse/drives (shared picker), in-memory
  working-file-list (mirrors `editor_full.py`'s `_working_files` pattern),
  `parse`/`preview` endpoints (parsing and filename-building logic stays
  server-side, not duplicated in JS — matches how the Full Editor already
  keeps its business logic backend-side), and `apply`. Whole router local-
  only gated at the `APIRouter(dependencies=...)` level, not per-endpoint —
  per §11's shared notes, the whole section is inert remotely, not just the
  destructive Apply step.
- `frontend/js/processingTools.js` + `admin.html`/`admin.js` — edit panel
  with independent File/All checkboxes per field, Auto-Increment (Issue→All
  only), case-style radio group, live preview (no explicit Preview button),
  Apply + summary modal. Per-file accumulation across selections implemented
  via a `renameFileOverrides` map so re-selecting a previously-edited file
  restores its checkbox/value state. Combined File+All edits across
  different fields (e.g. Series→All + Issue→File on one specific file) merge
  correctly per file; Auto-Increment falls back to one shared batch call
  (sequential numbering doesn't combine meaningfully with a per-file
  override anyway). Reorder via Move Up/Down buttons rather than full
  drag-and-drop — same practical effect (auto-increment respects display
  order) with far less implementation risk.
- `backend/rename_log.py` — `rename_log.md`, `DD/MM/YYYY HH:MM — old → new`.

**Verified — manual test, this session, against scratch fixture files (never
`L:\Comic Archives`).** Confirmed all three parser bugs fixed directly via
`POST /rename/parse` against the spec's own sample patterns (a 2026-dated
file, a `000`-numbered file, `Conan the Barbarian v05 - Twisting Loyalties`).
Loaded 4 scratch files via the picker; tested single-file edits accumulating
across two files simultaneously; tested re-selecting a file restores its
edited-field state; tested batch (All) mode correctly resets prior single-file
accumulation and applies to every loaded file; tested a combined Series→All +
Title→File(selected file) edit computing correctly per file; tested
Auto-Increment sequential numbering, including after a Move Up/Down reorder;
tested Clear Preview; tested Apply — confirmed the file was actually renamed
on disk and `rename_log.md` got the correct entry; tested the already-exists
collision guard (no partial-silent-failure, failed file remains in the
working set). Local-only gating verified by code (same `is_local_request()`
primitive already proven in v2.4 Item 1's testing) rather than a live remote
simulation, since a `curl` from this machine can't spoof a non-loopback peer
address.

**Docs.** `admin-spec-section-12-processing-tools.md` **folded into
`ADMIN_SPEC.md` §11** (renumbered §12.1–§12.4 → §11.1–§11.4) per the
resolution plan in `INDEX.md` and this item's own "on build" note in
`comicvault-changes-v2.4.md` — the standalone file is retired. `INDEX.md` and
`CLAUDE.md`'s doc tables updated to drop the now-nonexistent file.
`ADMIN_SPEC.md` §11.1 marked built; its status block updated.

---

## Session — 2026-07-01: v2.4 Item 11 — native CBR support (build)

**Goal.** Build the CBR design Item 5 scoped 2026-06-30 (`SPEC.md` §6.1/§7,
`EDITOR_SPEC.md` §3.1/§3.2) — full native read support across the scanner,
reader, and both editors. Biggest item in this batch: this is scanner/reader/
editor work, not a Processing Tools item.

**What changed.**
- `requirements.txt` — added `rarfile`. Confirmed as the first build sub-step
  (before writing any CBR-dependent code): `unrar` resolves via PATH
  (`C:\Program Files\WinRAR\unrar.exe`), no explicit `rarfile.UNRAR_TOOL`
  override needed on this machine.
- `backend/archive_formats.py` (new, shared) — `archive_namelist()` /
  `archive_read_bytes()` dispatch on `.cbz`/`.cbr`, plus
  `BAD_ARCHIVE_EXCEPTIONS` and `ENTRY_NOT_FOUND_EXCEPTIONS` tuples so callers
  don't hand-roll the zipfile-vs-rarfile exception handling three times.
  (`rarfile.RarFile.read()` raises its own `NoRarEntry` for a missing entry,
  not `KeyError` like `zipfile` — caught during review before it became a
  live bug in `reader.py`'s page-serving.)
- `backend/models.py` / `backend/database.py` — new `Issue.container_format`
  column (`"cbz"`/`"cbr"`), added via the same idempotent `ALTER TABLE`
  pattern as `favorites`/`personal_rating`, with a backfill `UPDATE` deriving
  the value from each existing row's `file_path` extension.
- `backend/scanner.py` — disk walk now matches `.cbz` **or** `.cbr`;
  `_parse_cbz()` (kept its name — still the single per-file parse entry
  point) branches via `archive_formats`, fails soft on a corrupt archive of
  either format (falls back to filename metadata, same as the existing bad-
  CBZ path, doesn't crash the scan pass); `_generate_thumbnail()` same
  dispatch; `_apply_metadata()` sets `container_format`; the filename-fallback
  regex now matches `.cbr` too.
- `backend/routers/reader.py` — `_sorted_pages()` and both page/cover byte-
  reads branch via `archive_formats`.
- `backend/editor/archive_io.py` — `find_xml_in_archive()` /
  `extract_xml_from_archive()` / `get_archive_page_count()` branch via
  `archive_formats`. `_rebuild_archive()` (shared by `write_comicinfo_to_cbz()`
  and `keep_single_xml()`) now detects a `.cbr` source, rebuilds to a sibling
  `.cbz` path instead of overwriting in place, deletes the original `.cbr`
  only after the new `.cbz` is confirmed written, guards against a sibling
  `.cbz` that already exists (raises, no clobber), and **returns the final
  path** so every caller can propagate it. Stale module docstring ("CBR
  support is dropped entirely... library is all-CBZ") corrected — this item
  was flagged as the one that owns that correction (§11.3.8's implementation
  note in the now-folded processing-tools scoping).
- `backend/routers/editor_basic.py` (`save_editor_fields`) and
  `backend/routers/editor_full.py` (`process_batch`, plus `resolve_file_xml`,
  `get_file_preview`, `get_file_page`) — capture `write_comicinfo_to_cbz()`'s
  returned path; when it differs from the original, Basic Editor updates the
  `Issue` row's `file_path`/`container_format` and **`db.flush()`s before**
  calling `scan_single_file()` (session is `autoflush=False` — without the
  flush, the rescan's `file_path` lookup wouldn't see the change and would
  insert a duplicate row instead of updating the existing one). Full Editor
  updates the in-memory working/queue entry's `path`/`filename` instead,
  since pre-library files have no DB row yet. `editor_full.py`'s
  `ALLOWED_EXTENSIONS` extended to `.cbr` so the picker actually surfaces CBR
  files for pre-library tagging.
- `backend/routers/admin.py` — `POST /api/scan/file`'s extension check
  extended to accept `.cbr`.

**Verified — manual test, this session, against the scratch environment
(never `L:\Comic Archives`).** Built a real CBR fixture with `Rar.exe`
(WinRAR trial, already installed) containing a `ComicInfo.xml` + one image.
Scanned it in: confirmed XML metadata parsed correctly, `container_format`
stored as `'cbr'` in the DB (not currently surfaced via the API response —
nothing client-side reads it yet, left as-is), thumbnail generated, cover and
page endpoints served correctly. Built a truncated/corrupt CBR: confirmed it
scanned in with `metadata_source="filename"` (fail-soft) and the scan
completed with `errors=0` — no crash. Edited the good CBR's metadata via
Basic Editor: confirmed the `.cbr` became a `.cbz`, the original was deleted,
and the DB row (same `id`, not a duplicate) updated its `file_path`/
`container_format`/edited fields correctly — this is what caught the missing-
`db.flush()` bug before it shipped. Repeated via Full Editor: add-to-working-
set, load XML fields, preview, single-page fetch, and Process All all worked
against a CBR, and Process All correctly updated the working-set entry's path
after the rebuild. Tested the no-clobber guard directly: pre-created a
colliding `.cbz` next to a `.cbr` with the same stem, attempted to save via
Full Editor, confirmed a clean error and both files left completely
untouched on disk.

**Docs.** `SPEC.md` §6.1 and its `container_format` schema row marked built.
`EDITOR_SPEC.md` §3.1/§3.2 marked built, with the `db.flush()` gotcha and the
no-clobber guard documented for anyone touching a save path later.

---

## Session — 2026-07-01: v2.4 Item 12 — Convert Archives

**Goal.** Build CBR→CBZ and PDF→CBZ conversion per `ADMIN_SPEC.md` §11.2
(re-scoped 2026-07-01 to the unified backup model). **Includes the cross-
review finding from the start of this build session** — Convert Archives'
picker was missing the same `*.bak` filename-suffix exclusion Convert Images
already had, which would let a permanently-kept `.bak` from a warned run get
silently reprocessed as a fresh input on the next pass (most relevant for
Item 16's automation, which re-runs Stage 1 on a schedule).

**What changed.**
- `requirements.txt` — added `pymupdf`. Confirmed it imports cleanly
  (`import fitz`) before writing any PDF-dependent code.
- `backend/backup_model.py` (new, shared with Item 13) —
  `stage_validate_and_replace()` implements the unified three-outcome table
  (§11.4.6): clean success auto-deletes the `.bak`; warnings keep it
  permanently; failure discards the staged file and leaves the original
  untouched. Takes `original_path`/`staged_path`/`target_path` as three
  separate arguments (not two) — Convert Archives always produces a
  *different* filename (`.cbr`/`.pdf` → `.cbz`), unlike an in-place same-
  filename rewrite, so "what gets renamed to `.bak`" and "where the staged
  file lands" are genuinely different paths, not one. `bak_already_exists()`
  is a separate pre-flight guard, checked before any conversion work starts
  (no point extracting/rezipping a file that's just going to be rejected).
- `backend/archive_convert.py` (new) — `convert_archive_file(source_path,
  from_format) -> ConvertResult`, router-independent (Item 16 will call it
  directly). `detect_archive_format()` ported unchanged from
  `arc_convert_util.py`. CBR→CBZ ports `arc_conv_helpers.py`'s tolerant RAR
  extraction (`ignore_crc_errors=True`, tracking a `crc_errors` list →
  `pages_skipped`); CBZ→CBR dropped entirely, no `create_rar_archive()` port.
  PDF→CBZ ports `arc_conv_pdf_proc.py`'s page-render loop, swapping CAPT's
  hardcoded `fitz.Matrix(1, 1)` for `fitz.Matrix(PDF_RENDER_DPI / 72, ...)`
  with `PDF_RENDER_DPI = 300` as a module constant.
- `backend/convert_log.py` — `convert_log.md`, three line formats (OK /
  OK-with-skips-and-bak-note / FAILED), with an `[AUTO]`-prefix parameter
  ready for Item 16 to use (not exercised yet — no automated trigger exists
  before Item 16).
- `backend/routers/convert.py` (new) — picker (`.bak` exclusion fix applied
  here), `convert_progress` singleton modelled on `scanner.py`'s
  `ScanProgress`, working file list, `POST /run` (background task) /
  `GET /status` polling.
- `frontend/admin.html` / `frontend/js/processingTools.js` — From-format
  radio (CBR/PDF), static "→ CBZ" label, Browse/Run buttons, live progress
  bar, summary modal reusing the shared `showPtSummary()` helper from Item 10.
- **Bug caught and fixed during manual testing** (not by review):
  `filePicker.js`'s `loadPtPickerDirectory()` built its URL as
  `` `${browseUrl}?path=...` `` unconditionally — correct for Rename's plain
  `browseUrl`, but Convert Archives' `browseUrl` already carries its own
  `?from_format=cbr` query string, so the result was a malformed
  double-`?` URL. The browser folded everything after the first `?` into a
  single `from_format` value and dropped `path` entirely, silently falling
  back to the Home directory instead of erroring — easy to miss without
  actually clicking through the picker. Fixed to join with `&` when the base
  URL already has a `?`.

**Verified — manual test, this session, against scratch fixture files (never
`L:\Comic Archives`).** Built real fixtures: a valid CBR (via `Rar.exe`,
already installed — WinRAR trial), a CBR with one entry corrupted by flipping
bytes near the end of the archive (to exercise `pages_skipped`), a 2-page PDF
(built with `fitz` itself), and a `.bak` file to prove the cross-review fix.
Confirmed the picker's CBR and PDF filters both correctly exclude the `.bak`
file. Ran both conversion directions: clean CBR→CBZ and PDF→CBZ each auto-
deleted their `.bak` (net effect: original replaced, no leftover); the
corrupted CBR converted with `pages_skipped=1`, flagged `success_with_
warning`, and kept its `.bak` permanently. Tested the `.bak`-already-exists
guard directly: re-attempting a conversion against a filename whose `.bak`
already existed failed cleanly with "Backup file already exists" before any
conversion work ran, original left completely untouched. Drove the full
picker→working-set→run→summary-modal flow through actual browser clicks
(not just API calls) — this is what caught the malformed-URL bug above,
since the API-level tests alone (hitting `/convert/browse` directly with a
correctly-built URL) wouldn't have exercised the buggy client-side
construction.

**Docs.** `ADMIN_SPEC.md` §11.2 marked built, cross-review fix noted.

**Amendment, same day, found during Item 16's build:** `POST /convert/run`'s
"already in progress" rejection returned `{running: true}` — indistinguishable
from the success response's `{running: true}`, since `running` reflects actual
state either way, not "did your request just start something." The frontend's
`if (res.running === false)` check could never fire, so the rejection toast
silently never displayed. Fixed by adding an explicit `started` field
(`true`/`false`) and updating the frontend to check that instead — same fix
applied to Item 13's `convert-images/run` (identical pattern) and Item 16's
own `processing-folder/run`. Not caught during this session's own testing
because the manual test never actually double-clicked Run while a conversion
was in flight — worth remembering for future background-job endpoints:
"is my request accepted" and "what's the current state" are two different
questions and need two different fields.

---

## Session — 2026-07-01: v2.4 Item 13 — Convert Images

**Goal.** Build WebP image conversion per `ADMIN_SPEC.md` §11.3, reusing
Item 12's `backend/backup_model.py` (the unified backup model is genuinely
shared, not just similar) and the Editor's flatten logic rather than porting
CAPT's separate implementation.

**What changed.**
- `backend/editor/archive_io.py` refactor — extracted `flatten_and_zip
  (extract_dir, target_dir) -> str` (builds a staged zip, doesn't move/replace
  anything) out of `_rebuild_archive()`, which is now a thin wrapper: call
  `flatten_and_zip()`, then `os.replace()` (its existing in-place-rewrite
  behaviour, unchanged for editor callers). This is the shared flatten step
  §11.3.4 calls for — Convert Images calls the same function directly rather
  than carrying a second implementation.
- `backend/image_convert.py` (new) — `convert_images_in_archive(archive_path,
  quality, lossless) -> ConvertImagesResult`, router-independent (Item 16
  target). Extracts via `archive_formats` (CBZ or CBR, content-detected, both
  load into the same working list — no From-format selector, unlike Convert
  Archives). Converts each `{.jpg,.jpeg,.tiff,.gif,.png,.bmp}` entry to WebP
  via Pillow; a per-image failure is skipped (counted, not aborting);
  `ComicInfo.xml`/already-`.webp` entries pass through unchanged. Rebuilds via
  `flatten_and_zip()` — always `.cbz` output, even for a CBR source (CBR is
  never written). Backup/safety via the same `backup_model.py` Item 12 uses.
- `backend/convert_images_log.py` — **line format decided independently of
  the doc sample**, which turned out to be stale (see below).
- `backend/routers/convert_images.py` (new) — picker (content-detected
  CBZ/CBR, `.bak` excluded — this one was already correctly scoped from the
  start, unlike Convert Archives), own `convert_images_progress` singleton
  (separate from Convert Archives'), quality/lossless options, run/status.
- `frontend/admin.html` / `frontend/js/processingTools.js` — Lossless
  checkbox + quality slider (default 95, slider disables when Lossless is
  checked), Run button, progress UI, summary modal.
- **Doc drift caught and fixed, not by review — by writing the log module
  and noticing it contradicted the spec it was implementing.**
  `ADMIN_SPEC.md` §11.3.7's audit-log sample still showed a clean-success
  line as `filename.cbz [OK] (backed up to filename.cbz.bak)` — left over
  from before the Item 15 backup-model unification, when Convert Images'
  original model kept every `.bak` permanently. The unified model auto-
  deletes a clean success's `.bak`, so that sample line was actively wrong.
  Implemented `convert_images_log.py` to match the *correct*, already-
  updated §11.3.5 body text and `convert_log.md`'s (§11.2.6) already-correct
  pattern instead of the stale sample, then fixed the sample itself in the
  same session.

**Verified — manual test, this session, against scratch fixture files (never
`L:\Comic Archives`).** Built a nested-folder CBZ (image entries two levels
deep, mixed jpg/png/gif) to exercise flatten; a CBZ with one entry replaced
by garbage bytes under a `.jpg` name to exercise `images_skipped`; a CBR.
Ran all three in one batch: the nested archive came back flattened
(`ComicInfo.xml`, `page001.webp`, `page002.webp`, `page003.webp`, no
`subfolder/` prefixes) with a clean `[OK]` and no `.bak`; the corrupt-image
archive converted its good image to WebP, left the corrupted one in its
original `.jpg` format untouched, flagged `success_with_warning` with
`images_skipped=1`, and kept its `.bak` permanently; the CBR came back as a
`.cbz` with a clean `[OK]` and no `.bak`. Tested the `.bak`-already-exists
guard directly and via the full picker→run→summary-modal UI flow — failed
cleanly, original untouched, file stayed in the working set for retry.
Confirmed Lossless correctly disables the quality slider in the UI.

**Docs.** `ADMIN_SPEC.md` §11.3 marked built; §11.3.7's stale audit-log
sample corrected to match the unified backup model.

**Amendment, same day, found during Item 16's build:** same `started`-vs-
`running` fix as Item 12's amendment above — `convert-images/run`'s
"already in progress" rejection was indistinguishable from success in the
JSON response, so the frontend's rejection toast could never fire. Fixed
alongside Item 12's and Item 16's.

---

## Session — 2026-07-01: v2.4 Item 16 — Processing Folder Automation

**Goal.** Build the two-stage scheduler/Run Now pipeline per `ADMIN_SPEC.md`
§11.4 — the final item in the CAPT-tooling cluster, depending on Items 11-13
being built first since it invokes their callables directly.

**What changed.**
- `backend/routers/processing_folder.py` (new) — settings (`GET`/`POST
  /processing-folder/config`, the keys listed in §11.4.4/§11.4.5), a
  folder-only picker (shared `file_picker.py`, `mode: 'folder'` on the
  frontend), `processing_folder_progress` singleton (`running`,
  `current_stage`, `stage_results`), and `run_pipeline()` — the actual
  two-stage orchestration, called by both "Run Now" and the scheduler.
  Re-implements the same content-detection + `.bak`-exclusion filtering
  Items 12/13's pickers use (`_convertible_archives()`/`_convertible_images()`)
  as plain filesystem listing, since automation doesn't go through the
  admin UI's HTTP picker endpoints at all. Per-stage exceptions are caught
  and logged without aborting the pipeline — the next enabled stage still
  runs. Saving a new schedule/time/day clears `next_processing_run` so the
  scheduler recomputes it fresh rather than firing against a stale time.
- `backend/scheduler.py` — new `processing_folder_loop()`, wall-clock
  scheduling (differs from `auto_scan_loop`/`backup_loop`'s elapsed-time
  polling): `_compute_next_processing_run()` computes the next daily/weekly
  fire time from the configured day/time, persisted to `config.json` as
  `next_processing_run` so a restart doesn't lose the schedule or fire
  immediately on catch-up. Skips a cycle if a run is already in progress,
  same guard shape as `auto_scan_loop`.
- `backend/main.py` — `processing_folder_loop()` registered as a background
  task in `lifespan`, alongside `auto_scan_loop`/`backup_loop`, with the
  same cancel-on-shutdown handling.
- `frontend/admin.html` / `frontend/js/processingTools.js` — folder picker,
  per-stage enable checkboxes + settings, schedule dropdown (Off/Daily/
  Weekly) + time/day inputs with a Save button, Next Run hint, Run Now
  button, progress label, summary modal.
- **`[AUTO]` tag semantics clarified during manual testing.** Initially
  wired "Run Now" to log as a plain (untagged) run and only the scheduled
  trigger as `[AUTO]` — re-reading §11.4.9 against the actual test output
  showed this was backwards: the tag distinguishes "came through the
  Processing Folder pipeline" (§11.4, either trigger) from "manual run via
  Convert Archives'/Convert Images' own admin-UI tools" (§11.2/§11.3 used
  directly) — not "scheduled vs. clicked." Both `run_pipeline()` call sites
  (Run Now's endpoint and the scheduler loop) now pass `auto=True`.
- **Two more instances of Item 12/13's `started`-vs-`running` bug (see
  those items' amendment notes above), caught here first.** `POST
  /processing-folder/run`'s "already in progress" rejection had the same
  `{running: true}` ambiguity, plus a second related bug in the frontend:
  the "No stages enabled" case is a raised `HTTPException`, which FastAPI
  serializes as `{detail: "..."}`, not the `{message: ...}` shape the
  success/rejection responses use — `postJSON()` doesn't check `res.ok`, so
  that response shape reaches the caller too, and the original check
  (`res.message.includes('No stages')`) could never match a `detail` field.
  Fixed `runPfNow()` to check both `res.started === false` and `res.detail`.

**Verified — manual test, this session, against a scratch processing folder
(never `L:\Comic Archives`).** Built a mixed folder: a CBR (Stage 1 input),
an already-CBZ file (Stage-1-ignored, Stage-2 input), and a leftover `.bak`
(must never be touched by either stage). Ran the full pipeline: confirmed
Stage 1 converted the CBR to CBZ; confirmed Stage 2 picked up **both** the
pre-existing CBZ **and** the CBZ Stage 1 had just produced — this is the
folder-level, not per-file, chaining behaviour §11.4.3 specifies, and it's
the one behaviour that's easy to get wrong (per-file chaining would have
missed Stage 1's output). Confirmed the `.bak` file appeared in neither
stage's results across two separate runs (proving it survives repeated
scheduled-style re-runs, not just one pass). Confirmed `[AUTO]`-tagged lines
in both `convert_log.md` and `convert_images_log.md` after fixing the tag
logic. Unit-tested `_compute_next_processing_run()` directly against six
cases (daily before/after today's slot, weekly before/after this week's
slot including a same-day boundary, and "off") — all correct; did not run
the actual 60-second-poll async loop live end-to-end (would require waiting
through real wall-clock time), relying instead on the same reviewed
polling-loop pattern already proven in `auto_scan_loop`/`backup_loop` plus
the isolated unit test of the one genuinely new piece of logic (the next-run
computation). Tested the already-running guard and the no-stages-enabled
guard through the actual UI, which is what caught both response-shape bugs
above — confirmed via a deterministic stubbed-response test that the fixed
`runPfNow()` correctly shows each toast once the right field is present.

**Docs.** `ADMIN_SPEC.md` §11.4 marked built.

---

## Session — 2026-07-02: File Rename — restore the "Add to Queue" workflow (post-Item 10 manual test fix)

**Goal.** During the v2.4 manual test pass, Item 10 (File Rename) tested
functionally sound but was found to have lost a piece of its intended
workflow somewhere between the original design and the 2026-07-01 build:
there was no way to deliberately add a file to a batch-apply list, and no
way to remove a single file from that list short of clearing it entirely.
Tez confirmed this against the original mockup
(`images/Filename-Editor.pdf`, described in
`images/digib00age/filename-editor-description.txt`): select a file →
parse/edit its fields → **explicitly** add it to a queue → the queue
doubles as the preview → Apply Rename processes everything queued. The
built version instead auto-accumulated into the Preview list on every
keystroke, with no explicit "add" gesture.

**What changed (frontend-only, `frontend/js/processingTools.js` +
`frontend/admin.html` + `frontend/css/style.css`).** No backend changes —
`/rename/preview` and `/rename/apply` already operated on file-id lists
exactly as this needed; only the frontend's timing/orchestration around
those calls changed.

- Removed the auto-preview-on-edit behaviour. Typing into a field or
  toggling File/All now only updates the edit panel's own state.
- New **Add to Queue** button (`addRenameToQueue()`): single-file mode
  (File-checked) queues just the selected file; batch mode (All-checked)
  queues every loaded file in one click, including the existing
  Auto-Increment-across-current-display-order behaviour. Neither box
  checked shows a toast instead of silently no-op'ing.
- Queued Files list (renamed from "Preview") now shows only the resulting
  new filename per row, not `old → new` — the old name is already visible
  at the same row position in Loaded Files, so the pairing is implicit.
- New per-row remove control (`removeFromRenameQueue()`) drops a single
  file back out of the queue without clearing the rest. "Clear Preview"
  keeps its existing whole-queue-wipe behaviour and label (matches the
  original mockup's own labelling).
- `moveRenameFile()` no longer re-triggers a live preview recompute on
  reorder (nothing to recompute anymore) — reordering now happens before
  clicking Add to Queue, which captures the display order at that moment.
- Layout reshaped into the mockup's two-row grouping (toolbar + list +
  edit-panel on top; toolbar + list + batch-options below) using the
  existing `pt-toolbar`/`pt-rename-*` CSS conventions, plus new
  `.pt-rename-row`/`.pt-rename-col-*` wrapper classes and a
  `.pt-remove-btn` style following the existing `.pt-reorder-btn` pattern.
- Fields stay Series/Title/Issue/Year (not the mockup's "Publisher" —
  confirmed with Tez; Year matches the current parser/spec and switching
  would need new backend parsing work, out of scope here).

**Verified — manual test, this session, against scratch files (never the
real library or `L:\Comic Archives`).** Loaded 3 scratch `.cbz` files via
the in-app picker. Single-file flow: selected a file, checked Title→File,
typed a new title, clicked Add to Queue — confirmed it appeared in Queued
Files showing only the new filename, and the matching Loaded Files row
picked up the queued highlight. Confirmed the per-row remove control drops
just that file back out (queue and Loaded Files both update, nothing else
affected). Batch flow: checked Series→All and Issue→All with
Auto-Increment on, clicked Add to Queue once — confirmed all 3 files
queued in one click with correctly sequential issue numbers in display
order. Clicked Apply Rename — got "Renamed 3 of 3 files", confirmed via
filesystem listing that the scratch files were actually renamed on disk,
confirmed `L:\Comic Archives` was never touched (never browsed there this
session). No console errors throughout. Deleted the scratch test files and
an unused `.claude/launch.json` created during testing as cleanup.

**Docs.** `ADMIN_SPEC.md` §11.1.5/§11.1.6 rewritten to describe the queue
workflow; §11.1 status line and `INDEX.md`'s `ADMIN_SPEC.md` row both note
the 2026-07-02 correction; Change Log entry added.

**Same-session follow-up.** Tez asked for two more small changes after
reviewing the queue fix:
- "Clear Loaded Files" renamed to **Clear All**, and its behaviour
  (`clearRenameFiles()`) now also resets the edit panel — all four field
  values and their File/All checkboxes — via a new
  `resetRenameFieldsPanel()`, not just the file/queue lists as before.
- Loaded Files rows gained the same per-file remove control Queued Files
  already had (`removeLoadedRenameFile()`), calling the existing
  `DELETE /rename/files/{file_id}` backend endpoint (previously unused by
  the frontend) to keep the backend's in-memory working set in sync.
  Removing the currently-selected file also resets the edit panel.

Verified live: loaded 2 scratch files, removed one via its row's remove
control (confirmed only that file dropped, count updated), selected the
remaining file, populated fields via parsing plus a manual Title→File
check, clicked Clear All (confirmed loaded files, queue, and all field
values/checkboxes reset to empty). No console errors. Scratch files
deleted after.

**Docs.** `ADMIN_SPEC.md` §11.1.2 gained a Change Log entry and two new
bullets describing Clear All and per-file removal.

---
