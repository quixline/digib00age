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

- **2026-07-28** — Favourite badge polish (border removed, heart nudged
  1px) and a proper Android Adaptive Icon (was a flat legacy icon, which is
  why it looked small next to Settings/Clock) — built and pushed to the
  Lenovo tablet, confirmed on-device. → `v2.6/progress.md` "Favourite badge
  polish, Android adaptive launcher icon"
- **2026-07-28** — `flutter-ui-sync-plan.md` closed out (archived); fixed two
  Flutter reading-progress bugs found during review: list-view read overlay
  not dropped like grid's, and Singles progress % stuck at 0/100 (now uses
  page-level progress like the web does). → `v2.6/progress.md`
  "flutter-ui-sync-plan.md closed out; two Flutter reading-progress bugs
  fixed"
- **2026-07-28** — BUG-032 fixed: page routes/`/static` send `Cache-Control:
  no-cache`, and `frontend/sw.js` switched page navigations to network-first
  (the actual cause of the stale-page symptom). New `browser-verify` skill.
  → `v2.6/progress.md` "BUG-032 fixed (stale pages after edits); new
  `browser-verify` skill"
- **2026-07-26** — Scanner batches `db.commit()` every 50 files instead of
  once per file (`backend/scanner.py`); per-file callers (editor rescans,
  `POST /api/scan/file`) unchanged. → `v2.6/progress.md` "Scanner
  commit-batching fix + CT issue-list slowness diagnosed"
- **2026-07-26** — User guide project kicked off: built `discovery`/`ux-copy`/
  `design-critique` skills, corrected `docs/user-guide-plan.md` to match the
  existing `/guide` route, produced `docs/guide-inventory.md` and
  `docs/tooltip-data.md` (Stages 1-2). No app behaviour changed.
- **2026-07-26** — User guide Stage 3: added `/guide/library`, `/guide/admin`,
  `/guide/editor`, `/guide/editor-basic`, `/guide/editor-full` routes and shell
  HTML pages, plus `frontend/css/guide.css`. Placeholder content only — Stage 4-6
  write the actual guide text.
- **2026-07-26** — User guide Stages 4-6: wrote full content for all guide pages
  (Library, Admin, Basic/Full Editor, plus the Overview index). Guide is now
  content-complete; tooltip wiring (Stage 7) and final review (Stage 8) remain.
- **2026-07-26** — User guide Stages 7-8, project closed out: built a vanilla-JS
  tooltip system (`frontend/js/tooltip.js` + `.db-tooltip` CSS) and wired
  `data-tooltip` across the whole app per `docs/tooltip-data.md`; fixed two
  real content bugs found along the way (Folder View's guide text described a
  Back/Mark-all-read row removed from the app 2026-07-17; Full Editor's guide
  was missing the fuzzy-credit-match dialog and the double-click-to-confirm
  ComicVine search gesture). All 9 plan stages done — see `v2.6/progress.md`.

- **2026-07-25** — `start.bat` launches the tray app detached (`start ""`)
  so its cmd host window closes itself immediately instead of staying open
  for the app's whole runtime. → `progress.md` "Tray App: Open Pages in
  App-Mode Window Instead of Browser Tab" (same session)
- **2026-07-25** — Tray app opens Library/Admin/Editor in an Edge/Chrome
  app-mode window instead of a regular browser tab. → `progress.md` "Tray
  App: Open Pages in App-Mode Window Instead of Browser Tab"
- **2026-07-25** — Full Editor: "+ Queue" turns blue once Genre/Format/Age
  Rating are all filled, and "Process All" disables once the queue has ≥1
  item. → `progress.md` "Full Editor: Queue-readiness color + Process All
  lockout"
- **2026-07-25** — Three cosmetic UI tweaks: Folder View card border (dark
  theme), Folder View year range under card name, Issue page Previous/Next
  nav now spans full width. → `progress.md` "Three cosmetic UI tweaks
  (Folder View border/year, issue nav)"
- **2026-07-25** — Service worker cache (`sw.js`) now self-versions from a
  content hash of `frontend/` instead of a hardcoded string, so future
  static-file deploys self-heal instead of serving stale cached pages
  indefinitely. → `DECISIONS.md`/`progress.md` "Service worker cache now
  versions itself from a content hash"
- **2026-07-25** — "Send to Full Editor" bulk-selection action also brought
  same-tab (was `window.open(..., '_blank')`) — now awaits the background
  file-add then navigates in place. → `DECISIONS.md`/`progress.md`
  "Send to Full Editor also brought same-tab"
- **2026-07-25** — Admin "Open Editor" link now navigates in the same tab
  (was `target="_blank"`) — matches the wordmark/admin-cog same-window nav
  pattern, contained within the installed PWA window. →
  `DECISIONS.md`/`progress.md` "Admin 'Open Editor' opens in the same tab"
- **2026-07-25** — Four cosmetic UI tweaks: favourite heart nudged 2px down
  without moving its circle badge, "Reading" card text blur removed in light
  theme, issue-detail inactive rating stars darkened 10% in light theme,
  Admin Library Scan cards made thinner (height, then a same-session
  follow-up narrowed them ~10px too, plus a narrower Scan Now pill). →
  `progress.md` "Four cosmetic UI tweaks"
- **2026-07-24** — Custom Tabs: removed the 4-visible-tab cap entirely (not
  raised) — dated from the old top-tab-bar design, moot since the v2.6 left
  sidebar already scrolls. Backend + admin UI cap logic deleted; no Flutter
  change needed. → `progress.md` "Custom Tabs: removed the 4-visible-tab cap"
- **2026-07-24** — Add Reading Queue: new "Queue Reading" bulk-selection and
  issue-detail-page action, backed by a fourth `CustomTab.basis_type`
  (`reading_queue`, singleton, library-wide) plus a new `Issue.queued_for_reading`
  boolean column — mirrors the Favourites pattern rather than a new join
  table. → `progress.md` "Reading Queue (new feature...)"
- **2026-07-24** — Add Genre Library follow-up: admin layout reorder ("Add
  Library" next to the View dropdown, "Add Favourites Library" moved after
  "Add Genre Library"), and fixed a bug where the genre dropdown went empty
  after adding a tab until a hard refresh. → `progress.md` "Add Genre
  Library" (follow-up fixes)
- **2026-07-24** — Add Genre Library: a new `basis_type='genre'` custom tab,
  scoped to one genre, added via a dropdown next to "Add Favourites Library" in
  Add/Remove Libraries; multiple genres can each get their own tab. →
  `progress.md` "Add Genre Library"
- **2026-07-24** — Flutter mobile reader: pinch-zoom added to Scroll mode
  (Page mode already had it). → `progress.md` "Flutter mobile reader:
  pinch-zoom in Scroll mode"
- **2026-07-24** — Flutter mobile reader: card polish — removed the green
  progress/read overlay from cover images (kept the percent pill and read
  dot), darkened inactive rating stars on the issue page in Light Theme
  only, and swapped the launcher icon for the current clean logo (was a
  blurred old export). → `progress.md` "Flutter mobile reader: card polish
  (read-state overlay, star contrast, launcher icon)"
- **2026-07-24** — Flutter mobile reader: Folder View built (new feature) —
  folder-mode custom tabs (e.g. "2000 AD") now drill down through real
  directory navigation instead of falling back to a flat grid; folder
  tiles and issue-file tiles both render via the existing library card
  widget. Backend addition: folder entries now include a computed
  `year_min`/`year_max`. → `progress.md` "Flutter mobile reader: Folder
  View (new feature)"
- **2026-07-24** — Flutter mobile reader: "Titles per page" pagination
  (25/50/75/100, default 25) added to Settings, applying to the Browse
  screen (library views + custom-library tabs) — numbered page bar ported
  from the web app's pagination look/behaviour, no backend changes needed.
  → `progress.md` "Flutter mobile reader: "Titles per page" pagination
  (follow-up to v2.6 Item 4)"
- **2026-07-24** — Web UI: Issue Detail's "Read" button now reads "Start
  Reading" / "Continue Reading" / "Read Again" to match the issue's read
  state. → `progress.md` "Web UI: Read button label matches read state"
- **2026-07-24** — Flutter mobile reader: card visual-parity porting (Phase
  B of the Phase A follow-up) — grid density 5→4 cards/row, gold favourite
  border replaced with a theme-token card border (white dark / black light)
  wrapping the whole card including title/meta, 3px cover inset on grid and
  list, heart badge replacing star, green-dot read badge replacing the full
  overlay and unread pill, meta line anchored to card bottom, new
  gradient-glow page background (color blobs, not blurred photos — an
  Impeller rendering issue killed the literal web-parity approach), light
  theme wordmark asset added, and three issue-detail-page fixes (credit
  overflow, real format pill, tappable genre pills). → `progress.md`
  "Flutter mobile reader: card visual-parity porting (Phase B)"
- **2026-07-23** — Flutter mobile reader: light/dark theme infrastructure
  built (Phase A of a phased follow-up to v2.6 Item 4) — `AppColors` is now a
  `ThemeExtension` with dark+light palettes mirroring the web app's tokens,
  new Appearance toggle (Auto/Light/Dark) in Settings, all widgets switched
  from static color constants to `Theme.of(context)`. Verified on Windows
  desktop and Tez's Lenovo tablet. Card visual-parity porting (Phase B) still
  to come. → `progress.md` "Flutter mobile reader: light/dark theme
  infrastructure (Phase A)"
- **2026-07-23** — Folder View folder-tile cards (any custom tab, e.g. 2000
  AD's year folders) restyled to match the main library/home cards: fixed
  dark-gradient background, hover-only glow ring (was always-on), matching
  light-theme border override added. → `progress.md` "Folder View folder-tile
  cards restyled to match main library cards"
- **2026-07-23** — Search ComicVine "Select Series" modal reworked: wider
  modal, description moved below the results list, Cancel/Issues/Ok moved to
  the bottom of the cover-preview column; ComicVine's stray embedded `<img>`
  in series/issue descriptions now stripped to plain text (`cleanup_html()`).
  → `progress.md` "Search ComicVine 'Select Series' modal: layout rework +
  stray-image fix"
- **2026-07-23** — BUG-033 fixed: Search Online "Best match" order was wrong
  once a search term hit the local CT cache (missing `ORDER BY` in the pinned
  dependency's cache-read query); `ct_bridge.py` now re-ranks results itself.
  → `progress.md` "BUG-033: Search Online 'Best match' order fix"
- **2026-07-23** — Basic PWA support added: manifest + service worker site-wide,
  new "Install App" button on Admin (built by Dispatch outside a Claude Code
  session, backfilled into docs after the fact). → `progress.md` "Basic PWA
  support (Install App button)"
- **2026-07-23** — Convert Images: Lossless checkbox and Quality slider now
  sit on one row. → `progress.md` "Convert Images: Lossless checkbox and
  Quality slider on one row"
- **2026-07-23** — Admin Converter page: Convert Archives / Convert Images
  sections now sit side by side instead of stacked. → `progress.md` "Admin
  Converter page: Convert Archives / Convert Images side by side"
- **2026-07-23** — Full Editor Select Issue list: fixed out-of-order issue
  numbers (backend now natural-sorts by issue number). → `progress.md` "Full
  Editor Select Issue list: fixed sort order"
- **2026-07-22** — Full Editor comic viewer: added click-drag panning while
  zoomed in (`grab`/`grabbing` cursor), since a zoomed page is usually
  oversized in both axes; follow-up fix same day for a classic flexbox
  centered-overflow bug that made the top/left of a zoomed cover
  unreachable by either the drag or the frame's own scrollbars.
  → `progress.md` "Full Editor comic viewer: drag-to-pan when zoomed in (2026-07-22)"
- **2026-07-22** — Fixed two bugs: Full Editor comic-viewer zoom-in had no
  visible effect (CSS `max-width/max-height: 100%` was clamping the inline
  zoom width back down); Library selection-bar's Deselect button closed the
  bar instead of just clearing the selection.
  → `progress.md` "Two bug fixes: Full Editor zoom-in, Library selection-bar Deselect (2026-07-22)"
- **2026-07-22** — Issue page: closed the flat-bg seam between the Back
  button row and the backdrop image below it (backdrop now extends up
  behind the Back button instead of stopping just below it).
  → `progress.md` "Issue page: close the flat-bg seam above the backdrop, behind the Back button (2026-07-22)"
- **2026-07-22** — Series/Issue backdrop crop moved from `center 20%` to
  `center 10%` — 20% was cropping into cover title-logo text, sometimes
  hiding the top title line entirely.
  → `progress.md` "Series/Issue backdrop crop was hiding the top title line (2026-07-22)"
- **2026-07-22** — List/Series view: fixed unreadable read-state text in light
  theme (was fixed white opacity); added rating stars to List View's last row;
  fixed Series/Issue backdrop bleeding under the sidebar at ≤640px widths.
  → `progress.md` "Three cosmetic INBOX design changes: List/Series read-state colour, List View rating stars, backdrop edge-bleed (2026-07-22)"

- **2026-07-22** — Card Size options raised to 30-100% (10% steps, replacing
  10/25/75%) to stop badge/pill overlays squashing at small sizes; Home strips
  now hold 25 cards instead of 15.
  → `progress.md` "Card size floor raised to 30%; Home strips hold 25 cards (2026-07-22)"
- **2026-07-22** — Light theme: split the Series/Issue Detail cover backdrop
  and the Home/Browse/Folder View cover "cloud field" background into their
  own light-theme tokens, tunable without touching dark.
  → `progress.md` "Light theme: split backdrop & library-page background controls from dark (2026-07-22)"
- **2026-07-22** — Issue Detail page: cover frame now matches the grid view's
  2:3 cover aspect ratio instead of reading squarer/shorter.
  → `progress.md` "Issue Detail cover: match grid-view cover aspect ratio (2026-07-22)"
- **2026-07-22** — Light theme: favourited-issue button now shows a gold
  border only, label stays its normal colour instead of also turning gold.
  → `progress.md` "Favourite button (light theme): border-only cue, no text-colour change (2026-07-22)"
- **2026-07-22** — Fixed the read-state badge (green dot, grid/list/home-strip
  cards) not updating live after a bulk Mark as Read/Unread action.
  → `progress.md` "Read-state badge: fix stale badge after bulk Mark Read/Unread (2026-07-22)"
- **2026-07-22** — Flag badge repositioned to bottom-right, filled solid red,
  and its background-circle opacity unified across every card that shows it.
  → `progress.md` "Flag badge: repositioned, red fill, consistent opacity everywhere (2026-07-22)"
- **2026-07-22** — Issue Detail page: added a missing flag-badge overlay on
  the cover for flagged-for-review state, and changed the toggle button's
  active label from "Flagged for Review" to "Flagged".
  → `progress.md` "Issue Detail page: missing Flagged-for-review icon (2026-07-22)"
- **2026-07-21** — Added a Delete action to the multi-select bottom toolbar:
  permanent DB+disk delete with a pill-button confirm modal (no DB-only tier).
  → `progress.md` "Bulk Delete added to multi-select toolbar (2026-07-21)"
- **2026-07-21** — Card backgrounds (`--surface-card`) split from general area
  backgrounds (`--surface`) as real per-theme tokens, so light theme can tune
  card colour independently of header/sidebar/panels without touching dark.
  → `progress.md` "Split card background from general area background (light
  theme)"
- **2026-07-21** — UI pass: fixed off-center pill text (card genre ribbon,
  Full Editor queue buttons), added pill background to the issue-detail rating
  stars, white-on-blue text on accent-colored pills, +3px/+5px card gaps on
  library grids and home strips, bulk Flag for Review now updates the card's
  flag badge live (no refresh), and the issue-detail Format pill now links to
  the series page (multi-issue "Series" format) or the genre-style fieldview
  filter (everything else).
- **2026-07-20** — Full Editor's multi-XML resolve now surfaces the real error
  when the underlying archive is corrupted (bad CRC on rebuild) instead of a
  generic "could not resolve" message — same fix also improves error messages
  for Basic Editor saves and Full Editor batch processing on corrupt archives.
- **2026-07-20** — Series Detail page: cover backdrop no longer clipped to a
  rounded, inset card (was reading as a gap top/sides on dark covers) — now
  bleeds edge-to-edge and shares one opacity/blur/fade recipe with the Issue
  Detail page's backdrop instead of two quietly-drifted versions.
- **2026-07-20** — Series Detail page: fixed the issue-row read-state border
  (and other state-dependent styling) not updating live on Mark as Read/Unread or
  Mark all read — `app.js` was never resyncing the row's CSS class after the
  initial render, only the status button. Pre-existing bug, unrelated to the CSS
  token split below.
- **2026-07-20** — CSS theme-token refactor: split `style.css`'s theme-variable
  system into `tokens-base.css`/`tokens-dark.css`/`tokens-light.css`; fixed two
  light-theme bugs (unreadable genre pill on grid cards, `.state-read` black
  overlay) along the way. BUG-032 (stale page cache) found and logged, not fixed.
- **2026-07-19** — Windows desktop reader now resizes/centers the window to 75% of
  the comic's actual cover page dimensions on open (capped to fit the screen),
  instead of a fixed 1280x720 for every comic.
- **2026-07-19** — Full Editor: Select Series modal gained a Sort control
  (Series A-Z / Year / Issues / Publisher, asc/desc toggle, defaults to
  ComicVine's own relevance order until manually changed) and Cancel/Issues/Ok
  buttons below the results list, left-aligned.
- **2026-07-19** — File Rename tool: output format changed from `Series - Title
  #Issue (Year)` to `Series #Issue - Title (Year)`, Edit Panel field order swapped
  to match (Series, Issue, Title, Year).
- **2026-07-19** — Auto Processing Schedule row: Day dropdown now disables unless
  Weekly is selected (Time disables when Off), and Schedule/Time/Day auto-save on
  change like the rest of the page instead of requiring a separate Save click.
- **2026-07-19** — Full Editor: removed the misplaced/nonfunctional Column 2
  "Clear" button, moved "Clear Queue" into Column 4's Queue Actions row (between
  Process Queue and Process All) as a matching white-text blue pill.
- **2026-07-19** — Fixed BUG-031: Full Editor's Process All wrote Increment #
  numbers in raw file-arrival order instead of the natural-sorted order shown in
  the Column 1 tree, scrambling issue numbers on larger batches. See
  `archive/bugs-fixed-archive.md` BUG-031.
- **2026-07-19** — Full XML Editor now pre-fills Series/Number/Year from the
  filename when a loaded file has no `ComicInfo.xml`, reusing the Filename Editor's
  parser (`rename_tool.parse_comic_filename`) instead of leaving the form blank.
- **2026-07-19** — Fixed BUG-030: Changed Files stat tile counted new-file inserts
  as "changes" (disagreeing with its own log, which never logs new files). Tile and
  log now both driven by genuine updates + rename/move matches only. See
  `archive/bugs-fixed-archive.md` BUG-030.
- **2026-07-19** — Admin Logs modal now defaults to showing only the most recent
  scan's entries (marker-line boundaries in `changed_files_log.md`/
  `new_files_log.md`/`missing_log.md`), instead of the full accumulated log file —
  full history still on disk, viewable via a text editor. See `v2.6/progress.md`,
  "Admin Logs modal defaults to most recent scan only" (2026-07-19).
- **2026-07-19** — Three UI tweaks: genre ribbon on grid/strip cards now
  links to the genre filter (same fieldview route as other genre tags),
  Admin page content sections narrowed and centred (Filename Editor to 75%,
  all others to 640px), Home Strip scroll arrows bled to the true page
  edge. See `v2.6/progress.md`, "Three UI tweaks…" (2026-07-19).
- **2026-07-18** — BUG-029 fixed: scanner now detects a plain on-disk
  rename/move via content hashing instead of creating a duplicate row and
  orphaning the old one — forward-only (hashes new/updated files going
  forward, no retroactive backfill of the existing library, since the dev DB
  will be wiped again before production). See `v2.6/progress.md`,
  `archive/bugs-fixed-archive.md`, `DECISIONS.md`.
- **2026-07-18** — BUG-026/BUG-027 fixed: Clear Database now also sweeps
  orphaned thumbnails, resets scan logs/timestamps, and VACUUMs the DB file,
  then restarts itself automatically (reusing Restore Database's BUG-016
  checkpoint/dispose pattern) — no more manual stop/start needed. See
  `v2.6/progress.md`, `archive/bugs-fixed-archive.md`, `DECISIONS.md`.
- **2026-07-18** — BUG-016 fixed: Restore Database now actually reverts DB
  state. Root cause was WAL replay — restore never cleared the `-wal`
  sidecar, so pending writes made after the backup got replayed straight back
  in on relaunch. Added `checkpoint_wal()`, applied to both backup and
  restore; restore also disposes the engine before deleting the sidecars
  (Windows file-lock issue found during testing). See `v2.6/progress.md`,
  `archive/bugs-fixed-archive.md`, `DECISIONS.md`.
- **2026-07-18** — BUG-013 fixed: scanner now checks file size alongside
  mtime to detect a same-mtime, different-content re-save. New `Issue.file_size`
  column, backfilled from disk for existing rows so the fix doesn't force a
  mass reprocess. Split the rename/move blind spot out as a new bug,
  **BUG-029** (not fixed — scanner still has no rename detection). See
  `v2.6/progress.md`, `BUGS.md`, `archive/bugs-fixed-archive.md`.
- **2026-07-18** — BUG-025 closed as not-a-bug: the Move Series/Singles
  Folders tool's intended workflow (Stage 3 Processing → Move → manual Scan)
  never has a pre-existing DB row to desync, since Processing is scan-excluded.
  The original report was the tool being pointed at already-in-library content
  (an atypical use). A defensive DB-sync fix was already built and kept as a
  no-op safety net rather than reverted. See `v2.6/progress.md`,
  `archive/bugs-fixed-archive.md`, `DECISIONS.md`.
- **2026-07-18** — BUG-028 fixed: macOS junk entries (`._*.jpg`,
  `__MACOSX/`) no longer counted as pages or picked as covers. Centralized
  filter applied across scanner, reader, Editor, and the Convert
  Archives/Convert Images processing tools (so it's also caught at ingest,
  not just read time); cover endpoint now respects `cover_path`; failed
  thumbnail generation now surfaces as a scan error instead of passing
  silently. 22 already-affected issues remediated (page_count and cover
  regenerated). See `v2.6/progress.md`, `archive/bugs-fixed-archive.md`,
  `DECISIONS.md`.
- **2026-07-18** — Performance re-baseline after the 2000 AD move (no code
  changed). Scanner measured at real scale for the first time (5,452 files,
  21.5 min — thumbnails 53%, per-file commits 18%, 4 archive opens/file);
  cold-start follow-up closed with a negative result; both N+1 fixes confirmed
  holding; a third `Issue.genres` N+1 found in `home.py`. DB was cleared and
  rebuilt to recover from the move. Four new bugs logged (BUG-025 to BUG-028).
  See `PERFORMANCE.md` §1B, `v2.6/progress.md`.
- **2026-07-18** — New Processing Tools: Move Series Folders / Move Singles
  Folders (v2.6 Item 10), moving folders out of Stage 3 into their correct
  library location, sharing the Folder Processing card with Sort by
  Filename. Recursive Series merge (handles container-style series like
  2000 AD), exact-duplicate blocking for `[YYYY]`/`(YYYY)` notation drift,
  near-miss warnings. See `v2.6/progress.md`, `ADMIN_SPEC.md` §11.7,
  `DECISIONS.md`.
- **2026-07-17** — Folder View: removed the in-page "← Back" / "Mark all
  read" row above the card grid (duplicated the browser's back button and
  the multi-select toolbar's mark-read action) so the grid sits flush under
  the menu bar, matching Browse. See `v2.6/progress.md`, `DECISIONS.md`.
- **2026-07-17** — Folder View subfolder cards: border swapped from flat
  1px to the redesigned cover-card's glow-ring/hover-lift treatment, cover
  image now gets the same 5px inset padding as `.cover-card--redesign`. See
  `v2.6/progress.md`.
- **2026-07-17** — Series View: issue rows redesigned as a 2-column card grid
  matching the List View redesign — 115px thumb, clickable genre tags (new
  `genres` field added to `GET /api/series/{id}`), permanent card glow +
  hover lift, and the same read/unread text-emphasis swap. See
  `v2.6/progress.md`.
- **2026-07-17** — List View redesign: 2-column layout (collapses to one on
  narrow windows), 50px column gap + 10px row top padding + 25px row gap,
  genre tags are now links to the fieldview genre filter, read/unread text
  emphasis swapped so unread issues stand out instead of read ones, and
  unread summary text brightened to 90% white. Scoped entirely to List View
  — Grid View unaffected. See `v2.6/progress.md`.
- **2026-07-17** — Cover-card resting shadow split into a permanent white
  glow ring + hover-only drop shadow (was always both, read inconsistently
  between Home strips and the Grid), root-caused and fixed a hard clip line
  on the glow from an `overflow-x`/`overflow-y` CSS coupling, and shrank
  the Issue Detail page's Edit XML / Flag for Review pills. See
  `v2.6/progress.md`.
- **2026-07-17** — Issue Detail page: Mark as Read now updates the cover
  frame colour and progress bar live (no refresh needed, progress bar now
  Reading-only), added a "Read"/"Continue Reading" button above Mark as
  Read that opens the desktop reader, cover backdrop now spans full-bleed
  to the sidebar with a lighter top fade and a slight blur, and Edit XML +
  Flag for Review now share a row at equal width with the flag emoji
  dropped. See `v2.6/progress.md`.
- **2026-07-17** — Multi-select: added shift-click range select (selects
  every card between the anchor and the shift-clicked card) and fixed a bug
  where deselecting the last remaining selected card also navigated to that
  card's issue/series page instead of just exiting selection mode. See
  `v2.6/progress.md`.
- **2026-07-17** — Desktop reader (Flutter): fixed Scroll mode (the default
  reading mode) never reporting reading progress to the server at all — the
  "Reading" left-nav filter showed nothing after reading partway through an
  issue and closing it, because `ReadingProgress.status` never left
  `"unread"`. Also fixed Scroll mode never resuming your saved page on
  reopen, and the bottom-bar page slider being a no-op (or a crash risk for
  local files) in Scroll mode. See `v2.6/progress.md`; BUG-024 in
  `archive/bugs-fixed-archive.md`.
- **2026-07-17** — Issue detail page cover card: found and fixed the actual
  root cause of the recurring "blur glow won't show up" reports — the glow
  layer was being added to `.issue-cover-img` (an `<img>` itself), and
  `::before` never renders on replaced elements. Added a `.cc-cover-glow`
  wrapper `<div>` per Design's recipe, confirmed the blur now actually
  computes and renders on both read states. See `v2.6/progress.md`.
- **2026-07-17** — Issue detail page cover card: rebuilt as a "collector
  card" slab (metallic bezel + state-coloured mat + dark inner frame,
  three real nested layers replacing the old box-shadow ring) per Tez's
  supplied design mockup, plus an on-cover favourite heart badge synced to
  the existing Favorite button; follow-ups added a soft state-coloured
  blur between the cover's black border and the mat line, then sized the
  whole card up 25%, dropped the hover-lift effect, and thickened the
  image border + all three frame layers by 5px each; final follow-up
  reverted the black border back to 3px, tightened the gap before the mat
  line, and grew both the cover art and the mat ring. See
  `v2.6/progress.md`.
- **2026-07-17** — Issue detail page cover card: switched the black gap
  before the state ring from a blurred box-shadow to a crisp 6px border
  (the shadow version wasn't visible enough at normal size), and gave the
  cover a real offset drop shadow (Tez's `.image-with-shadow` recipe) that
  casts onto the bezel for a lifted look. See `v2.6/progress.md`.
- **2026-07-17** — Issue detail page cover card: thicker metal bezel ring
  (+3px), thinner read-state ring (-1px), added an embossed/dropped inset
  border around the cover image. Issue page only, grid cards unaffected.
  See `v2.6/progress.md`.
- **2026-07-17** — Issue detail page: capped the Summary paragraph's width
  (was stretching full-window-wide on large screens) and preserved
  paragraph breaks from `\n\n` in ComicInfo.xml's Summary field (was
  rendering as one run-on paragraph). See `v2.6/progress.md`.
- **2026-07-17** — Restyled the selection toolbar's Deselect pill to match
  the other action pills (dark background, same hover state) instead of
  the removed Cancel button's transparent/muted look. See
  `v2.6/progress.md`.
- **2026-07-17** — Removed the redundant Cancel button from the selection
  toolbar (identical to Deselect); Deselect and Done remain. See
  `v2.6/progress.md`.
- **2026-07-17** — Fixed selection toolbar's Done pill showing black text
  on its blue background instead of white. See `v2.6/progress.md`.
- **2026-07-17** — Bulk-select toolbar's rating stars now clear the rating
  when clicked again at the selection's current value, matching the
  issue-page rating control's behaviour. See `v2.6/progress.md`.
- **2026-07-17** — Fixed bulk-select toolbar's rating action: it patched a
  dead pre-redesign cover badge instead of the actual rating row in the
  card's info block, so a new rating showed a stray star on the cover and
  didn't update the visible rating. See `v2.6/progress.md`.
- **2026-07-17** — Bulk-select toolbar actions (Mark Read/Unread, Favorite,
  Flag for Review, Rate, Send to Full Editor) no longer auto-clear the
  selection after firing, so multiple actions can be applied to the same
  selected cards; added a Deselect button to clear it explicitly. See
  `v2.6/progress.md`.
- **2026-07-17** — Fixed Hanken Grotesk not rendering anywhere (`body` had a
  hardcoded fallback font stack instead of the `--font-sans` token); removed
  the green `.has-pending`/`.is-scanning` borders from Admin scan-section
  cards. See `v2.6/progress.md`.
- **2026-07-16** — Fixed BUG-023: library cover image could stay stale for up to
  24h after an archive edit + rescan (browser cache regression from v2.6 Item 2
  Phase 4). Cover URLs now carry a version stamp tied to the scanner's own
  change-detection instead of a blind time-based cache. See
  `docs/archive/bugs-fixed-archive.md` BUG-023 and `v2.6/progress.md`.
- **2026-07-16** — Process change: Inbox triage paused indefinitely
  (capture-only in Chat/Cowork/Code alike, until Tez says otherwise). See
  `v2.6/progress.md` "Inbox triage paused" and `DECISIONS.md`.
- **2026-07-15** — Card redesign (v2.6 Item 9): new border/genre-ribbon/
  favourite-badge/flag-badge/progress-pill look applied to the main library
  grid, Home Page Strips, and Folder View's flat file cards, via a new
  `.cover-card--redesign` CSS modifier class (Series Detail rows and list
  view untouched). Home Strip cards widened to fit the same full-size
  badges. See `SPEC.md` §20.20 and `v2.6/progress.md` "Card redesign"
  sessions.
- **2026-07-15** — Added Review Queue (v2.6 Item 8): flag any issue for
  review (Issue Detail button or bulk multi-select), filter the library to
  flagged-only, and batch-send a selection straight into the Full Editor's
  working set. Full Editor now rescans + auto-clears the flag when saving an
  already-catalogued issue (a scoped exception to its normal DB-agnostic
  rule). See `EDITOR_SPEC.md` §13, `MENU_BAR_SPEC.md` §2.8, and
  `v2.6/progress.md` "Review Queue" session.
- **2026-07-15** — Basic Editor popup-open perf fix: `GET`/`POST
  /api/editor/{issue_id}` consolidated 3 redundant archive opens into 1;
  parallelized the popup's formats/genres fetches. See
  `PERFORMANCE.md` finding #11 and `v2.6/progress.md` "Basic Editor
  popup-open perf fix".
- **2026-07-15** — Dropped 4 of 6 legacy raw-CSV credit columns (`inker`/
  `colorist`/`letterer`/`cover_artist`, confirmed dead) from `issues`;
  `writer`/`penciller` deliberately kept (still power search/Group-by-Writer/
  series-card display). Roadmap triage same session: Advanced Search page and
  multiple scan locations/series-overview-field ruled out; `Later` lane
  removed from `roadmap.html`. See `v2.6/progress.md` "Legacy credit-column
  cleanup + roadmap triage".
- **2026-07-15** — Site-wide scrollbar restyle (matching the filter-dropdown
  look) across the main app and the XML Editor; fixed a same-session
  regression where it caused the Editor's Genre dropdown popup to render
  light instead of dark. See `v2.6/progress.md` "Site-wide layout width,
  multi-cover background, scrollbars".
- **2026-07-15** — Random library-page background reworked from one
  corner-masked cover to a multi-cover "cloud field" (up to 4 blurred, soft-
  masked covers spread across the whole content area) — fixes the "doesn't
  cover enough" complaint on the 2026-07-13 original. See `v2.6/progress.md`
  "Site-wide layout width, multi-cover background, scrollbars".
- **2026-07-15** — Header and main content are full-width site-wide (was
  capped at a centred 1440px column); settled on a 30px L/R gutter. See
  `v2.6/progress.md` "Site-wide layout width, multi-cover background,
  scrollbars".
- **2026-07-14** — Full Editor 4-column redesign (v2.6 Item 7): `/editor` goes
  from 3 columns to a 4-column workspace (folder→series→issue tree · editor with
  genre chips + apply-to-all column · viewer with Fit/Fullscreen/lazy thumbnail
  strip · queue) + a footer status bar. Visual reskin of the Claude Design export;
  all `/api/editor/full/*` endpoints reused (one additive `?w=` thumbnail param).
  Rebuilt locally after the cloud build couldn't push. See `v2.6/progress.md`
  "Full Editor 4-column redesign".

- **2026-07-14** — Open Issue Detail cover in the Windows desktop reader
  (v2.6 Item 6): clicking a comic's cover on `/issue/{id}` now launches the
  Windows reader (registered via Settings) directly into that issue,
  cold-start and warm-start both handled. Closes the long-parked
  `ROADMAP.md` "Reader-launch feature". See `v2.6/progress.md` "Open Issue
  Detail cover in the Windows desktop reader (v2.6 Item 6)".
- **2026-07-14** — Fixed filter dropdowns (Genre/Format/Decade/Year)
  rendering behind cover cards — a stacking-context regression from the
  2026-07-13 random cover background change. See `v2.6/progress.md` "Filter
  dropdowns rendering behind cover cards (bug fix)".
- **2026-07-14** — Windows Desktop Reader (v2.6 Item 5): the existing shared
  Flutter app now works properly as a Windows desktop reader — Android-only
  code paths guarded, keyboard paging added, native window rebranded to
  digib00age. Closes BUG-021. See `v2.6/progress.md` "Windows Desktop Reader
  built (v2.6 Item 5)".
- **2026-07-13** — Mobile app icon (Android + Windows) now uses `favicon.png`
  (the digib00age "oo" mark), same asset as the tray icon and web favicon.
  Cosmetic. See `v2.6/progress.md` "App icon: favicon.png (digib00age
  mark)".
- **2026-07-13** — Mobile Browse title-count fix: "All" now matches the web's
  grand-total-of-individual-comics count (was showing a card count instead,
  2,080 vs the web's 5,427); "Singles"/"Series" no longer fragment a
  multi-issue series into a phantom extra "singles" card when one of its
  issues is individually mistagged (found 8 real cases, e.g. "Nowhere
  Men") — mobile now filters client-side like the web does, instead of via
  the backend's issue-level `group=` param. See `v2.6/progress.md` "Browse
  title counts didn't match the web".
- **2026-07-13** — Mobile UI Redesign (v2.6 Item 4): full rail-based scaffold
  redesign of the Flutter tablet app — persistent nav rail, Home/Browse/
  Series Detail/Issue Detail screens, dark theme matching the web
  redesign. Built and verified on Tez's real Lenovo tablet against the real
  library/server, including three real bugs on-device testing caught that
  static analysis didn't. A fourth bug — no path anywhere in the new
  navigation actually opened the Reader — was found after Tez's manual
  pass; fixed, and Tez subsequently confirmed Start Reading/Continue
  Reading both work. See `v2.6/progress.md` "Mobile UI Redesign built
  (v2.6 Item 4)".
- **2026-07-13** — Random cover background correction: now spans the full
  content area (was clipped to the centered `.container` column, leaving
  flat gutters on wide screens) and mutes blue-toned covers instead of
  reading overly blue. See `v2.6/progress.md` "Random cover background:
  full-width + reduce blue cast".
- **2026-07-13** — Random library-page cover background: Home, Browse
  (All/Singles/Series), and custom tabs (flat or Folder View) now show a
  subtle blurred cover image behind the page, anchored top-right, randomly
  picked from whatever that surface actually shows (never the whole
  library) and re-picked once per surface-entry. See `SPEC.md` §20.19 and
  `v2.6/progress.md` "Random library-page cover background".
- **2026-07-13** — Issue Detail cover now has a slight zoom + white border
  on hover. See `v2.6/progress.md` "Issue Detail cover: hover zoom + white
  border".
- **2026-07-13** — Tray icon base glyph now reuses `favicon.png` (the
  digib00age mark) instead of the old programmatic purple book glyph; the
  existing 3-state coloured dot (green/amber/red) is unchanged. Visual-only
  exception to the 2026-07-07 "tray app stays ComicVault-branded" scope
  decision — see `DECISIONS.md`. See `v2.6/progress.md` "Tray icon base
  glyph now reuses favicon.png".
- **2026-07-13** — Series Detail page pagination (v2.6 Item 3): the
  `/series/{id}` issue list is now paginated, same page-size setting and
  page-number control as Browse — a large series (2000 AD, 2,483 issues) no
  longer loads its whole issue list in one page. See `v2.6/progress.md`
  "Series Detail page pagination (v2.6 Item 3)".
- **2026-07-13** — Performance fixes Phase 5 (v2.6 Item 2): fixed the
  Full Editor's page-preview N+1 (finding #6, measured live for the first
  time this session) — `backend/routers/editor_full.py` now caches the
  archive's sorted image list instead of re-parsing it on every
  preview/page call. **v2.6 Item 2 (Performance fixes) is now complete**
  — all 5 phases from the 2026-07-09 baseline built and verified. See
  `PERFORMANCE.md` for the re-baseline.
- **2026-07-13** — Performance fixes Phase 4 (v2.6 Item 2): `GET
  /api/cover/{id}` now sends `Cache-Control`/`ETag` and honors
  `If-None-Match` with a real 304 (Starlette's `FileResponse` computed an
  ETag but never checked incoming requests against it). Verified via
  TestClient and direct HTTP against the live server. See `PERFORMANCE.md`
  for the re-baseline.
- **2026-07-13** — Performance fixes Phase 3 (v2.6 Item 2): reader's
  `_sorted_pages()` now caches the sorted page list per archive (keyed on
  mtime+size), instead of re-parsing the ZIP central directory on every
  page request. Cache-hit ~0.1ms vs a cold parse. See `PERFORMANCE.md` for
  the re-baseline.
- **2026-07-12** — Performance fixes Phase 2 (v2.6 Item 2): fixed two N+1
  queries in `GET /api/series/{id}` for large series (per-issue
  `ReadingProgress` query, plus a lazy-loaded-genres N+1 the original
  baseline hadn't named) — 2000 AD (2,483 issues) 4,969 queries/2.5-2.7s
  down to 9 queries/~0.33-0.42s. See `PERFORMANCE.md` for the re-baseline.
- **2026-07-12** — Performance fixes Phase 1 (v2.6 Item 2): fixed the two
  N+1 queries in `GET /api/library` (lazy-loaded genres, per-series
  `ReadingProgress` query) — 7,508 queries/3.9-4.1s down to 13 queries/
  ~0.63-0.67s. See `PERFORMANCE.md` for the re-baseline.
- **2026-07-12** — Fixed BUG-022: bulk star rating from the multi-select
  bottom toolbar wasn't reflected on cards (backend was already correct;
  client-side DOM/cache patch was missing). Also investigated a stale-cover
  report (Dusk - Poor Tom) and confirmed it was a browser-cache false alarm,
  not a defect.
- **2026-07-12** — `docs/` converted from a Google Drive junction to a plain
  repo folder (git tracking unaffected); Cowork's nightly doc-scan automation
  retired as a consequence, its files moved to `archive/`.
- **2026-07-12** — Confirmed the doc-scan cancellation is permanent, not
  pending a replacement; Claude Code is now the master controller for
  planning/triage/build/docs, with outside planning docs (Design, Chat)
  treated as reference input rather than a required pipeline stage.

---

- **2026-07-11** — Basic Editor save made async: the modal now closes as
  soon as validation passes instead of blocking on the archive rebuild;
  the rebuild + rescan finish in the background (poll `GET /api/editor/
  {issue_id}/save-status`), with a toast on completion/failure and a `409`
  guard against a second concurrent save on the same issue. Accepted
  trade-off: a background failure after navigating away is silent
  (`DECISIONS.md`).
- **2026-07-11** — Inbox cosmetic pass (5 items, not a build-queue item):
  favourite badge changed from gold star to red heart on white bg (true
  circle, fixed same session after an egg-shape report); unread badge text
  changed from black to white; new personal-rating pill (vertical gold
  stars, bottom-right of grid cards, matches bottom-toolbar rating pill
  styling); selected-card indicator changed from a blue dot to a gold
  checkmark on dark grey; all Admin stat cards (Library Stats + all six
  Library Scan cards) now share one uniform borderless baseline, corrected
  same session from an initial 3-of-6 mismatch — functional status borders
  (scan in progress, unread log entries) unaffected.
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
