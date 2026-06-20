# ComicVault — HOME_STRIPS_SPEC.md (V2.1)

> **How to use this document**
> Paste this entire file into a Claude Code session alongside `SPEC.md` for context on the
> existing system this plugs into. This is the single source of truth for the Editable
> Home Page Strips feature (v2.1). Record any deviations at the bottom of this file
> (Change Log), same convention as `SPEC.md`, `EDITOR_SPEC.md`, and `CUSTOM_TABS_SPEC.md`.
>
> **Status:** Built and verified (2026-06-19) — see `progress.md` "V2.1 — Home Strips
> Built (2026-06-19)" for the build log. This was the second v2.1 feature tackled
> (after `CUSTOM_TABS_SPEC.md`). Taskbar app changes and mobile reader changes are
> tracked in `comicvault-changes.md`, which supersedes the now-removed
> `v2_1-main-new-features.md`.

---

## 1. Overview & Goals

Make the Home page's cover strips admin-editable, while leaving the existing default
strips structurally untouched (not removable, not editable), and allowing the admin to
add up to 5 additional strips, each based on a single field+value filter or a single
folder.

**Note on SPEC.md drift:** SPEC.md Section 20.4 documents 5 default strips (including
Random Single and Random Series). The live build has since diverged from that — this
spec reflects the **actual current state**, below. SPEC.md Section 20.4 should be
corrected separately to match; not done as part of this feature, flagging so it isn't
missed.

**Existing default strips (unchanged content/logic), in order:**
1. **Continue Reading** — issues with status "reading". **Conditionally visible**: only
   rendered at all when at least one such issue exists. When present, it is always
   pinned to the top, ahead of every other strip (default or added).
2. **Recently Added** — most recently imported.
3. **Random Unread** — a random unstarted comic. Refreshes each visit.
4. **Random Genre** — a genre picked at random; heading shows the plain genre name.

These keep their current behaviour exactly as built. The only new capability applied to
them is **reordering** (see Section 5) — though Continue Reading's "always pinned to
top when present" rule takes precedence over its stored `position` (see Section 4.4).

**New capability — admin-added strips:**
- Up to **5** additional strips (cap chosen for performance — each strip is a query
  against the library, more strips means more home-page load work).
- Each added strip is based on **one** of:
  - A single field + single value (Genre, Publisher, Writer, Artist, Format, Decade,
    Year, Rating, or B&W — the same nine dimensions as the existing filter dropdowns),
    **or**
  - A single folder (+ subfolders) — same folder-scoping mechanism as Custom Tabs
    (`CUSTOM_TABS_SPEC.md`), reused here rather than reimplemented.
- No combining criteria within one strip (e.g. no "Genre=Horror AND Decade=1990s") —
  keep each strip to one filter dimension or one folder.
- Each strip shows **15 covers max**, same as existing strips, with a clickable heading
  → full listing page, same as existing strips.

---

## 2. Data Model

Single unified table, `home_strips`, holding **both** default and admin-added strips.
Unifying them (rather than treating defaults as separate hardcoded markup) is what
makes "reorder everything together" (Section 5) straightforward — position is just a
column every row has.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | |
| `is_default` | BOOLEAN NOT NULL | `true` for the 4 existing strips, seeded once via migration. Locks `name`, `basis_type`, `field_name`, `field_value`, `folder_path` from editing or deletion — only `position` is mutable for these rows (and for the Continue Reading row specifically, `position` is stored but overridden at render time per Section 4.4). |
| `name` | TEXT NOT NULL | Heading shown on the home page. Admin-set for added strips; fixed text for defaults ("Random Genre" still computes its displayed genre name live per SPEC.md 20.4 — this column is the static heading label, not the dynamic per-visit genre name). |
| `basis_type` | TEXT NOT NULL | `'builtin'` (the 5 defaults, logic lives in existing code, not driven by the columns below), `'field'`, or `'folder'` |
| `field_name` | TEXT NULLABLE | One of: `genre`, `publisher`, `writer`, `artist`, `format`, `decade`, `year`, `rating`, `bw`. Only set when `basis_type = 'field'` |
| `field_value` | TEXT NULLABLE | The specific value within `field_name` (e.g. `"Horror"`). Only set when `basis_type = 'field'` |
| `folder_path` | TEXT NULLABLE | Only set when `basis_type = 'folder'`. Same validation rules as `CUSTOM_TABS_SPEC.md` Section 4.1 |
| `order_mode` | TEXT NULLABLE | `'random'` or `'fixed'`. Not applicable to `'builtin'` rows (each default strip's randomness is already defined by its own existing logic) |
| `sort_field` | TEXT NULLABLE | Only used when `order_mode = 'fixed'`: `'title'`, `'newest'`, or `'recent'` — reuses the existing Title/Newest/Recent sort vocabulary from SPEC.md 20.2, applied to the filtered set instead of the whole library |
| `visible` | BOOLEAN NOT NULL DEFAULT 1 | Only meaningful for non-default rows — defaults are always visible and this column is unused/ignored for them (see Section 4.4) |
| `position` | INTEGER NOT NULL | Explicit display order, mutable for **all** rows including defaults |
| `created_at` | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | |

### Migration

Seed 4 rows with `is_default = true`, `basis_type = 'builtin'`, `position = 0..3` in
the current default order (Continue Reading, Recently Added, Random Unread, Random
Genre), `name` set to each strip's current static heading text.

---

## 3. Caps

- **Maximum 5 non-default strips total** (visible + hidden combined — unlike Custom
  Tabs, there's no separate "stored vs visible" distinction needed here since the
  performance concern is about total strip count existing, not just what's currently
  shown). Enforce server-side on create.

---

## 4. Backend

### 4.1 Field-value population

For `basis_type = 'field'`, the admin UI needs live values per `field_name` to populate
a second dropdown once the field is chosen (e.g. picking "Genre" then seeing every
genre actually in the DB). Reuse the existing live-populated filter-dropdown endpoints
already built for the browse filter bar (SPEC.md 20.2 — Genre, Publisher, Writer,
Artist, Format, Decade, Year, Rating, B&W are all already DB-driven there). Don't
duplicate this logic; point the new admin UI at the same source.

### 4.2 Folder validation

Identical rules to `CUSTOM_TABS_SPEC.md` Section 4.1 — must exist on disk, should
resolve under a configured library root (warn, don't block, if outside).

### 4.3 Endpoints (suggested)

- `GET /api/admin/home-strips` — list all rows (default + added, visible + hidden)
- `POST /api/admin/home-strips` — create a non-default strip: `{name, basis_type,
  field_name?, field_value?, folder_path?, order_mode, sort_field?}`. Validates per
  4.1/4.2, enforces the 5-strip cap (Section 3), assigns next `position`.
- `PATCH /api/admin/home-strips/{id}` — update a non-default strip's editable fields,
  or update `visible`. For `is_default = true` rows, only `position` may be changed via
  this endpoint — reject attempts to change anything else on a default row with a clear
  error rather than silently ignoring it.
- `PATCH /api/admin/home-strips/reorder` — bulk position update, `[{id, position}, ...]`
  covering all rows (default and non-default together), since reordering mixes them
  freely.
- `DELETE /api/admin/home-strips/{id}` — hard delete. Reject with a clear error if
  `is_default = true`.
- `GET /api/home/strips` — the actual home-page data endpoint (likely already exists
  per SPEC.md's `backend/routers/home.py`; extend it). Returns all `visible` strips
  (non-Continue-Reading defaults always included) in `position` order, with Continue
  Reading rendered first whenever it has any matching issues (per 4.4), each resolved
  to up to 15 covers:
  - `builtin` → existing per-strip logic, unchanged
  - `field` + `random` → 15 random matching issues, computed fresh on every request
    (cadence = every visit, confirmed — no session caching needed, this simplifies
    the implementation versus the existing once-per-session Random Genre behaviour)
  - `field` + `fixed` → 15 matching issues ordered by `sort_field`, same every request
  - `folder` + `random` → 15 random issues under that folder path, fresh every request
  - `folder` + `fixed` → 15 issues under that folder path, ordered by `sort_field`

### 4.4 Default-row visibility and pin behaviour

Three of the four default strips (Recently Added, Random Unread, Random Genre) are
always shown — no hide control for them in this build, matching "current default
strips can't be removed or edited" (reordering is the only capability available on
these rows). Don't expose a visibility toggle for these `is_default = true` rows in
the admin UI; `visible` is functionally always-true for them and can be ignored.

**Continue Reading is the one exception**, and existing, unchanged behaviour — not a
new rule introduced by this feature:
- It only renders when at least one issue has status "reading." This is existing logic
  in `builtin` strip resolution, not driven by the `visible` column.
- When it renders, it is **always pinned first**, ahead of every other strip regardless
  of stored `position`. Its `position` value still exists in the table (so the reorder
  list, Section 5.1, can display it at whatever position the admin last dragged it to —
  useful for if/when this pin rule is ever revisited), but `GET /api/home/strips`
  should render it first whenever present, overriding the position-sort for every
  other row.

---

## 5. Frontend

### 5.1 Admin page — Advanced Settings section

New "Home Page Strips" subsection, same locked/unlock pattern as Custom Tabs and the
rest of Advanced Settings.

Contents:
- **Ordered list of all 9 possible rows** (4 default + up to 5 added), drag-reorderable
  (or up/down buttons if drag-and-drop is more than this needs) — calls the bulk
  `reorder` endpoint on change. Continue Reading's row should carry a note in this list
  (e.g. "pinned first when active") so the admin isn't confused when dragging it
  elsewhere has no visible effect while a reading-status issue exists.
- Default rows show name + a "Default" badge, **no edit or delete controls**, just
  their position in the reorder list.
- Added rows show: name, basis summary (e.g. "Genre: Horror" or folder path), order
  mode + sort field if fixed, a visible/hidden toggle, and a **Delete** button (hard
  delete, confirm dialog — same wording convention as Custom Tabs: only removes the
  strip definition, never touches files or library data).
- **"Add Strip" form**: name field, then a basis-type choice:
  - **Field-based**: dropdown of the 9 field names → second dropdown of live values
    for the chosen field (per 4.1)
  - **Folder-based**: same Browse/manual-path picker pattern as Custom Tabs
  - Then **order mode**: Random, or Fixed (+ a Title/Newest/Recent dropdown if Fixed
    is chosen)
  - "Add Strip" disabled once 5 non-default strips already exist, with an explanatory
    note (delete one first to add another — no hidden-on-creation path, consistent with
    the Custom Tabs cap decision)

### 5.2 Home page rendering

Strips render in `position` order, defaults and added strips interleaved exactly as
ordered. Each strip's heading is clickable → full listing page, same mechanism already
in place for the default strips (extend it to cover field/folder-based strips —
likely just pointing the "view all" link at a filtered All-tab style query for field
strips, or the relevant custom-tab-style folder query for folder strips, rather than
building a new listing page type).

---

## 6. Explicitly Out of Scope (This Build)

- Combining multiple criteria in one strip
- Per-strip admin control over random-refresh cadence beyond the random/fixed choice
  already specified (no "refresh every N minutes" or similar)
- Editing or hiding default strips (reorder only)
- Flutter app — web UI only, consistent with Custom Tabs scope decision
- Any change to the existing 5 default strips' own internal logic

---

## 7. Build Order (suggested)

1. `home_strips` table + migration seeding the 4 defaults
2. Backend CRUD endpoints (4.3) + field-value reuse (4.1) + folder validation (4.2) +
   cap enforcement (Section 3)
3. Extend `GET /api/home/strips` to resolve `field` and `folder` basis types per 4.3,
   leaving `builtin` rows on existing logic untouched
4. Reorder endpoint + admin UI drag/reorder list (5.1)
5. Admin "Add Strip" form (5.1), reusing the Custom Tabs folder picker and the existing
   filter-dropdown value sources
6. Home page rendering update (5.2) — position-ordered, clickable headings wired to
   the right listing view per basis type
7. Manual test pass: reorder defaults + added strips together, add a field-based strip,
   add a folder-based strip, hit the 5-strip cap, hide/show, hard delete, confirm
   defaults remain un-editable/un-deletable throughout

---

## 8. Change Log

> Record any deviations from this spec here with date and reason.

| Date | Change | Reason |
|---|---|---|
| 2026-06-19 | Section 5.1 reorder UI built as up/down arrow buttons, not drag-and-drop. | Tez's explicit choice between the two options the spec allows — matches this codebase's existing preference for plain controls over custom widgets (e.g. Custom Tabs' visible/hidden toggle button). |
| 2026-06-19 | Section 5.2's "clickable heading → full listing page" implemented as two new transient browse surfaces, `fieldview` and `folderview` (`?surface=fieldview&field=&value=` / `?surface=folderview&folder=`), reusing the existing All-tab rendering pipeline (filters, sort, grouping, pagination) scoped server-side via new `field`/`value`/`folder_path` query params on `GET /api/library`. Applied **only to admin-added (field/folder) strips** — the 4 default strips' headings remain plain, non-clickable text, unchanged from their current behaviour. | 5.2's wording ("same mechanism already in place for the default strips") assumes defaults already have clickable headings; they don't — that capability was never actually built despite `SPEC.md` §20.4 describing it. Building it for defaults too would be new scope this feature doesn't require (§6: "no change to the existing default strips' own ... logic"), so left as a separate, unfixed gap rather than absorbed into this session. |
| 2026-06-19 | Continue Reading's resolution logic now lives in `backend/routers/home.py` (`_strip_continue_reading`), duplicating the query already in `backend/routers/library.py`'s standalone `GET /api/reading/continue` rather than calling it. | No cross-router imports exist anywhere else in this codebase; the query is ~6 lines. The standalone endpoint is left completely unmodified since the Flutter app depends on it and is explicitly out of scope (§6). |
