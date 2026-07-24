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
| `basis_type` | TEXT NOT NULL DEFAULT 'folder' | `'folder'` (original v2.1 behaviour) or `'favorites'` (v2.4 — see Section 10). Existing rows get `'folder'` via migration default, no behaviour change |
| `folder_path` | TEXT NOT NULL | Absolute path on disk when `basis_type = 'folder'`. Must resolve under a configured library root (see Section 4). For `basis_type = 'favorites'` rows, stored as `""` (empty string) and never read — see Section 10.1 for why the column stays `NOT NULL` rather than being migrated to nullable |
| `visible` | BOOLEAN NOT NULL DEFAULT 1 | Controls nav display only — does not affect storage |
| `created_at` | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Sort key for nav order among visible tabs |

No new columns on `issues` (the favourites tab reuses the existing `Issue.favorites`
boolean). No scanner changes. A folder tab's content is computed **at query time** —
filter already-scanned issues by file path prefix; a favourites tab's content is
computed the same way, filtering by `Issue.favorites == True` instead — neither is a
new ingestion rule.

---

## 3. Caps & Visibility Rules

- **No cap on visible tabs (removed 2026-07-24).** The original 4-visible-tab limit
  dated from when custom tabs rendered as a top tab bar with genuinely limited
  horizontal space. The nav moved to a left sidebar in v2.6 (Section 5.2) and the
  sidebar already scrolls vertically when content overflows, so the space
  constraint the cap protected against no longer applies. See Change Log.
- **No cap on total stored rows** for folder-based tabs. Admin can create as many tab
  definitions as they like.
- **Maximum 1 favourites-basis tab, stored or visible, ever.** Unlike folder tabs
  (which differ by path), every favourites tab would have identical content —
  allowing more than one only wastes a slot on a duplicate. The "Add Favourites Tab"
  button (Section 10.2) disables itself once one exists, in either visibility state.
- **Maximum 1 reading-queue-basis tab, stored or visible, ever** — same reasoning
  and same disable-button pattern as favourites (Section 10.10).
- **Maximum 1 genre-basis tab per distinct genre value** — a second tab for the same
  genre would be a duplicate; different genres each get their own tab freely
  (Section 10.9).

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
  - New tabs always default to **visible**. No visible-count cap (removed
    2026-07-24, Section 3) — the "Add Tab" button is only ever disabled by its own
    singleton/dedup rules (Favourites, Reading Queue, one-per-genre), never by how
    many tabs are already visible.
- **"Add Favourites Tab" button (v2.4 — see Section 10.2)**: a separate, single-click
  control next to "Add Tab" — no form, no folder picker. Creates a `basis_type =
  'favorites'` row directly, pre-filled name "Favourites" (renameable afterward via
  the same row controls as any other tab). Disabled once a favourites-basis tab
  already exists (stored or visible — Section 3), and counts toward the same
  4-visible cap as folder tabs.

### 5.2 Nav bar

Order (unchanged fixed portion): Home, All, Singles, Series, then 2000 AD (hardcoded,
unchanged), then visible custom tabs in `created_at` order.

If nav is currently static markup (per Section 4.3), it needs to render the custom-tab
links dynamically from the nav config response.

**v2.6 update (2026-07-07):** the nav itself moved from a top tab bar to a left
sidebar (v2.6 Item 1 Phase B) — see the Change Log. The ordering and dynamic-render
mechanism described above are otherwise unchanged: custom tabs still render from
`GET /nav/config` in `created_at` order, just into the sidebar's "Libraries" section
(UI copy only — this spec's "Custom Tabs" terminology is unchanged internally, per
the open question flagged in `docs/v2.6/comicvault-changes-v2.6.md` Item 1).

### 5.3 Tab content page

Reuse the existing All-tab rendering path (filter bar, sort, group-by, grid/list
toggle, pagination) wholesale — point it at the new filtered-issues endpoint/param
instead of the unfiltered All query. There should be no new UI component needed here;
this is the entire reason "flat, All-tab style" was chosen over a bespoke per-tab
layout.

---

## 6. Explicitly Out of Scope (This Build)

- Reordering custom tabs (creation order only, for now)
- ~~Nav overflow / responsive handling for many visible tabs at once (up to 9 tabs
  total possible: 4 fixed + 2000 AD + 4 custom — will assess once tabs are actually
  in use and the bar's been seen in practice, rather than guessing now)~~ **Moot as
  of 2026-07-24** — the visible-tab cap this bullet assumed is gone (Section 3), and
  the left sidebar (Section 5.2) already scrolls vertically for any number of items;
  verified against a larger-than-4 tab count same day. No responsive/overflow work
  was needed beyond what already existed.
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
| 2026-06-30 | Added §10 Favourites Tab (v2.4 Item 4) — new `basis_type` column (`'folder'`/`'favorites'`), library-wide favourites filtering reusing the existing flat-tab render path and client-side filter bar, dedicated "Add Favourites Tab" one-click control, `folder_path = ""` convention (no nullable-column migration), `view_mode` locked to `'flat'`, server-side guards rejecting Folder View endpoints/edits on favourites-basis rows, live-removal-on-unfavourite fix scoped to the shared toggle handler (benefits the existing All-tab filter too), and BUG-017 (All-tab Favourites filter missing favourited issues inside series) bundled into the same build. | Scoping session 2026-06-30 — `comicvault-changes-v2.4.md` Item 4; code read directly (`models.py`, `library.py`, `path_utils.py`, `admin.py`, `app.js`) before design decisions were made. |
| 2026-07-07 | §5.2's nav bar moved from a top tab bar to a left sidebar ("Libraries" section, UI copy only). `loadCustomTabsNav()` (`app.js`) now renders into `#sidebarLibraries` instead of appending `.surface-btn`s to `.surface-nav`, and runs on `series.html`/`issue.html` too (not just the library page) so the Libraries list is always visible. Ordering and the `GET /nav/config` data source are unchanged. | v2.6 Item 1 Phase B (left sidebar nav) — see `docs/v2.6/progress.md`. |
| 2026-07-09 | §9.6's Folder View breadcrumb (`renderFolderBreadcrumb()`) removed, replaced by a "← Back" button using the same real-history pattern as Series/Issue's back links; search-mode label split out into its own `#folderSearchLabel` element. | Tez's post-redesign UI tweak pass, now that `BUG-014` made `history.back()` reliable app-wide — see `docs/v2.6/progress.md` and `DECISIONS.md`. |
| 2026-07-23 | §9.2's folder cards (`.folder-card`, both plain and `.has-cover`) restyled to match the main library's redesigned card face (`.cover-card--redesign`): fixed dark gradient background (dark theme) replacing the flat `var(--surface-card)` fill, the always-on faint white idle ring removed in favour of hover-only glow, and a matching light-theme bordered-ring override added (previously had none). Folder-tile issue cards (`buildFolderFileCard()`) already shared the redesigned card CSS and needed no change. | Tez flagged the folder/series tiles (e.g. 2000 AD's year folders) as visually inconsistent with the main library/home cards — applies to any custom tab using Folder View, not just 2000 AD. See `docs/v2.6/progress.md`. |
| 2026-07-24 | §1's "Flutter app — web UI only" statement superseded for Folder View: new §9.7 added — Flutter now has a real `FolderScreen` with directory drill-down for `view_mode: 'folder'` tabs, reusing the existing `CoverCard` widget for both folder and issue-file tiles. §9.5's folder-contents endpoint gained `year_min`/`year_max` per folder entry to support this. | Tez asked for Folder View's mobile card styling to match the main library cards; building that surfaced that Folder View didn't exist in Flutter at all yet. See `docs/v2.6/progress.md`. |
| 2026-07-24 | §3's 4-visible-tab cap removed entirely (not raised) — `MAX_VISIBLE_CUSTOM_TABS` and all five call sites deleted from `backend/routers/admin.py` (`create_custom_tab()`'s four basis-type branches, `update_custom_tab()`'s visible-flip check); `frontend/js/admin.js`'s duplicate client-side cap/`ctCapHint` logic removed; `frontend/admin.html`'s `ctCapHint` span and the "Up to 4 can be visible at once" intro copy removed. §5.1 and §6 updated to match. No Flutter change — it never had a client-side cap, and `NavRail`'s `SingleChildScrollView` already handled any tab count. | Tez: the cap dated from the old top-tab-bar design where horizontal space was genuinely scarce; the v2.6 left-sidebar redesign already scrolls vertically, so the constraint no longer applies. Immediate driver was Genre Library tabs competing with Favourites/Reading Queue/folder tabs for the same 4 slots, blocking multi-genre use on the Flutter mobile reader in particular. Verified live: pushed the web sidebar to 15 visible tabs (admin UI + direct API calls) with no 409s and correct whole-sidebar scroll. See `docs/DECISIONS.md`. |

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
load on a surface switch). Back/forward/refresh/bookmark/share-link all land on the
exact folder level expected.

**On-page back control changed 2026-07-09:** the drill-down navigation above (and
its per-level `pushState` entries) is unchanged, but the visible "go back" UI is
not a breadcrumb anymore — see the note at the end of §9.6.

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
  via `is_under()` (`path_utils.py`), grouped in Python — no N+1. Each folder entry
  also carries `year_min`/`year_max` (added 2026-07-24 for the Flutter client, §9.7)
  — the min/max `Issue.year` across everything recursively under that folder, both
  `null` if none of its issues have a year set.
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
- ~~Breadcrumb rendering from the active path (`renderFolderBreadcrumb()`).~~
  **Removed 2026-07-09** — `renderFolderBreadcrumb()` deleted along with the
  `#folderBreadcrumb` element. Replaced by a real "← Back" button (`#folderBackBtn`),
  the same `window.history.back()`-when-possible / `href="/"`-fallback pattern
  Series/Issue's own back links use (`BUG-014`'s fix). Trades the breadcrumb's
  jump-to-any-ancestor-level shortcut for consistency with the rest of the app —
  Tez's explicit call once BUG-014 made `history.back()` reliable app-wide; see
  `DECISIONS.md`. The search-mode label that used to render into the breadcrumb
  element (`"Search results for \"…\""`) now has its own dedicated element,
  `#folderSearchLabel`, next to the Back button.
- Search-mode toggle wired into the existing inline search bar
  (`startFolderViewSearch()` / `clearFolderViewSearch()`), scoped to surfaces where
  `isFolderViewTab(activeSurface)` is true.
- "Mark all read" button at folder level (`markFolderViewRead()`).
- Folder View flat file cards plug into the existing multi-select mechanism
  (`makeSelectable()`) the same way the old 2000 AD prog cards did — no new
  mechanism needed.

### 9.7 Flutter Mobile Reader (added 2026-07-24)

**§1's original "Flutter app — web UI only, custom tabs do not need to appear in
this round" statement no longer applies to Folder View** — built 2026-07-24, see
Change Log and `docs/v2.6/progress.md`. §1 text left as-written per this doc's own
convention (see the v2.2 note at the top of this file).

- `flutter_app/lib/screens/folder_screen.dart` (`FolderScreen`/`FolderFilter`) —
  one directory level per screen, pushed via a `'/folder'` route
  (`shell_screen.dart`); `NavKind.library` tabs with `view_mode == 'folder'` route
  here instead of the flat `BrowseScreen`.
- Folder tiles and issue-file tiles both render through the **same** `CoverCard`
  widget the rest of the library uses (`flutter_app/lib/widgets/cover_card.dart`)
  — not a separate widget, unlike the web's still-distinct `.folder-card` CSS
  family (§9.2/§9.6). Folder tiles show cover, name, and "`year_min`–`year_max` ·
  N issues" (or a single year when `year_min == year_max`, or no year segment at
  all when both are `null`); no genre ribbon, rating, or favourite/flagged badge
  (backend returns `has_favorite`/`has_flagged_review` per folder but the Flutter
  card doesn't surface them yet).
- Navigation: a "← Back" pill (shown only below the tab root) pops one level —
  mirrors the web's current back-button behaviour (§9.2's 2026-07-09 note), not a
  breadcrumb trail.
- No search mode (§9.3) or per-folder Mark All Read (§9.4) on the Flutter side yet
  — out of scope for this build, not attempted.
- Verified live on Tez's Lenovo tablet against the real "2000 AD" tab; see
  `docs/v2.6/progress.md` for the full verification narrative.

---

## 10. Favourites Tab (v2.4)

**Built and manually tested 2026-07-01 — `comicvault-changes-v2.4.md` Item 9.**

Scoped 2026-06-30 (`comicvault-changes-v2.4.md` Item 4). A library-wide custom tab
showing every issue with `Issue.favorites = true`, regardless of which folder it
lives in. Reuses the existing flat-tab rendering path wholesale — the filter bar
(Genre, Publisher, Format, Rating, Decade, Year, B&W, Stars, and the existing
Favourites menu-bar toggle) already runs client-side on top of whatever pool the
active surface fetched (`getFilteredLibrary()`, confirmed by reading `app.js`
directly), so "Genre: Crime within Favourites" needs no new filter-bar code —
it's the existing mechanism applied to a favourites-only pool.

### 10.1 Why `folder_path` stays `NOT NULL`

`custom_tabs.folder_path` was created `NOT NULL` in the original migration, and this
codebase's only proven migration pattern (`_add_missing_custom_tab_columns()`,
`database.py`) is additive-column-only — it has never relaxed a constraint, and
doing so in SQLite means a full table rebuild, not a simple `ALTER TABLE`. Given
BUG-016 was exactly this class of risk (something that read correctly in the code
but broke on first real exercise), favourites-basis rows store `folder_path = ""`
rather than attempting a nullable migration. Every code path branches on
`basis_type`, never on whether `folder_path` is truthy — `""` is never read or
relied upon as a sentinel beyond "this row isn't folder-based."

### 10.2 Admin — "Add Favourites Tab"

Separate button next to "Add Tab" (§5.1), no form. One click:
`POST /admin/custom-tabs {"basis_type": "favorites"}` — no `name` or `folder_path`
required in the payload (`create_custom_tab` gets a `basis_type` branch that skips
the existing `if not name or not folder_path` requirement entirely for this case).
Server assigns `name = "Favourites"`, `folder_path = ""`, `view_mode = "flat"`,
`visible = true` (subject to the existing 4-visible cap, §3). Name is renameable
afterward through the same row controls every other tab uses — no new UI needed
for that.

Button disables itself once a favourites-basis tab already exists, in either
visibility state (§3) — checked the same way the "Add Tab" button already checks
the 4-visible cap.

### 10.3 Backend — query resolution

`GET /api/library`'s `tab_id` resolution (`backend/routers/library.py`,
`get_library()`) gains a `basis_type` branch:

```python
if tab_id is not None:
    tab = db.query(CustomTab).filter(CustomTab.id == tab_id).first()
    if not tab:
        raise HTTPException(status_code=404, detail="Custom tab not found")
    if tab.basis_type == "favorites":
        all_issues = [i for i in all_issues if i.favorites]
    else:
        tab_folder = tab.folder_path
# existing `if tab_folder:` block continues unchanged for folder-basis tabs
```

Filtering happens before the per-series groupby, same as the existing folder/field/
search filters — a series card only ever reflects issues that actually matched (same
principle as BUG-010's fix, and the reason BUG-017 below doesn't affect this new tab).

### 10.4 Backend — guards on favourites-basis rows

- `view_mode` is forced to `"flat"` at creation and **locked** — `PATCH
  /admin/custom-tabs/{id}` must reject any attempt to set `view_mode = "folder"` on a
  favourites-basis row (Folder View has no meaning without a real `folder_path`).
- `PATCH /admin/custom-tabs/{id}` must reject any attempt to edit `folder_path` or
  `basis_type` on a favourites-basis row — same protection pattern
  `HOME_STRIPS_SPEC.md` §4.3 already uses for `is_default` rows (only specific fields
  mutable, clear error otherwise, not silent ignoring).
- The three Folder View endpoints (`GET /library/tab/{id}/folder`,
  `POST /library/tab/{id}/folder/mark-read`, `GET /library/tab/{id}/search`) must
  return `400` if called against a `basis_type = "favorites"` tab, rather than
  evaluating `is_under(file_path, "")` against an empty `folder_path` (undefined
  behaviour — not a safe "matches nothing"). This is a server-side guard, not just a
  frontend one — `view_mode` locking (above) should prevent the frontend from ever
  calling these for a favourites tab, but the backend must not trust that.

### 10.5 Live removal on un-favourite

Un-favouriting a card while viewing the Favourites tab should remove it from view
immediately, without a page reload or surface switch. This is **not** new behaviour
scoped to this tab alone — today, un-favouriting a card while the existing All-tab
Favourites menu-bar filter (`activeFavorites`, `MENU_BAR_SPEC.md` §2.3) is active
also fails to remove it live; the toggle handler (`applyFavoriteToDom()`, `app.js`)
updates the in-memory `favorites` flag but never re-runs `getFilteredLibrary()` +
re-render. Fix once, in the shared favourite-toggle handler, so both the existing
All-tab filter and the new Favourites tab get consistent live removal — building it
for the new tab only would leave the older, already-shipped filter looking broken by
comparison.

### 10.6 Empty state

Zero favourites anywhere in the library (e.g. fresh install) — the tab's empty-state
message should read something Favourites-specific ("No favourites yet — star some
issues to see them here"), not the generic "No comics match these filters," or it
reads as broken rather than simply empty.

### 10.7 Related fix bundled into this build — BUG-017

Scoping this tab surfaced an existing bug in the *current* All-tab Favourites filter
(not the new tab — see 10.3's note on why the new tab doesn't inherit it). Full
write-up: `BUGS.md` BUG-017. Bundled into the same build session (v2.4 Item 9) since
it's the same file, same function, same data model, and shipping a new Favourites
tab while the existing Favourites filter stays subtly broken elsewhere would be a
confusing place to leave things.

### 10.8 Out of scope (this build)

- Combining a folder restriction with the favourites filter on one tab row (e.g.
  "favourites within my Marvel folder") — considered and rejected during scoping;
  nobody asked for it and it breaks the single-criterion pattern `HomeStrip` already
  established for the same reason.
- ~~Generic field-based custom tabs (Genre/Publisher/etc. as a tab's own scoping
  criterion, the way `HomeStrip` supports for strips) — `basis_type` as a column
  doesn't preclude adding a third value later, but no admin UI for it is being built
  now.~~ **Superseded 2026-07-24 — see §10.9.** Genre shipped as a third
  `basis_type`; Publisher/Writer/etc. remain out of scope until asked for.
- Removing the "Add Tab" form's manual-path text input now that the Browse picker
  works reliably — flagged during scoping as redundant, but unrelated to this
  feature; tracked separately via `INBOX.md`.

### 10.9 Genre Library (v2.6)

**Built and manually tested 2026-07-24.** A third `basis_type` value, `'genre'`,
scoping a tab to every issue tagged with one specific genre — library-wide,
like Favourites, not folder-restricted. Multiple genres can each get their own
tab (unlike Favourites, capped at one row ever); each is still subject to the
existing 4-visible-tab cap (§3).

**Data model** — one new nullable column, `custom_tabs.field_value` (added the
same additive-migration way as `view_mode`/`basis_type`,
`_add_missing_custom_tab_columns()` in `database.py`), storing the genre name
for `basis_type = 'genre'` rows. No separate `field_name` column was added
(unlike `HomeStrip`'s `field_name`/`field_value` pair) — `basis_type = 'genre'`
already fixes the dimension, so a second column naming it would be redundant.

**Admin — "Add Genre Library"**: a dropdown (sourced from the existing
`GET /api/browse/genres`, the same endpoint Home Strips' Genre field already
uses) plus its own button, next to the "Add Favourites Library" control. The
dropdown excludes genres that already have a tab. Unlike Favourites' payload
(`{"basis_type": "favorites"}`, no other fields), this POSTs
`{"basis_type": "genre", "field_value": "<genre>"}`. Server rejects a repeat of
the same genre value with 409 (dedup is per-genre-value, not "one row ever"
like Favourites); the tab's `name` is set to the genre string itself, unprefixed
(e.g. "Horror", not "Genre: Horror") — the admin row's path-line text shows
`Genre: <value>` for clarity in the list, but the sidebar-facing `name` stays
plain.

**Query resolution** — `get_library()`'s `tab_id` branch gains a `basis_type ==
"genre"` case alongside `favorites`/folder, filtering `all_issues` through the
already-existing `matches_field(issue, "genre", tab.field_value)` helper
(`path_utils.py`) — the same genre-membership test the filter bar and
field-based Home Strips already use. Zero new queries; `Issue.genres` is
already eager-loaded for this endpoint.

**Guards** — same treatment as Favourites (§10.4): `view_mode` forced to
`"flat"` at creation and locked via `PATCH`; `folder_path`/`basis_type`/
`field_value` are all locked on `PATCH`. The three Folder View endpoints'
favourites-only guard was generalized from `basis_type == "favorites"` to
`basis_type != "folder"`, so genre tabs are blocked from Folder View the same
way, without an ever-growing exclusion list (this also changed the guards'
error message from "...for a favourites-basis tab" to the generic "Folder
View is not available for this tab", now that two non-folder types exist).

**Empty state** — mirrors §10.6: a genre tab with nothing tagged reads
`No comics tagged "<genre>" yet.` instead of the generic filters message.

**Out of scope, same as before** — Publisher/Writer/Format/etc. as their own
`basis_type` remain unbuilt; only Genre was asked for.

### 10.10 Reading Queue (v2.6)

**Built and manually tested 2026-07-24.** A fourth `basis_type` value,
`'reading_queue'` — a library-wide, singleton "read later" tab, same shape as
Favourites (§10.1-10.6), not folder-restricted, capped at one row ever.
Requested directly (not derived from an existing filter concept the way
Genre reused `matches_field()`), since no explicit per-issue membership
mechanism existed anywhere in the app before this — Custom Tabs up to this
point were all computed/virtual filters over existing issue metadata, never
an explicit add/remove set.

**Data model** — one new boolean column, `Issue.queued_for_reading` (added
the same additive-migration way as `Issue.favorites`/`flagged_for_review`,
`_add_missing_issue_columns()` in `database.py`), defaulting to `False`. This
mirrors `favorites` exactly rather than introducing a join table — see
`DECISIONS.md` for why a membership table wasn't used.

**Selection bar + issue detail page** — "📖 Queue Reading" in the multi-select
bottom bar (`frontend/js/app.js`, `ensureSelectionToolbar()`) and "📖 Add to
Reading Queue" / "📖 Queued" on the issue detail page
(`buildQueueReadingToggle()`), both mirroring the Favourite toggle's
bulk-endpoint-with-one-id pattern:
`POST /api/progress/bulk/queue-reading` / `/api/progress/bulk/unqueue-reading`
(`backend/routers/progress.py`), same `BulkIssueIds` body as every other bulk
action. Card-level state is the `is-queued-reading` class, toggled the same
way `is-favorite` is.

**Admin — "Add Reading Queue Library"**: a plain button (no dropdown, unlike
Genre) next to "Add Favourites Library", since this is a singleton like
Favourites, not one-per-value like Genre. POSTs
`{"basis_type": "reading_queue"}`; server enforces the 409-if-already-exists
singleton rule and the existing 4-visible-tab cap (§3), same as Favourites.

**Query resolution** — `get_library()`'s `tab_id` branch gains a
`basis_type == "reading_queue"` case alongside `favorites`/`genre`/folder,
filtering `all_issues` on `Issue.queued_for_reading` before the per-series
groupby — same principle as the favourites branch (§10.3).

**Guards** — same treatment as Favourites/Genre (§10.4/§10.9): `view_mode`
forced to `"flat"` at creation and locked via `PATCH`; `folder_path`/
`basis_type`/`field_value` are all locked on `PATCH`. The Folder View
endpoints' `basis_type != "folder"` guard (generalized in §10.9) already
covers `reading_queue` without further changes.

**Live removal on dequeue** — mirrors §10.5: un-queuing a card while viewing
the Reading Queue tab removes it from view immediately (`applyQueueReadingToDom()`
drops it from `tabLibraryCache` for any `reading_queue`-basis tab and
re-renders), without a page reload.

**Empty state** — mirrors §10.6/§10.9: `No comics queued yet — use Queue
Reading to add some.` instead of the generic filters message.

**Known limitation** — the redesigned cover card (`cover-card--redesign`)
already has all four corners spoken for by existing badges (favourite/unread/
flag-review/rating), so Reading Queue doesn't get its own corner badge; it
gets only the box-shadow ring (`--accent` blue), which — like the older
favourite/flag-review rings — is explicitly suppressed on `.cover-card--redesign`
by a 2026-07-15 "rewind" fine-tune that made badges the only state signal on
that card variant. In practice this means the ring is visible on the
non-redesigned Folder View / issue-row surfaces but not on the primary
redesigned grid card; the "Queued"/"Add to Reading Queue" button state and
the Reading Queue tab itself remain the reliable signal there. Flagged as a
known gap rather than solved, since fixing it would mean relitigating the
four-corner badge layout, which nobody asked for as part of this build.

