# digib00age Feature Inventory

> Compiled for Stage 1 of `docs/user-guide-plan.md`. Sourced from live navigation of
> `http://localhost:9424` plus `frontend/*.html`, `frontend/js/*.js`, and the spec docs
> (`SPEC.md`, `EDITOR_SPEC.md`, `ADMIN_SPEC.md`, `CUSTOM_TABS_SPEC.md`,
> `HOME_STRIPS_SPEC.md`, `MENU_BAR_SPEC.md`). Product name in the UI is **digib00age**;
> internal code/API terms ("ComicVault", "Custom Tabs") are noted where the UI copy
> differs, since the guide should use the UI's own words.
>
> One open bug worth flagging for guide content: **BUG-032** — page routes send no
> `Cache-Control` header, so a browser can occasionally serve a stale cached page after
> an update (a hard refresh fixes it). Not user-facing under normal use; not mentioned
> further below unless a specific page section needs the caveat.

---

## Global Chrome — every page

### Site header (`site-header`)
- Sidebar toggle (☰): only on Library/Series/Issue pages — shows/hides the left nav sidebar; state persists via `localStorage` (`cv_sidebar_collapsed`).
- Logo/wordmark ("digib00age" lockup, light+dark variants swapped by theme): links to `/`.
- Search bar (Library page only, `#searchWrap`): inline live search, shown only while a browse surface (Series/Singles/All/Home) is active; placeholder text changes per surface ("Search All", "Search Singles", "Search Series").
- Admin/Settings gear icon: links to `/admin`. Dims and becomes inert (`.settings-btn--disabled`) when Remote Administration is off and the session is non-local — icon stays visible, just non-functional.
- Login/Logout button (`#logoutBtn`): hidden until `checkAuthStatus()` resolves; label and behavior depend on auth state (see Admin → Password Protection below). Present on every page.
- Admin page additionally shows a plain "Admin" label next to the logo instead of the search bar.
- Full Editor page additionally shows "</> XML Editor" brand text, a "Search ComicVine" button, and a "Search GoodReads" external link, in place of the search bar.

### Left sidebar (`app-sidebar`) — Library/Series/Issue pages only
- Primary nav: Home, All, Singles, Series (icon buttons; expand to icon+label when sidebar is un-collapsed).
- Quick status shortcuts: Unread, Reading, Read — each jumps to the All surface pre-filtered to that read status (not a per-surface filter; always lands on All).
- Libraries section: dynamically populated list of admin-created Custom Tabs (folder-scoped, Favourites, Reading Queue, Genre tabs), in creation order. Each shows a single-letter badge (first letter of the name, or "#" if it starts with a digit) when the sidebar is collapsed, full name when expanded.
- Sidebar auto-sizes its expanded width to the longest label present (clamped 140–320px).

### Menu bar (`#menuBar`) — shown on all browse surfaces (Series/Singles/All/Folder View custom tabs), hidden on Home, Admin, Full Editor, and issue detail
- Sort dropdown: A–Z, Newest, Recent, Issues, Pages (Pages hidden/disabled on Series/Singles surfaces and all Folder View tabs, since page count isn't a meaningful aggregate there).
- Ascending/Descending toggle (↑/↓ arrow icon): flips current sort direction.
- Grid/List view toggle (☰/⊞ icon): switches card layout; persists via `localStorage` (`cv_view_mode`).
- Rated filter dropdown: 1–5 stars; narrows to issues at exactly that personal rating.
- Favourites filter toggle (★ Favourites): shows only favourited items. In Folder View, a folder card stays visible if anything under it is favourited.
- Flagged filter toggle (🏳 Flagged): shows only issues flagged for review (same folder-visibility rule as Favourites).
- Group by dropdown: No grouping / Year / Genre / Publisher / Writer / Format. Flat-View-only — hidden on Folder View (which already groups by directory).
- Secondary filter dropdowns: Genre, Format, Decade, Year, Rating, B&W — apply to flat issue cards; in Folder View they filter the flat file cards at the current level, folder cards are unaffected.
- Clear Filter pill: resets every active filter/sort/search/grouping at once; only visible once at least one filter is active.
- Title/item count (e.g. "5,453 Titles"): live count for the current surface + filters.
- Fieldview banner: appears in place of the count when viewing a filtered "field view" (e.g. clicking a genre tag) — shows what's being filtered and a Clear link.

### Selection bar (`#selectionToolbar`) — floating bar, appears app-wide once a selection starts
- Entry: long-press (~500ms) any card/row, click its hover-reveal select-dot (grid view only), or Shift+click a second card for range-select.
- Selection count ("N selected").
- Mark Read / Mark Unread — bulk status change for every selected item.
- ★ Favorite — toggles favourite; button label follows whether *all* selected items are already favourited (acts as Un-favorite if so).
- 📖 Queue Reading — toggles Reading Queue membership, same all-selected-already logic as Favorite.
- 🏷 Flag for Review — toggles the review flag, same logic.
- → Send to Full Editor — resolves selection to file paths and adds them to the Full Editor's working set (skips its folder picker), opens `/editor` in the same tab.
- Star rating row (✕ clear, then ★1–★5) — bulk-sets personal rating; clicking a rating every selected item already has clears it instead.
- 🗑 Delete — opens a confirmation modal ("all data and the files will be deleted, no going back"); on confirm, permanently deletes the file(s) from disk and the DB row(s).
- Deselect — clears the current selection but stays in selection mode.
- Done — exits selection mode entirely.
- Selecting a series-aggregate card (not a Singles card) selects the whole series; bulk actions expand it server-side to every issue in it.

---

## Library Home — `/` (surface=home)

### Home strips (`#homeStrips`)
- Continue Reading — issues with status "reading". Conditionally shown (only if at least one exists); always pinned first regardless of stored order.
- Recently Added — most recently scanned-in issues.
- Random Unread — a random unstarted comic; re-rolls every visit.
- Random Genre — a genre picked at random each visit; the strip heading shows the actual genre name (e.g. "ART").
- Admin-added strips (up to 5): each based on one field+value (Genre/Publisher/Writer/Artist/Format/Decade/Year/Rating/B&W) or one folder; Random or Fixed (Title/Newest/Recent) order. Clickable heading opens a full filtered listing (`fieldview`/`folderview` surface) — default strips' headings are plain text, not clickable.
- Each strip shows up to 25 covers with left/right scroll arrows (fade/disable at either end).
- Strip card anatomy: cover image, title, year, genre ribbon (first genre, links to a genre filter), issue number (series) or page count (singles), star rating row if rated, flag badge (top-left) if flagged for review, read-state dot badge (top-right) if fully read, progress track/fill bar if partially read. No multi-select on Home strips.
- Random full-bleed page background composited from covers currently shown.
- Empty state: "No content yet." if every strip is empty. Load-failure state shows the error message and a Retry button (20s request timeout).

---

## Library Browse — Series / Singles / All — `/?surface=series|singles|all`

- Same menu bar as described globally; same cover-card grid.
- **Series** surface: only multi-issue series (aggregate cards).
- **Singles** surface: only single-issue "series" (each card links straight to its one issue).
- **All** surface: everything, series aggregated + singles together.
- Cover card anatomy (grid view): cover image, hover-reveal select-dot (top-left corner), flag badge (if flagged for review), read-state dot badge (fully read), progress bar overlay (partial read: series uses read/total issue ratio, singles use real page position), title, year, genre ribbon, issue count (series) or page count (singles), star rating row.
- List view: same cards laid out as rows, with extra metadata visible (genre tags, publisher/first writer, summary snippet, "X% Read" text instead of a progress bar).
- Clicking a series card opens `/series/{id}`; a Singles card opens `/issue/{id}` directly.
- Pagination: page-size driven by Admin → Pagination setting (25/50/100/200/500, default 50), persisted client-side.
- Card size: driven by Admin → Card Size (30–100%), applies to every cover-grid site-wide.
- Empty/loading states: "Loading library…" while fetching; "Could not reach the server. Is it running?" on fetch failure.

### Fieldview / Folderview (transient surfaces)
- Reached only via a clickable link elsewhere (genre tag, writer/artist credit link, a Home Strip's clickable heading) — not part of the persistent nav.
- Fieldview: flat listing filtered to one field+value (e.g. every issue by a given Writer). Shows a banner with a Clear link.
- Folderview: flat listing filtered to one folder path — used by folder-based Home Strips' "view all" link (distinct from a Folder-View-mode Custom Tab, which is its own persistent surface — see below).

---

## Series Page — `/series/{id}`

- Back link (real browser history — goes back one step, or `/` if none).
- Hero: backdrop image (blurred cover), series title, publisher · year, genre tags (link to genre fieldview), issue count ("N issues"), "Mark all read" button.
- If reached via a filtered/search context, a banner shows "Showing N of M issues — filtered by X" with a "View full series" link back to the unfiltered page.
- Issue list: one row per issue — thumbnail, `#N` + title, year · page count, genre tags, summary snippet, in-progress bar (if reading), status button (○ unread / ▶ reading / ✓ read, click to toggle read/unread directly from the list).
- Client-side pagination of the issue list (same page-size setting as Browse).
- Each row supports the same multi-select gesture (long-press/select-dot/shift-click) as grid cards, selecting individual issues.
- "Mark all read" marks every currently-unread issue in the series as read in one action; button shows "Marking…" then "All read ✓" with a green background on completion.

---

## Issue Detail Page — `/issue/{id}`

- Back link (real browser history).
- Faint full-bleed cover backdrop behind the content.
- Collector-card-framed cover art (metallic bezel/mat/inner frame), links to `comicvault://read/{id}` (the Windows/Android Flutter reader's registered protocol handler — no effect if no handler is registered on the current device/browser).
- Favourite badge (❤, top overlay) and flag badge, shown only when set.
- Progress bar under the cover, shown only while status is "reading".
- "Start Reading" / "Continue Reading" / "Read Again" button (same `comicvault://read/{id}` link, text reflects current read status) — a text affordance for the same action as the cover.
- Mark as Read / ✓ Read toggle button.
- ☆ Add to Favorites / ★ Favorited toggle.
- 📖 Add to Reading Queue / 📖 Queued toggle.
- Star rating control (1–5, click the current value again to clear — matches BUG-009's fixed behaviour).
- Edit XML button — opens the Basic Editor modal for this issue.
- Flag for Review / Flagged toggle.
- Metadata column: series title (large heading), badges row (issue number "#N of Count", format badge — links to the series page if it's a multi-issue "Series"-format issue, otherwise to a format fieldview; B&W badge if applicable), publisher · year · language line, genre tags, Summary section, Story Arc section (with part number if set), Credits section (Writer/Artist only — each name links to a fieldview of everything they're credited on; other credit roles are stored but not shown), "Rated: X · N pages" line.
- Prev/Next issue navigation bar at the bottom (only shown if a neighbour exists) plus a link back to the series (or `/` for a Singles issue).

---

## Folder View — a Custom Tab set to "Folder View" mode (e.g. the default "2000 AD" library)

Reached via a Libraries sidebar entry whose `view_mode` is `folder` (Admin → Add/Remove Libraries → View dropdown). Differs from a flat Custom Tab by browsing the folder's actual on-disk directory structure instead of one flat filtered list.

- Same menu bar as Flat View, minus Grouping (folders already group by directory) and the "# of Pages" sort option; all other sort/filter/favourite/flag/search controls behave the same, scoped to the current folder level.
- Mixed grid at each folder level: subfolders render as folder cards (recursive issue count across everything underneath, a random representative thumbnail re-rolled every visit, year range if available), loose files render as normal flat issue cards.
- Clicking a folder card drills one level down; there is no in-page Back/breadcrumb control — going up a level means using the browser's own Back button (reuses `history.pushState`). **Correction 2026-07-26:** an earlier pass of this inventory claimed a "← Back" button and a folder-level "Mark all read" button here; neither exists in the current code — both were part of a back-nav/mark-all-read row removed from Folder View on 2026-07-17 (see `frontend/css/style.css` comment above `.folder-search-label`), before this inventory was written. Fixed here and in `frontend/guide-library.html` during Stage 7.
- Search inside a Folder View tab replaces the current folder's grid with flat, depth-agnostic results across the whole tab's subtree, each showing its folder path; clearing the search returns to the folder level that was active before.
- A folder card stays visible under the Favourites/Flagged filters if anything anywhere underneath it matches, even if nothing at the folder's own root does.

---

## Admin — `/admin`

### Top action row
- Back — returns to the library.
- User Guide — navigates to `/guide` in the same tab (was `target="_blank"` until 2026-07-30, made consistent with the Admin/Editor links alongside it).
- Open Editor — navigates to `/editor` (Full Editor) in the same tab.
- Backup Database — triggers an immediate manual DB backup to the configured backup folder.
- Password Reset — opens a Change Password modal (current + new password); only functional once a password is already set.
- Forgot Password? — always-available info modal explaining the manual/local-disk-only recovery procedure (stop server, clear `admin_password_hash`/`admin_password_salt` in `config.json`, restart).
- Install App — hidden unless the browser fires `beforeinstallprompt` (site installable, not already installed); triggers the native PWA install prompt.

### Library Stats (always visible, top of page)
- Stat cards: Total Files, Series, Singles, Total Read (count + %), In Progress (status = reading).

### Library Scan (always visible, top of page)
- Stat cards: Last Scan (date), Files Found, New Files — each has its own "Logs" button opening a modal with that scan category's recent log entries; a green border appears on a card when its log has unread new entries since last opened.
- Scan Now (action card) — triggers a full library rescan; expands inline with a live progress bar and log output while running; reports an error count if any thumbnails failed to generate.

### Settings navigation
Category cards (Library Management, Library Appearance, Processing Tools, Editor Options, Advanced Settings) each expand a row of sub-item cards; picking a sub-item swaps the content pane below. Advanced Settings' sub-items additionally require the "Unlock" checkbox (next to the sub-item row) before their fields become editable.

#### Library Management
- **Auto Scan Settings** — frequency dropdown (Off/1hr/6hr/12hr/1day/3days/7days/1month) and a "Scan on launch" checkbox.
- **DB Backup Schedule** — backup destination folder (native OS picker, local sessions only), frequency dropdown (Off/day/week/month/6 months/year), Last Backup timestamp (with a red error line if the last scheduled attempt failed).
- **Restore DB** — pick a `.db` backup file (native picker) and Restore Database button; replaces the entire live database (including Custom Tabs/Home Strips) and restarts the server; takes an automatic pre-restore safety snapshot first. Local sessions only.
- **Access Logs** — logs folder path (with a Copy button) and a Log Size Limit (MB) input + Save.
- **Library Folders** — Scan Roots list (add/remove folders scanned into the library) and Exclude Patterns list (folder names/patterns skipped during scan, e.g. "Processing").

#### Library Appearance (no unlock gate)
- **Home Page Strips** — reorderable list (arrows) of all strips, defaults (Continue Reading/Recently Added/Random Unread/Random Genre) marked "Default" and movable only, not editable/deletable. Add Strip form: name, Field-basis (dropdown of 9 fields → live value dropdown) or Folder-basis (path input + Browse), Random/Fixed order (+ Title/Newest/Recent if Fixed); capped at 5 added strips.
- **Add/Remove Libraries** (internally "Custom Tabs") — list of all tabs (name, folder path, visible/hidden toggle, Delete with confirm). Add Tab form: name + folder path (Browse picker or manual text entry) + View mode (Flat/Folder View). Separate one-click "Add Genre Library" (dropdown of genres not already tabbed), "Add Favourites Library" (disables once one exists), "Add Reading Queue Library" (disables once one exists) buttons.
- **Theme Selection** — Match Windows / Light / Dark dropdown.
- **Card Size** — 30–100% dropdown, applies to every cover grid site-wide.
- **Pagination** — page-size dropdown (25/50/100/200/500); Home strips always show a fixed count regardless.

#### Editor Options (no unlock gate)
- **Genre List** — add/remove entries in the editors' enforced Genre dropdown/chip list; at least one value must remain; removing a value doesn't retag issues already using it.
- **Format List** — same, for the Format dropdown.

#### Advanced Settings (behind the Unlock checkbox)
- **Password Protection** — "Require a password" checkbox (setting it prompts for a new password + confirm in the same action); disabling requires re-entering the current password inline; "Allow Remote Administration" checkbox (only enable-able once password protection is on). A hint explains these can only be changed from a local (127.0.0.1) session.
- **Change Server Port** — numeric port input + Save & Restart (restarts the server, disconnects active users); Reader Location text field + Save Location (no functional effect currently, reserved).
- **Wipe Database** — Clear Database button (confirm dialog); permanently deletes all library data (issues, genres, credits, reading progress, orphaned People rows) but never touches Custom Tabs/Home Strips. Local sessions only.
- **Wipe Reading State** — Clear Reading Progress button (confirm dialog); deletes only read/unread/current-page data, keeps everything else. Local sessions only.

#### Processing Tools (local-sessions-only; greyed out remotely with an explanatory hint)
- **Filename Editor** — Browse/Clear All buttons, a loaded-files list, an edit panel (Series/Issue/Title/Year text fields each with independent File/All checkboxes), Auto-Increment Issue Numbers checkbox (enabled only when Issue→All is checked), Case style radios (No change/Title Case/ALL UPPER/all lower), Add to Queue button, a Queued Files preview list, Clear Preview and Apply Rename buttons. Renames any file type by parsed/edited filename fields; no library scan triggered; no undo — review the preview before applying.
- **Converter: Archives & Images** — two sub-tools sharing this pane:
  - **Convert Archives**: From CBR/From PDF radio (target is always CBZ), Browse/Clear Loaded Files, a loaded-file list, Run Conversion button, live progress bar. Keeps the original as a `.bak` only if some pages were skipped; a clean conversion deletes the `.bak`.
  - **Convert Images**: Lossless checkbox + quality slider (1–100, default 95), Browse/Clear Loaded Files, loaded-file list, Run Conversion, live progress. Converts CBZ/CBR images to WebP and repacks (CBR input always rebuilds as CBZ); same `.bak`-on-warning-only rule.
- **XML Tagging** — folder picker, "Save on Low Confidence" checkbox, Match Ratio Threshold slider (10–100%, default 80), ComicVine API Key field + "Save & Test" button (persists the key immediately, separately tests it against ComicVine and shows pass/fail), Run button, result summary + expandable error detail list. Matches files in a folder against ComicVine and writes matched metadata into ComicInfo.xml; settings here are shared with (not duplicated from) Auto Processing's CT Auto-Tag stage.
- **Folder Processing** — Script dropdown (Sort by Filename / Move Series Folders / Move Singles Folders), folder picker, Run button, result summary + detail list. Sort by Filename moves each loose CBZ/CBR directly under the chosen folder into its own same-named subfolder; the Move scripts move each immediate subfolder into its correct place in the library tree. No library scan triggered by any of these — manual "Scan Now" (or Auto Scan) still needed afterward.
- **Auto Processing** — Processing Folder picker; three enable checkboxes with inline sub-options: Convert Archives (From CBR/PDF radio), CT Auto-Tag ("Detailed settings in XML Tagging" note, no controls duplicated here), Convert Images (Lossless + quality slider); Schedule dropdown (Off/Daily/Weekly) + time picker + day-of-week dropdown (enabled only when relevant); Run Now button; next-scheduled-run hint text. Runs Convert Archives → CT Auto-Tag → Convert Images in that fixed order against one folder. File Rename is deliberately not part of this pipeline (its live-preview safety net doesn't survive unattended automation).

### Modals shared across Admin
- Scan log viewer (per scan-stat-card "Logs" button) — shows the most recent scan's entries only; full history is in the log file on disk.
- Choose Folder picker (Add/Remove Libraries, Home Strips) — breadcrumb + tree view, restricted to under a configured library root.
- Shared Processing Tools file/folder picker — breadcrumb + tree, Home/Up-one-level/Select All/Deselect All, not restricted to the library root (can browse any drive), no recursion (loads only the chosen folder's direct contents).
- Processing Tools result/summary modal — generic "X of Y" outcome + per-file error list, reused by Rename/Convert Archives/Convert Images.
- Change Password modal, Password Recovery modal (both described above).

---

## Basic Editor — modal, opened via "Edit XML" on `/issue/{id}`

- Tabs: Main, More.
- **Main tab**: Series Title, Issue Title, Issue Number, Year, Genre (multi-checkbox grid, required — at least one), Format (dropdown, required), Age Rating (dropdown, required), Black & White checkbox, Summary textarea.
- **More tab**: Count, Page Count, Writer, Penciller, Publisher, Story Arc, Language (free text with a datalist of common languages), Notes (defaults to "Modified with the CAPT" if blank).
- No Increment Number control (single-file scope only — that's Full Editor-only).
- Save button stays disabled until at least one Genre is checked and both Format and Age Rating are set (existing values that no longer match the enforced lists load blank and must be actively re-picked before saving).
- Save is asynchronous: the modal closes immediately after the XML is validated/merged, a toast shows "Saving in background…", then "Saved" (or a failure message) once the archive rebuild + library rescan finishes; a second save attempt on the same issue while one is still running is blocked with a 409/notice.
- On save, if the typed Writer/Penciller name is close to an existing credited person, a native confirm dialog offers to use the existing spelling instead (does not block the save either way).
- Cancel / × closes without saving; clicking outside the modal also closes it.

---

## Full Editor — `/editor`

Pre-library staging tool — operates on files not yet in the ComicVault database (or, via "Send to Full Editor" from the selection bar, on already-catalogued issues, which get an automatic rescan on save). Four-column layout + footer status bar.

### Header
- "</> XML Editor" brand label.
- Search ComicVine button — searches ComicVine for the currently-focused file's Series (required; Issue #/Year/Issue Count read along as filters, Title unused).
- Search GoodReads — plain external link to goodreads.com (no field wiring).
- Admin cog link, Login/Logout button.

### Column 1 — Load / Select Files
- Select Folder button — opens the Explorer picker (breadcrumb tree, Home/Up-one-level/Select All/Deselect All, no library-root restriction, no recursion — loads only a chosen folder's direct contents; multi-select within one folder).
- Clear button — clears the whole working set and resets the form.
- Library path display (currently loaded root).
- Expandable folder → series → issue tree of loaded files; issue rows show an "XML" badge when a ComicInfo.xml is present and a low-confidence (red border) indicator for `NeedsReview`-flagged files; natural-sorted (001 < 002 < 010).
- Up/Down arrow keys move keyboard focus through the tree (shared focus/load mechanic with mouse click — whichever moves focus loads that file into Columns 2/3).
- Stats: Files Found / With XML / Without XML.

### Column 2 — Edit ComicInfo.xml
- Same Main/More tab field set as the Basic Editor, plus:
  - Increment # checkbox next to Issue Number (auto-increment across the loaded list in display order — no "Apply to All" checkbox, it's the sole exception).
  - "Apply to All" checkbox next to every other field — only checked fields get bulk-applied by Process All; unchecked fields keep each file's own value.
  - Genre is removable chips + a "＋ Add genre" dropdown (not a checkbox grid, unlike Basic Editor).
- ＋ Queue button — adds the current file to the Edited Files Queue (Column 4) using its current form state.

### Column 3 — Comic Viewer
- Zoom in / Zoom out / Fit buttons, Prev/Next page with an "X / Y" counter, Fullscreen button.
- Click-drag pan when zoomed past 100%.
- Lazy page-thumbnail strip below the viewer, current page highlighted, click to jump.
- Cover auto-loads when a file is focused; other pages load on demand.

### Column 4 — Edited Files Queue
- "N files in queue" count, with a "⚠ counts differ" warning when the loaded-file count and queued count don't match (a completion check for a batch session).
- Per-file queue cards (✓ / filename / "Edited" / ✕ remove).
- Process Queue — writes XML to every queued file (this is the save action; no separate Save button); queue auto-empties on success.
- 🗑 Clear Queue — abandons the queue without processing.
- Process All — writes XML to every *loaded* file (bypassing the Queue), applying only the checked "Apply to All" fields batch-wide.
- All three buttons disabled until the Queue is non-empty (Process All is the exception — enabled once files are loaded).

### Footer status bar
- Selected file name, XML Status (Valid ✓ / warning if none or multiple ComicInfo.xml present), Low Confidence count, Queued count.

### Modals
- Multi-ComicInfo.xml resolution — shown when an archive contains more than one XML file; side-by-side read-only comparison, pick which to keep (others are deleted from the archive on save).
- Process All error summary — dismissible modal listing per-file failures when a batch save has errors.
- Search ComicVine — Select Series / Select Issue, one modal with two internal steps:
  - **Select Series**: sortable results table (Series/Year/Issues/Publisher; Best Match default, computed by fuzzy title-match + issue-count tiebreak — not a raw passthrough), cover preview + description, Cancel / Issues / Ok buttons (Ok fast-paths onto the first issue in the list).
  - **Select Issue**: natural-sorted issue list (Issue #/Date/Title), cover preview + description, "← Back to Series" (returns to cached results, no re-fetch), confirming applies the picked issue's metadata to the form (full overwrite, not a merge).

---

## Guide Placeholder — `/guide`

Currently a static placeholder page (pre-dates this guide-build project): a short paragraph on Browse/Read/Custom Tabs/Admin, and the same "Forgot your Admin password?" recovery text as the Admin modal. This page is what the rest of the `user-guide-plan.md` stages replace.

---

## Design tokens in use (for guide styling reuse — not a full CSS inventory)

- Colour: `--bg`, `--surface`, `--surface-2`, `--surface-3`, `--surface-card`, `--accent` (+`-hover`/`-press`/`-tint`/`-text`), `--text`, `--text-2`, `--text-3`, `--green`, `--blue`, `--danger` (+`-text`), `--border`, `--read-overlay` (+`-text`).
- Radius: `--radius`, `--radius-xs`, `--radius-md`, `--radius-lg`, `--radius-pill`.
- Spacing: `--space-0` through `--space-16` (4px scale).
- Type: `--font-sans` (Hanken Grotesk), `--font-mono` (JetBrains Mono), `--weight-regular` through `--weight-black`, `--text-2xs` through `--text-3xl`, `--leading-*`, `--tracking-*`.
- Layout: `--header-h` (56px), `--sidebar-w` (auto-sized, 140–320px), `--container-pad-x`, `--card-min`, `--control-md`.
- Shadow/effects: `--shadow-card`, `--shadow-pop`, `--focus-ring`, `--scrim`, `--pagebg-blur`, `--pagebg-blob-opacity`.
- Light/dark theme swap is driven by `document.documentElement.dataset.theme`, set from `localStorage.cv_theme` (`'auto'|'light'|'dark'`), applied via `tokens-dark.css`/`tokens-light.css` overriding `tokens-base.css`.

---

## [UNCLEAR — check source / live-verify] items

- ~~Full Editor Search ComicVine / Basic Editor fuzzy-credit confirm dialogs~~ —
  **resolved, Stage 8 (2026-07-26):** the fuzzy-credit dialog is a real native
  `confirm()`, identical wording in both editors (`editor_full.js`/
  `editor_basic.js`, `warnOnFuzzyCredits()`): `"{name}" is close to an existing
  {writer/artist}: "{closest_match.name}".\n\nOK = use "{closest_match.name}"
  instead\nCancel = save "{name}" as typed`. Search ComicVine itself has **no**
  confirm dialog at all — attempting a search with no Series value shows an
  inline `.editor-error` message ("Need to enter a series name to search."),
  not a native popup (`openSearchOnline()`, `editor_full.js`). Confirmed from
  source, consistent with how every other native-dialog entry in this
  inventory was resolved (native `confirm()` popups freeze Chrome automation,
  so these are always read from source rather than triggered live).
- **`comicvault://` Read link behaviour on a machine with no Flutter reader
  installed** — per source, nothing happens (browser's own "can't open this
  link" affordance). Still not independently verified live — the dev machine
  used for every Chrome-automation pass this project has run on on does have
  the reader registered, so the "not installed" case can't be reproduced from
  here regardless of automation health. Accepted as low-risk and left as-is;
  the guide already frames it as a heads-up ("if that app isn't installed...
  clicking Read won't do anything visible").
- ~~Live visual confirmation of card badge positions/colours~~ — **resolved,
  Stage 8 (2026-07-26):** the browser-automation viewport issue that blocked
  this during Stage 1 didn't recur in later sessions. Confirmed via live
  screenshots (Library/All grid, an issue detail page) during Stage 7's
  tooltip-verification pass — cover cards, badges, and the issue-page layout
  all render as this document already described.
- ~~Exact wording of native `confirm()` dialogs~~ — resolved by reading `admin.js` directly (not opened live, since native `confirm()` popups freeze Chrome automation — per this project's standing working notes): Restart Server → "This will restart the server and disconnect active users. Continue?"; Restore Database → "Restore database from "{filename}"? This replaces your ENTIRE database — including Custom Tabs and Home Page Strips — and restarts the server. A safety snapshot is taken first."; Clear Reading Progress → "Clear all reading progress? This resets every issue to unread and erases all saved page positions for your entire library. Issue metadata and comic files are not affected."; Clear Database → "Clear the entire database? This permanently deletes all issues, genres, credits, and reading progress — your whole library record — and also removes cached thumbnails. Comic files on disk and Custom Tabs/Home Strips are not affected."; Custom Tab Delete → "Delete tab "{name}"? This only removes the tab definition — it will not touch any comic files or library data."; Home Strip Delete → same wording, "strip" in place of "tab"; Genre/Format List delete-while-in-use → "\"{name}\" is used by N issue(s) — remove it from the {Genre/Format} list anyway? Existing issues keep their current value; this only removes \"{name}\" from future selection."
