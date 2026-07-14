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
