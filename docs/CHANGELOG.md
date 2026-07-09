# ComicVault — Changelog

Terse, one-line-per-entry index, newest first. Each line is a pointer into the
matching version's `progress.md` section heading — read there for the full
narrative, what was verified, and any gotchas. Bug fixes already logged in
`BUGS.md` aren't repeated here unless they also got their own `progress.md` session
entry. **Entries dated 2026-06-28 or earlier point into `archive/v2.3/progress.md`**
(progress.md became version-scoped starting with v2.4, archived alongside v2.3's
close) — **entries from 2026-06-29 through 2026-07-02 point into
`archive/v2.4/progress.md`** (v2.4 closed 2026-07-02, folder moved to `archive/`).
**Entries from 2026-07-03 through 2026-07-05 point into
`archive/v2.5/progress.md`** (v2.5 closed 2026-07-05, folder moved to `archive/`).
**Entries from 2026-07-07 onward point into `v2.6/progress.md`** (v2.6 opened
2026-07-06).

---

- **2026-07-09** — First performance-diagnostics baseline (not a build-queue
  item, no code changes): confirmed two hard N+1 findings (`/api/library`
  fires 7,508 queries, `/api/series/{largest}` fires 4,969) and a reader
  page-cache gap (never-read vs re-read pages cost the same) with real
  numbers across in-process, HTTP, and browser tests; cover images never
  honor cache revalidation (0/15 sampled got a 304); USB drive itself tested
  healthy, cold-idle drive effect inconclusive. New standing doc
  `docs/PERFORMANCE.md`.
- **2026-07-09** — Post-redesign UI tweak pass (not a formal build-queue
  item): header login/logout drift fixed on Issue/Series detail (missing
  settings-cog markup); Folder View's breadcrumb replaced with a real "←
  Back" button; Grid/List toggle relocated and "|" separators added
  throughout the menu bar; Publisher filter dropdown removed (stays as a
  Group by option); "Read" button removed from Issue detail
  (`comicvault://` deep link, non-functional outside the Flutter app);
  Series detail Genre tags fixed to be real links (parity with Issue
  detail); Clear Filter pill unified in both look and position across the
  dropdown-filter and fieldview-banner trigger paths; login popup
  compacted with a new Cancel button; Full Editor's "Search Online"
  renamed "Search ComicVine" plus a new "Search GoodReads" link, both
  centred over the XML Editor column; Admin's Last Scan card trimmed to
  date-only. Full detail in `v2.6/progress.md`.
- **2026-07-08** — BUG-015 fixed: fieldview filter (genre tag/writer/artist/
  home-strip links) had no UI way to clear and showed no indication of what
  was filtering it. Genre dropdown "Clear" row (the initial proposal) only
  covered genre; generalized the Series page's existing scoped-view banner
  pattern for fieldview instead, with a real-navigation clear link. Writer/
  artist values resolved to a display name via a new `label=` param plus a
  backend `field_value_label` addition for home-strip links.
- **2026-07-08** — BUG-014 fixed: back-button regression (landed on Home
  instead of the originating tab). Root cause was `switchSurface()` never
  writing to the URL for the four main browse surfaces; extended Folder
  View's already-working `pushState`/`popstate` pattern app-wide. Live
  testing also found Chrome's back/forward cache was randomly masking the
  bug in manual testing, explaining why two prior fixes didn't stick.
- **2026-07-08** — Web UI Redesign Phase E built (v2.6 Item 1): Series/
  Issue detail visual polish — **v2.6 Item 1 is now fully complete.** A
  line-by-line comparison against Design's `SeriesScreen`/`IssueScreen`
  found the scope was much smaller than assumed (issue-row treatment,
  genre tags, credits grid, ratings already matched). Two real gaps
  fixed: `.series-backdrop-img` had `opacity: 1.5` (a bug — clamps to
  full strength, not the intended 0.28 wash) and the Issue detail page
  had no backdrop at all (added a new faint 440px top-fading one).
  Formalized `--blur-backdrop`/`--backdrop-opacity`/`--backdrop-overlay`
  as real tokens. → `v2.6/progress.md` "Phase E built (Series/Issue detail
  visual polish) — v2.6 Item 1 complete (2026-07-08)"
- **2026-07-08** — Web UI Redesign: CoverCard selection circle (v2.6 Item
  1): full Design-vs-implementation scan (`CoverCard.jsx` and other
  remaining components pulled from the Design bundle) found one real gap
  — a hover-reveal selection circle on cover cards, a discoverable
  single-click alternative to the existing long-press-to-select gesture.
  Added to Browse grid + Folder View cards (grid view only); Home strips
  excluded (no selection feature there). Zero changes to the existing
  selection state machine. Everything else checked in the scan (read-state
  colours, badges, progress bar, hover-lift, header, Admin StatCard)
  already matched Design. → `v2.6/progress.md` "Design-vs-implementation
  scan + CoverCard selection circle built (2026-07-08)"
- **2026-07-07** — Web UI Redesign Phase D follow-up fix (v2.6 Item 1): a
  stray horizontal scrollbar was showing on every open dropdown panel
  (`.fd-panel` set `overflow-y` without `overflow-x`, which the CSS spec
  computes to `auto` too) — fixed with `overflow-x: hidden`.
- **2026-07-07** — Web UI Redesign Phase D follow-up (v2.6 Item 1): styled
  the Browse filter bar's *open* dropdown panel (screenshot-driven
  request) — new `frontend/js/filterDropdown.js` layers a themed custom
  panel over each native `<select>`, which stays hidden-but-functional in
  the DOM as the source of truth (zero `app.js` changes). Reverses Phase
  D's original "kept native select" scope call now that the open-menu
  styling was explicitly asked for. → `v2.6/progress.md` "Phase D
  follow-up built (styled open-dropdown panel) (2026-07-07)"
- **2026-07-07** — Web UI Redesign Phase D built (v2.6 Item 1): Browse
  screen filter/sort bar restyled to match the Design reference —
  borderless/minimal controls (`.filter-select`, sort-direction/
  favourites/view-toggle buttons, `Clear`), a divider after Favourites,
  and the view toggle grouped with the title count on the right. Visual
  only, every field/control unchanged; kept native `<select>` dropdowns
  rather than rebuilding Design's custom popup-listbox component. →
  `v2.6/progress.md` "Phase D built (Browse filter/sort bar restyle)
  (2026-07-07)"
- **2026-07-07** — Web UI Redesign Phase C2c follow-up (v2.6 Item 1): moved
  the "Unlock advanced settings" checkbox out of its own row into the
  Advanced Settings sub-item nav row as a compact "Unlock" control, per
  Tez's request right after C2b shipped. → `v2.6/progress.md` "Follow-up —
  Phase C2c" (under the Phase C2b session entry)
- **2026-07-07** — Web UI Redesign Phase C2b built (v2.6 Item 1): Admin page
  IA restructure completed with the last category, **Processing Tools**
  (Filename Editor, Converter: Archives & Images, new standalone **XML
  Tagging** tool, Folder Processing, Auto Processing). Real backend work:
  new `backend/routers/xml_tagging.py`; `ct_autotag_log.py`'s
  `append_entry()` gained an `auto` param (was automation-only); Match
  Ratio Threshold/Save on Low Confidence/ComicVine API Key moved out of
  Auto Processing's pane into XML Tagging's (same shared config/endpoints,
  not duplicated). Every existing element ID preserved. Verified with a
  real functional round-trip against synthetic scratch data. → `v2.6/
  progress.md` "Phase C2b built (Admin IA restructure, part 3 — Processing
  Tools, final category) (2026-07-07)"
- **2026-07-07** — Web UI Redesign Phase C2a built (v2.6 Item 1): Admin page
  IA restructure extended to **Editor Options** (Genre List, Format List —
  unlocked, same treatment as Phase C1's Home Strips/Libraries) and
  **Advanced Settings** (Password Protection, Change Server Port + Reader
  Location, Wipe Database, Wipe Reading State — split out of the old single
  "Danger Zone" subsection into two sub-items, all four still behind the
  "Unlock advanced settings" gate). Every existing element ID preserved;
  `admin.js` only extended `ADMIN_CATEGORIES` with 2 new entries — no other
  logic changed. Processing Tools stays old-style, moved to its own Phase
  C2b (needs backend work for a new standalone XML Tagging tool). → `v2.6/
  progress.md` "Phase C2a built (Admin IA restructure, part 2) (2026-07-07)"
- **2026-07-07** — Web UI Redesign Phase C1 built (v2.6 Item 1): Admin page
  restructured from one long scrolling page into a category → sub-item →
  content-pane nav, for **Library Management** and **Library Appearance**
  (10 sub-items) — the two categories Design actually built content for.
  Every existing element ID preserved; only new additive `bindAdminNav()`
  wiring, no existing `admin.js`/`processingTools.js`/`filePicker.js`
  function touched. Home Page Strips and Add/Remove Libraries moved out
  from behind the "Unlock advanced settings" gate (decided, see
  `DECISIONS.md`). Processing Tools/Editor Options/Advanced Settings stay
  in their old always-visible form until Phase C2. → `v2.6/progress.md`
  "Phase C1 built (Admin IA restructure, part 1) (2026-07-07)"
- **2026-07-07** — Web UI Redesign Phase B built (v2.6 Item 1): top
  `.surface-nav` tab bar and the header's status-pills row replaced with a
  collapsible left sidebar (Home/All/Singles/Series, Unread/Reading/Read
  shortcuts, dynamic Libraries section), added to all three real pages
  (index/series/issue). Read-status filtering is now a global "jump to
  All, filtered" sidebar shortcut, not a per-surface toggle — a deliberate
  behaviour narrowing matching the approved design, documented in
  `MENU_BAR_SPEC.md`/`CUSTOM_TABS_SPEC.md`. Phase C (Admin IA restructure)
  and D (Series/Issue visual polish) queued next. → `v2.6/progress.md` "Web
  UI Redesign Phase B built (2026-07-07)"
- **2026-07-07** — Web UI Redesign Phase A built (v2.6 Item 1, Design→Code
  handoff from the `digib00age` Claude Design project): design-token palette
  (colour/typography/spacing/elevation) merged into `style.css` site-wide, and
  a visible brand rename to **digib00age** (header logo, page titles, favicon)
  — internal/codebase name stays ComicVault. No structural or nav changes yet;
  Phases B (left sidebar nav), C (Admin IA restructure), and D (Series/Issue
  visual polish) are queued next. → `v2.6/progress.md` "Web UI Redesign Phase A
  built (2026-07-07)"

- **2026-07-05** — Mobile ↔ Server Reading-State Sync built (v2.5 Item 3):
  reading progress made offline on the tablet now persists back to the
  ComicVault DB. New `GET /api/issue/{id}/download` and `POST /api/sync/progress`
  (last-write-wins by timestamp, no schema change) on the backend; a new
  download-for-offline feature, `SyncStore`/`SyncService`, and sync-trigger/
  status UI on the Flutter side — including a download feature that wasn't
  in the original scope doc but turned out to be a hard prerequisite. A
  timezone-skew bug in the conflict comparison was caught during plan review,
  before reaching a device. Tez confirmed "signed off, passed" on the real
  tablet; one planned check (visually confirming the `server_kept` outcome)
  was blocked by a separate, pre-existing gap — no working reader exists
  outside the Flutter app right now (`BUGS.md` BUG-021, logged not fixed
  here). → `v2.5/progress.md` "Mobile ↔ Server Reading-State Sync built —
  v2.5 Item 3 (2026-07-05)"
- **2026-07-05** — New Processing Tool built: Sort by Filename (`ADMIN_SPEC.md`
  §11.5, v2.5 Item 2). Moves each CBZ/CBR file directly inside a chosen folder
  into its own same-named subfolder, ported from the standalone
  `create-folders-from-file.py` script. A collision-rule gap (an unrelated file
  already sitting in the target folder wasn't being caught) was found via
  scratch testing and fixed before the manual pass — see `DECISIONS.md`. Tez
  confirmed "test passed" via the live Admin UI. → `progress.md` "Sort by
  Filename Processing Tool built — v2.5 Item 2 (2026-07-05)"
- **2026-07-05** — BUG-017 fixed and verified on-device: Android had no file
  association for `.cbz` — tapping one in a file manager never offered
  ComicVault under "Open With". Added Android intent-filters for `.cbz`
  (scoped to `.cbz` only — the app has no RAR decoder, so `.cbr` stays
  unassociated), plus a fix for a second bug found during testing: Flutter's
  default `FlutterActivity` behavior was auto-consuming the incoming intent
  as a bogus route push before the app's own handling ever ran, crashing
  with "Could not find a generator for route" (fixed via
  `shouldHandleDeeplinking() = false`). Verified extensively via `adb`
  (manifest resolution, crash-free intent handling) and finally confirmed by
  Tez tapping a real `.cbz` on the tablet — ComicVault appeared under Open
  With and opened it correctly. → `v2.5/progress.md` "Session — 2026-07-05
  (BUG-017 fix — Android .cbz file association)"
- **2026-07-04** — BUG-008 fixed: removed the Flutter app's broken 2000 AD
  tab entirely (Tez's call — not worth building a Custom Tabs equivalent for
  Flutter just to replace it). Deleted `two_thousand_ad_screen.dart`, dropped
  the tab from `library_screen.dart` (4 tabs → 3), removed the dead
  `get2000adYears()`/`get2000adYear()` API calls. 2000 AD issues themselves
  are unaffected — still browsable via Series/Singles/All like any other
  publisher. Verified on Tez's tablet. This closes the last open item from
  the 2026-07-04 mobile-bugs report. → `v2.5/progress.md` "Session —
  2026-07-04 (BUG-008 fix — 2000 AD tab removed)"
- **2026-07-04** — BUG-020 fixed and verified on-device (release build):
  Flutter app crashed when selecting a large local CBZ. Two causes — an
  OOM crash picking any file over ~250MB (replaced `file_selector` with a
  native streaming picker), and a silent MIME-type mismatch that made some
  `.cbz` files unselectable (picker now accepts any file type). A follow-on
  memory issue surfaced once those were fixed (archive re-decoded per page,
  all pages eagerly loaded, full-resolution image decode) — fixed with
  archive caching, lazy per-page reads, and resolution-capped decoding.
  Confirmed stable on Tez's tablet in a release build; debug builds still
  show heavier memory use on very large files. → `v2.5/progress.md`
  "Session — 2026-07-04 (BUG-020 diagnosis and fix)"
- **2026-07-04** — BUG-019 fixed and verified on-device: Flutter app couldn't
  connect to the server. Two stacked causes — `checkConnection()` was hitting
  an admin-only route that 403s over LAN by design (fixed with a new
  unauthenticated `GET /api/ping`), and separately the tablet's saved server
  URL had a stale port. Confirmed working on the real Lenovo tablet after
  both fixes. → `v2.5/progress.md` "Session — 2026-07-04 (BUG-019 on-device
  verification)"
- **2026-07-04** — v2.5 Item 1 closed: added a configurable Match Ratio
  Threshold slider (10–100%, default 80) to Processing Folder Automation's
  CT Auto-Tag stage, replacing the previous hardcoded 80% value. Every
  auto-save control in that section now shows a brief "Saved" toast. Fixed
  a misleading-results bug caught during Tez's deferred low-confidence
  real-world test (a 5-file comparison against his standalone ComicTagger)
  — the run-complete summary counted legitimate no-match/skipped outcomes
  as "succeeded", reporting "5 of 5" when only 4 were actually tagged; the
  underlying audit log was accurate throughout. Item 1's one remaining open
  question (low-confidence/real-world match testing) is done — item
  closed, `meta/roadmap.html` Now #1 card removed. → `v2.5/progress.md`
  "Session — 2026-07-04 (close-of-session)"
- **2026-07-04** — v2.5 Item 1: ComicTagger + ComicVine integration built and
  manually verified — Full Editor's Search Online (two-step Select Series/
  Select Issue modal, `NeedsReview` indicator) and Processing Folder
  Automation's new CT Auto-Tag stage. Three real bugs found and fixed
  during Tez's own live testing: `identify_file()` now falls back to
  filename parsing and assumes issue 1 for one-shots when an archive has
  no embedded XML (was silently short-circuiting to `no_match`); match
  thresholds lowered to 80%; the tagging write path now does a follow-up
  full-issue fetch so credits (Writer/Penciller/Inker/etc.) actually land,
  and the field mapping was expanded to capture everything CT/ComicVine
  supplies (mirroring `comicapi/tags/comicrack.py`'s own write mapping)
  rather than just the fields the editor UI exposes — including fixing raw
  HTML leaking into `Summary` instead of clean text. Low-confidence-match
  testing explicitly deferred to Tez (sourcing sample material himself),
  not blocking this item's close-out. → `v2.5/progress.md` "Session —
  2026-07-03/04: v2.5 Item 1 — ComicTagger + ComicVine integration"

- **2026-07-02** — BUG-018 fixed (off-cycle, after v2.4's close — never tied
  to a numbered version item). Scanner's `_parse_cbz()` now finds
  `ComicInfo.xml` at any folder depth in an archive, not just the root, by
  reusing the same `find_xml_in_archive()`/`extract_xml_from_archive()`
  helpers the Basic/Full Editors already used. Verified unit-level (nested/
  root/no-xml scratch archives), end-to-end via `scan_single_file()` against
  a temporary DB row, and live in the UI + Basic Editor — all cleaned up
  after. `SPEC.md` §6 corrected. → `archive/bugs-fixed-archive.md` BUG-018
- **2026-07-02** — v2.4 closed. All 16 items resolved: Items 1–7, 9–13, 15–16
  built and manually verified; Items 8/14 (Flatten Archive) dropped, superseded
  by BUG-018 (fixed same day, off-cycle — see above; did not block this
  close-out). Two post-test fixes landed the same day as close-out: File
  Rename's "Add to Queue" workflow and an Auto-Increment field-wiping bug
  (both below), and a Processing Folder Automation scheduler investigation
  that found no bug (see below). `docs/v2.4/` moved to `docs/archive/v2.4/`
  as one bundle; tagged `v2.4` locally. `meta/roadmap.html`'s Now lane
  updated with the first three v2.5 holding-list items. →
  `archive/v2.4/progress.md`
- **2026-07-02** — Processing Folder Automation: investigated a report
  that scheduled runs weren't firing. No bug found — live-reproduced the
  wall-clock scheduler firing correctly (Daily, Weekly, and via the real
  admin UI). Root cause was the Schedule dropdown being left on "Off"
  while Day/Time were changed and saved — that row is the one setting on
  the page that doesn't auto-save, unlike everything else. Logged as a
  `[change]` candidate in `INBOX.md`, not fixed this session. → `progress.md`
  "Session — 2026-07-02: Processing Folder Automation — scheduler
  investigation (Item 16 post-test)"
- **2026-07-02** — File Rename: restored the "Add to Queue" workflow lost
  in the 2026-07-01 build — explicit Add to Queue button (single-file or
  batch), Queued Files list doubles as the preview (new-filename-only),
  per-file queue removal. Same-session follow-ups: "Clear Loaded Files"
  renamed **Clear All** and now also resets the edit panel's fields,
  Loaded Files rows gained a per-file remove control, and a bug fix where
  enabling Auto-Increment wiped Series/Title/Year from every queued file
  (backend's shared-batch-call preview endpoint has no per-file baseline
  fallback — fixed by routing Auto-Increment through the same per-file
  resolution the rest of batch mode already used). Frontend-only fix,
  found during post-build manual testing against the original mockup and
  real (non-library) test files. → `progress.md` "Session — 2026-07-02:
  File Rename — restore the 'Add to Queue' workflow"
- **2026-07-01** — v2.4 Item 16: Processing Folder Automation built — closes
  out the CAPT-tooling cluster. Two-stage scheduled/on-demand pipeline
  (Convert Archives → Convert Images, fixed order) invoking Items 12/13's
  callables directly, wall-clock scheduler (daily/weekly), `[AUTO]`-tagged
  audit-log lines. Manual test confirmed folder-level chaining (Stage 2
  picks up Stage 1's freshly-produced output, not just pre-existing files)
  and that leftover `.bak` files are never reprocessed across repeated runs.
  Found and fixed a response-shape bug affecting "already running"
  rejections on all three Processing Tools run endpoints (Items 12, 13, 16)
  — the rejection was indistinguishable from success in the JSON response,
  so the UI's rejection toast could never actually display. → `progress.md`
  "Session — 2026-07-01: v2.4 Item 16 — Processing Folder Automation"
- **2026-07-01** — v2.4 Item 13: Convert Images built — WebP conversion for
  CBZ/CBR (CBR always rebuilds as CBZ), reusing the Editor's flatten logic
  and Item 12's unified backup model (`backend/backup_model.py`). Caught and
  fixed a stale doc sample: `ADMIN_SPEC.md` §11.3.7's audit-log example
  still showed the pre-unification "always backed up" wording. Manual test
  passed. → `progress.md` "Session — 2026-07-01: v2.4 Item 13 — Convert
  Images"
- **2026-07-01** — v2.4 Item 12: Convert Archives built — CBR→CBZ and
  PDF→CBZ, background job + live progress, unified backup model
  (`backend/backup_model.py`, shared with Item 13). Cross-review fix folded
  in: the picker now excludes `*.bak` files, matching Convert Images. Caught
  and fixed a real bug during UI testing (picker URL construction broke when
  the browse endpoint already had its own query string). Manual test passed.
  → `progress.md` "Session — 2026-07-01: v2.4 Item 12 — Convert Archives"
- **2026-07-01** — v2.4 Item 11: native CBR support built — scanner, reader,
  Basic Editor, and Full Editor all read/scan/thumbnail/serve `.cbr` files;
  editing a CBR rebuilds it as `.cbz` on save (original deleted only after
  the rebuild is confirmed written, guarded against clobbering an existing
  sibling `.cbz`), same rule across all three editing surfaces. New shared
  `backend/archive_formats.py` dispatch, new `Issue.container_format`
  column. Manual test passed (including a caught-and-fixed missing-`flush()`
  bug that would've duplicated the DB row on a CBR→CBZ save). → `progress.md`
  "Session — 2026-07-01: v2.4 Item 11 — native CBR support (build)"
- **2026-07-01** — v2.4 Item 10: File Rename Tool built (batch/single-file
  renaming based on parsed Series/Issue/Title/Year, no undo). Three parser
  bugs fixed (stale year ceiling, zero-issue stripping, whitespace/dash
  artifacts). Built the shared Processing Tools picker/log infrastructure
  reused by Items 12/13/16. `admin-spec-section-12-processing-tools.md`
  folded into `ADMIN_SPEC.md` §11, standalone file retired. Manual test
  passed. → `progress.md` "Session — 2026-07-01: v2.4 Item 10 — File Rename
  Tool"
- **2026-07-01** — v2.4 Item 9: Favourites as a library-wide Custom Tab
  category, plus bundled BUG-017 fix (All-tab Favourites filter now correctly
  aggregates across a whole series, not just its #1 issue). Manual test
  passed. → `progress.md` "Session — 2026-07-01: v2.4 Item 9 — Favourites as a
  Custom Tab category"
- **2026-06-29** — v2.4 Item 3: empty-results 📚 icon replaced with the
  ComicVault logo image; extended (Tez's call, beyond original item scope) to
  all 10 other emoji-based empty/error states in `app.js` for consistency.
  Manual test passed. → `progress.md` "Session — 2026-06-29: v2.4 Item 3 —
  empty-results icon → logo image"
- **2026-06-29** — v2.4 Item 2: default server port changed from 8000 to 9424,
  resolving the Windows port-exclusion conflict (BUG-004) at the source.
  Surfaced a separate operational gotcha: stopping the server from the tray
  menu doesn't kill the process — fully quit/relaunch the tray app after a
  port change. Manual test passed. → `progress.md` "Session — 2026-06-29: v2.4
  Item 2 — default server port → 9424"
- **2026-06-29** — v2.4 Item 1: Admin — remote requests are now blocked from
  every `/api/admin/*`/`/api/editor/*` endpoint and the `/admin`/`/editor`
  pages whenever Remote Administration is off, including the previously-open
  default state (password protection off). Cog icon stays visible but inert
  for a blocked remote session. Manual test passed. → `progress.md` "Session —
  2026-06-29: v2.4 Item 1 — restrict all admin access for remote users when
  Remote Administration is off"
- **2026-06-28** — Manual test pass v2.3 Items 10–13: Items 10 (Password Recovery), 11 (Backup frequency), 13 (Card Size 75%) passed; Item 12 (Restore Database) failed — BUG-016 logged. → `progress.md` "Session — 2026-06-28: Manual test pass, v2.3 Items 10–13"
- **2026-06-27** — v2.3 Item 13: Admin Card Size — added a 75% option between
  50% and 100%.
- **2026-06-27** — v2.3 Item 12: Admin Restore Database — renamed "Scheduled
  Backup" section to "Database Backup", split into Scheduled Backup / Restore
  Backup subsections, added a native file-picker restore flow with a
  pre-restore safety snapshot and full server restart.
- **2026-06-27** — v2.3 Item 11: Admin Scheduled Backup — trimmed the frequency
  dropdown from ~20 entries down to 6 (Off/day/week/month/6 months/1 year).
- **2026-06-27** — v2.3 Item 10: Admin Password Recovery — added a "Forgot
  Password?" button/popup to the Admin Top Action Row with manual `config.json`
  recovery steps.
- **2026-06-27** — Fixed folder-view card sizing/image-fit mismatch vs standard
  cards (`.folder-card.has-cover` aspect-ratio bug). Fixed BUG-003 (removed dead
  duplicate `GET /api/reading/continue` route in `progress.py`).
- **2026-06-26** — v2.3 post-test fix pass (`docs/2.3-fixes.md`, Fixes 1–9, plus
  two additional steps raised mid-session). Menu bar: collapsed the unintended
  second row into one (status pills moved to the header, secondary filters +
  count merged into the menu-bar row), fixed a CSS shorthand bug that broke
  edge alignment with the header/card grid, widened the search bar, and — per
  Tez's mid-session request — extended secondary filters and the full menu row
  to Folder View (previously Flat-View-only). Multi-select: favourite toggle
  now actually toggles (was add-only), added a rating-clear button (was
  invisible due to a colour-matches-background bug, also fixed). Full Editor:
  Process All errors now open a dismissible modal instead of an unbounded
  inline wall of text. Auth: login popup no longer fires on the unprotected
  library page, the auth button is now always visible with a Login/Logout
  label, disabling password protection requires re-entering the current
  password, and clicking Login with no password set shows an explanation
  dialog instead of a doomed-to-fail form. Admin: Last Scan persists across
  server restarts, the changed-files log now distinguishes metadata-only vs.
  archive(page-count) changes, and a new Last Backup indicator + scheduler
  failure surfacing was added to the Scheduled Backup block. See
  `docs/progress.md` for the full build narrative.

- **2026-06-24** — v2.3 Item 9 (final v2.3 item): Admin destructive actions +
  Donate placeholder. New "Danger Zone" in Advanced Settings — Clear Database
  (wipes issues/genres/credits/reading progress + orphaned People rows, leaves
  Custom Tabs/Home Strips intact) and Clear Reading Progress, both gated
  local-only and confirm()-gated like the existing Delete Tab flow. New
  Donate button + "Coming soon" placeholder modal in the top action row. The
  Full Editor admin cog-link (also part of this item per spec) was already
  built in the Item 6 session. See `docs/progress.md` for the full build
  narrative.

- **2026-06-24** — v2.3 Item 8: Admin scheduled database backup + server
  listening port. New Scheduled Backup section (native OS folder dialog for
  the destination — not the existing library-scoped picker, which can't
  reach paths outside the library — + a 22-option frequency dropdown); the
  existing manual Backup Database button now uses the same destination once
  set. New Server Listening Port field in Advanced Settings — saving
  confirms, then restarts the server (self-exit, relying on the tray app's
  existing crash-recovery to relaunch on the new port). See
  `docs/progress.md` for the full build narrative.

- **2026-06-24** — v2.3 Item 7: Admin scan log cards + Logs area + Auto Scan
  Options. Each of the 4 scan stat cards (Last Scanned, New Files, Changed
  Files, Missing Records) now has a persistent on-disk log in `/logs/`, a
  "Logs" button to view it, and a green-border indicator for unviewed entries.
  New Logs section (folder path display + log size limit) and Auto Scan
  Options (frequency dropdown + scan-on-launch) under Library Scan. Resolved
  the spec's open "what counts as changed" TODO by reading `scanner.py`
  directly — see `DECISIONS.md` and `BUGS.md` BUG-013 for a confirmed
  pre-existing detection gap (size-only changes with an unchanged mtime).
  See `docs/progress.md` for the full build narrative.

- **2026-06-24** — v2.3 Item 6: Admin password protection + Remote Administration
  toggle. Single shared password gates `/admin`, `/editor`, the Basic Editor popup,
  and all `/api/admin/*` + `/api/editor/*` endpoints (off by default, no behaviour
  change until enabled). Stateless signed-cookie sessions, in-memory brute-force
  lockout, local-only enforcement on enable/disable/password-change/remote-toggle.
  See `docs/progress.md` for the full build narrative.

- **2026-06-23** — Full Editor Process All gained a per-field "Apply to: All"
  checkbox (default unchecked) — only checked fields bulk-apply across every
  loaded file; unchecked fields keep each file's own value. Issue Number has
  no checkbox (governed by the existing Increment # mechanism only). Backend
  validation fix alongside it: enforced-field checks (Genre/Format/AgeRating)
  now validate each file's *effective* merged result, not just the partial
  checked-fields payload. See `EDITOR_SPEC.md` §5.2 and v2.3 build plan Item 5.
- **2026-06-23** — Multi-select scope expanded to Series-aggregate cards:
  long-press-selecting a series card now expands to every issue in that
  series server-side before a bulk Read/Unread/Favorite/Rate action runs,
  same meaning as the existing "Mark all read" series-detail button. See
  `SPEC.md` §20.15 and v2.3 build plan Item 4.
- **2026-06-23** — Card behaviour additions shipped: larger favourite-star
  badge with a black border, a thin gold border on favourited cards
  (coexisting with the existing read-state colours), a wider issue-page star
  rating row, and a new light/dark theme system (auto-matches Windows, with
  a manual override in Admin → Appearance). See `SPEC.md` §20.17 and v2.3
  build plan Item 3.
- **2026-06-23** — Unified menu bar (sort dropdown + asc/desc toggle, star
  rating filter, favourites filter, shared grid/list toggle) shipped across
  Flat View and Folder View, replacing the old three-state sort-cycle button.
  Folder View gained full parity — sort/filter now apply there too, including
  a new recursive "any descendant favourited" flag on folder cards. See
  `MENU_BAR_SPEC.md` and v2.3 build plan Item 2.
- **2026-06-23** — Folder View folder cards now show a representative cover
  image: one randomly-selected cached thumbnail from any issue recursively
  under that folder, re-rolled on every request. No new pipeline — reuses
  the existing per-issue thumbnail cache. See `CUSTOM_TABS_SPEC.md` §9.2.
- **2026-06-22** — v2.2 shipped: 2000 AD's hardcoded fixed-tab surface fully
  removed (endpoints, nav button, year-grid UI, all code paths); Custom Tabs
  gained a `view_mode` (`flat`/`folder`) — Folder View generalises 2000 AD's
  old year-grid into a reusable per-tab mode with recursive folder/file
  browsing, real history-backed navigation, depth-agnostic search, and
  recursive Mark All Read. 2000 AD itself becomes an ordinary Folder View
  custom tab post-build. `CUSTOM_TABS_SPEC.md` amended (§9); both
  `comicvault-changes-2.1.md` and `comicvault-changes-v2.2.md` backlogs now
  closed. → `progress.md` "Session — 2026-06-22: v2.2 — Folder View + 2000 AD
  removal"
- **2026-06-22** — Both Tier 3 items done: Home page search bar (copy unified
  with the browse tabs — "Search All"/"Search Singles"/"Search Series"); card
  size control (10%/25%/50%/100%), then reworked into Admin → Pagination and
  extended to Home strips and the 2000 AD year picker (both had been missed
  initially and stayed hardcoded). **`comicvault-changes-2.1.md` backlog now
  fully closed** (renamed from `comicvault-changes.md`). →
  `progress.md` "Session — 2026-06-22: Tier 3 — search bar + card size (+ rework)"
- **2026-06-22** — All 9 Tier 2 ride-along items done: clickable genre tags
  on `/issue/{id}`, restyled "Clear" filter button, Format added to Grouping
  menu, "Mark all read" on 2000 AD Year page, pagination 25 option, Admin
  "Save Advanced Settings" renamed to "Save Location" and moved onto the
  path's row, Scan Now / Clean Up card border states, and an `.admin-main`
  padding shorthand bug fixed (was overhanging the header by 20px each
  side). → `progress.md` "Session — 2026-06-22: Tier 2 — full batch"
- **2026-06-22** — Tier 1 bug fix: All tab, list view — read/part-read cards'
  list-only fields (`.list-genres`, `.list-pub-writer`, `.list-summary`) stayed
  dim grey instead of picking up the white-text override grid view's
  `.cover-title`/`.cover-count`/`.cover-year` already had for those states.
  Added to the same override block. → `progress.md` "Session — 2026-06-22:
  Tier 1 — List view read-state text colour"
- **2026-06-22** — Tier 1 bug fix, second correction: the 2000 AD Years page's
  "All Years" button had the same labeling inconsistency, missed by a silent
  (unflagged) scoping judgment during the prior fix. Label changed to "Back";
  click behavior intentionally left as its existing in-page toggle, not real
  history, since year selection never pushes a history entry. → `progress.md`
  "Session — 2026-06-22: Tier 1 — Back button inconsistency (2000 AD Years
  page)"
- **2026-06-22** — Tier 1 bug fix, corrected: the 2026-06-21 Admin-only fix
  below was incomplete — Issue and Series detail pages had the same guessed-
  destination problem, missed because the prior session was terminated by an
  error before it got there. All three back links now use real
  `history.back()` with a plain "Back" label. → `progress.md` "Session —
  2026-06-22: Tier 1 — Back button inconsistency (full fix)"
- **2026-06-21** — Tier 1 bug fix: Admin's Back link now uses real browser
  history (`history.back()`) with a label derived from where the user came
  from, instead of a hardcoded link to `/`. → `progress.md` "Session —
  2026-06-21: Tier 1 — Back button inconsistency (fix)"
- **2026-06-21** — Tier 4 Item 3 (Session C, frontend): clickable Writer/Artist
  credit links on `/issue/{id}`, dropdowns removed, editor fuzzy warn-on-save.
  Tier 4 Item 3 now fully complete. An incident during testing modified a real
  CBZ's metadata; fully restored and verified, full account + a newly-found
  unrelated bug (BUG-007) in `progress.md`/`BUGS.md`. → `progress.md` "Session —
  2026-06-21: Tier 4 Item 3 — Session C"
- **2026-06-21** — Tier 4 Item 3 (backend + real migration): Writer/Artist entity
  dedup — new `people`/`issue_credits` tables, scanner integration, candidate-
  duplicate detection (76 pairs, 35 confirmed merges), real migration run against
  the live library. Frontend click-through UI deferred to a later session. →
  `progress.md` "Session — 2026-06-21: Tier 4 Item 3"
- **2026-06-21** — Tier 4 Item 2: Multi-select + Favorites/Rating built (long-press
  card selection, bulk Read/Unread/Favorite/Rate toolbar, new `favorites`/
  `personal_rating` Issue fields, standalone favorite/rating controls on the issue
  detail page). → `progress.md` "Session — 2026-06-21: Tier 4 Item 2 — Multi-select +
  Favorites/Rating"
- **2026-06-20** — Tier 4 Item 1: Genre/Format admin editor built (Format reversed
  from locked constant to admin-editable list; both Genre and Format got add/remove
  UI in Admin, neither had one before). → `progress.md` "Session — 2026-06-20: Tier 4
  Item 1 — Genre/Format admin editor"
- **2026-06-19** — BUG-004 investigated: server failed to bind port 8000 after an OS
  restart (Windows/WSL2 port-exclusion conflict, not a code defect). → `progress.md`
  "Session — 2026-06-19: BUG-004, server failed to start after OS restart"
- **2026-06-19** — Tray app menu redesign: split Stop/Start, added Close, dark-mode
  menu, self-service login-autostart toggle. → `progress.md` "V2.1 — Tray App Menu
  Redesign (2026-06-19)"
- **2026-06-19** — Home Strips built (`HOME_STRIPS_SPEC.md`). → `progress.md` "V2.1 —
  Home Strips Built (2026-06-19)"
- **2026-06-19** — Custom Tabs built (`CUSTOM_TABS_SPEC.md`). → `progress.md` "V2.1 —
  Custom Tabs Built (2026-06-19)"
- **2026-06-18** — Full/Basic Editor UI polish pass. → `progress.md` "V2 — Full Editor
  / Basic Editor UI Polish (2026-06-18)"
- **2026-06-18** — Startup failure found and fixed. → `progress.md` "V2 — Startup
  Failure Found and Fixed (2026-06-18)"
- **2026-06-18** — First manual test pass fixes, incl. BUG-002 (Full Editor Queue
  button gating). → `progress.md` "V2 — First Manual Test Pass Fixes (2026-06-18)"
- **2026-06-18** — Full Editor built (batch pre-library tagging). → `progress.md` "V2
  — Full Editor Built (2026-06-18)"
- **2026-06-18** — Basic Editor built (single-issue popup editor). → `progress.md` "V2
  — Basic Editor Built (2026-06-18)"
- **2026-06-18** — Pre-migration data-hygiene report built. → `progress.md` "V2 —
  Pre-Migration Data-Hygiene Report Built (2026-06-18)"
- **2026-06-18** — Editor genres endpoint built. → `progress.md` "V2 — Editor Genres
  Endpoint Built (2026-06-18)"
- **2026-06-18** — Editor core built (shared XML read/merge/write logic, ported from
  CAPT). → `progress.md` "V2 — Editor Core Built (2026-06-18)"
- **2026-06-18** — V2 migration setup complete (repo cloned from V1, BUG-001 scanner
  thumbnail fix applied). → `progress.md` "V2 — Migration Setup Complete (2026-06-18)"
- **2026-06-17** — V1 build and testing complete. → `progress.md` "V1 — Build and
  Testing Complete (2026-06-17)"
- **2026-06-12** — Phase 6: Tray app + Admin page complete. → `progress.md` "Phase 6 —
  Tray App + Admin (Complete)"
- **2026-06-12** — Phases 1–5: Scanner/DB, REST API, Web UI, Issue Detail page, Flutter
  app — V1 core complete. → `progress.md` Phases 1–5
