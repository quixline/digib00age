# ComicVault — CUSTOM_TABS_SPEC.md (V2.1)

> **How to use this document**
> Paste this entire file into a Claude Code session alongside `SPEC.md` for context on the
> existing system this plugs into. This is the single source of truth for the Custom Tabs
> feature (v2.1). Record any deviations at the bottom of this file (Change Log), same
> convention as `SPEC.md` and `EDITOR_SPEC.md`.
>
> **Status:** Built and verified (2026-06-19) — see `progress.md` "V2.1 — Custom Tabs
> Built (2026-06-19)" for the build log. This was the first v2.1 feature tackled; the
> others (editable home strips — see `HOME_STRIPS_SPEC.md`, taskbar app changes, mobile
> reader changes) were tracked in `comicvault-changes-2.1.md` (closed
> 2026-06-22, renamed from `comicvault-changes.md`), which supersedes the
> now-removed `v2_1-main-new-features.md`.
>
> **v2.2 update:** Section 1's and Section 6's statements that the hardcoded 2000 AD
> tab is untouched/out of scope are **superseded** — see §9 below. The 2000 AD fixed
> surface has been fully removed; its useful behaviour (browse-by-folder, organised by
> year) is generalised into the new Folder View mode any custom tab can use. Left the
> original text below as-written rather than editing it, per this doc's own Change Log
> convention — §9 and the Change Log entry are the record of what changed and why.

---

## 1. Overview & Goals

Add admin-managed, folder-scoped library tabs. A custom tab is a flat, filtered view of
the library — same design and behaviour as the existing **All** tab (filters, sort,
group-by, grid/list toggle, pagination) — restricted to issues whose file path falls
under one chosen folder (including subfolders).

**Explicitly out of scope / not touched by this feature:**
- The existing **2000 AD** tab. It stays exactly as-is: hardcoded, two-level year-grid
  display, built from `series = '2000 AD'`. It is *not* migrated into the new
  `custom_tabs` table and is not generalised. It simply continues to sit in the nav
  alongside whatever custom tabs are visible.
- Flutter app. This build is **web UI only**. Custom tabs do not need to appear in the
  Flutter reader app in this round.
- Nav reordering of custom tabs, and nav overflow handling for many visible tabs — see
  Section 6.

This is a clean, additive feature: no scanner changes, no changes to `format_group`
logic, no changes to existing fixed tabs (Home, All, Singles, Series) or to 2000 AD.

---

## 2. Data Model

New table: `custom_tabs`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | |
| `name` | TEXT NOT NULL | Admin-set label, shown in nav when `visible = true` |
| `folder_path` | TEXT NOT NULL | Absolute path on disk. Must resolve under a configured library root (see Section 4) |
| `visible` | BOOLEAN NOT NULL DEFAULT 1 | Controls nav display only — does not affect storage |
| `created_at` | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Sort key for nav order among visible tabs |

No new columns on `issues`. No scanner changes. A custom tab's content is computed
**at query time** — filter already-scanned issues by file path prefix — not a new
ingestion rule.

---

## 3. Caps & Visibility Rules

- **Maximum 4 tabs with `visible = 1` at any time.** This is a nav-space limit, not a
  storage limit.
- **No cap on total stored rows.** Admin can create as many tab definitions as they
  like; toggling `visible` off frees a slot for another to be shown without losing the
  definition.
- Enforce the visible-cap server-side (reject/409 on attempting to set a 5th tab
  visible) — don't rely on the admin UI alone to prevent it.

---

## 4. Backend

### 4.1 Folder validation

On create (and on toggling a hidden tab back visible, in case the folder no longer
exists), validate `folder_path`:
- Must exist on disk (`os.path.isdir`)
- Should resolve under a currently configured library root (`config.json` /
  `LIBRARY_ROOT` plus any additional configured roots from the admin page's library
  folders section). If it resolves but is **outside** all configured roots, allow the
  save but surface a warning in the response (e.g. `warning` field) — admin's call,
  but the tab will simply show 0 issues since nothing under that path is scanned.

### 4.2 New endpoints (suggested — adjust to match existing route conventions)

- `GET /api/admin/custom-tabs` — list all stored tabs (visible and hidden)
- `POST /api/admin/custom-tabs` — create `{name, folder_path}`. Server validates path
  per 4.1, enforces the visible-cap if defaulting to visible, returns the created row.
- `PATCH /api/admin/custom-tabs/{id}` — update `name`, `folder_path`, and/or `visible`.
  Enforce visible-cap here too when flipping `visible` from 0 → 1.
- `DELETE /api/admin/custom-tabs/{id}` — hard delete the row. No file-system side
  effects whatsoever — this only removes the tab definition.
- `GET /api/admin/browse?path=...` — reuse the existing editor's folder-browse logic
  (`/browse` in the editor backend, gated to library-root-adjacent paths) for the
  server-side native-style folder picker. If the existing `/browse` endpoint is
  already general-purpose, point the new admin UI at it directly rather than
  duplicating logic.
- `GET /api/tabs/{id}/issues` (or extend the existing All-tab issues endpoint with an
  optional `tab_id` / `folder_path` filter param) — returns issues filtered by
  `file_path` prefix matching the tab's `folder_path`, otherwise identical query
  shape/params to the All tab (filters, sort, group-by, pagination) so the frontend can
  reuse its existing All-tab rendering code path.

### 4.3 Nav config endpoint

Whatever endpoint currently feeds the frontend's nav bar (or if there isn't one and
nav is currently static HTML) should now also return the list of visible custom tabs
(`id`, `name`) in `created_at` order, so the frontend can render them without a
separate round-trip on every page load. If nav is currently hardcoded markup, this is
the point where it needs to become at least partially dynamic.

---

## 5. Frontend

### 5.1 Admin page — Advanced Settings section

Add a new "Custom Tabs" subsection inside the existing locked Advanced Settings
fieldset (same unlock-checkbox gating as the rest of that section).

Contents:
- **List of all stored tabs** (visible and hidden together, no separate collapsed
  section — hidden ones visually marked, e.g. greyed out or a "Hidden" badge).
  Per row: name, folder path, a visible/hidden toggle, and a **Delete** button.
- **Delete** opens a confirm dialog. Wording must be explicit that this only removes
  the tab definition and never touches actual comic files or library data — this is a
  destructive-sounding action and the admin should not have to wonder what it deletes.
- **"Add Tab" form**: name text input + folder selection, offering two ways to set the
  path:
  - **Browse** button → opens the folder-browse picker (reuse/extend the editor's
    `file_mgmnt`-style picker UI, pointed at the new `/browse` endpoint per 4.2)
  - **Manual path** text input as a fallback, since the Browse picker reflects the
    server's filesystem and won't be useful when administering remotely (e.g. from the
    laptop) — both inputs write to the same `folder_path` field, manual entry just
    skips the picker.
  - New tabs always default to **visible**. "Add Tab" submit button is **disabled**
    (with a short explanatory note, e.g. "4 tabs already visible — hide one first")
    whenever 4 tabs are already visible. Admin must hide an existing tab before adding
    a new one — no hidden-on-creation path.

### 5.2 Nav bar

Order (unchanged fixed portion): Home, All, Singles, Series, then 2000 AD (hardcoded,
unchanged), then visible custom tabs in `created_at` order.

If nav is currently static markup (per Section 4.3), it needs to render the custom-tab
links dynamically from the nav config response.

### 5.3 Tab content page

Reuse the existing All-tab rendering path (filter bar, sort, group-by, grid/list
toggle, pagination) wholesale — point it at the new filtered-issues endpoint/param
instead of the unfiltered All query. There should be no new UI component needed here;
this is the entire reason "flat, All-tab style" was chosen over a bespoke per-tab
layout.

---

## 6. Explicitly Out of Scope (This Build)

- Reordering custom tabs (creation order only, for now)
- Nav overflow / responsive handling for many visible tabs at once (up to 9 tabs total
  possible: 4 fixed + 2000 AD + 4 custom — will assess once tabs are actually in use
  and the bar's been seen in practice, rather than guessing now)
- Any change to 2000 AD's tab, code path, or data model
- Flutter app changes
- Public-repo fork work (separate future effort: empty DB, four fixed tabs only, no
  2000 AD at all, this feature carried over as-is into that fork when it happens)

---

## 7. Build Order (suggested)

1. `custom_tabs` table + migration
2. Backend CRUD endpoints (4.2) + folder validation (4.1) + visible-cap enforcement
3. Filtered-issues query (extend existing All-tab query with folder-path filter)
4. Nav config update (4.3) + dynamic nav rendering (5.2)
5. Admin page "Custom Tabs" section (5.1), including Browse-picker reuse from the
   editor and the manual-path fallback
6. Tab content page wiring (5.3) — should mostly be "point existing All-tab view at a
   new endpoint param," not new UI
7. Manual test pass: add a tab, confirm content matches folder, hide/show, hit the
   4-visible cap, delete, confirm deleted tab's folder/files are untouched on disk

---

## 8. Change Log

> Record any deviations from this spec here with date and reason.

| Date | Change | Reason |
|---|---|---|
| 2026-06-19 | Section 5.1's folder picker reuses the Full Editor's picker *CSS* (`.editor-overlay`/`.editor-modal`/`.fe-picker-*`) but not its multi-select checkbox interaction — Custom Tabs only ever needs one folder, so it's click-to-descend-a-folder-row plus a single "Select This Folder" button instead. | A custom tab has exactly one `folder_path`; the editor's checkbox multi-select (built for adding many files/folders to a working set at once) doesn't apply. |
| 2026-06-19 | Added a small fix beyond the spec's text: cached custom-tab names in `sessionStorage` so the existing issue/series back-link label (previously only aware of the four fixed surface names) shows the tab's actual name instead of falling back to "Library" when navigating from a custom tab. Navigation itself was already correct without this — label only. | Not addressed by the spec; found while verifying the `from=tab-{id}` back-link round trip end to end. |
| 2026-06-22 | Added `view_mode` (`flat`/`folder`) to `custom_tabs`. Folder View generalises 2000 AD's old hardcoded two-level year-grid into a reusable per-tab mode: recursive folder/file mixed-grid browsing with real history-backed navigation, depth-agnostic search, and recursive Mark All Read. The 2000 AD fixed tab is fully removed; 2000 AD becomes an ordinary custom tab (Folder View) post-build, consuming a normal visible-tab slot. | v2.2 planning — 2000 AD's bespoke view was always meant to be removed before the app went public; Folder View captures the part of its behaviour that was actually useful and makes it available to any custom tab. |
| 2026-06-23 | Resolved the folder-card image gap flagged 2026-06-22 (§9.2): random cached issue thumbnail from anywhere in the folder's subtree, re-rolled every request. Considered and rejected an explicit `folder.jpg`/`cover.jpg`/`poster.jpg` convention with its own thumbnail pipeline — reusing existing per-issue thumbnails achieves the same goal (better than a blank icon) with no new pipeline, file convention, or invalidation logic. | Design discussion 2026-06-23 session; see `comicvault-changes-v2.3.md`. |
| 2026-06-23 | Built the above same day: `get_tab_folder_contents()` (`library.py`) now returns a `cover_path` per subfolder (random choice over issue ids already collected in its single pass); `buildFolderCard()` (`app.js`) renders it image-on-top/info-below (new `.folder-card.has-cover` CSS), falling back to the 📁 icon on no-cover or image load error. | Implementation session 2026-06-23; see `progress.md`. |

---

## 9. Folder View (v2.2)

### 9.1 View Mode (extends §2 Data Model)

New column on `custom_tabs`:

| Column | Type | Notes |
|---|---|---|
| `view_mode` | TEXT NOT NULL DEFAULT 'flat' | `'flat'` (existing v2.1 behaviour, unchanged) or `'folder'` (new) |

Existing rows get `'flat'` via migration default (`_add_missing_custom_tab_columns()`,
`database.py`, same pattern as `_add_missing_issue_columns()`) — no behaviour change
for tabs created before this shipped. The Admin "Add Tab" / per-row edit controls
(§5.1) let an admin choose or change view mode after creation, without recreating
the tab.

### 9.2 Folder View — Browse mode

At any folder level (starting at the tab's `folder_path` root), render a **mixed
grid**:
- Loose files directly in that folder render as flat issue cards — same card shape
  as the All tab/flat-mode tabs, page count shown.
- Subfolders render as folder cards, showing a **recursive** issue count (every
  issue anywhere underneath that folder, not just direct children).
- A folder with no subfolders left renders as a pure flat file grid (the terminal
  case — most custom tabs pointed at a normally-structured library folder will hit
  this immediately, since folder = series/single there).

**Folder card images (resolved 2026-06-23):** each folder card additionally shows
a representative image — a random cached thumbnail drawn from any issue
recursively under that folder, via `ORDER BY RANDOM() LIMIT 1` scoped to the same
subtree query the recursive issue count (above) already runs. No new image
pipeline: this reuses existing per-issue cached thumbnails as-is, so there's no
new file convention (no `folder.jpg`/`cover.jpg`/`poster.jpg`), no scanner
changes, and no cache invalidation to manage.

Re-randomizes on every request — page load, refresh, or navigating back into the
folder may show a different cover each time. Deliberate choice over a stable/
pinned image, for a "kept alive" feel consistent with the existing Random Unread/
Random Genre home strips. A folder with no issues anywhere underneath it (count
of 0) shows the plain folder icon, unchanged.

Built 2026-06-23 — see Change Log below and `progress.md`.

Clicking a folder card drills into that folder, repeating the same mixed-grid logic
one level down.

**Navigation uses real browser history**, via the surface convention
`?surface=tab-{id}&path=<relative-path>` (a deliberate explicit `history.pushState`
per drill-down, paired with one `popstate` listener — this SPA never does a real page
load on a surface switch, unlike the simpler `history.back()`-only pattern Issue/
Series back-links use, which is enough for them since they only ever need to go up
one level). Back/forward/refresh/bookmark/share-link all land on the exact folder
level expected. Breadcrumbs derive from the URL's `path` param.

### 9.3 Folder View — Search mode

When a search term is entered inside a Folder View tab, browse mode is replaced
entirely by flat, depth-agnostic results (`GET /api/library/tab/{id}/search?q=`),
scoped to the whole tab's folder subtree rather than the current folder level, with
each result showing its folder path so the user can see where it lives. Clearing the
search returns to browse mode at whatever folder level was active before the search
started.

### 9.4 Mark All Read (per folder)

A "Mark all read" action available at any folder level in browse mode, scoped
**recursively** — it marks every issue anywhere under the current folder as read,
matching what the folder's displayed issue count represents.

### 9.5 Backend

- `GET /api/library/tab/{id}/folder?path=` — folder-contents endpoint for browse
  mode: immediate child folders (each with a recursive issue count) and immediate
  child files (issue cards), at one level. Single query over the tab's whole subtree
  via `is_under()` (`path_utils.py`), grouped in Python — no N+1.
- `GET /api/library?tab_id=...` (existing, unchanged) — remains the flat-mode
  tab's own content query; Folder View does not use it (see search note below).
- `GET /api/library/tab/{id}/search?q=` — new, file-shaped (via the existing
  `_issue_to_dict()`) flat search across the tab's whole subtree. Added because the
  flat-mode endpoint above is series-grouped, not per-file, and Folder View search
  needs per-file results with folder paths.
- `POST /api/library/tab/{id}/folder/mark-read?path=` — recursive mark-all-read,
  reuses `_get_or_create_progress()` (`progress.py`) rather than duplicating the
  upsert logic.

### 9.6 Frontend

- Folder/file mixed-grid rendering (`renderFolderView()`, `buildFolderCard()`,
  `buildFolderFileCard()` — the last one is the old 2000 AD prog card's body,
  generalised with non-2000AD-specific labels).
- `path`-based history wiring (`pushFolderViewUrl()`, `goToFolderPath()`, one
  `popstate` listener).
- Breadcrumb rendering from the active path (`renderFolderBreadcrumb()`).
- Search-mode toggle wired into the existing inline search bar
  (`startFolderViewSearch()` / `clearFolderViewSearch()`), scoped to surfaces where
  `isFolderViewTab(activeSurface)` is true.
- "Mark all read" button at folder level (`markFolderViewRead()`).
- Folder View flat file cards plug into the existing multi-select mechanism
  (`makeSelectable()`) the same way the old 2000 AD prog cards did — no new
  mechanism needed.
