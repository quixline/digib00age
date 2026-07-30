# Tooltip Data

> Source for Stage 7 implementation. Do not modify without updating Stage 7.
> Written from `docs/guide-inventory.md` per `ux-copy` skill guidance (Stage 2 of
> `docs/user-guide-plan.md`).
>
> **Stage 7 verification pass (2026-07-26):** every selector hint below has been
> checked against the live DOM/source and corrected where wrong — almost none of
> the original guessed selectors matched the real class/id names. The
> "Verified" column reflects final implementation state, not the original guess.
> Two features described in the original inventory (Folder View's "← Back" and
> "Mark all read") turned out not to exist at all — removed from the app on
> 2026-07-17, before Stage 1's inventory pass ran. Fixed in
> `docs/guide-inventory.md` and `frontend/guide-library.html` too.

## Global Chrome — every page

### Site header

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Sidebar toggle (☰) | `#sidebarToggleBtn` | Show or hide the sidebar | ✓ wired (index/series/issue.html) |
| Admin/Settings gear icon | `.settings-btn` | Open admin settings | ✓ wired (index/series/issue/editor_full.html); dynamic via `auth.js` |
| Admin/Settings gear icon, disabled state (remote session, Remote Administration off) | `.settings-btn--disabled` | Admin access is off for remote sessions | ✓ wired — `auth.js`'s `checkAuthStatus()` sets `dataset.tooltip` alongside the existing class toggle |

### Left sidebar (`#appSidebar`)

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Home nav icon | `.app-sidebar-item[data-surface="home"]` | Go to the home page | ✓ wired; also added `aria-label` (was lost when sidebar is collapsed — label span gets `display:none`) |
| All nav icon | `.app-sidebar-item[data-surface="all"]` | Browse all issues and series | ✓ wired + aria-label |
| Singles nav icon | `.app-sidebar-item[data-surface="singles"]` | Browse single-issue titles | ✓ wired + aria-label |
| Series nav icon | `.app-sidebar-item[data-surface="series"]` | Browse multi-issue series | ✓ wired + aria-label |
| Unread shortcut | `.app-sidebar-item[data-quick-status="unread"]` | Show unread issues in the All view | ✓ wired + aria-label |
| Reading shortcut | `.app-sidebar-item[data-quick-status="reading"]` | Show in-progress issues in the All view | ✓ wired + aria-label |
| Read shortcut | `.app-sidebar-item[data-quick-status="read"]` | Show finished issues in the All view | ✓ wired + aria-label |
| Libraries entry (custom tab), collapsed single-letter badge | `.app-sidebar-item[data-tab-surface]` | `Open ${tab.name}` (dynamic) | ✓ wired in `app.js` `loadCustomTabsNav()`, replacing the old plain `title = tab.name` |

### Menu bar (`#menuBar`, index.html only — not present on series/issue.html)

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Ascending/Descending toggle | `#sortDirBtn` | Reverse the sort order | ✓ wired |
| Grid/List view toggle | `#viewToggle` | **One button, not two** — dynamic: "Switch to list layout" / "Switch to grid layout" depending on current mode | ✓ wired in `app.js`, updates on click and on init |
| Favourites filter toggle | `#favFilterBtn` | Show only favourited items | ✓ wired |
| Flagged filter toggle | `#flagReviewFilterBtn` | Show only issues flagged for review | ✓ wired |
| Clear Filter pill | `#filterClear` | Reset every active filter, sort, search and grouping | ✓ wired |

### Selection bar (built dynamically in `app.js`'s `ensureSelectionToolbar()` — appended to `document.body`, same on every page)

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| ★ Favorite | `#selFavorite` | Favourite selected items, or un-favourite if all already are | ✓ wired |
| 📖 Queue Reading | `#selQueueReading` | Add selected to Reading Queue, or remove if already queued | ✓ wired |
| 🏷 Flag for Review | `#selFlagReview` | Flag selected for review, or unflag if already flagged | ✓ wired |
| → Send to Full Editor | `#selSendToFullEditor` | Open selected issues in Full Editor for XML editing | ✓ wired |
| Star rating row — ✕ clear | `.rating-clear` (inside `.selection-rate`) | Clear rating for all selected items | ✓ wired |
| Star rating row — ★1–★5 | `.selection-rate .rating-star[data-value]` | Set rating for selected items; click again to clear | ✓ wired — also added `dataset.value` (wasn't set before, for consistency with the issue-page rating control) |
| 🗑 Delete | `#selDelete` | Permanently deletes selected files and their data — no going back | ✓ wired |
| Deselect | `#selDeselect` | Clear selection but stay in selection mode | ✓ wired |
| Done | `#selDone` | Exit selection mode | ✓ wired |

**Deliberately skipped (self-labelled/unambiguous):** Logo/wordmark, Search bar, Login/Logout button, "Admin" label text, Sort dropdown, Rated filter dropdown, Group by dropdown, Genre/Format/Decade/Year/Rating/B&W filter dropdowns, Title/item count, Fieldview banner's Clear link, Mark Read / Mark Unread bulk buttons (`#selMarkRead`/`#selMarkUnread`).

---

## Library Home — `/` (surface=home)

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Strip scroll arrow — left | `.strip-arrow.strip-arrow--left` | Scroll left | ✓ wired (also has matching `aria-label`, pre-existing) |
| Strip scroll arrow — right | `.strip-arrow.strip-arrow--right` | Scroll right | ✓ wired |
| Admin-added strip heading (clickable) | `.section-label.section-label--link` | View the full filtered list | ✓ wired |

**Deliberately skipped:** Retry button (self-labelled), genre ribbon link on strip cards (destination obvious from text), default strip headings (not clickable, plain text), favourite/flag/read-state/progress badges on cards (informational, not interactive).

---

## Library Browse — Series / Singles / All — `/?surface=series|singles|all`

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Hover-reveal select-dot (grid card, top-left) | `.select-dot` | Select this item | ✓ wired (had `aria-label="Select"` already) |

**Deliberately skipped:** Fieldview/Folderview banner Clear link (obvious from text), pagination controls (no icon-only element described).

---

## Series Page — `/series/{id}`

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| "Mark all read" button (hero) | `#markAllBtn` | Mark every unread issue in this series as read | ✓ wired |
| Status button (○ unread / ▶ reading / ✓ read) per issue row | `.status-btn` | Toggle read/unread status | ✓ wired — replaced the old dynamic `title = "Status: ${status}"` (three call sites) with one static tooltip |

**Deliberately skipped:** Back link, "View full series" link (both obvious from link text/label).

---

## Issue Detail Page — `/issue/{id}`

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Cover art (links to `comicvault://read/{id}`) | `.issue-cover-link` | Opens in the digib00age reader app, if installed | ✓ wired |
| Star rating control | `.rating-control .rating-star[data-value]` | Rate this issue 1–5 stars; click again to clear | ✓ wired |
| Edit XML button | `.btn-edit-xml` | Edit this issue's metadata (title, genre, credits, etc) | ✓ wired |
| Format badge, multi-issue series | `.format-badge` (links to `/series/{id}`) | Go to this issue's series | ✓ wired — conditional, both branches set from the same `linksToSeries` check that decides the `href` |
| Format badge, single issue | `.format-badge` (links to fieldview filter) | Browse other issues in this format | ✓ wired |
| Prev/Next issue nav | `.nav-issue-btn.nav-prev` / `.nav-issue-btn.nav-next` | — | **Skipped** — both already carry visible "← Previous"/"Next →" text; judged genuinely self-labelled on review, unlike the original Stage 2 call |

**Deliberately skipped:** Start Reading/Continue Reading/Read Again button, Mark as Read/✓ Read toggle, ☆ Favourites toggle, 📖 Reading Queue toggle, Flag toggle (all self-labelled with state-reflecting text), B&W badge (not interactive), Writer/Artist credit links (destination obvious).

---

## Folder View — a Custom Tab set to "Folder View" mode

**Correction, Stage 7 (2026-07-26):** this section's only entry (a folder-level
"Mark all read" button) and its "Deliberately skipped" Back button both described
a back-nav/mark-all-read row that was removed from Folder View on 2026-07-17 —
before Stage 1's inventory pass ran. Neither element exists in the current DOM.
Fixed in `docs/guide-inventory.md` and `frontend/guide-library.html` too. No
tooltip-worthy controls remain in Folder View beyond what Global Chrome already
covers (folder/file cards are plain click-throughs, not ambiguous).

---

## Admin — `/admin`

### Top action row

No tooltips written — every control here is a self-labelled text button/link (Back, User Guide, Open Editor, Backup Database, Password Reset, Forgot Password?, Install App) whose action is already clear from its visible label.

### Library Scan

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Per-card "Logs" button | `.log-btn[data-log]` | View recent log entries for this scan category | ✓ wired (both the field-card and Missing Records-card instances, `admin.js`) |
| Scan Now | `#scanNowBtn` | Scan the entire library for new and changed files | ✓ wired |

### Settings navigation

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Unlock checkbox (Advanced Settings gate) | `#advancedLockWrap` (label) | Unlock these fields for editing | ✓ wired |

### Library Management

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Restore Database button | `#restoreBtn` | Replaces your entire database, including Custom Tabs and Home Strips, and restarts the server | ✓ wired |
| Access Logs — Copy button | `#copyLogsPathBtn` | Copy the logs folder path | ✓ wired |
| Scan Roots / Exclude Patterns — remove | `.folder-remove-btn` (`makeFolderRow()`, `admin.js`) | — | **Resolved, no tooltip needed** — confirmed live: it's a plain text "Remove" button, not icon-only as the `[NEEDS VERIFICATION]` flag guessed. Self-labelled, skipped per the ux-copy rule. |

### Library Appearance

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Home Page Strips reorder — move up | `.hs-arrow-btn` (▲, `makeHomeStripRow()`) | Move this strip up | ✓ wired |
| Home Page Strips reorder — move down | `.hs-arrow-btn` (▼) | Move this strip down | ✓ wired |
| Default strip row (Continue Reading/Recently Added/Random Unread/Random Genre) | the "Default" `.ct-hidden-badge` inside `makeHomeStripRow()` | Default strips can be reordered but not edited or removed | ✓ wired on the badge itself (no dedicated row-level class exists — it's the same `.ct-tab-row` markup, just missing the toggle/delete buttons) |
| Library visible/hidden toggle | `.ct-visible-toggle` (`makeCustomTabRow()`) | Show or hide this library in the sidebar | ✓ wired |
| Library Delete (with confirm) | `.folder-remove-btn` inside `makeCustomTabRow()` (same class as the Scan Roots remove button, but a distinct element/instance) | Removes this tab definition only — comic files and library data are untouched | ✓ wired directly on this specific button instance in JS, not via the shared class |

**Deliberately skipped:** Add Strip form fields (Field/Folder-basis, Random/Fixed order), Theme Selection dropdown, Card Size dropdown, Pagination dropdown, "Add Genre/Favourites/Reading Queue Library" buttons (self-labelled), Home Strip's own per-strip Delete button (not in original Stage 2 list; "Visible"/"Hidden" toggle explained above but Delete here judged low-ambiguity enough to leave alone).

### Editor Options

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Genre/Format List — remove entry | `.folder-remove-btn` inside `renderEditableValueList()` | Remove from the list — issues keep their current value (or "At least one value must remain" when disabled) | ✓ wired — dynamic, mirrors the pre-existing conditional `title` |

### Advanced Settings

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| "Allow Remote Administration" checkbox | `#authRemoteLabel` (label) | Let non-local devices access Admin (requires a password) | ✓ wired |
| Change Server Port — Save & Restart | `#savePortBtn` | Restarts the server and disconnects active users | ✓ wired |
| Reader Location — Save Location | `#saveAdvancedBtn` | Reserved for future use — has no effect yet | ✓ wired |
| Wipe Database — Clear Database button | `#clearDbBtn` | Permanently deletes all issues, genres, credits and reading progress — not files or tabs | ✓ wired |
| Wipe Reading State — Clear Reading Progress button | `#clearProgressBtn` | Resets every issue to unread and erases saved page positions | ✓ wired |

**Deliberately skipped:** "Require a password" checkbox (self-labelled).

### Processing Tools

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Filename Editor — per-field "File" checkbox ×4 | `#renameSeriesFile` / `#renameIssueFile` / `#renameTitleFile` / `#renameYearFile` | Apply this edit only to the current file | ✓ wired |
| Filename Editor — per-field "All" checkbox ×4 | `#renameSeriesAll` / `#renameIssueAll` / `#renameTitleAll` / `#renameYearAll` | Apply this edit to every loaded file, not just this one | ✓ wired |
| Filename Editor — Auto-Increment Issue Numbers checkbox | `#renameAutoIncrement` | Increase each file's issue number by one, in list order | ✓ wired — note: this checkbox is `disabled` until Issue→All is checked, and a disabled control doesn't fire hover events in Chromium, so the tooltip is inert until enabled. Left as-is since the row already has inline text explaining the disabled condition. |
| Filename Editor — Apply Rename button | `#renameApplyBtn` | Renames all queued files on disk — no undo, review first | ✓ wired |
| Convert Archives — Run Conversion | `#convertRunBtn` | Converts loaded files to CBZ; keeps a .bak only if pages were skipped | ✓ wired |
| Convert Images — Lossless checkbox | `#convertImagesLossless` | Preserve full image quality (larger file size) | ✓ wired |
| Convert Images — quality slider | `#convertImagesQuality` | Compression quality, 1–100 — higher keeps more detail | ✓ wired |
| Convert Images — Run Conversion | `#convertImagesRunBtn` | Converts images to WebP and repacks the archive | ✓ wired |
| XML Tagging — "Save on Low Confidence" checkbox | `#pfCtSaveLowConfidence` | Tag files even when the ComicVine match confidence is low | ✓ wired |
| XML Tagging — Match Ratio Threshold slider | `#pfCtMatchThreshold` | Minimum match confidence required to accept a ComicVine tag | ✓ wired |
| XML Tagging — "Save & Test" (API key) | `#pfComicVineKeyTestBtn` | Save the API key and verify it works with ComicVine | ✓ wired |
| XML Tagging — Run button | `#xtRunBtn` | Match files against ComicVine and write tags to ComicInfo.xml | ✓ wired |
| Folder Processing — Script dropdown options (Sort by Filename / Move Series / Move Singles) | `<option>` inside `#fsScriptSelect` | — | **Not implementable** — native `<select>` dropdown options are rendered by the OS, not in the page's hoverable DOM; a custom JS tooltip can't attach to them while the list is open. This content already lives in the admin-card-hint text above the control and in `guide-admin.html`. |
| Folder Processing — Run button | `#fsRunBtn` | Run the selected script — scan the library afterward to see changes | ✓ wired |
| Auto Processing — Run Now button | `#pfRunNowBtn` | Run enabled steps now: Convert Archives → CT Auto-Tag → Convert Images | ✓ wired |

**Deliberately skipped:** Browse/Clear All buttons, Case style radios, Add to Queue, Clear Preview, From CBR/From PDF radio, Convert Archives/CT Auto-Tag/Convert Images enable checkboxes (self-labelled), Schedule dropdown + time/day pickers.

### Modals shared across Admin

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Custom Tab / Home Strip folder picker (`#ctPickerOverlay`) — Home/Up buttons | — | — | **Does not exist** — corrected. This picker (`admin.js`'s `loadCtPickerDir`/`renderCtPickerRoots`) navigates only via breadcrumb links and drive-letter root buttons (both self-labelled), no dedicated Home/Up control. Original inventory row was wrong. |
| Shared Processing Tools picker — Home button | `#ptPickerHomeBtn` | Go to the starting folder | ✓ wired |
| Shared Processing Tools picker — Up One Level button | `#ptPickerUpBtn` | Go up one folder level (this picker can browse any drive) | ✓ wired |
| Full Editor's own file picker (`#fePickerOverlay`) — Home button | `#fePickerHomeBtn` | Go to the starting folder | ✓ wired (bonus — same shared picker pattern, not in the original inventory but caught during Stage 7) |
| Full Editor's own file picker — Up One Level button | `#fePickerUpBtn` | Go up one folder level (this picker can browse any drive) | ✓ wired |

**Deliberately skipped:** Select All/Deselect All (self-labelled).

---

## Basic Editor — modal, opened via "Edit XML" on `/issue/{id}` (fetched from `/static/editor_basic.html`)

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Save button (disabled state) | `#editorSaveWrap` (wrapping `<span>` around `#editorSaveBtn`) | Save is enabled once a genre, format and age rating are set | ✓ wired — **had to wrap the button**: a native `disabled` button doesn't fire `mouseover` in Chromium, so a tooltip on the button itself would never show while disabled. `updateSaveButtonState()` sets/clears the wrap's `data-tooltip` alongside the existing disabled toggle; cleared entirely once enabled. |
| Close (×) | `#editorCloseBtn` | Close without saving | ✓ wired |

**Deliberately skipped:** Main/More tabs, Genre checkbox grid, Cancel button (self-labelled), Notes field default text (not interactive).

---

## Full Editor — `/editor`

### Header

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Search ComicVine button | `#feSearchOnlineBtn` | Search ComicVine using this file's Series, Issue #, Year | ✓ wired |
| Search GoodReads link | (plain `<a href="https://www.goodreads.com">`, no id) | Opens goodreads.com — does not search using this file's data | ✓ wired |

### Column 1 — Load / Select Files

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Select Folder button | `#feSelectFolderBtn` | Load files from one folder only — subfolders aren't included | ✓ wired |
| Clear button | `#feClearListBtn` | Clear all loaded files and reset the form | ✓ wired |

### Column 2 — Edit ComicInfo.xml

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Increment # checkbox | `#fe-increment` | Increase issue number by one for each file, in list order | ✓ wired |
| "Apply to All" checkbox (per field, ×14) | `.fe-apply-all[data-field]` | Include this field when Process All runs on every loaded file (Count/PageCount get a field-specific variant) | ✓ wired — replaced the pre-existing generic `title="Apply to all"` on all 14 |
| Genre chip — remove (✕) | `.fe-genre-chip-x` | Remove this genre | ✓ wired |
| ＋ Queue button | `#feQueueBtn` (tooltip on parent `.fe-panel-foot`) | Add this file to the queue with its current edits | ✓ wired |

### Column 3 — Comic Viewer

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Zoom in / Zoom out / Fit / Prev page / Next page / Fullscreen / thumb-strip prev-next | `#feZoomInBtn` / `#feZoomOutBtn` / `#feFitBtn` / `#fePrevBtn` / `#feNextBtn` / `#feFullscreenBtn` / `#feThumbPrev` / `#feThumbNext` | — | **Deliberately left as native `title`** — all eight already carry an accurate native `title` and start `disabled` (no file loaded); converting to `data-tooltip` would make them silently stop showing anything while disabled, a real regression versus the current native-tooltip behaviour, for a purely cosmetic style win. Not worth the trade. |

### Column 4 — Edited Files Queue

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| ✕ remove (per queue card) | `.fe-queue-remove` | Remove this file from the queue | ✓ wired |
| Process Queue button | `.fe-queue-action-wrap` around `#feProcessQueueBtn` | Save XML to every queued file — this is the save action | ✓ wired — wrapped (same disabled-hover reason as the Basic Editor Save button); new `.fe-queue-action-wrap` CSS class added to keep the 3-button equal-width flex layout intact |
| 🗑 Clear Queue button | `.fe-queue-action-wrap` around `#feClearQueueBtn` | Empty the queue without saving any changes | ✓ wired |
| Process All button | `.fe-queue-action-wrap` around `#feProcessAllBtn` | Save checked fields to every loaded file, bypassing the queue | ✓ wired |

### Modals

| Element description | Real selector | Tooltip text | Verified |
|---|---|---|---|
| Multi-ComicInfo.xml resolution — keep-this-one action | "Keep this one" `<button class="btn-primary">` inside `feMultiXmlCandidates` (no unique class; tooltip set directly on the created element) | Keep this ComicInfo.xml and delete the other(s) from the archive | ✓ wired |
| Search ComicVine — "Ok" (Select Series step) | `#feSoOkBtn` | Use the top match and skip straight to its issue list | ✓ wired |
| Search ComicVine — confirm issue (Select Issue step) | `<tr>` rows in `#feSoIssueTbody` | Double-click to apply this issue's data, overwriting all current fields | ✓ wired — **corrected**: there is no dedicated confirm button for this step (only the Series step has one); confirming is a double-click on the row, which the tooltip now surfaces since that gesture isn't otherwise discoverable |

**Deliberately skipped:** Page-thumbnail strip, footer status bar (informational), "Issues"/Cancel buttons (self-labelled), "← Back to Series" link (destination obvious).

---

## Guide Placeholder — `/guide`, `/guide/library`, `/guide/admin`, `/guide/editor*`

No tooltip-worthy controls — these are content pages (prose, nav links, anchors),
not interactive controls in the sense this system targets. `tooltip.js` isn't
loaded on guide pages.

---

## Implementation notes (Stage 7)

- **System**: `frontend/js/tooltip.js` — single delegated listener on
  `document.body`, ~500ms show delay, flips below the anchor if there's no room
  above, dismissed on scroll/resize/Escape, skipped entirely after a touch
  pointerdown. Styled via `.db-tooltip` in `frontend/css/style.css` (tokens-based,
  matches the existing `.admin-toast` visual language).
- **Convention**: `data-tooltip="..."` on the element to be hovered (or an
  ancestor — delegation uses `closest('[data-tooltip]')`).
- **Disabled buttons don't fire hover events in Chromium.** Three spots needed a
  wrapping `<span data-tooltip="...">` around the real (sometimes-disabled)
  button rather than the attribute living on the button directly: Basic Editor's
  Save button (`#editorSaveWrap`), and Full Editor's three queue-action buttons
  (`.fe-queue-action-wrap`). Full Editor's eight viewer/thumb-strip controls hit
  the same issue but were left on native `title` instead, since that already
  worked correctly and converting would have been a net regression for a purely
  cosmetic gain.
- **Old native `title` attributes were replaced, not layered on top of** —
  everywhere a `data-tooltip` was added to an element that already had a
  `title` doing the same job, the `title` was removed so only one tooltip shows.
  Icon-only controls that lost their `title` and had no other accessible name
  (the four sidebar-icon buttons, quick-status shortcuts, custom-tab entries)
  got an explicit `aria-label` added at the same time so screen readers and the
  collapsed-sidebar icon-only state aren't worse off.
- **Loaded on**: `index.html`, `series.html`, `issue.html`, `admin.html`,
  `editor_full.html`. Not loaded on guide pages (nothing to tooltip) or
  `editor_basic.html` (fragment, fetched into `issue.html` which already has it).
