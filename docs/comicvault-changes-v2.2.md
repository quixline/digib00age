# ComicVault — v2.2: Remove 2000 AD Fixed Tab + Folder View for Custom Tabs

> **Closed out 2026-06-22 — fully built and verified.** All of Parts A–D below are
> done: 2000 AD's hardcoded surface is removed; Folder View shipped as a new
> `view_mode` on Custom Tabs; the build was amended into `CUSTOM_TABS_SPEC.md` §9
> (with a Change Log entry there); the manual test pass in Part D was run against
> real data via a separate test-server instance, including recreating 2000 AD as an
> ordinary Folder View custom tab. See `progress.md` "Session — 2026-06-22: v2.2 —
> Folder View + 2000 AD removal" for the full build/verification record. Kept here
> for history — there is no active backlog doc until a `comicvault-changes-v2.3.md`
> (or similar) is created.
>
> **How to use this document**
> This is the active planning / build reference for v2.2. Paste it into a Claude Code
> session alongside `SPEC.md` and `CUSTOM_TABS_SPEC.md`.
> Part A is a cleanup task (confirmed hit list below — grep already done). Part B is the
> actual feature build, written as an amendment to append to `CUSTOM_TABS_SPEC.md` (new
> sections + a Change Log entry) — don't create a new spec file, this is a mode of the
> existing Custom Tabs feature, not a separate one. Part C is the build order.
> Part D is the manual test pass — note it also covers verifying the 2000 AD fixed tab
> is gone.

---

## Part A — Remove the 2000 AD fixed tab (full cleanup)

This is a generalisation, not a pure deletion: the *behaviour* (browse-by-folder,
drill into a folder, see issues) is being kept — it's being folded into Folder View
(Part B) as a general capability. What's being removed is the **hardcoded special
case**: the fixed nav entry, the `series = '2000 AD'` query, the bespoke
route/surface code, and every other place the codebase singles 2000 AD out by name.

**Confirmed hit list** (grep already completed — these are the only locations):

**`backend/routers/home.py`**
- `GET /api/2000ad/years` endpoint — filter hardcoded to `Issue.series == "2000 AD"`
- `GET /api/2000ad/year/{year}` endpoint — same hardcoded filter
- Both live in the "Home & 2000 AD Router" file. Remove both endpoints entirely.
  The file's docstring lists them — update that too.

**`frontend/index.html`**
- Nav button: `<button class="surface-btn" data-surface="2000ad">2000 AD</button>`
- Entire `<div id="adView" hidden>` block (level-1 year grid + level-2 year detail,
  including `#adYearGrid`, `#adYearDetail`, `#adBackBtn`, `#adMarkAllBtn`)

**`frontend/js/app.js`**
- `activeSurface` state var comment: remove `| 2000ad` from the comment string
- `VALID` surfaces array in `initLibrary()`: remove `'2000ad'` entry
- `isBrowseSurface()`: no change needed — `'2000ad'` is already absent from it
- `switchSurface()`: remove `document.getElementById('adView').hidden = ...` line and
  the `else if (surface === '2000ad') { await load2000AD(); }` branch
- `redirectHomeSearchToAll()`: remove `document.getElementById('adView').hidden = true`
- Remove functions: `load2000AD()`, `render2000ADYears()`, `buildYearCard()`,
  `buildAdProgCard()`, `load2000ADYear()`, `markAllReadAdYear()`
  (approximately lines 1020–1165 in the current file — confirm exact range before
  removing)
- Multi-select comment block (top of MULTI-SELECT section): update
  "2000 AD prog cards" to "Folder View flat file cards" — do this as part of
  Step 8 (multi-select compat check) once Folder View is built, not at removal time
- `SEARCH_PLACEHOLDERS`: no change needed — `'2000ad'` is already absent

**`frontend/css/style.css`**
- `/* ── 2000 AD year grid ───... */` block: `#adYearGrid`, `.year-card`,
  `.year-card:hover`, `.year-card-cover`, `.year-card-cover img`, `.year-card-year`,
  `.year-card-range` (~30 lines, around line 563)
- `/* 2000 AD year detail heading */` block: `.ad-year-heading` (~7 lines, around
  line 602)

**Confirmed NOT present (no action needed):**
- No other Python files under `backend/` reference 2000 AD
- No `TwoThousandAD` or `2000AD` identifiers anywhere in the codebase
- No page-level route `/2000ad` in `main.py` — the surface was always SPA/client-side
- The `sessionStorage` back-link label fix (CUSTOM_TABS_SPEC.md §8, 2026-06-19) patched
  around "four fixed surface names" (Home/All/Singles/Series). 2000 AD was never in
  that fix; removing 2000 AD does not require simplifying or touching it.

**Do not touch:** the actual `2000 AD` files/folders on disk, or the `series` value
itself in scanned metadata — those are real data, untouched. Only the hardcoded
*code path* is being removed. Once this ships, Tez will manually re-add 2000 AD as
an ordinary custom tab (Folder View mode) via the Admin UI — that's a normal user
action, not part of this build.

---

## Part B — Amend `CUSTOM_TABS_SPEC.md`: Folder View

Append the following as new sections to `CUSTOM_TABS_SPEC.md` (renumber to fit after
existing §6, before the current §7 Build Order / §8 Change Log — or append as new
top-level sections and resequence, whichever keeps the doc cleanest). Add a Change
Log entry per the existing convention.

### View Mode (extends §2 Data Model)

New column on `custom_tabs`:

| Column | Type | Notes |
|---|---|---|
| `view_mode` | TEXT NOT NULL DEFAULT 'flat' | `'flat'` (existing v2.1 behaviour, unchanged) or `'folder'` (new) |

Existing rows get `'flat'` via migration default — no behaviour change for tabs
created before this ships. Admin's "Add Tab" / edit form (§5.1) gets a new control
to choose view mode at creation, and it should be editable after creation (an admin
might want to flip an existing flat tab to folder view without recreating it).

**Migration note:** `database.py`'s `init_db()` already calls
`_add_missing_issue_columns()` which does ALTER TABLE for additive Issue columns —
follow the same pattern: add a `_add_missing_custom_tab_columns()` function that runs
`ALTER TABLE custom_tabs ADD COLUMN view_mode TEXT NOT NULL DEFAULT 'flat'` if the
column is absent, and call it from `init_db()`. Do not rely on `create_all()` for
this — it only creates missing *tables*, not missing columns on an existing table.

### Folder View — Browse mode

At any folder level (starting at the tab's `folder_path` root), render a **mixed
grid**:
- Loose files directly in that folder render as flat issue cards — same card as
  the All tab, page count shown.
- Subfolders render as folder cards, showing a **recursive** issue count (every
  issue anywhere underneath that folder, not just direct children).
- A folder with no subfolders left renders as a pure flat file grid (the terminal
  case — most custom tabs pointed at a normally-structured library folder will hit
  this immediately, since folder = series/single there).

Clicking a folder card drills into that folder, repeating the same mixed-grid logic
one level down.

**Navigation uses real browser history**, not an in-page toggle — this is a
deliberate departure from how the old 2000 AD years page worked (which used a DOM
show/hide toggle on `adBackBtn`, not `history.back()`). Each level down pushes a
history entry and updates the URL (e.g. `/tabs/{id}?path=<relative-path>`), so
back/forward/refresh/bookmark/share-link all land on the exact folder level expected.
This matches the `history.back()` convention already established elsewhere
(`CHANGELOG.md` 2026-06-21/06-22 back-button fixes) — Folder View should follow
the same pattern, not reintroduce the old toggle behaviour.

Breadcrumbs derive from the URL's `path` param.

### Folder View — Search mode

When a search term is entered inside a Folder View tab, browse mode is replaced
entirely by **flat, depth-agnostic results**: same filter/sort/grid-list/pagination
machinery as the All tab (reuse that rendering path, same as flat-mode custom tabs
already do), scoped to the whole tab's folder subtree rather than the current
folder level, with each result showing its folder path so the user can see where
it lives. Clearing the search returns to browse mode at whatever folder level was
active before the search started.

### Mark All Read (per folder)

A "Mark all read" action available at any folder level in browse mode, scoped
**recursively** — it marks every issue anywhere under the current folder as read,
matching what the folder's displayed issue count represents (the count and the
action must agree, since the count is what told the user how much "all" means
before they clicked it).

### Backend

- A folder-contents endpoint for Folder View browse mode: given a tab `id` and a
  relative `path` under its `folder_path`, return immediate child folders (each
  with a recursive issue count) and immediate child files (issue cards), at that
  level only — this is distinct from the existing flat-mode issues endpoint.
- The existing flat-mode issues endpoint (`GET /api/library?tab_id=...`) is reused
  as-is for Folder View's search mode — just confirm its folder-path-prefix filter
  already covers "whole subtree" (it should, since that's exactly what flat mode
  already does for the tab's root via `is_under()` in `library.py`).
- A recursive "mark all read" endpoint scoped by tab `id` + relative `path`.
- Recursive issue-count computation for folder cards — confirm this is cheap enough
  to compute per-card at the library's current size (~5,500 issues); the existing
  `is_under()` filter in `path_utils.py` is the right primitive to reuse here. If
  N+1 query patterns show up, flag it rather than shipping something that'll slow
  down as the library grows.

### Frontend

- New folder-grid template/component for browse mode (mixed file+folder cards).
- Route/history wiring for `path`-based navigation (per the history behaviour above).
- Breadcrumb rendering from the active path.
- Search-mode toggle that swaps the folder-grid for the reused All-tab-style flat
  result list, and back again on clear.
- "Mark all read" button at folder level, wired to the new recursive endpoint.
- Folder View flat file cards must remain compatible with the existing multi-select
  mechanism (long-press to select, bulk Read/Unread/Favorite/Rate) — see Part A's
  note on updating the multi-select scope comment in `app.js` (MULTI-SELECT block).

### Out of scope (unchanged from existing Custom Tabs scope, §6)

- Nav reordering, nav overflow handling
- Flutter app
- Anything not explicitly listed above

---

## Part C — Build order

1. Confirm Part A hit list is complete via a fresh grep before touching anything
   (the list above was produced by a docs-session code read, not a live grep —
   Code should verify it matches the repo state at build time)
2. `custom_tabs.view_mode` column + migration (add `_add_missing_custom_tab_columns()`
   in `database.py`, call from `init_db()`, default `'flat'` for existing rows)
3. Folder-contents backend endpoint (recursive counts) + recursive mark-all-read
   endpoint
4. Folder-grid frontend component + history/URL wiring + breadcrumbs
5. Search-mode wiring (reuse existing flat-mode issues endpoint, swap rendering)
6. Mark-all-read button wiring
7. Admin UI: add view-mode choice to the Add/Edit Tab form (§5.1 amendment)
8. Multi-select compatibility check on Folder View's flat file cards; update the
   multi-select scope comment in `app.js` from "2000 AD prog cards" to
   "Folder View flat file cards"
9. Remove 2000 AD: API endpoints (`/api/2000ad/years`, `/api/2000ad/year/{year}`),
   nav button, `adView` HTML block, `app.js` functions and surface references,
   and CSS blocks — per the confirmed hit list in Part A
10. Manual test pass (Part D)

---

## Part D — Manual test pass

In addition to the existing Custom Tabs test pass (§7 of the original spec — add a
tab, confirm content matches folder, hide/show, hit the 4-visible cap, delete,
confirm untouched files on disk), add:

- **Confirm 2000 AD fixed tab fully removed** — no nav entry; API endpoints
  `/api/2000ad/years` and `/api/2000ad/year/{year}` return 404; no leftover
  references found by a fresh grep for "2000 AD" / "2000ad" / "adView" in
  `backend/`, `frontend/js/`, `frontend/*.html`, `frontend/css/`
- Recreate 2000 AD as an ordinary custom tab, Folder View mode, pointed at its
  on-disk folder — confirm the year-folder structure renders as expected in browse
  mode, with recursive counts matching reality
- Drill down multiple levels (where applicable), confirm back/forward/refresh all
  land on the correct folder level
- Search inside the 2000 AD custom tab — confirm results are depth-agnostic and
  show folder path per result (this is the searchability 2000 AD never had before)
- Mark all read at a folder level, confirm it's recursive and matches the displayed
  count
- Confirm multi-select still works on flat file cards inside Folder View
- Confirm a tab created before this build (flat mode, untouched) still behaves
  exactly as it did in v2.1 — no regression from the new `view_mode` column

---

## Change Log entry to add to `CUSTOM_TABS_SPEC.md` §8

| Date | Change | Reason |
|---|---|---|
| *(fill in on build)* | Added `view_mode` (`flat`/`folder`) to `custom_tabs`. Folder View generalises 2000 AD's old hardcoded two-level year-grid into a reusable per-tab mode: recursive folder/file mixed-grid browsing with real history-backed navigation, depth-agnostic search, and recursive Mark All Read. The 2000 AD fixed tab is fully removed; 2000 AD becomes an ordinary custom tab (Folder View) post-build, consuming a normal visible-tab slot. | v2.2 planning — 2000 AD's bespoke view was always meant to be removed before the app went public; Folder View captures the part of its behaviour that was actually useful and makes it available to any custom tab. |
