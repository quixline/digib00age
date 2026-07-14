# ComicVault — v2.6: Build Plan

> **Status: Item 1 — ✅ complete as of 2026-07-08.** Handed to Code
> 2026-07-07, built across Phases A/B/C1/C2a/C2b/C2c/D/E plus two
> cross-cutting follow-ups (open-dropdown-panel styling, CoverCard
> selection circle) — see each phase's own status note below for detail.
> `docs/v2.6/` created 2026-07-06, alongside Item 1's handoff, per
> `ROADMAP.md`'s established pattern (working folder created alongside
> implementation, not ahead of it). This redesign was scoped visually in
> Claude Design (canvas exploration + inline annotations), not through a
> written spec pass — exact layout, colour, typography, and spacing
> values live in the Design handoff itself, not duplicated here. This doc
> tracks scope boundaries, decisions, and build status only.
>
> **How to use this document**
> This is the ordered build queue for v2.6. Paste into a Claude Code
> session alongside the Design handoff. Items are marked ✅ when built and
> verified. Bugs and minor fixes are tracked separately in `BUGS.md` —
> don't add them here unless they block a build item.
>
> **Always reference items from other docs as "v2.6 Item N", never bare
> "Item N"** — see `meta/working-rules.md` "Version-qualified references."

---

## Item 1 — Web UI Redesign (navigation, admin page, visual system)

**Feature.** Full visual/structural redesign of the web UI, built in Claude
Design and handed to Code via the Design→Code connector.

**In scope:**
- Navigation relocated from top tabs to a left-side nav.
- "Tabs" reconceived as "Libraries" — side nav supports multiple library
  entries (previously Custom Tabs).
- Full colour palette and typography system overhaul, site-wide.
- Spacing system overhaul, site-wide.
- Admin page: full visual overhaul, including a stats-card redesign.
- Home strips: unchanged — carried over as-is from the current design.

**Full per-screen scope checklist (added 2026-07-07 — the bullets above
and the phase list below are both prose summaries, not an itemised list;
this is the itemised one, cross-checked directly against the Design
project's `screens.jsx`/`parts.jsx`/`admin.jsx`, not just described from
memory. Update this checklist, not just the phase list, if anything else
turns up.):**

| Screen | What changes | Phase |
|---|---|---|
| Header (all pages) | Slim bar: sidebar toggle, brand lockup, search, settings, login/logout | B ✅ |
| Left sidebar (all pages except Admin) | Primary nav, status shortcuts, Libraries list, collapse/expand | B ✅ |
| Home | Strips unchanged | out of scope (unchanged) |
| **Browse (All/Singles/Series/a custom tab's flat listing)** | Filter/sort bar restyled — visual only, every existing field/control kept. | D ✅ |
| **CoverCard (Browse grid + Folder View — Home strips excluded, no selection feature there)** | Hover-reveal selection circle added, closing the one real gap found in a full Design-vs-implementation scan of `CoverCard.jsx` (read-state colours, badges, progress bar, hover-lift all already matched from Phase A). | ✅ (2026-07-08, cross-cutting, not tied to one lettered phase) |
| Series detail | Backdrop opacity bug fixed (was rendering full-strength, not the intended subtle wash); issue-row treatment, tag/genre chips, credits layout all already matched Design, confirmed via line-by-line comparison, not just assumed. | E ✅ |
| Issue detail | New faint cover backdrop added (previously had none at all). Two-column layout, badges, credits, ratings, toggle buttons all already matched Design. | E ✅ |
| Admin | Category → sub-item → content-pane IA restructure | C1 ✅ / C2a ✅ / C2b ✅ — complete |

**Browse filter/sort bar — what's actually different (found in
`screens.jsx`'s `BrowseScreen`, confirmed against the live Design canvas
screenshot, not the possibly-stale handoff bundle):**
- Design's bar: `A–Z` sort dropdown (options include Z–A/Year/Recently
  Added/**Rating** folded in as a sort mode) · sort-direction toggle (↑) ·
  `★ Favourites` toggle · divider · `Genre`/`Format`/`Decade`/`Publisher`/
  `B&W` dropdowns · [spacer] · grid/list toggle · big `N Titles` count.
  Controls are borderless/minimal — no background box, no visible border
  until interacted (`.ds-filter`/`.ds-mb-btn` in `Library.html`'s kit-local
  CSS: `background:none; border:none; color:var(--text-secondary)`,
  active/hover just changes text colour to accent).
- Real app's current bar (`frontend/index.html` `#menuBar`, unchanged by
  Phases A/B): separate `Rated` star dropdown, separate `Year` filter
  *alongside* `Decade`, a `Group by` dropdown, and a `Clear` button — none
  of which appear in the design's `BrowseScreen` at all. Controls are
  boxed pills (`.filter-select` / `.sort-dir-btn` etc. — `background:
  var(--surface-2); border: 1px solid var(--border); border-radius: ...`),
  the pre-redesign visual language, just re-coloured by Phase A's token
  swap, not restructured.

**Resolved 2026-07-07 (was an open question, see `DECISIONS.md` for the
full rationale):** `Group by`, the separate `Year` filter, the separate
`Rated` dropdown, and `Clear` are **not** being dropped. Design was
working from an incomplete snapshot of the app's files and never had
visibility into these controls — their absence from the mockup isn't a
scope decision, it's a gap in what Design saw. **Phase D is a visual
restyle only** — every current field/control in `#menuBar` stays exactly
as-is functionally; only the styling (borderless/minimal controls,
hover/active states, spacing) changes to match the Design output.

**Detail source:** Claude Design canvas + inline annotations, handed to
Code directly via the Design connector — not duplicated into this doc.
Refer to the live Design project for exact layout/spacing/colour values
and any per-element implementation notes.

**Explicitly out of scope for this item (deliberately left for later):**
- BUG-014 (back-button/header unification) — separate pass once this
  lands, not bundled in.
- BUG-015 (genre filter can't be cleared) — parked, revisit after
  redesign is in.
- Mobile/Flutter UI redesign — separate item, scoped independently, not
  started.

**Open question, not blocking handoff:** "Libraries" replacing "Custom
Tabs" in the UI — does this rename ripple into `CUSTOM_TABS_SPEC.md`'s own
terminology, or does the spec keep "Custom Tabs" as the internal/technical
name while the UI surfaces "Libraries"? Decide before post-build spec
updates, not before build starts.

**Also confirmed with Tez, 2026-07-07 (not in the original scope bullets
above):** the design system's own readme frames this as a full visible
brand rename — **digib00age** replaces "ComicVault" in the header logo,
page titles, and favicon. "ComicVault" stays as the repo/internal/codebase
name (DB, API, `config.json`, tray app) — this is UI-visible-copy only.

**Build sequencing (decided 2026-07-07, given the size of this item):**
phased across multiple sessions rather than one continuous build —
- **Phase A — ✅ built 2026-07-07.** Design tokens (colour/typography/
  spacing/elevation) merged into `style.css` site-wide, plus the brand
  rename above. No structural/nav changes. Manually verified in dark and
  light theme across Home/Browse/Series/Issue/Admin — see
  `v2.6/progress.md` for the full build/verify log.
- **Phase B — ✅ built 2026-07-07.** Left sidebar nav replaces the top
  `.surface-nav` tab bar and header status-pills row, across all three real
  pages (index/series/issue — the design's single-SPA-shell assumption
  doesn't hold in the real app). Read-status filtering is now a sidebar
  shortcut that always jumps to All, pre-filtered — not a per-surface
  toggle like before; matches the approved design exactly, documented as a
  deliberate behaviour change in `MENU_BAR_SPEC.md`/`CUSTOM_TABS_SPEC.md`.
  Manually verified in dark and light theme — see `v2.6/progress.md`.
- **Phase C1 — ✅ built 2026-07-07.** Admin page IA restructure, part 1:
  category → sub-item → content-pane nav for **Library Management** and
  **Library Appearance** (the 10 sub-items Design actually built content
  for) — see the mapping table above. Every existing `admin.html` element
  ID preserved; `admin.js`/`processingTools.js`/`filePicker.js` untouched
  except one new additive `bindAdminNav()` function. Home Page Strips and
  Add/Remove Libraries moved out from behind the "Unlock advanced
  settings" gate (`DECISIONS.md`). Manually verified in dark and light
  theme, including one real functional round-trip test (Card Size change
  → localStorage → revert) — see `v2.6/progress.md`.
- **Phase C2a — ✅ built 2026-07-07.** Admin page IA restructure, part 2:
  category → sub-item → content-pane nav for **Editor Options** (Genre
  List, Format List — moved out from behind the advanced-settings lock,
  same treatment as Phase C1's Home Strips/Libraries) and **Advanced
  Settings** (Password Protection, Change Server Port + Reader Location
  folded into one sub-item, Wipe Database, Wipe Reading State — split out
  of the old single "Danger Zone" subsection into two separate sub-items;
  all four stay behind the existing "Unlock advanced settings" gate, not
  reclassified). Every existing `admin.html` element ID preserved;
  `admin.js` extended only by adding two entries to the existing
  `ADMIN_CATEGORIES` array — `bindAdminNav()` itself unchanged. Processing
  Tools section untouched, still old-style always-visible. Manually
  verified in dark and light theme, all 4 new sub-items and the
  lock/unlock gate — see `v2.6/progress.md`.
- **Phase C2b — ✅ built 2026-07-07.** Admin page IA restructure, part 3
  (final category): **Processing Tools** — Filename Editor, Converter:
  Archives & Images (Convert Archives + Convert Images combined into one
  pane), **new standalone XML Tagging tool**, Folder Processing (Sort by
  Filename), Auto Processing (Processing Folder Automation minus the three
  fields relocated to XML Tagging). Real backend work: new
  `backend/routers/xml_tagging.py` modeled on `filename_sort.py`, reusing
  `ct_autotag_file()`/`ct_bridge.*` verbatim; `ct_autotag_log.py`'s
  `append_entry()` gained an `auto: bool = False` param (was
  automation-only, hardcoded `[AUTO]`); registered in `main.py`. The
  ComicVine API key/threshold/save-low-confidence fields moved out of Auto
  Processing's pane into XML Tagging's (same stored config fields, same
  IDs, same existing config/test endpoints — reused, not duplicated); Auto
  Processing keeps its CT Auto-Tag enable checkbox. Every pre-existing
  `admin.html` element ID preserved; `admin.js` extended with one more
  `ADMIN_CATEGORIES` entry. Manually verified in dark and light theme, all
  5 sub-items, plus a real functional round-trip (synthetic scratch CBZ,
  not real library data — XML Tagging run confirmed a non-`[AUTO]` log
  line written alongside untouched `[AUTO]` lines from prior automation
  runs; Save & Test re-verified from its new location) — see
  `v2.6/progress.md`. **Admin page IA restructure (Phases C1/C2a/C2b) is
  now complete** — every category is nav-driven, nothing left on the old
  one-long-scrolling-page layout.
- **Phase D — ✅ built 2026-07-07.** Browse screen filter/sort bar restyle —
  visual only, every current field/control kept exactly as-is (resolved
  2026-07-07, see `DECISIONS.md`). Restyled `.filter-select`/`.sort-dir-
  btn`/`.fav-filter-btn`/`.view-toggle-btn`/`.group-by-select`/`.filter-
  clear` to the borderless/minimal `.ds-filter`/`.ds-mb-btn` treatment,
  fetched directly from the Design project this session (`Library.html`'s
  kit-local CSS, `screens.jsx`'s `BrowseScreen`) rather than relying on
  the prior session's description. Added a vertical divider after
  Favourites and grouped the view toggle with the title count on the
  right, matching Design's layout — pure CSS + one small HTML reorder, zero
  `app.js` changes. **Scope call:** Design's dropdowns are a fully custom
  popup-listbox component (`components/library/Dropdown.jsx`), not a
  native `<select>` — kept the real app's native `<select>` elements and
  restyled only their closed-state trigger appearance, rather than
  rebuilding them as custom widgets (real new interactive-component work,
  not a restyle, and not justified just to reskin a browser-owned popup
  list). Manually verified: every control still filters/sorts/toggles
  identically (Genre filter functional round-trip, Favourites toggle,
  Clear, grid/list view toggle all re-tested), dark and light theme, Flat
  View and Folder View (a Custom Tab's listing) both confirmed, no console
  errors — see `v2.6/progress.md`.
- **Phase D follow-up — ✅ built 2026-07-07.** Styled *open* dropdown panel
  (screenshot-driven request — Design's dropdowns are a custom popup
  listbox, and a native `<select>`'s open state can't be restyled via CSS
  at all, which is exactly the scope call Phase D's own decision entry had
  made). New `frontend/js/filterDropdown.js` layers a custom trigger+panel
  over each `.filter-select` in `#menuBar`, matching
  `components/library/Dropdown.jsx`'s `.ds-dropdown-panel`/`.ds-dropdown-
  opt` styling — the real `<select>` stays in the DOM (hidden, not
  removed) as the single source of truth, so `app.js` needed **zero**
  changes. See `DECISIONS.md` for the sync mechanism this required
  (`Object.defineProperty` on `.value` + a `MutationObserver` on
  `class`/`hidden`).
- **CoverCard selection circle — ✅ built 2026-07-08.** Found via a full
  Design-vs-implementation scan (`components/library/CoverCard.jsx`
  compared against `app.js`'s `buildCoverCard()`/`buildFolderFileCard()`/
  `buildStripCard()`) triggered by a screenshot Tez shared. A hover-reveal
  14px circle, bottom-left of the cover image, single-click alternative to
  the existing long-press-to-select gesture — stays visible (filled with
  an accent dot) once selected, independent of hover. Grid view only
  (Browse + Folder View); Home strips excluded since they have no
  selection feature to hook into. No changes to the existing selection
  state machine (`enterSelectionMode`/`toggleSelected`/`exitSelectionMode`,
  the selection toolbar, or the pre-existing whole-card `.selected` ring) —
  see `v2.6/progress.md` for the full comparison-scan results (everything
  else in `CoverCard.jsx` already matched, Phase A's token remap having
  done a genuinely thorough job).
- **Phase E — ✅ built 2026-07-08.** Series/Issue detail visual polish.
  Line-by-line comparison of Design's `screens.jsx` (`SeriesScreen`/
  `IssueScreen`) and `elevation.css` tokens against the real
  `style.css`/`app.js` found the scope was much narrower than the
  original checklist framing implied — issue-row treatment, genre tag
  chips, credits grid, rating stars, status/favourite toggle buttons were
  all already matching (same pattern as the Browse/CoverCard scans
  earlier this item). Two real, concrete gaps: (1) `.series-backdrop-img`
  had `opacity: 1.5` (clamps to full strength — a bug, not a design
  choice) instead of Design's intended `0.28` wash; (2) the Issue detail
  page had no backdrop at all. Formalized `--blur-backdrop`/
  `--backdrop-opacity`/`--backdrop-overlay` as real tokens (values read
  directly from Design's `elevation.css`), fixed the Series bug, and
  added a new faint 440px top-fading backdrop to `buildIssueDetail()`
  matching Design's fainter/taller Issue-page variant. See
  `v2.6/progress.md` for the full comparison and `DECISIONS.md` for the
  one scope call made along the way (the backdrop doesn't extend behind
  the static "← Back" button).

**Status:** Handed to Code 2026-07-07. Phases A, B, C1, C2a, C2b, and D
(plus its open-dropdown-panel follow-up and a small C2b follow-up polish)
built and verified 2026-07-07; the CoverCard selection circle and Phase E
followed on 2026-07-08 — **v2.6 Item 1 (Web UI Redesign) is now
complete.** The Admin IA restructure, the Browse bar (including its open
dropdowns), CoverCard, and Series/Issue detail all now match the Design
reference.

---

## Item 2 — Performance fixes (from the 2026-07-09 `PERFORMANCE.md` baseline)

**Feature.** Working through the fixable findings ranked in
`docs/PERFORMANCE.md`'s first baseline, one at a time — each phase gets its
own manual test + commit before the next starts (per `CLAUDE.md` Section 3).
Not-fixable-in-code findings from that baseline (scanner-at-scale, cold-idle
drive effect, the `localhost` DNS artifact) are out of scope here — see
`PERFORMANCE.md` §1 for why.

- **Phase 1 — ✅ built and manually verified 2026-07-12.** `GET /api/library`
  N+1 fix (`backend/routers/library.py`): eager-load `Issue.genres` via
  `selectinload` (was accessed per-issue via lazy relationship across
  ~5,400 issues) and batch the per-series `ReadingProgress` query into one
  query across all issues in scope (was one query per unique series, 2,080
  series = 2,080 round-trips). In-process check: **7,508 → 13 queries,
  3.9-4.1s → ~0.63-0.67s median**. Manually verified: All Library loads
  visibly faster, no console errors, after a reader-server restart.
- **Phase 2 — ✅ built and manually verified 2026-07-12.** `GET /api/series/{id}`
  N+1 for large series (finding #2): batched the per-issue `ReadingProgress`
  query the same way Folder View's existing `progress_map` pattern already
  does. Also found and fixed a second N+1 the original baseline didn't name
  as root cause — the series-wide genre aggregation (`all_genres`) was also
  lazy-loading `Issue.genres` per issue; fixed with the same
  `selectinload(Issue.genres)` pattern as Phase 1. In-process check: 2000 AD
  (2,483 issues) **4,969 → 9 queries, 2.5-2.7s → ~0.33-0.42s median**; Postal
  (25 issues) 53 → 5 queries. Manually verified live after a reader-server
  restart: 2000 AD loads fast, no console errors.
- **Phase 3 — ✅ built and manually verified 2026-07-13.** Reader
  page-serving (findings #4/#5): `_sorted_pages()`
  (`backend/routers/reader.py`) now caches the sorted page list per archive
  path in-process, keyed on `(mtime, size)` so a rescan/replace invalidates
  automatically, instead of re-parsing the ZIP central directory on every
  `/api/page/{id}/{n}`, `/api/issue/{id}/pages`, and cover-fallback call.
  In-process check (issue 11, Four Horsemen #1): cold parse 5,483ms (this
  file was genuinely cold-disk this run, consistent with finding #9's
  cold-idle drive variance, not a regression) → warm cache-hit
  0.08-0.13ms. Manually verified live after a reader-server restart:
  flipping through several pages of a comic, no console errors.
- **Phase 4 — ✅ built and manually verified 2026-07-13.** Cover image
  caching (finding #3): `GET /api/cover/{id}` (`backend/routers/reader.py`)
  now sends `Cache-Control: public, max-age=86400` + an `ETag`, and honors
  `If-None-Match` with a real `304` — Starlette's `FileResponse` computed an
  ETag but never checked it against the incoming request, so nothing was
  ever actually revalidated before this fix. Verified via `TestClient`
  in-process, then against the live already-restarted server over direct
  HTTP: first request 200 with headers, second request with that ETag as
  `If-None-Match` → 304. Tez confirmed live: All Library loads faster with
  no console errors (a same-URL scripted browser reload didn't show 304s in
  the network log — a browser-automation cache-revalidation quirk, not a
  server issue, ruled out by the direct-HTTP check against the same
  process).
- **Phase 5 — ✅ built and manually verified 2026-07-13.** Full Editor
  page-preview (finding #6): unmeasured in the original baseline
  (admin-auth-gated) — Tez temporarily disabled admin password protection
  so this could be measured live. On a 1,220-page compendium, page loads
  took 25-330ms each (up to 3.7MB base64 JSON per page) with **zero**
  improvement on repeat requests — confirmed the same root cause as
  findings #4/#5 (re-parsing the ZIP central directory on every call), just
  in `backend/routers/editor_full.py`, a separate module that didn't share
  `reader.py`'s Phase 3 cache. **Scope call:** fixed the page-list N+1 only
  (same `(mtime, size)`-keyed cache pattern as Phase 3, via a new
  `_cached_image_list()` used by both `/preview` and `/page/{n}`) —
  deliberately left the full-res/base64 image encoding itself unfixed, a
  separate, more invasive change with editor-UX tradeoffs (image quality)
  not in scope for this pass. Verified via direct HTTP against the live
  server: repeat page requests dropped from flat/no-improvement
  (68ms→65ms) to a real cache benefit (153ms→53ms, 91ms→16ms across
  different pages).

**Status:** All 5 phases built and manually verified 2026-07-12/13 —
**v2.6 Item 2 (Performance fixes) is now complete.** Every fixable finding
from the 2026-07-09 `PERFORMANCE.md` baseline has been addressed; the
not-fixable-in-code findings (scanner-at-scale, cold-idle drive effect, the
`localhost` DNS artifact) remain as documented, unfixed observations per
`PERFORMANCE.md` §1/§3.

---

## Item 3 — Series Detail page pagination

**Feature.** From `INBOX.md`: "add pagination to /series/id" — the Series
Detail page's issue list (`SPEC.md` §20.6/20.7) rendered every issue in the
series flat, unpaginated, unlike every other browse surface. Large series
(2000 AD, 2,483 issues) rendered the entire list in one page load with no
way to jump around it.

- **✅ built and manually verified 2026-07-13.** Client-side pagination
  added to the Series Detail issue list (`frontend/js/app.js`
  `initSeries()`/`renderSeriesIssuePage()`), reusing the same page-size
  setting (`cv_page_size`, admin-configurable per `SPEC.md` §20.13) and the
  same page-number control look/behaviour as Browse (`‹ 1 2 3 … N ›`) —
  `renderPagination()`'s click/render logic was pulled out into a shared
  `renderPaginationControls(container, current, totalPages, onPageChange)`
  helper so both surfaces stay behaviourally identical instead of
  duplicating the control. `/api/series/{id}` still returns the full issue
  list in one response (unchanged); pagination slices client-side same as
  Browse already does for its filtered library.
- Verified live against the running dev server (`localhost:9424`, real
  library, read-only): 2000 AD (2,483 issues) paginates into 50 pages of 50
  (last page correctly 33 issues, `›` disabled on page 50); Postal (25
  issues, under one page) shows no pagination row, matching Browse's
  single-page behaviour. No console errors on either page load.

---

## Item 4 — Mobile UI Redesign (Flutter tablet app)

**Feature.** The Flutter-side counterpart to Item 1 — full rail-based
scaffold redesign of the tablet app (`flutter_app/`) to match the
digib00age web UI, per `design_handoff_tablet_app/README.md` (options 2a
portrait / 2b landscape from `Flutter App Redesign.dc.html`). Split out
from Item 1 as its own independently-scoped item on 2026-07-05 (`ROADMAP.md`
"Scope: Mobile UI Redesign") — not assumed to carry Item 1's phased
build/scope 1:1, since the two apps don't share a codebase.

**In scope:**
- Persistent left nav rail (64px collapsed / 196px expanded, 180ms
  animation), default collapsed in portrait / expanded in landscape, with a
  manual toggle override.
- Four screens replacing the old tab-based `LibraryScreen`/`SeriesScreen`:
  Home (strips), Browse (grid/list, driven by the rail's filters —
  All/Singles/Series/Unread/Reading/Read/a custom library), Series Detail,
  Issue Detail (no "Edit XML" button — app-only omission per the design
  spec).
- Dark theme tokens (`lib/theme/tokens.dart`) matching the web design
  system's colours/typography/spacing.
- Read-state visuals (unread/progress/read), favourite ring+badge, unread
  count badge, optimistic mark-read/favourite/rating updates — mirrored
  from `frontend/js/app.js`'s existing logic so the app and web UI agree on
  what counts as "unread"/"progress"/"read" for a series.

**✅ built and manually verified 2026-07-13.** New: `lib/theme/tokens.dart`;
`lib/models/custom_tab.dart`; `lib/screens/shell_screen.dart` (root scaffold
— rail + nested `Navigator`, replaces `LibraryScreen` at route `/`),
`home_screen.dart`, `browse_screen.dart`, `series_detail_screen.dart`,
`issue_detail_screen.dart`; `lib/widgets/nav_rail.dart`, `app_top_bar.dart`,
`cover_card.dart`, `status_button.dart`, `blurred_backdrop.dart`,
`comic_search_delegate.dart`, `offline_library_view.dart` (last two
extracted from the old `library_screen.dart`, reused unchanged). Extended
`Series`/`Issue` models (`favorites`, `personal_rating`, `read_count`,
`reading_count`, `writers`, `page_count`) and `ApiService`
(`getNavConfig()`, `getHomeStrips()`, `toggleFavorite()`, `setRating()`,
`getLibrary()` threaded with `tabId`/`field`/`value`/`q`) — no backend
changes needed, every endpoint already existed. Removed
`library_screen.dart`/`series_screen.dart`, fully superseded. Added
`google_fonts` dependency (Hanken Grotesk) — see `DECISIONS.md`.

**Three real bugs found and fixed via on-device testing** (Lenovo tablet,
real library/server), not caught by `flutter analyze` or a simulator:
1. Cover cards overflowing their allotted height on Home strips and Browse
   grid (2-line-title sizing math was short).
2. Series Detail eagerly built every issue row into one `Column` —
   instant for small series, an ~8s frozen spinner for 2000 AD (2,483
   issues). Switched to a lazy `SliverList.separated`.
3. `_IssueRow`'s card combined a non-uniform `Border` (status-coloured left
   edge, grey elsewhere) with a `borderRadius` — `BoxDecoration` silently
   refuses to paint that combination (no error banner, nothing in `adb
   logcat` unless a live Dart console is attached via `flutter run`), so
   every issue row in every series rendered as a blank grey box. Fixed by
   layering the coloured edge as a separate `Positioned` strip instead of
   folding it into the border.

**Two follow-up fixes from Tez's own manual pass** (same day): Browse was
missing the logo/search/settings header the design prototype also shows
there (only `HomeScreen` had it) — extracted into a shared `AppTopBar`
widget, used by both. The nav rail rendered vertically centered instead of
top-anchored — `Row(children: [NavRail, Expanded(...)])` had no
`crossAxisAlignment`, defaulting to `center`; added
`CrossAxisAlignment.stretch`.

**Fourth bug, found via a post-approval code review.** After Tez confirmed
the two follow-up fixes and asked for docs to be updated, a final code
check before writing this entry found that **nothing in the new
navigation reached the Reader at all** — the design mockup's Issue Detail
left column lists only Mark as Read/Add to Favourites/rating stars, no
read-entry-point, and the old `library_screen.dart`'s direct issue→reader
tap was removed along with the rest of that file. Every screen (Home,
Browse, Series Detail) now routes a tap through to Issue Detail, and Issue
Detail itself had no way to actually open a comic — a real dead end, not a
cosmetic gap. Fixed by adding a `_PrimaryButton` ("Start Reading" /
"Continue Reading" / "Read Again", depending on read status) plus a tap on
the cover image itself, both pushing `/reader` on the root navigator.
**Tez confirmed both Start Reading and Continue Reading work correctly.**

**Verified manually by Tez** on the real Lenovo tablet, real library/server:
Home strips, rail collapse/toggle, All/Singles/Series/Unread/Reading/Read
filters, grid↔list toggle, Series→Issue drill-in, mark-read/favourite/
rating (confirmed persisted server-side), portrait↔landscape rail default
with real custom libraries (2000 AD/Favourites/All the A's), offline mode
still reaches Settings, the two follow-up fixes above, and Start
Reading/Continue Reading.

**Fifth bug, reported by Tez after the above:** Browse's "All" count showed
2,080 (card count) against the web's 5,427 for the same library, and
"Singles" showed 1,870 against the web's 1,862. Root-caused directly
against the live server (`/api/library` vs `/api/library?group=Singles`)
rather than guessed at — two distinct causes, both fixed together:
1. **Count semantics.** `frontend/js/app.js`'s `isFlatSurface()` shows the
   grand total of *individual comics* (sum of each card's `issue_count`)
   for All/a custom library/the read-state shortcuts, but a plain *card*
   count for Series/Singles (`SPEC.md` §20.1/20.3 — Browse's own doc
   already specified this, the mobile build just hadn't implemented the
   distinction). `browse_screen.dart` was using card count uniformly.
   Added `_isFlatCount`, mirroring `isFlatSurface()`'s exact surface list.
2. **Singles/Series fragmentation.** `browse_screen.dart` filtered via the
   backend's `GET /api/library?group=` param, which filters at the
   *issue* level before grouping into series — so any series with mixed
   `format_group` values across its issues (found 8 real cases: e.g.
   "Nowhere Men", a 12-issue series, has one issue individually tagged
   `Singles`) produces a phantom extra 1-issue "singles" card for that
   stray issue, on top of the real series card. The web never hits this:
   it fetches the full ungrouped library once and filters client-side by
   each series-group's own single representative `format_group` (the
   cover issue's), so a mixed series always resolves to exactly one
   card, under whichever format its cover issue carries. Changed
   `browse_screen.dart` to do the same — fetch `getLibrary()` unfiltered,
   filter by `s.formatGroup` client-side — matching
   `frontend/js/app.js`'s `getFilteredLibrary()`. Custom-tab (Libraries)
   fetches are unaffected — those are genuinely server-scoped
   (folder/favourites), not a subset of the same "All" pool.
   Verified against the live server's actual JSON (not just re-running the
   app) before rebuilding: new logic produces exactly 5,427 / 1,862 / 218
   for All/Singles/Series, matching the web precisely. Confirmed again
   on-device after rebuilding.

**Scope decisions, not hidden in code — see `DECISIONS.md` for the full
rationale on each:**
- Home strip cards (issue-level, `/api/home/strips`) don't show the
  favourite ring or unread-count badge — the endpoint doesn't return
  `favorites`/`unread_count` for individual issues, only `/api/library`'s
  series-level cards do (used by Browse).
- Tapping a card: `format_group == 'Singles'` → straight to Issue Detail
  (skips a redundant "series of one" page); otherwise → Series Detail.
- Manual "sync now" button/snackbar (previously in `LibraryScreen`'s app
  bar) dropped — not in the new design spec; background sync still runs
  automatically on load and on return-from-reader.
- Icons for house/grid/book/layers use Material `Icons.*_outlined` rather
  than adding the `lucide_icons` package — avoids an unpinned new
  dependency for a purely cosmetic difference.
- Light theme not built this pass (dark-first, matching Item 1's own
  approach) — `AppColors` ships dark-only.

---

## Item 5 — Windows Desktop Reader

**Feature.** From `INBOX.md`: "rebuild desktop reader with new design"
(tracked as `BUGS.md` BUG-021, now closed — see
`archive/bugs-fixed-archive.md`). Added retroactively to this build queue,
not pre-scoped here before building.

`flutter_app/` was already one shared Dart codebase targeting both Android
and Windows (`windows/` platform folder present since the V1 initial
commit), but the Windows target had never been rebuilt, tested, or polished
— all live development, including Item 4's rail redesign, had been Android
tablet-only. Rather than porting/rewriting from the old standalone V1
Windows app (`D:\workshop\cBook_Server\flutter_app`), this extends the
existing shared codebase for Windows — same rail nav, reader, and
browse/home/series/issue screens as mobile, by construction.

**In scope, built and manually verified 2026-07-14:**
- Guarded the Android-only local-file-picker `MethodChannel`
  (`local_cbz_service.dart`) to no-op on non-Android platforms; hid the
  "Open local CBZ file" button + "Recent files" list in
  `offline_library_view.dart` on Windows. Desktop is expected to be on the
  same LAN as the server, so local-file reading was descoped there rather
  than given a Windows-native picker — the "Downloaded" offline section is
  unaffected (reads via `DownloadService`, not the picker).
- Confirmed the Android-only immersive-mode `SystemChrome` call in
  `reader_screen.dart` is a harmless no-op on Windows.
- Added keyboard support to the reader: Left/Up = prev, Right/Down = next,
  Escape = back (`toolbar_overlay.dart`, wired from `reader_screen.dart`).
  Fixed `nextPage()`/`prevPage()` in `comic_page_view.dart` to actually
  animate in Scroll mode too (previously a no-op there — the
  `PageController` those methods drove was never attached to the
  `ListView`); added a matching `ScrollController` to
  `LocalComicPageViewState`, which had none at all before.
- Rebranded the native Windows shell — `windows/runner/main.cpp` (window
  title) and `Runner.rc` (`FileDescription`/`ProductName`) — from the stock
  "comicvault" to "digib00age", matching the brand used elsewhere (favicon,
  mobile home screen). The Windows launcher icon
  (`flutter_launcher_icons`'s `windows:` block) was already current.
- Reviewed `CoverCard`/`BrowseScreen`'s grid and `ShellScreen`'s rail+content
  layout for desktop reflow — confirmed width-adaptive by construction
  (`AspectRatio` + ellipsis text, `SliverGridDelegateWithMaxCrossAxisExtent`,
  `Row`/`Expanded`), no fixed-width assumptions found.

**Out of scope (explicitly deferred):**
- The web `/issue/{id}` cover-image → "open in reader" integration — a
  separate future task.
- Registering the `comicvault://` URI scheme in the Windows registry —
  deferred to that same future integration task.
- Any installer/distributable packaging (`flutter build windows` release,
  shortcuts, pystray tray-launcher integration) — separate from the
  already-parked `ROADMAP.md` "cross-platform installer" item. Verified via
  `flutter run -d windows` only, not a built release.

**Verified:** `flutter analyze` clean; two clean rebuild/launch cycles with
no startup or reader-entry exceptions. Tez manually confirmed navigation
(rail → Home/Browse/Series/custom libraries) and reading (both modes) work
via `flutter run -d windows`.

---

## Item 6 — Open Issue Detail cover in the Windows desktop reader

**Feature.** From `INBOX.md`: "open reader from web library" — clicking an
issue's cover on the web UI's `/issue/{id}` page now launches the Windows
desktop reader (v2.6 Item 5) directly into that issue. Closes out
`ROADMAP.md`'s long-parked "Reader-launch feature" entry, now that a
working Windows reader actually exists to launch into.

This isn't new ground — a "Read" button existed on this exact page before
and deep-linked via `comicvault://read/{id}`, but was **removed 2026-07-09**
(`docs/DECISIONS.md` "Read button removed from Issue detail") because
nothing on Windows had a handler registered for the scheme — clicking it
did nothing. The Flutter app's own deep-link parsing (`main.dart`'s
`_initDeepLinks()`/`_handleLink()`, via the `app_links` package) already
correctly handled `comicvault://read/{id}` and always had; that was never
the actual gap. Confirmed by reading the `app_links-6.4.1` package source
directly (`app_links_plugin.cpp`, `app_links_plugin_c_api.cpp`, and its
`example/` app) that two real pieces were missing:

1. **No Windows Registry entry** registering the `comicvault://` protocol —
   `app_links` provides the cold-start argv-parsing plumbing and a
   `WM_COPYDATA`-based live-forwarding listener, but the registry
   registration itself lives only in the package's `example/` folder
   (`windows_protocol.dart`), not its published public API.
2. **No single-instance forwarding** — a second `comicvault://` link
   clicked while the reader is already running would have launched a
   second exe process; nothing detected the existing window or forwarded
   the link into it.

Cold start needed zero Dart-side changes — `app_links`'s own `GetLink()`
re-derives the URI from the new process's command line independently.
Warm start and the registry entry were the two real gaps, both closed this
session.

**Confirmed with Tez before building:** scope is the Issue Detail page's
cover only (Browse/Series grid cards keep navigating to their detail pages
as today); protocol registration happens via an explicit "Register as this
PC's comic reader" button in the Flutter app's Settings screen, not
silently on every launch — writing to the Windows registry should be a
visible, deliberate action.

**Built:**
- `flutter_app/pubspec.yaml`: added `win32`/`ffi` dependencies (not
  previously present).
- `flutter_app/lib/services/protocol_handler_service.dart` (new):
  `register()`/`unregister()`/`isRegistered()`, writing
  `HKEY_CURRENT_USER\Software\Classes\comicvault` (no admin elevation
  needed) with `shell\open\command` pointed at
  `Platform.resolvedExecutable` — the app self-discovers its own exe path,
  no dependency on the Admin "Reader Location" field (`ADMIN_SPEC.md`
  §7.6), which was always for a different, never-built mechanism.
  `isRegistered()` reads the key back and confirms it points at *this* exe,
  so a stale entry from a moved/rebuilt exe correctly reads as
  unregistered rather than falsely "already done."
- `flutter_app/lib/screens/settings_screen.dart`: new "Windows Reader"
  section (Windows-only, `Platform.isWindows`-gated) with a
  register/unregister toggle button and current-state text.
- `flutter_app/windows/runner/main.cpp`: added `SendAppLinkToInstance()`
  (adapted from `app_links`'s own example) — `FindWindow` for an existing
  `"digib00age"`-titled window before creating a new one; if found, calls
  `SendAppLink(hwnd)` (from `app_links_plugin_c_api.h`, already linked via
  `generated_plugin_registrant.cc`/`generated_plugins.cmake` — just needed
  the `#include`), restores/foregrounds it, and exits without creating a
  second window. Fixed a real bug in the reference example while adapting
  it: its `SetWindowPos(0, HWND_TOP, ...)` passed a null handle instead of
  `hwnd`.
- `frontend/js/app.js`'s `buildIssueDetail()`: wrapped the existing
  `.issue-cover-img` in an `<a href="comicvault://read/{id}">` rather than
  a JS click handler, letting the browser's own protocol-confirmation flow
  handle the rest. `frontend/css/style.css`: added `.issue-cover-link {
  display: block; }` so the wrap doesn't affect layout — the existing
  `:hover` zoom/border effect targets the `<img>` itself and needed no
  changes.

**Out of scope (unchanged from Item 5's own deferrals):** any
installer/distributable packaging; the inherent same-machine-only
limitation of a custom URI scheme (browser and reader must be on the same
Windows PC) is accepted, not solved.

**Verified:** registry read/write logic confirmed correct via a standalone
`dart run` script exercising `register()`/`isRegistered()`/`unregister()`
against the real Windows registry (left unregistered afterward — that test
run's `Platform.resolvedExecutable` was `dart.exe`, not the real app, so it
intentionally didn't leave a live registration behind). Cover-link markup
confirmed via live DOM inspection (`href="comicvault://read/1"`) and hover
styling confirmed unaffected via screenshot. `flutter analyze` clean; two
clean native rebuild/launch cycles with no exceptions. Tez manually
completed the full loop: registered via Settings, confirmed cold-start
(reader closed, clicked cover, accepted the browser prompt, launched
straight into the issue) and warm-start (reader already open, clicked a
different issue's cover, existing window came to front and navigated
there rather than a second process appearing), and confirmed Browse/Series
grid cover clicks are unaffected.

---

## Item 7 — Full Editor 4-column redesign

**Change.** From `INBOX.md`: "the Full Editor has been redesigned using Claude
Design." The Full Editor (`/editor`) moves from its original **three-column**
layout (File Management + Queue / XML Editor / Image Viewer) to a **four-column
workspace + a footer status bar**, matching the same Claude Design pass that
produced Item 1's web redesign. Structural change → full workflow, `EDITOR_SPEC.md`
§5 updated (new §5.4 supersedes the §5.2 layout), three `DECISIONS.md` entries.

The Claude Design export (`D:\workshop\Claude Design\full editor`,
`4-Column Full Editor.dc.html`) is an `x-dc` **prototype** (mock data, design-system
runtime). Only its *visual design* was reproduced, using the app's existing CSS
token system (already a near-exact match to the design-system tokens) + vanilla JS.
**No prototype runtime was ported; every `/api/editor/full/*` endpoint is reused
unchanged** except one small optional viewer enhancement. This is a layout +
interaction reskin — save/write/validation/increment/ComicVine-search data paths are
untouched.

**Rebuilt locally, not from the cloud build.** This was first built by a cloud
Ultraplan session, but that container had no git remote and a GitHub-blocking egress
policy, so it could never push and the delivered patches never reached the PC (full
context: `temp/build-not-deployed.md`). Rebuilt from scratch on the local `main` per
Tez's call (2026-07-14) — see `DECISIONS.md`.

**Four columns (from the export):**
1. **Load / Select Files** — `Select Folder` (opens the existing modal picker) loads
   the in-memory working set, now rendered as an inline **folder → series → issue
   tree** (grandparent/parent directory grouping, natural-sorted issues, XML badges,
   low-confidence dots) instead of a flat list. Bottom stats bar: Files Found / With
   XML / Without XML.
2. **Edit ComicInfo.xml** — Main/More tabs, an `Apply to All` column header, each
   field paired with its apply-to-all checkbox in a right-hand column. **Genre is now
   removable chips + a "＋ Add genre" dropdown** (replaces the checkbox grid). Format /
   Age Rating stay native selects. Action row: `＋ Queue` / `Clear` (Clear now resets
   the form).
3. **Comic Viewer** — toolbar with zoom / **Fit** / page nav / **Fullscreen**, plus a
   **lazy page-thumbnail strip** (windowed, click-to-jump, active page highlighted).
   **No Rotate** (explicitly dropped by Tez).
4. **Edited Files Queue** — moved to its own column: `Clear Queue`, "N files in
   queue" + counts-differ warning, per-file cards (✓ / name / "Edited" / ✕),
   `Process Queue` / `Process All`.

Plus a **footer status bar**: Selected / XML Status (Valid ✓ for a single parsed
XML; warning for 0 or >1) / Low Confidence / Queued.

**Built:**
- `frontend/editor_full.html`: 4-column `<main>` grid + `<footer>` status bar; Search
  ComicVine / GoodReads moved into the header. All four modals (picker, multi-XML,
  process-error, Search Online) and both `<script>`s preserved verbatim. All 16
  `Apply to All` `data-field`s kept intact (Process All behaviour unchanged).
- `frontend/js/editor_full.js`: `renderFileTree()` (+ `buildFileTree`,
  `commonRootPath`, `naturalCompare`) replaces the flat list and its drag-reorder;
  genre chips (`renderGenreChips`/`addGenre`/`removeGenre`); queue cards;
  viewer `fitViewer()`/`toggleFullscreen()` + lazy thumbnail strip
  (`renderThumbStrip`/`loadThumbImage`, `?w=` downscale, cached); `updateStatusBar()`.
  All file-load / queue / process / picker / multi-XML / Search-Online code reused.
- `frontend/css/style.css`: 4-column grid + footer, `--control-md` token, and the
  tree / genre-chips / apply-to-all-column / viewer-toolbar / thumbnail-strip /
  queue-card / status-bar styles; responsive collapse at 1500/900px. Post-build
  density pass (tighter field spacing so Main fits without scrolling) + three UI
  fixes (genre single-border control, Summary checkbox centred, Increment # label in
  front of its checkbox and aligned in the apply column).
- `backend/routers/editor_full.py`: optional `?w=` downscale param on
  `GET /editor/full/files/{id}/page/{n}` (JPEG q70) for the thumbnail strip;
  full-resolution page bytes returned unchanged when absent.

**Out of scope / dropped:** drag-and-drop reorder of the loaded list (no meaning in a
grouped tree — `DECISIONS.md`); the mock's "Help" header button (nothing to point it
at). No backend behaviour change beyond the additive `?w=` param.

**Verified:** driven end-to-end in a browser against the real library (loaded
*Before the Incal* / *Benjamin* from `L:\Comic Archives\B\Series`, read-only — no
archive writes, working set + queue cleared afterward): tree grouping + natural sort
+ XML badges + stats, issue-click loads editor + viewer, genre chips seed from XML
and add/remove, all 16 apply-to-all `data-field`s confirmed present, viewer page +
real lazy thumbnail strip + Fit/zoom/fullscreen, queue card + counts-differ + footer
status bar; console clean. Tez manually ran a single file all the way through to
adding it to the library. **Series/multi-file path and the tightened layout are
Tez's own follow-up hand-test.** Note: static assets are served without
`cache-control`, so `/editor` needs a hard-refresh (Ctrl+F5) after deploy to pick up
the new HTML/CSS/JS; the `?w=` param needs a tray-server restart (strip works without
it, heavier).
