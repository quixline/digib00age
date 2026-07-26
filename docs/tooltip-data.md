# Tooltip Data

> Source for Stage 7 implementation. Do not modify without updating Stage 7.
> Written from `docs/guide-inventory.md` per `ux-copy` skill guidance (Stage 2 of `docs/user-guide-plan.md`).

## Global Chrome — every page

### Site header

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Sidebar toggle (☰) | `.sidebar-toggle` | Show or hide the sidebar |
| Admin/Settings gear icon | `.settings-btn` | Open admin settings |
| Admin/Settings gear icon, disabled state (remote session, Remote Administration off) | `.settings-btn--disabled` | Admin access is off for remote sessions |

### Left sidebar

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Home nav icon (collapsed) | `.nav-item[data-nav="home"]` | Go to the home page |
| All nav icon (collapsed) | `.nav-item[data-nav="all"]` | Browse all issues and series |
| Singles nav icon (collapsed) | `.nav-item[data-nav="singles"]` | Browse single-issue titles |
| Series nav icon (collapsed) | `.nav-item[data-nav="series"]` | Browse multi-issue series |
| Unread shortcut | `.nav-shortcut[data-status="unread"]` | Show unread issues in the All view |
| Reading shortcut | `.nav-shortcut[data-status="reading"]` | Show in-progress issues in the All view |
| Read shortcut | `.nav-shortcut[data-status="read"]` | Show finished issues in the All view |
| Libraries entry, collapsed (single-letter badge) | `.sidebar-library-item` | Open this library — badge shows its first letter |

### Menu bar (`#menuBar`)

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Ascending/Descending toggle (↑/↓) | `.sort-direction-toggle` | Reverse the sort order |
| Grid view icon | `.view-toggle[data-mode="grid"]` | Show items in a grid |
| List view icon | `.view-toggle[data-mode="list"]` | Show items as a list |
| Favourites filter toggle (★ Favourites) | `.filter-favourites` | Show only favourited items |
| Flagged filter toggle (🏳 Flagged) | `.filter-flagged` | Show only issues flagged for review |
| Clear Filter pill | `.clear-filter-pill` | Reset every active filter, sort, search and grouping |

### Selection bar (`#selectionToolbar`)

| Element description | Selector hint | Tooltip text |
|---|---|---|
| ★ Favorite | `.sel-action[data-action="favorite"]` | Favourite selected items, or un-favourite if all already are |
| 📖 Queue Reading | `.sel-action[data-action="queue"]` | Add selected to Reading Queue, or remove if already queued |
| 🏷 Flag for Review | `.sel-action[data-action="flag"]` | Flag selected for review, or unflag if already flagged |
| → Send to Full Editor | `.sel-action[data-action="send-editor"]` | Open selected issues in Full Editor for XML editing |
| Star rating row — ✕ clear | `.sel-rating-clear` | Clear rating for all selected items |
| Star rating row — ★1–★5 | `.sel-rating[data-value]` | Set rating for selected items; click again to clear |
| 🗑 Delete | `.sel-action[data-action="delete"]` | Permanently deletes selected files and their data — no going back |
| Deselect | `.sel-action[data-action="deselect"]` | Clear selection but stay in selection mode |
| Done | `.sel-action[data-action="done"]` | Exit selection mode |

**Deliberately skipped (self-labelled/unambiguous):** Logo/wordmark, Search bar, Login/Logout button, "Admin" label text, Sort dropdown, Rated filter dropdown, Group by dropdown, Genre/Format/Decade/Year/Rating/B&W filter dropdowns, Title/item count, Fieldview banner's Clear link, Mark Read / Mark Unread bulk buttons.

---

## Library Home — `/` (surface=home)

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Strip scroll arrow — left | `.strip-scroll[data-dir="left"]` | Scroll left |
| Strip scroll arrow — right | `.strip-scroll[data-dir="right"]` | Scroll right |
| Admin-added strip heading (clickable) | `.strip-heading[data-clickable="true"]` | View the full filtered list |

**Deliberately skipped:** Retry button (self-labelled), genre ribbon link on strip cards (destination obvious from text), default strip headings (not clickable, plain text), favourite/flag/read-state/progress badges on cards (informational, not interactive).

---

## Library Browse — Series / Singles / All — `/?surface=series|singles|all`

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Hover-reveal select-dot (grid card, top-left) | `.card-select-dot` | Select this item |

**Deliberately skipped:** Fieldview/Folderview banner Clear link (obvious from text), pagination controls (no icon-only element described).

---

## Series Page — `/series/{id}`

| Element description | Selector hint | Tooltip text |
|---|---|---|
| "Mark all read" button (hero) | `.series-mark-all-read` | Mark every unread issue in this series as read |
| Status button (○ unread / ▶ reading / ✓ read) per issue row | `.issue-status-btn` | Toggle read/unread status |

**Deliberately skipped:** Back link, "View full series" link (both obvious from link text/label).

---

## Issue Detail Page — `/issue/{id}`

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Cover art (links to `comicvault://read/{id}`) | `.issue-cover-link` | Opens in the digib00age reader app, if installed |
| Star rating control | `.issue-rating-stars` | Rate this issue 1–5 stars; click again to clear |
| Edit XML button | `.edit-xml-btn` | Edit this issue's metadata (title, genre, credits, etc) |
| Format badge, multi-issue series | `.format-badge[data-links-to="series"]` | Go to this issue's series |
| Format badge, single issue | `.format-badge[data-links-to="format"]` | Browse other issues in this format |
| Prev issue nav | `.issue-nav[data-dir="prev"]` | Go to the previous issue |
| Next issue nav | `.issue-nav[data-dir="next"]` | Go to the next issue |

**Deliberately skipped:** Start Reading/Continue Reading/Read Again button, Mark as Read/✓ Read toggle, ☆ Favourites toggle, 📖 Reading Queue toggle, Flag toggle (all self-labelled with state-reflecting text), B&W badge (not interactive), Writer/Artist credit links (destination obvious).

---

## Folder View — a Custom Tab set to "Folder View" mode

| Element description | Selector hint | Tooltip text |
|---|---|---|
| "Mark all read" at a folder level | `.folder-mark-all-read` | Mark every issue in this folder and its subfolders as read |

**Deliberately skipped:** "← Back" button (self-labelled), folder card click-through (not ambiguous).

---

## Admin — `/admin`

### Top action row

No tooltips written — every control here is a self-labelled text button/link (Back, User Guide, Open Editor, Backup Database, Password Reset, Forgot Password?, Donate, Install App) whose action is already clear from its visible label.

### Library Scan

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Per-card "Logs" button (Last Scan / Files Found / New Files) | `.scan-stat-logs-btn` | View recent log entries for this scan category |
| Scan Now | `.scan-now-btn` | Scan the entire library for new and changed files |

### Settings navigation

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Unlock checkbox (Advanced Settings gate) | `.advanced-unlock-checkbox` | Unlock these fields for editing |

### Library Management

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Restore Database button | `.restore-db-btn` | Replaces your entire database, including Custom Tabs and Home Strips, and restarts the server |
| Access Logs — Copy button | `.access-logs-copy-btn` | Copy the logs folder path |
| Scan Roots — remove folder `[NEEDS VERIFICATION: confirm this is an icon-only control, not a text button]` | `.scan-root-remove-btn` | Stop scanning this folder |
| Exclude Patterns — remove pattern `[NEEDS VERIFICATION: confirm this is an icon-only control, not a text button]` | `.exclude-pattern-remove-btn` | Stop excluding this pattern from scans |

**Deliberately skipped:** Auto Scan Settings frequency dropdown + "Scan on launch" checkbox, DB Backup Schedule fields.

### Library Appearance

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Home Page Strips reorder — move up | `.strip-reorder[data-dir="up"]` | Move this strip up |
| Home Page Strips reorder — move down | `.strip-reorder[data-dir="down"]` | Move this strip down |
| Default strip row (Continue Reading/Recently Added/Random Unread/Random Genre) | `.strip-row--default` | Default strips can be reordered but not edited or removed |
| Library visible/hidden toggle | `.library-visibility-toggle` | Show or hide this library in the sidebar |
| Library Delete (with confirm) | `.library-delete-btn` | Removes this tab definition only — comic files and library data are untouched |

**Deliberately skipped:** Add Strip form fields (Field/Folder-basis, Random/Fixed order), Theme Selection dropdown, Card Size dropdown, Pagination dropdown, "Add Genre/Favourites/Reading Queue Library" buttons (self-labelled).

### Editor Options

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Genre/Format List — remove entry | `.list-entry-remove-btn` | Remove from the list — issues keep their current value |

### Advanced Settings

| Element description | Selector hint | Tooltip text |
|---|---|---|
| "Allow Remote Administration" checkbox | `.allow-remote-admin-checkbox` | Let non-local devices access Admin (requires a password) |
| Change Server Port — Save & Restart | `.save-port-restart-btn` | Restarts the server and disconnects active users |
| Reader Location — Save Location | `.save-reader-location-btn` | Reserved for future use — has no effect yet |
| Wipe Database — Clear Database button | `.wipe-database-btn` | Permanently deletes all issues, genres, credits and reading progress — not files or tabs |
| Wipe Reading State — Clear Reading Progress button | `.wipe-reading-state-btn` | Resets every issue to unread and erases saved page positions |

**Deliberately skipped:** "Require a password" checkbox (self-labelled).

### Processing Tools

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Filename Editor — "All" checkbox per field | `.filename-field-all-checkbox` | Apply this edit to every loaded file, not just this one |
| Filename Editor — "File" checkbox per field | `.filename-field-file-checkbox` | Apply this edit only to the current file |
| Filename Editor — Auto-Increment Issue Numbers checkbox | `.filename-auto-increment-checkbox` | Increase each file's issue number by one, in list order |
| Filename Editor — Apply Rename button | `.filename-apply-rename-btn` | Renames all queued files on disk — no undo, review first |
| Convert Archives — Run Conversion | `.convert-archives-run-btn` | Converts loaded files to CBZ; keeps a .bak only if pages were skipped |
| Convert Images — Lossless checkbox | `.convert-images-lossless-checkbox` | Preserve full image quality (larger file size) |
| Convert Images — quality slider | `.convert-images-quality-slider` | Compression quality, 1–100 — higher keeps more detail |
| Convert Images — Run Conversion | `.convert-images-run-btn` | Converts images to WebP and repacks the archive |
| XML Tagging — "Save on Low Confidence" checkbox | `.xml-tagging-low-confidence-checkbox` | Tag files even when the ComicVine match confidence is low |
| XML Tagging — Match Ratio Threshold slider | `.xml-tagging-threshold-slider` | Minimum match confidence required to accept a ComicVine tag |
| XML Tagging — "Save & Test" (API key) | `.xml-tagging-save-test-btn` | Save the API key and verify it works with ComicVine |
| XML Tagging — Run button | `.xml-tagging-run-btn` | Match files against ComicVine and write tags to ComicInfo.xml |
| Folder Processing — "Sort by Filename" option | `.folder-script-option[value="sort-by-filename"]` | Move each loose comic into its own same-named subfolder |
| Folder Processing — "Move Series Folders" option | `.folder-script-option[value="move-series"]` | Move each subfolder into its correct place for multi-issue series |
| Folder Processing — "Move Singles Folders" option | `.folder-script-option[value="move-singles"]` | Move each subfolder into its correct place for single issues |
| Folder Processing — Run button | `.folder-processing-run-btn` | Run the selected script — scan the library afterward to see changes |
| Auto Processing — Run Now button | `.auto-processing-run-now-btn` | Run enabled steps now: Convert Archives → CT Auto-Tag → Convert Images |

**Deliberately skipped:** Browse/Clear All buttons, Case style radios, Add to Queue, Clear Preview, From CBR/From PDF radio, Convert Archives/CT Auto-Tag/Convert Images enable checkboxes (self-labelled), Schedule dropdown + time/day pickers.

### Modals shared across Admin

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Folder picker — Home button | `.picker-home-btn` | Go to the library root folder |
| Folder picker — Up-one-level button | `.picker-up-btn` | Go up one folder level |
| Shared Processing Tools picker — Home/Up-one-level buttons | `.tools-picker-home-btn` / `.tools-picker-up-btn` | Go to the starting folder / Go up one folder level (this picker can browse any drive) |

**Deliberately skipped:** Select All/Deselect All (self-labelled).

---

## Basic Editor — modal, opened via "Edit XML" on `/issue/{id}`

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Save button (disabled state) | `.basic-editor-save-btn[disabled]` | Save is enabled once a genre, format and age rating are set |
| Close (×) | `.basic-editor-close-btn` | Close without saving |

**Deliberately skipped:** Main/More tabs, Genre checkbox grid, Cancel button (self-labelled), Notes field default text (not interactive).

---

## Full Editor — `/editor`

### Header

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Search ComicVine button | `.search-comicvine-btn` | Search ComicVine using this file's Series, Issue #, Year |
| Search GoodReads link | `.search-goodreads-link` | Opens goodreads.com — does not search using this file's data |

### Column 1 — Load / Select Files

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Select Folder button | `.select-folder-btn` | Load files from one folder only — subfolders aren't included |
| Clear button | `.editor-clear-btn` | Clear all loaded files and reset the form |

### Column 2 — Edit ComicInfo.xml

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Increment # checkbox | `.increment-issue-checkbox` | Increase issue number by one for each file, in list order |
| "Apply to All" checkbox (per field) | `.apply-to-all-checkbox` | Include this field when Process All runs on every loaded file |
| Genre chip — remove (✕) | `.genre-chip-remove` | Remove this genre |
| ＋ Queue button | `.queue-file-btn` | Add this file to the queue with its current edits |

### Column 3 — Comic Viewer

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Zoom in | `.viewer-zoom-in` | Zoom in |
| Zoom out | `.viewer-zoom-out` | Zoom out |
| Fit button | `.viewer-fit` | Fit page to window |
| Prev page | `.viewer-page-nav[data-dir="prev"]` | Previous page |
| Next page | `.viewer-page-nav[data-dir="next"]` | Next page |
| Fullscreen button | `.viewer-fullscreen-btn` | View in fullscreen |

### Column 4 — Edited Files Queue

| Element description | Selector hint | Tooltip text |
|---|---|---|
| ✕ remove (per queue card) | `.queue-card-remove` | Remove this file from the queue |
| Process Queue button | `.process-queue-btn` | Save XML to every queued file — this is the save action |
| 🗑 Clear Queue | `.clear-queue-btn` | Empty the queue without saving any changes |
| Process All button | `.process-all-btn` | Save checked fields to every loaded file, bypassing the queue |

### Modals

| Element description | Selector hint | Tooltip text |
|---|---|---|
| Multi-ComicInfo.xml resolution — keep-this-one action | `.xml-resolution-keep-btn` | Keep this ComicInfo.xml and delete the other(s) from the archive |
| Search ComicVine — "Ok" (Select Series step) | `.comicvine-series-ok-btn` | Use the top match and skip straight to its issue list |
| Search ComicVine — confirm issue (Select Issue step) | `.comicvine-issue-confirm-btn` | Apply this issue's data, overwriting all current fields |

**Deliberately skipped:** Page-thumbnail strip, footer status bar (informational), "Issues"/Cancel buttons (self-labelled), "← Back to Series" link (destination obvious).

---

## Guide Placeholder — `/guide`

No tooltip-worthy controls — static placeholder page with no interactive elements beyond plain text links. Being replaced by later stages of this project.

---

## Notes on [NEEDS VERIFICATION] items

- **Scan Roots / Exclude Patterns remove controls** (Library Management) — the inventory doesn't specify whether removing a folder/pattern from these lists uses an icon-only button or a text button; wrote tooltips assuming icon-only per the usual pattern for list-row removal, flagged for Stage 7 to confirm against the live DOM.
- Two items the inventory itself already flags as unverified were deliberately **not** given tooltip entries here since they aren't hoverable UI controls: the Full Editor "Search ComicVine" / Basic Editor fuzzy-credit-match dialogs are native `confirm()` popups, not tooltip targets. Their wording (once confirmed live) belongs in guide body copy, not a tooltip.
- The `comicvault://` reader link tooltip ("Opens in the digib00age reader app, if installed") is written from source behaviour per the inventory; the inventory notes this wasn't verified live on a machine with no reader registered. Low risk, but worth a quick sanity check before Stage 7 ships it.
