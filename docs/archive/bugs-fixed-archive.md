# ComicVault — Fixed Bugs Archive

Historical record of resolved defects, split out of `BUGS.md` 2026-06-29 to keep the
live file lean. Not version-scoped — a bug found during one version's work can get
fixed during a later one, so this isn't bundled under any `archive/vN.M/` folder.
Append-only; entries kept exactly as they were in `BUGS.md` at the time of move.

---

### BUG-023 — Cover image doesn't update in the library after an archive edit + rescan

**Found:** 2026-07-16, user report (`INBOX.md`, "cover change in archive takes a
long time to show in the library, refresh doesn't speed it up"). Reproduced with:
cover shown as a double-cover/open-book spread, archive unpacked, page edited down
to a single cover page, archive repacked, library rescanned. The scan correctly
detected the change, but the library grid kept showing the old cover for minutes —
neither a normal reload (F5) nor a hard reload (Ctrl+Shift+R) fixed it reliably.
User flagged it as a possible regression of an earlier 2026-07-12 "not a bug"
report about a removed cover persisting after scan (also referenced in BUG-022's
Found note) — correctly, per the root cause below.

**Where:** `backend/routers/reader.py`'s `GET /api/cover/{issue_id}`, and every
place across `backend/routers/library.py` / `backend/routers/home.py` that built a
cover URL as the literal `f"/api/cover/{issue.id}"`.

**Root cause:** confirmed live against issue 5469 — the scanner was working
correctly (archive mtime, DB `date_modified`, and the regenerated thumbnail file on
disk all matched, thumbnail already fresh on disk within ~2 minutes of the edit).
The problem was purely the browser's HTTP cache. v2.6 Item 2 Phase 4
(2026-07-13, `PERFORMANCE.md` finding #3) added `Cache-Control: public,
max-age=86400` to `/api/cover/{id}` to stop re-transferring unchanged thumbnails on
every grid view — a real win for covers that never change. But the URL was always
the same static `/api/cover/{id}` string, so once a browser had fetched it, it was
entitled to reuse the cached bytes for a full 24h *without ever contacting the
server*, regardless of what changed server-side. No reload gesture reliably forces
revalidation for images set via JS (`img.src = item.cover_path`) after the initial
page load, which is how every cover in this app is rendered
(`frontend/js/app.js`) — so the "several minutes, refresh doesn't help" symptom was
really "up to 24 hours, no client action can force it," just not run out yet.

**Fixed, 2026-07-16.** Rather than forcing per-request revalidation (`no-cache`,
which works but adds a round trip to every cover load), cache-busting was moved
into the URL itself: added `path_utils.cover_url(issue)`, which appends a `?v=`
version stamp built from `Issue.date_modified` — the same field the scanner already
stamps with the archive's filesystem mtime the instant it detects and applies a
change (`scanner.py:407`), at second-level granularity matching the scanner's own
unchanged-file tolerance. All 9 call sites that built the raw `/api/cover/{id}`
string now go through this helper (`library.py` lines 92, 220, 478, 508, 615, 712,
888 — plus Folder View's subfolder-cover pick, which needed
`subfolder_issue_ids: dict[str, list[int]]` changed to retain full `Issue` objects
instead of bare ids so `.date_modified` was available; and `home.py` line 54).
`reader.py`'s `COVER_CACHE_CONTROL` was kept at a long, now-safe
`"public, max-age=86400, immutable"` — unchanged covers keep the original
zero-request 24h cache Phase 4 intended, changed covers get a structurally
different URL the instant a rescan updates that row, so the browser cache-misses
and fetches fresh automatically. The existing ETag/`If-None-Match`/304 logic
(Phase 4) was left in place as cheap defense-in-depth for the rare
`date_modified is None` fallback case.

**Verified live:** built a scratch two-page CBZ (red cover), scanned it in as an
isolated test issue (id 5502, never touching real library files or the real DB
beyond that one test row), confirmed the served cover pixel was red and the
`cover_path` carried a version stamp. Repacked the same archive with a green cover,
rescanned via `POST /api/scan/file`, confirmed the version stamp changed
(`v=20260716215540` → `v=20260716215608`) and the new URL served the green cover
immediately — no delay, no reload gymnastics. Test issue, its thumbnail, and the
scratch archive were all deleted afterward; real library/DB confirmed untouched.

---

### BUG-022 — Bulk star rating (multi-select bottom toolbar) doesn't update cards

**Found:** 2026-07-12, user report while investigating an unrelated stale-cover
report (that one turned out to be a browser-cache false alarm, not a real bug —
not logged). Selecting one or more cards and clicking a star in the bottom
selection toolbar's rating widget produced no visible change on the card(s).

**Where:** `frontend/js/app.js`. The bulk-action toolbar
(`ensureSelectionToolbar()`) wires every button through
`runBulkAction(path, extraBody, applyFn)`, which POSTs to the bulk endpoint and
then, only if a third `applyFn` argument was passed, patches the DOM/cache to
reflect the change immediately (`applyReadStateToDom`, `applyFavoriteToDom`).
The two star-rating call sites (clear-rating and the five rating buttons) never
passed an `applyFn` — so nothing patched the `.card-rating-pill` or the cached
`personal_rating` in `allLibrary`/`tabLibraryCache`/`viewLibraryCache`/
`searchLibraryCache` after a successful bulk rate.

**Root cause:** the `.card-rating-pill` UI (`SPEC.md` §20.18) was added
2026-07-11, after the original bulk-toolbar code — `applyReadStateToDom`/
`applyFavoriteToDom` existed for the badges that were present at the time, but
no equivalent `applyRatingToDom` was ever added for the pill. The backend write
itself (`POST /api/progress/bulk/rate` → `bulk_set_rating()` in
`backend/routers/progress.py`) was correct throughout and shared with the
single-issue rating control (which self-patches its own local state, so it
never depended on `runBulkAction`'s `applyFn` and wasn't affected) — this was a
client-side reflection gap, not a persistence bug. Confirmed via a scratch DB
read that the rating persisted correctly even before the fix; a full reload
would have shown it.

**Fixed, 2026-07-12.** Added `applyRatingToDom(ids, rating)` /
`_patchRatingInCaches(id, rating)` (mirroring `applyFavoriteToDom`/
`_patchFavoritesInCaches`) and wired them as the `applyFn` for both the
clear-rating and per-star click handlers in `ensureSelectionToolbar()`.

**Verified live** against the running dev server via direct function calls
(`selectOrToggle`, then a real `.click()` on the toolbar's star/clear buttons)
on a browse-grid card: the `.card-rating-pill` appeared with the correct star
count immediately after rating, and disappeared immediately after clearing —
both times without a page reload, and both times confirmed against the actual
DB row (`personal_rating` column) to rule out a false-positive from cache-only
patching.

---

### BUG-014 — Back-button regression: returns to Home instead of the originating tab

**Found:** 2026-06-27, inbox capture (3 repro cases reported across two separate
inbox lines). Third fix attempt — same defect class was already found and "fixed"
twice before (`archive/comicvault-changes-2.1.md` Tier 1, 2026-06-21 and a
2026-06-22 follow-up) only to resurface.

**Root cause:** `frontend/js/app.js`'s `switchSurface()` (the function behind every
Home/All/Singles/Series tab switch) only called `history.pushState()` for Folder View
custom tabs — the four main browse surfaces never wrote anything to the URL. So when a
user opened an issue/series (a real navigation) and hit Back, the browser returned to
whatever the last *real* history entry was — almost always bare `/`, which then
defaulted to Home. A second, independent bypass (`redirectHomeSearchToAll()`,
triggered by typing in Home's search box) did the same thing via hand-rolled DOM
changes that never touched history at all. Folder View already solved this correctly
via `pushFolderViewUrl()` — it was the reference pattern, just never extended to the
rest of the app.

**Why this felt "random" across three fix attempts:** live testing (2026-07-08) found
the *same* action (All → issue → Back) produced two different outcomes across two
attempts — once correctly landing back on "All" (Chrome's back/forward cache silently
restored the previous page's live JS state), once landing on Home (a real reload
occurred, hitting the actual defect). The code bug was fully deterministic throughout;
what made it look inconsistent was that browser bfcache heuristics randomly masked it.
The 2026-06-21/22 fixes replaced a guessed-destination back link with a correct
`window.history.back()` call, which was necessary but not sufficient — it depended on
a real history entry existing for "the surface the user came from," which items above
show was essentially never created for the four main tabs.

**Fixed, 2026-07-08.** Extended Folder View's `pushState`/`popstate` convention
(`/?surface=…&path=…`) to every surface: `switchSurface()` now writes the URL on every
branch (not just Folder View), `redirectHomeSearchToAll()` was rewritten to route
through `switchSurface()` instead of duplicating its DOM logic, the `popstate` listener
and `initLibrary()` now share one `parseSurfaceState()` parser (previously two
independently-drifting parsers) and restore `field`/`value`/`folder`/`status` in
addition to `surface`/`path`, and the very first page load now gets a
`history.replaceState()` so it's no longer indistinguishable from "no surface was ever
recorded." The now-fully-dead `from=` query-param plumbing (`buildStripCard()`,
`buildCoverCard()`, `buildIssueRow()`, `initSeries()`'s `from` read) was removed in the
same session — it stopped being read by the back-link logic back in the 2026-06-21/22
fix and had been inert ever since.

Admin page's back link (`admin.js`) was reviewed and left unchanged — it's a
structurally independent `history.back()` implementation whose only entry point is a
literal `href="/"`, never routed through `switchSurface()` or the `surface=`
convention, so it was never exposed to this defect.

**Verified live** against the running dev server, each case run twice (a plain Back
click, and a forced hard-reload-then-Back to guarantee a bfcache miss, since that's
the scenario that actually broke before): All→issue→Back, Series→series-detail→Back,
Series→series-detail→issue→Back→Back, Home-search→All→issue→Back, and Folder View's
existing 2-level drill-down→Back→Back (confirmed not regressed by the `{replace}`
option added to `pushFolderViewUrl()`). All land on the correct origin surface.

---

### BUG-015 — Genre field-view filter has no UI way to clear, and survives back-navigation incorrectly

**Found:** 2026-06-27, inbox capture.

**Where:** Selecting a genre from an issue page correctly navigates to a filtered
field-view (`/?surface=fieldview&field=genre&value=Comedy`). From there, the Genre
dropdown didn't visually reflect the active filter, a different tab switch left the
filter and URL value untouched underneath, and stale URL state meant back-navigation
into a visually-reset list could restore the wrong filter.

**Tez's initial proposed fix** — add a "Clear" first row to the Genre dropdown — was
investigated and found to only cover the genre case. Fieldview is not genre-specific:
it's also reached via writer/artist credit links and admin-configured home strips
(publisher/format/decade/year/rating/B&W, per `admin.js`'s `HS_FIELD_LABELS`), and
there's no dropdown at all for writer/artist in the toolbar — a Genre-dropdown-only fix
would have left those cases with no clear mechanism whatsoever.

**Root cause:** two completely separate, unrelated mechanisms shared the word "Genre."
The Genre dropdown (`<select id="genreFilter">`) is bound to a module-level
`activeGenre` variable, applying an additional client-side narrowing layer on top of
whatever pool is loaded. Fieldview (`viewField`/`viewFieldValue`, set only inside
`switchSurface()`) drives a separate, server-scoped API call. Neither touched the
other, and fieldview itself showed zero context — no banner, no indicator, just a
generic "N Titles" count with no mention of what was filtering it.

**Fixed, 2026-07-08.** Rather than touch the Genre dropdown, generalized an existing,
better-fitting pattern already in the codebase — the Series detail page's BUG-010 fix,
which shows a "Showing X of Y issues — filtered by Z. View full series" banner with a
real-navigation clear link for an analogous scoped-view problem. Added a generic
fieldview banner (`renderFieldviewBanner()`, `app.js`) shown above the cover grid
whenever `activeSurface === 'fieldview'`, reading `"{count} Titles — {FieldLabel}:
{value}"` with a "Clear filter" link doing a real navigation to `/?surface=all` — a
real page navigation rather than a JS state reset, sidestepping the exact class of
"JS state vs. URL" desync bug that caused BUG-014. Writer/artist values are a
`Person.id`, not human-readable — added a `label=` URL param, populated at the two
credit-link-construction sites (which already have the name in scope) and via a new
`field_value_label` field resolved server-side in `backend/routers/home.py` for the
one site (admin home-strip links) that doesn't have the name client-side. `viewField`/
`viewFieldValue`/new `viewFieldLabel` state threads through the same shared
`parseSurfaceState()`/`buildSurfaceUrl()`/`writeSurfaceUrl()` path the BUG-014 fix
established, rather than adding a second, independently-drifting parser.
`hasActiveFilters()`/`clearAllFilters()` were deliberately left blind to fieldview
state (commented explaining why) — blanking `viewField`/`viewFieldValue` in place
without changing `activeSurface` would empty the grid via a cache-miss, not unfilter
it; leaving a fieldview genuinely requires a real navigation, which the banner's own
link already provides.

**Bonus (Tez's call):** the Genre dropdown now cosmetically mirrors an active genre
fieldview's value (purely visual, doesn't touch `activeGenre`), synced once per
`switchSurface()` call rather than on every re-render, specifically to avoid fighting
a user's own manual dropdown selection while already on a fieldview.

**Robustness fix found during live verification:** `renderFieldviewBanner()` initially
had no null-check on the banner DOM element, which crashed the entire render pipeline
(stuck on "Loading…") when a stale cached copy of `index.html` (predating this fix)
was served alongside a fresh `app.js` — a realistic scenario across any deploy where
HTML/JS versions can momentarily skew, not just a testing artifact. Added a guard.

**Verified live** against the running dev server, including the two highest-risk paths
end-to-end: a genre tag on an issue page, a writer credit link (URL carries
`&label=`, banner shows the resolved name not the numeric id, survives a hard
refresh and Back/Forward), a temporary admin-configured writer-basis home strip
(confirming the new backend `field_value_label` round-trips correctly — "4 Titles —
Writer: A. J. Lieberman"), the Clear filter link, cleanup-on-navigate-away via the
sidebar, a secondary Format-dropdown filter layered on top of a fieldview (banner
count updates correctly, the global Clear button clears only the Format narrowing and
leaves the fieldview scoping intact), and decade/B&W value formatting ("1990s",
"Yes"/"No"). Test home-strip scaffolding removed after verification.

---

### BUG-010 — 2000 AD writer credit link doesn't filter the issue list

**Found:** 2026-06-23, inbox triage.

**Where:** Issue page for a 2000 AD-tagged issue (e.g. year 1979, issue #174) — clicking
a writer's series card (e.g. "2000 AD — writer in 1104 issues + 7 singles") opens the
full 2000 AD prog run, not a list filtered to issues credited to that writer.

**Impact:** The writer series card states correct totals (counts appear right) but the
click-through doesn't filter — it shows the full series, making the writer's credit
link functionally useless for browsing their specific contributions.

**Generalised, 2026-06-29:** not isolated to 2000 AD or to the issue-page credit link —
any series card reached from a credit/field-filtered context (a Writer/Artist credit
link, or any future field-filtered fieldview) opened the unfiltered full series, since
`GET /api/series/{id}` (`backend/routers/library.py`) never accepted a field/value
filter at all — it always returned every issue in the series regardless of how the
user navigated there. Repro confirmed with "search All for Alan Moore": the match
surfaces "2000 AD" as a series card (since at least one of its 2483 issues credits Alan
Moore), but clicking it opened all 2483 issues, not just his 117.

**First fix pass (credit-link path) was incomplete — caught immediately by Tez
re-testing the original "search All for Alan Moore" repro itself:** that repro doesn't
go through the credit-link path at all. The inline "All" search box was, and still is,
a separate code path — `getFilteredLibrary()`'s inline search matched client-side
against each series' aggregated `writers` array (a flattened union across every issue
in the whole series) and returned the series' *full*, unscoped `issue_count`. So
searching "Alan Moore" reported "2,515 Titles (2,483 in 2000 AD)" — the full series
totals, not his actual ~146 credited issues — and clicking through (e.g. into "2000 AD
Yearbook", 4 issues, only 1 actually by Moore) still opened all 4, not the 1 that
matched. The first fix only handled the credit-link's `person_id`-based filter; it
didn't touch the inline search box's own separate, still-broken aggregation.

**Fixed properly, 2026-06-29.** Added `matches_search()` to `backend/path_utils.py`
(same field set as `GET /api/search`: series/title/writer/characters/story_arc/
publisher) and a new optional `q` param on `GET /api/library` and `GET /api/series/
{id}`, applied the same way the existing `field`+`value` param already was — filtering
issues *before* the per-series groupby, so a series' `issue_count` reflects only the
issues that actually matched `q`, not the whole series. The inline "All" search box
(`bindSearchEvents()` in `app.js`) now calls `GET /library?q=` (cached per query in
the new `searchLibraryCache`) instead of filtering the unscoped `allLibrary` aggregate
client-side; `getFilteredLibrary()` uses that server-scoped pool whenever a search is
active on the plain All/Series/Singles surfaces (custom tabs/fieldview/folderview keep
the old client-side substring filter — they're already server-scoped views, search is
just a secondary local narrowing there, not the primary scoping mechanism). Series
cards built while a search is active now carry `?q=` onto their link; `initSeries()`/
`buildSeriesHeader()` read it back and pass it to `GET /series/{id}`, showing the same
"Showing N of M issues — matching 'X'. View full series" banner as the credit-link
case.

Verified directly against the live API:
- `GET /library?q=Alan%20Moore` → "2000 AD" `issue_count: 117` (not 2483), "2000 AD
  Yearbook" `issue_count: 1` (not 4) — 146 issues total across 15 series, not the
  full-series totals the old client-side match reported.
- `GET /series/5470?q=Alan%20Moore` (2000 AD Yearbook) → `issue_count: 1`,
  `total_issue_count: 4`, `issues: [5470]` — exactly the one issue Tez confirmed is
  actually credited to Alan Moore, matching the repro's expectation precisely.
- `GET /series/248?q=Alan%20Moore` (2000 AD) → `issue_count: 117`,
  `total_issue_count: 2483`.
- Unfiltered `GET /library` and `GET /series/248` (no `q`) confirmed unchanged —
  full series, no regression.

---

### BUG-009 — Star rating doesn't clear to Unrated

**Found:** 2026-06-23, inbox triage.

**Where:** Issue page (`/issue/{id}`) star rating row.

**Impact:** Clicking an already-highlighted star (i.e. the current rating) should drop
the rating to Unrated (NULL). Currently it floors at 1 star — once any rating is set,
there's no way to return to Unrated via this interaction.

**Addendum, 2026-06-27 (inbox capture):** the multi-select toolbar's `✕` "Clear
rating" button (added 2026-06-26, Fix 2) already covers the bulk-selection case.
This bug is specifically about the single-issue page (`/issue/{id}`) star row,
where the desired fix is: clicking an already-highlighted star a second time clears
the rating to Unrated — same gesture, no separate control needed.

**Fixed, 2026-06-29.** `frontend/js/app.js`'s `buildRatingControl()` star click
handler now checks whether the clicked star's value already equals
`data.personal_rating`; if so it sends `rating: 0` instead of the star's value
(reusing the same `POST /api/progress/bulk/rate` endpoint the multi-select toolbar's
clear button already uses — that endpoint already accepted `0` as "clear", per its
existing `BulkRating` validator in `backend/routers/progress.py`, no backend change
needed). Verified directly against `/api/progress/bulk/rate` on a scratch-state real
issue (#1, originally unrated): rate→3 confirmed 3, then rate→0 (the same call the
new click handler now makes when re-clicking star 3) confirmed back to 0/null —
issue left in its original unrated state afterward.

---

### BUG-007 — Basic Editor's multi-line textarea fields (Summary) round-trip with doubled line breaks on every save

**Found:** 2026-06-21, incidentally — while verifying Tier 4 Item 3's editor fuzzy-
warn-on-save feature against a real issue (`2000AD #011 (1977)`), saving the form
(which submits every field, not just the one being tested) revealed that the
`Summary` field's blank lines double on every save: a single blank line between
paragraphs (`\n\n` in the original XML) becomes a doubled blank line (`\n\n\n\n`,
confirmed on-disk as literal `\r\r\n` sequences) after going through the Basic
Editor's save flow once. Re-saving again would presumably double it further each
time.

**Where:** `frontend/js/editor_basic.js` `onEditorSubmit()` (collects the `<textarea>`
value via `FormData`) → `backend/editor/field_merge.py` `build_xml_from_fields()`
(merges it into the XML). Not yet root-caused precisely — likely the browser's
textarea-to-FormData line-ending normalization (`\n` → `\r\n`) combined with
`field_merge.py` independently adding its own line separator when writing the
`<Summary>` tag, compounding on each save.

**Impact:** Any issue whose Summary is edited and saved through the Basic Editor
gets visually-doubled blank lines in its description, worsening on repeated saves.
Purely cosmetic (doesn't affect parsing — `_text()` still extracts the full string
correctly either way) but degrades readability over time. Pre-existing — unrelated
to Tier 4 Item 3, not introduced by it, just exposed by testing that happened to
touch a real issue. Not fixed in this session (out of scope for Item 3's no-ride-
alongs framing) — flagging per session convention.

**Fixed.** - Can't reproduce the double line issue. Tez; 29/6/26
(A future session should: confirm the exact mechanism (check whether
`field_merge.py` adds `\r\n` on top of an already-`\r\n`-converted textarea value),
then normalize line endings once, consistently, rather than compounding them.)

---

### BUG-011 — Admin "Scan Roots" Add button doesn't open file dialog

**Found:** 2026-06-23, inbox triage.

**Where:** Admin page — "Add" button under Scan Roots / Library Folders section.

**Impact:** Clicking "Add" should open a folder/file picker dialog so a new scan root
can be added. Currently does nothing. Admin page is otherwise functional; existing
scan roots still work.

**Fixed.** Not actually a Bug - Clicking Add after manually entering a new scan location Adds it to the list - misunderstanding of function not error in function; Tez 29/6/26

---

### BUG-012 — Library fails to initialise after changing theme in Admin, then navigating back

**Found:** 2026-06-23, manual test pass during v2.3 Item 3 (card behaviour additions).

**Where:** Library page (`/`), right after switching the Admin → Appearance theme
setting and navigating back to the library.

**Impact:** Library shows "Failed to initialise. Cannot read properties of null
(reading 'addEventListener')" with a Retry button, instead of loading normally.
`initLibrary()`'s catch block (`frontend/js/app.js`) is catching a `null.addEventListener`
call from one of `bindSurfaceNav()`/`bindFilterEvents()`/`bindSearchEvents()` — exactly
which element was null isn't confirmed yet. A hard refresh cleared it immediately, and
repeating the theme switch + back-navigation afterward did not reproduce it — so this
looks like a one-time/intermittent state issue (possibly browser back/forward-cache
restoring a stale DOM, or a race between the new theme anti-flash inline script and
the rest of page load), not a deterministic break in the new theme code itself.

**Fixed** — No issues found when changing theme; Tez 29/6/26

---

### BUG-003 — Dead duplicate route: `GET /api/reading/continue` defined twice

**Found:** 2026-06-19, while building the Home Strips feature (`HOME_STRIPS_SPEC.md`)
and tracing how "Continue Reading" was resolved before folding it into the unified
`GET /api/home/strips` endpoint.

**Where:** The route was defined in both `backend/routers/progress.py` (line ~219) and
`backend/routers/library.py` (line ~631) — identical path, same query intent, slightly
different implementation. `main.py` registers `library.router` before `progress.router`,
so `library.py`'s version always won; `progress.py`'s copy was unreachable dead code.

**Impact:** None — the live version (`library.py`) was correct throughout and is what
the Flutter app calls. Purely a maintenance hazard: a future edit to the dead copy
would have silently done nothing.

**Fixed:** 2026-06-27 — removed the unreachable duplicate (`get_continue_reading`) from
`backend/routers/progress.py`. `library.py`'s `reading_continue` remains the sole
implementation; no behaviour change since it was already winning registration order.

---

### BUG-006 — CSV-splitting helpers didn't dedupe a literal repeated name within one field

**Found:** 2026-06-21, while scratch-testing the Tier 4 Item 3 migration (Writer/
Artist entity dedup) against a copy of the real DB, before the real run.

**Where:** `backend/scanner.py`, `_split_csv()` (used by both `_genres()` and the
new `_credits()`/`_sync_credits()` added for Item 3).

**What happened:** Some real `ComicInfo.xml` Penciller/Inker fields contain a
literal repeated name, e.g. `"Chris Shehan, Maan House, Chris Shehan, Maan House"` —
175 issues affected (114 penciller + 61 inker) across the real library. Splitting
this CSV without deduplicating produced two identical entries, which crashed the new
Person/IssueCredit migration with a `UniqueConstraint` violation on
`(issue_id, person_id, role)` the moment it hit the first affected issue.

**Impact before the fix:** would have crashed `scan_single_file()`'s credit-sync on
any of these 175 issues going forward, not just the one-time migration — same
crash risk existed latently in `_sync_genres()`'s composite-PK insert for Genre,
just never triggered (zero real issues currently have a duplicated Genre value).

**Fix:** `_split_csv()` now deduplicates (order-preserving, via `dict.fromkeys`)
after stripping. Fixes both the credit-sync path and defensively covers Genre's
identical latent vulnerability. `backend/migrate_people.py`'s own independent
CSV-splitting (it doesn't go through `scanner._split_csv`, which operates on XML
elements, not arbitrary DB-stored strings) got the same fix applied separately,
including a second dedup pass *after* resolving through the merge-decision map,
since two different raw names can collide onto the same canonical name post-merge.

**Status:** Fixed in `scanner.py` and (separately) `migrate_people.py` before the
real migration ran. Verified by re-running the migration against the same 175
affected issues afterward with no errors.

---

### BUG-005 — New bulk progress endpoint swallowed by an existing route's path pattern

**Found:** 2026-06-21, while live-testing the new bulk endpoints for Tier 4 Item 2
(Multi-select + Favorites/Rating) against a scratch copy of the real DB, before the
frontend ever touched them.

**Where:** `backend/routers/progress.py` — the new `POST /api/progress/bulk/mark-read`
was registered *after* the existing `POST /api/progress/{issue_id}/mark-read`.

**What happened:** Both routes are two path segments after `/progress/`. Starlette
matches registered path templates in order and returns the first structural match
regardless of whether type conversion succeeds — `/progress/bulk/mark-read` matched
`/progress/{issue_id}/mark-read` first, with `issue_id` bound to the string `"bulk"`,
which failed `int` parsing and returned a 422 instead of ever reaching the new bulk
endpoint. Same collision applied to `bulk/mark-unread` against
`{issue_id}/mark-unread`. (`bulk/favorite`, `bulk/unfavorite`, `bulk/rate` were
unaffected — no existing route shares that suffix.)

**Fix:** Moved the new bulk route registrations (and their `BulkIssueIds`/`BulkRating`
request models) above the existing `/progress/{issue_id}/mark-read` /
`/mark-unread` routes in the same file, with a comment explaining why the ordering
matters. Re-verified both the new bulk routes and the pre-existing single-issue routes
work correctly via curl against the scratch server afterward.

**Status:** Fixed in `progress.py`. General hazard worth remembering for any future
route added under an existing `{param}/...` path: a new literal-segment route needs to
be registered *before* a parameterized route it could collide with, not just given a
different-looking name.

---

### BUG-004 — Tray app shows "Start ComicVault at login" ticked but server doesn't start on login; manual Start also fails

**Found:** 2026-06-19, first login after an OS restart following the prior session's
tray app changes (split Stop/Start, add Close, dark menu, login autostart toggle —
commit `6fc1840`). That session's testing was done but the OS restart + fresh login
happened afterward, outside the tested window.

**What happened:** Tray app started automatically at login as expected, and the
"Start ComicVault at login" menu item correctly showed as ticked. However the backend
server subprocess kept exiting immediately. Manually invoking Start from the tray menu
also failed — not a tray-app or autostart bug at all.

**Root cause — not in ComicVault's code.** `tray/reader_stdout.log` showed the actual
uvicorn error on every restart attempt:
`ERROR: [Errno 13] ... [winerror 10013] an attempt was made to access a socket in a
way forbidden by its access permissions` when binding `0.0.0.0:8000`.
`netsh interface ipv4 show excludedportrange protocol=tcp` confirmed port 8000 fell
inside a Windows TCP port-exclusion range (`7981–8080`) — `netstat` showed nothing
actually listening on 8000, i.e. Windows itself was refusing the bind, not a
competing process. `hns`/`vmms`(Hyper-V)/`WSL Service` were all running on this
machine; WSL2/Hyper-V's networking stack reserves blocks of TCP ports for NAT at
boot, and on this particular boot the reserved block happened to swallow port 8000.
This explains why manual Start also failed: it's an OS-level bind refusal, independent
of how the process is launched.

**Fix applied this session:** Restarted the `winnat` service (`net stop winnat` /
`net start winnat`) to force Windows to recompute its port-exclusion ranges. Confirmed
8000 was no longer excluded afterward, and the tray app's own health-check loop
(30s interval) picked this up on its next retry without any further action — log
shows `Reader server is up.` at 18:46:28, `netstat` confirmed `0.0.0.0:8000 LISTENING`,
and `GET /api/admin/stats` returned 200.

**Not a recurring code defect, but a recurring environmental risk:** any future
reboot can reproduce this if WSL2/Hyper-V's networking service happens to claim a
range overlapping port 8000 again. There is no permanent code-level fix being applied
in this session (would require either changing ComicVault's port to one outside
commonly-claimed ranges, or scripting a winnat restart into the startup sequence —
neither attempted here; flagging as a possible `ROADMAP.md` item rather than doing it
under this bug ticket).

**Status:** Resolved for this session by restarting `winnat`. Tray app and
`start_server.py` both behaved correctly throughout — no code changes were needed or
made.

---

### BUG-002 — Full Editor's Queue button stayed disabled for any file whose existing Genre/Format/AgeRating wasn't already enforced-valid

**Found:** 2026-06-18, during Tez's first manual test pass after the Full Editor build.

**Where:** `frontend/js/editor_full.js`, `updateValidityGate()` (now renamed
`updateActionButtonStates()`).

**What happened:** Queue (and Process All) were gated on the same Genre/Format/
AgeRating validity check as the Basic Editor's Save button. For any loaded file whose
current values didn't already pass (e.g. a genre like "Zombie" not in the enforced
list — the exact kind of file the pre-migration report exists to flag), Queue was
disabled immediately on focus, before Tez had a chance to fix anything. Reported as
"the Queue button is dead."

**Root cause:** `EDITOR_SPEC.md` Section 4.4 ("Existing-value mismatch behaviour") is
explicitly titled **Basic Editor only** — the hard validation gate was never meant to
apply to Full Editor. It got carried over by extension when building Full Editor's
form, which shares the same field markup/JS patterns as Basic Editor's popup.

**Fix:** Queue is now only gated on whether a file is focused; Process All only on
whether any files are loaded; Process Queue only on whether the queue is non-empty.
Validity enforcement for Full Editor happens server-side at process time only
(`backend/editor/validation.py`, already in place) — invalid fields are reported as
per-file errors without aborting the rest of the batch, matching the intended
workflow (queue first, fix fields, process after). The now-pointless
genre/format/agerating `change` listeners that only existed to re-run this check were
removed.

**Status:** Fixed in `editor_full.js`. Basic Editor's Save button is unaffected — its
gate is correctly scoped per Section 4.4.

---

### BUG-001 — Scanner skips thumbnail generation for unchanged-mtime files, even if the thumbnail file is missing

**Found:** 2026-06-18, during V2 migration setup.

**Where:** `backend/scanner.py`, incremental scan logic (~line 419), "skip if unchanged"
branch based on `date_modified` comparison against the DB.

**What happens:** The scanner only generates a thumbnail on the new-file or
updated-file branches. If a file's `date_modified` in the DB already matches its
on-disk mtime, the scanner skips it entirely — including thumbnail generation — even
if no thumbnail file actually exists on disk for that issue.

**How it surfaced:** V2 was set up from a copied database (`comicvault.db` copy) but
without copying `thumbnails/` (deliberately, since thumbnails are gitignored and
assumed regenerable). Every file's `date_modified` in the copied DB still matched disk
mtime, so the scan treated all 5,429 files as "skipped" and none of them got a
thumbnail — `thumbnails/` was left at 0 files despite a full scan reporting 0 errors.

**Why it matters beyond this one case:** This isn't specific to the migration. Any
future scenario where the DB is restored/copied without its thumbnails — backup
restore, disk recovery, fresh deploy from a DB dump — will hit the same silent gap.
The scan reports success (0 new, 0 updated, 0 errors) with no indication that cover
art is missing.

**Proper fix (applied 2026-06-18):** The skip-if-unchanged branch in `scan_single_file`
now checks whether the expected thumbnail file (`{issue.id}.jpg`) exists on disk before
skipping. If missing, it calls `_generate_thumbnail` and updates `cover_path` even
though the DB row's metadata is otherwise unchanged — the file still counts as
"skipped" in scan stats, it just no longer silently leaves a missing thumbnail behind.

Applied to **V2 only** (`comicvault_v2/backend/scanner.py`). V1's `scanner.py` is
unmodified — V1 is being kept as-is and is not being changed going forward.

**Workaround applied for V2's existing data (does not by itself fix the bug):** Cleared
`date_modified` for all rows in `comicvault_v2.db` only (V1 untouched), then re-ran the
scan so every file was treated as updated and thumbnails generated. This got V2's
existing copied DB into a correct state; the scanner fix above is what prevents the
same gap from recurring on any future DB copy/restore.

**Verification:** Deleted one issue's thumbnail file manually, ran a scan — confirmed
only that issue regenerated its thumbnail while the rest of the library (5,428 other
issues, unchanged, thumbnails present) was still skipped quickly. Full-library scan
timing was unaffected by the fix (~5 seconds for all 5,429 files, matching pre-fix
skip-path timing).

**Status:** Fixed in V2. V1 retains the original (unfixed) logic by design.

---

### BUG-017 — All-tab Favourites filter only checks one issue per series, misses favourited issues elsewhere in that series

**Found:** 2026-06-30, scoping session for the new Favourites Tab (v2.4 Item 4 —
see `CUSTOM_TABS_SPEC.md` §10.7).

**Where:** `backend/routers/library.py`, `get_library()` — the per-series result dict
sets `"favorites": cover_issue.favorites`, where `cover_issue` is whichever single
issue in the series sorts first by issue number (typically issue #1). The existing
Black & White flag two lines below does the structurally correct thing for the same
kind of series-wide aggregation: `has_bw = any(i.black_and_white for i in issues)` —
"does *any* issue in this series have it." Favourites copies one issue's flag
instead of aggregating across the series.

**What happens:** Favouriting issue #14 of a 20-issue series (without ever touching
issue #1) leaves the series card's `favorites` flag `false`. The All-tab Favourites
menu-bar filter (`activeFavorites`, `MENU_BAR_SPEC.md` §2.3) then hides the entire
series, even though it contains a favourited issue. Singles are unaffected — a
Single is its own one-issue series, so the one issue's flag is always the correct
one to check. Confirmed live by Tez: filtering by Genre: Crime shows both series and
singles cards as expected; toggling Favourites on top of that only shows the
favourited Singles, silently dropping a series known to contain a favourited issue.

**Impact:** The Favourites filter has been understating results for series (not
singles) since it shipped — anyone who favourites issues that aren't a series'
lowest-numbered issue won't see that series under the Favourites filter at all.

**Does not affect the new Favourites Tab** (`CUSTOM_TABS_SPEC.md` §10) — that tab
filters issues by `Issue.favorites == True` *before* grouping into series cards, so
every series card it builds is already known to contain a favourited issue. This bug
is specific to the existing All-tab filter's group-first-check-second order.

**Fixed, 2026-07-01 — v2.4 Item 9 build session, bundled with the new Favourites
Tab (same file, same function, same data model).** Changed
`"favorites": cover_issue.favorites` to
`"favorites": any(i.favorites for i in issues)`, matching the existing `has_bw`
pattern immediately below it in the same function. Verified against a scratch
library: favourited issue #2 of a 3-issue scratch series (not #1), confirmed the
series now surfaces under the All-tab Favourites filter.

---

### BUG-018 — Scanner misses ComicInfo.xml nested in a subfolder inside the archive

**Found:** 2026-06-30, investigated by Code while scoping v2.4 Item 8 (Flatten
Archive). Originated as a feature-scoping session, turned into root-cause work
when Tez recalled Flatten Archive had been built for a reason he couldn't
remember at the time — this is that reason.

**Where:** `backend/scanner.py:275-276` — `_parse_cbz()` does an exact-equality
check (`n.lower() == "comicinfo.xml"`) against the zip's `namelist()`, which only
matches root-level entries. An archive with `ComicInfo.xml` inside a subfolder
(alongside its images, rather than at the zip root) never matches, so the scanner
falls back to filename-guessed metadata — no series/credits/etc. — and the issue
looks "broken" in the library and Basic Editor.

Confirmed narrower than it first looked: the **editors are not affected**. Both
Basic Editor (`backend/routers/editor_basic.py:100-103`) and Full Editor
(`backend/routers/editor_full.py:216-244`) already use `find_xml_in_archive()` /
`extract_xml_from_archive()` (`backend/editor/archive_io.py:22-42`), which match
`*.xml` anywhere in the archive regardless of folder depth. And saving through
either editor already flattens the archive on write
(`write_comicinfo_to_cbz()` → `_rebuild_archive()`,
`backend/editor/archive_io.py:57-103`) — existing, intentional behavior, not
changed by this fix. So a nested-folder archive that somehow got linked to an
issue record loads and edits fine; the bug is purely in the scanner's *initial*
read, not in editing or in the flatten-on-save path.

**Why this stayed hidden:** Tez's own library was already fully processed (flat
archives only) by the time this app was in regular use, so the bug never
surfaced against real data — only found by digging into why Flatten Archive had
been built as a CAPT tool in the first place.

**Impact:** Anyone adding unedited/freshly-downloaded archives with nested
ComicInfo.xml gets silently-wrong metadata on import, with no error — looks like
a normal but unusually sparse issue.

**Supersedes v2.4 Item 8 (Flatten Archive).** Confirmed with Tez this bug is the
reason Flatten Archive was built as a CAPT tool originally — once fixed,
nested-folder archives read correctly on import (this fix) and self-flatten on
first edit (existing behavior), so there's no remaining case a standalone Flatten
tool would still need to handle. See `DECISIONS.md` and
`archive/v2.4/comicvault-changes-v2.4.md` Item 8.

**Fixed, 2026-07-02 — off-cycle session after v2.4's close** (never tied to a
numbered version item; Items 8/14, the tools it superseded, were dropped rather
than replaced by it). Implemented the scoped plan exactly as written in
`archive/v2.4/code-handoffs/bug-018-nested-comicinfo-scanner-fix.md`:
`_parse_cbz()` (`backend/scanner.py`) now calls `find_xml_in_archive()` /
`extract_xml_from_archive()` (the same helpers both editors already used),
filtered to entries ending in `comicinfo.xml` (case-insensitive) and taking the
first match, instead of the old exact-equality `namelist()` check that only ever
matched root-level entries. Parses via `ET.fromstring()` on the extracted string
content instead of `ET.parse()` on a zip file handle. No other files changed —
`archive_io.py`'s flatten-on-save behavior is untouched, and no rebuild happens
at scan time, per the plan's explicit decision.

Verified three ways against scratch files only (never the real library):
1. **Unit-level**, calling `_parse_cbz()` directly against three constructed
   archives — nested-folder XML now correctly returns `metadata_source="xml"`
   with the real series/number/writer fields (previously would have
   filename-fallen-back); a root-level-XML archive still parses correctly
   (regression check); a no-XML archive still falls back to filename parsing
   correctly (regression check).
2. **End-to-end via `scan_single_file()`** against a real (temporary) DB row:
   inserted a nested-XML scratch archive, confirmed the resulting `Issue` row
   had `metadata_source == "xml"` and the correct series/number/credits, then
   deleted the row (cascade-deleted genres/credits/progress) to leave the DB
   exactly as found.
3. **Live UI check** — the temporary issue displayed correctly on `/issue/{id}`
   (title, issue number, writer credit all correct) and opened correctly
   pre-filled in the Basic Editor, confirming the "editable without needing
   Full Editor first" requirement from the fix plan. Closed without saving,
   then deleted the scratch DB row as in step 2.

No CBR-specific test was needed — `find_xml_in_archive()`/
`extract_xml_from_archive()` already dispatch through `archive_formats._opener()`,
the same CBZ/CBR-agnostic helper both editors use, so the fix covers CBR
identically to CBZ with no separate code path.

---

### BUG-019 — Flutter app doesn't connect to the server

**Found:** 2026-07-04, same report as BUG-020 (still open, see `BUGS.md`).

**Root cause confirmed 2026-07-04**, by reading `backend/auth.py` /
`backend/main.py` directly plus a live curl reproduction: `ApiService.checkConnection()`
(`flutter_app/lib/services/api_service.dart`, called at library-screen startup and
from the Settings "Test Connection" button) pings `GET /api/admin/stats`. That route
is mounted with `dependencies=_auth_gate` (`main.py` line 129), and `require_admin_auth`
(`backend/auth.py` line 108) rejects any request whose peer host isn't `127.0.0.1`/`::1`
with a 403 whenever `remote_admin_enabled` is off — which is the default
(`config.json` currently has it `false`). This gating was added for v2.4 Item 1
(remote-admin gating, closed 2026-06-29) — it didn't exist yet the last time the
Flutter app was actively used, which is why this reads as a new failure now rather
than something that was always broken. The network-change theory Tez raised was
ruled out: curl from this machine's LAN IP (192.168.0.151) showed `/api/admin/stats`
403ing while ordinary data routes (`/api/library`) returned 200 — the server was
reachable over the LAN exactly as expected; the connectivity *check itself* was
hitting a route that was never meant to be reachable remotely.

**Fix (code, 2026-07-04):**
- `backend/routers/home.py` — added `GET /api/ping`, an intentionally unauthenticated
  liveness route (mounted via `home.router`, which carries no `_auth_gate`), returning
  `{"status": "ok"}`.
- `flutter_app/lib/services/api_service.dart` — `checkConnection()` now calls
  `/api/ping` instead of `/api/admin/stats`.

**Second, independent root cause found during on-device verification (2026-07-04,
later session):** the auth-gating fix above was correct but not sufficient on its
own — Tez's tablet had USB debugging authorization sorted out this session
(previously blocking, per the first pass's notes), enabling a real rebuild +
install + on-device test for the first time. That first on-device test *still*
showed "Server offline" despite the `/api/ping` fix being installed. Reading the
tablet's actual saved settings (`adb shell run-as com.comicvault.comicvault cat
.../shared_prefs/FlutterSharedPreferences.xml`) showed `flutter.server_url` was
`http://192.168.0.151:8000` — port **8000**, not **9424** where the server
actually listens (`netstat` confirmed nothing listening on 8000 at all). This is
a stale value saved in the app's own local settings from some earlier point,
unrelated to the auth-gating bug — the first session's curl-based verification
never caught it because it tested the right port directly rather than exercising
the app's actual stored configuration. Both causes had to be fixed for the
tablet to actually connect: the code fix (`/api/ping`) alone would still have
left the app pointed at a dead port.

**Fixed, 2026-07-04 — verified on the real Lenovo tablet (device `HGR3SJY1`)**:
built and installed a debug APK (`flutter build apk --debug` /
`flutter install -d HGR3SJY1 --debug`) with the `/api/ping` fix, launched the
app, corrected the saved server URL to `http://192.168.0.151:9424` via the
Settings screen's own text field and "Test connection" button (not a raw prefs
edit — exercises the real save path), confirmed "Connected successfully",
saved, and relaunched fresh: the offline banner was gone, the Series/Singles/
All/2000 AD tabs appeared, and the library loaded real cover images from the
server over the LAN. Screenshots taken during verification were scratch files,
deleted after confirming — no repo files retained from the test.

**Note for anyone hitting "offline" again after a server IP/port change:** check
the app's own Settings screen first (`ComicVault server URL` field) before
assuming a code regression — this bug was two independent causes stacked
together, and the simpler one (a stale saved address) is easy to miss if you
only look at the harder one (the auth-gating logic).

---

### BUG-020 — Flutter app crashes when selecting a CBZ on the tablet

**Found:** 2026-07-04, OPDS/3rd-party-reader scoping session — Tez reported the
app has been in this state "a while," not caught earlier because all recent
attention was on server/web dev.

**Root cause confirmed 2026-07-04 (later session), by live repro on Tez's real
Lenovo tablet with logcat capture** — the "Open local CBZ file" flow
(`library_screen.dart` `_openLocalFile()` → `LocalCbzService.pickFile()` →
`file_selector`'s system document picker), the only local-file path in the app,
reachable whenever the server shows offline. Tez asked "could it be file
association?" — two independent, both-real bugs turned up; one is exactly
that, the other isn't:

- **Cause 1 (the actual "crash"):** picking a real 346 MB CBZ died instantly
  with a captured `FATAL EXCEPTION`:
  ```
  java.lang.OutOfMemoryError: Failed to allocate a 345506792 byte allocation
    with 2753277 free bytes ... growth limit 268435456
      at dev.flutter.packages.file_selector_android.FileSelectorApiImpl.toFileResponse
  ```
  `file_selector_android` materializes the whole picked document into a single
  Java byte array before returning it to Dart, rather than streaming it.
  Android's default per-app heap ceiling is 256 MB; any CBZ over ~200–250 MB
  (not unusual for a high-res scan) blew this every time.
- **Cause 2 (the "file association" one):** `content query` against
  `content://media/external/file` showed two different `.cbz` files on the same
  device carrying two different OS-assigned MIME types
  (`application/x-cbz` vs `application/vnd.comicbook+zip`, depending on when/how
  each was indexed). `LocalCbzService`'s `XTypeGroup(extensions: ['cbz'])` only
  matched one of these in the system picker's filter — files with the other
  MIME type were visible in the picker (generic icon, no thumbnail) but tapping
  them did nothing at all: confirmed via `uiautomator dump` the grid item was
  genuinely clickable, and via `dumpsys activity activities` that the tap never
  left the picker activity. No crash, no error — just a dead tap.

**Fix, built and verified 2026-07-04 (same session as diagnosis) — three
rounds, each caught by testing on Tez's real tablet rather than by reasoning
alone:**

1. **Native streaming picker.** Replaced `file_selector` with a custom
   `MethodChannel` (`comicvault/local_file_picker`) handled in
   `MainActivity.kt`: launches `ACTION_OPEN_DOCUMENT` with `type = "*/*"`
   (fixes Cause 2 directly — no OS-level MIME filter left to drift out of sync)
   and streams the result to a cache file via `ContentResolver.openInputStream()`
   in fixed 64KB chunks (fixes Cause 1 — memory use is flat regardless of file
   size, never materializes the whole file at once). `file_selector` and all
   its platform packages removed from `pubspec.yaml`.
2. **Archive caching, `LocalCbzService`.** `listPages()`/`readPage()` used to
   independently re-read and re-decode the entire file from disk on *every*
   call — for a 136-page issue, that's 136 full reads of a 346 MB file, not
   136 reads of one page each. Fixing Cause 1 got far enough to actually reach
   this code path for the first time (it never ran before — the old picker
   crashed first), which is how this was found: the app now survived the pick
   but was killed by Android's system-wide low-memory killer ~30–45s later,
   RSS around 2 GB. Now decodes the archive once per file, cached by path, and
   reuses it for every subsequent page read.
3. **Lazy per-page reads + resolution-capped decode.** Even with caching,
   `LocalReaderScreen._load()` still eagerly extracted *every* page up front
   into a `List<Uint8List>` before showing anything — for this issue, all 136
   pages' worth of decompressed image bytes held in memory at once. Changed to
   count pages only; `LocalComicPageView` now calls `LocalCbzService.readPage()`
   on demand inside its `ListView.builder`/`PageView.builder` `itemBuilder`s, so
   only pages actually built are decoded. Also added `Image.memory(...,
   cacheWidth: ...)` capped to the device's own physical screen width — this
   issue's pages happened to be 1988×3056px (~24 MB per page once decoded raw),
   and Flutter decodes at full source resolution by default regardless of
   display size. `LocalCbzService.clear()` added and called from
   `LocalReaderScreen.dispose()` so the cached archive doesn't outlive the
   reader screen (it's otherwise a long-lived singleton for the app's whole
   session).

**Verified on Tez's real Lenovo tablet (`HGR3SJY1`, 3.7 GB total RAM) against
both the originally-broken 346 MB / 136-page CBZ and the MIME-mismatched 56 MB
Cyberpunk 2077 file:**
- Both files now pick successfully (Cause 2 confirmed fixed — the previously
  dead tap now works).
- **Debug builds still struggle with the 346 MB file** — even after all three
  fixes, a debug build held ~2 GB RSS and still got killed by the OS after
  ~20–45s, whether idle or scrolling. Debug builds carry substantially heavier
  baseline memory overhead (JIT runtime, debug metadata, no tree-shaking) than
  release builds.
- **The release build is stable** — same file, same device: RSS held flat
  around 200–212 MB through 80+ seconds idle and through normal-paced
  scrolling, versus the ~800 MB–2 GB that triggered kills before. This is the
  build that actually ships, so this is the number that matters.
- The smaller 56 MB Cyberpunk file was stable in both debug and release
  throughout.

**Note for anyone testing this again:** if a debug build (`flutter run` /
`flutter build apk --debug`) seems to still struggle with a very large local
CBZ, that's expected given the above — test against a release build before
concluding the fix regressed. This tablet's 3.7 GB total RAM is also unusually
tight for this device class; an even larger scan (or a device with less RAM
still) could in principle still hit this ceiling. The fix removes the
*reliable, every-time* crash — it doesn't raise a hard guaranteed ceiling.

---

### BUG-008 — Flutter app's 2000 AD tab calls endpoints removed in v2.2

**Found:** 2026-06-22, flagged by the nightly doc scan.

**Where it was:** `flutter_app/lib/screens/two_thousand_ad_screen.dart` —
`TwoThousandAdTab` called `GET /api/2000ad/years`; `TwoThousandAdYearScreen`
called `GET /api/2000ad/year/{year}`. Both endpoints were removed in v2.2
(Part A, `backend/routers/home.py`) — the web-side 2000 AD surface was
removed intentionally and its behaviour generalised into Folder View (Custom
Tabs, `CUSTOM_TABS_SPEC.md` §9), but Flutter was explicitly out of scope for
v2.2, so the Flutter tab was never replaced or removed — just left calling
endpoints that no longer existed.

**Fix, 2026-07-04 — Tez's call: remove the tab entirely, not build a Custom
Tabs equivalent for Flutter.** Custom Tabs is a web-only feature with no
Flutter counterpart, and wasn't worth building just to replace this one
broken tab (that scoping question, if it ever comes up, is separate and
bigger than this fix). Removed:
- `flutter_app/lib/screens/two_thousand_ad_screen.dart` — deleted entirely
  (`TwoThousandAdTab`, `TwoThousandAdYearScreen`, and their supporting
  widgets).
- `library_screen.dart` — `TabController` changed from `length: 4` to
  `length: 3`; removed the `Tab(text: '2000 AD')` entry and the
  `TwoThousandAdTab` child from the `TabBarView`; removed the now-unused
  import.
- `api_service.dart` — removed `get2000adYears()`/`get2000adYear()`, the two
  methods that called the removed backend endpoints.

**Not a data-loss concern:** 2000 AD issues already in the library (progs,
yearbooks, specials, etc.) aren't affected — they're ordinary series/issues
and remain fully browsable through the regular Series/Singles/All tabs
exactly like any other publisher's comics. Only the dedicated year-grouped
browsing tab (which depended on the removed endpoints) is gone.

**Verified on Tez's real Lenovo tablet** — rebuilt and installed a debug
APK: the library screen now shows exactly three tabs (Series/Singles/All),
confirmed the 2000 AD series/issues (2000 AD, 2000 AD Sci-Fi Special,
30 Days of Night, etc.) still appear normally in Series and All, and tapped
through all three tabs with no errors or crashes.

**This closes out the last open item from the 2026-07-04 mobile-bugs
report** (BUG-019 connection failure, BUG-020 CBZ-select crash, and this —
all found in the same report, all independent root causes, all now fixed).

---

### BUG-017 — Android: no file association for .cbz to open in the app

**Found:** 2026-07-04 (late), Tez, outside a build session — inbox capture
during Sunday triage 2026-07-05.

**Scope decision, before building:** the title as originally logged said
"cbz/r," but the Flutter reader has no RAR decoder anywhere in its code —
`LocalCbzService` decodes exclusively via `ZipDecoder()`. Confirmed with Tez:
scope this fix to `.cbz` only. Associating `.cbr` too would have put
ComicVault in the "Open With" list for files it can't actually read, trading
"no app can open this" for a different, equally unhelpful error. `.cbr`
stays unassociated — exactly as unopenable as it was before, no regression.

**Fix, 2026-07-05:**
- `AndroidManifest.xml` — two new `<intent-filter>` blocks on `.MainActivity`
  for `ACTION_VIEW`: one matching the MIME types real file managers actually
  send for zip-based comic archives (`application/vnd.comicbook+zip`,
  `application/x-cbz`, `application/zip`), one as a fallback matching the
  literal `.cbz` extension via `pathPattern` for managers that send
  `application/octet-stream` or no useful type at all (requires
  `mimeType="*/*"` alongside the pattern — omitting it restricts the filter
  to untyped intents, which real "Open With" launches essentially never are).
- `MainActivity.kt` — new `resolveSharedUri` method on the existing
  `comicvault/local_file_picker` channel, reusing the already-existing
  `copyToCache()` helper (written for the local file picker, BUG-020) to
  stream a `content://`/`file://` URI into a cache file and return a real
  path.
- **A second, previously-invisible bug found during testing:**
  `FlutterActivity`'s default behaviour auto-converts any incoming
  `ACTION_VIEW` intent into a raw `Navigator.pushNamed()` call using the
  URI's literal path as the route name — before `app_links`' own
  `uriLinkStream` (what `main.dart`'s `_handleLink` listens on) ever saw it.
  Since a path like `/storage/emulated/0/Download/foo.cbz` isn't a
  registered route, this crashed with "Could not find a generator for
  route" and silently swallowed the intent. This is a stock Flutter/Android
  embedding behaviour, unrelated to anything specific to this fix — fixed by
  overriding `shouldHandleDeeplinking()` to return `false` in `MainActivity`,
  so `app_links` is the sole path handling incoming intents. (Root-caused by
  attaching `flutter run` directly to the tablet and reading the live Dart
  exception — plain `adb logcat` on an installed APK didn't surface it
  clearly enough to diagnose.)
- `local_cbz_service.dart` — thin `resolveSharedUri()` wrapper.
- `main.dart` — `_handleLink()` now routes any `content://`/`file://` URI
  (as opposed to the existing `comicvault://read/{id}` case) through
  `resolveSharedUri()` and into the existing `/reader/local` route, the same
  one the in-app file picker already uses.

**Verified:** extensively via `adb` against Tez's real tablet before any
manual step — `pm resolve-activity`/`dumpsys package` confirmed Android
resolves ComicVault as a `.cbz` handler; firing real `VIEW` intents
confirmed no crash post-fix and traced (via temporary debug prints, removed
before final build) that the intent correctly reaches `resolveSharedUri`
with no exceptions in the Dart/native bridge. The one thing `adb` couldn't
simulate — a real, permission-granted `content://` URI, since Android's
scoped storage rejects a hand-built `file://` URI with `EACCES`, and
MediaStore's raw path querying is itself locked down — was confirmed by
Tez's own manual test: tapped a `.cbz` in the file manager, ComicVault
appeared under Open With, selected it, opened correctly into the reader.

---

### BUG-021 — No working reader outside the Flutter app (web UI has none by design; V1's Windows reader was never carried into V2)

**Found:** 2026-07-05, during v2.5 Item 3's (Mobile ↔ Server Reading-State
Sync) manual verification pass — needed a second way to view/change a
comic's reading progress to confirm the sync conflict rule's `server_kept`
case didn't get visibly clobbered, and neither option worked.

**Where:** Two separate causes, not one bug:
- The web UI has no reader page at all — `SPEC.md` §11 already documents
  this as by-design ("`reader.html` is NOT built — the Read button in
  `issue.html` deep-links into the Flutter app"), not a regression. Still
  true, still by-design — unaffected by this fix, and not what this bug was
  actually tracking (see Impact below).
- The standalone Windows reader EXE built during V1 was never rebuilt or
  moved across into this V2 checkout — it isn't present/functional here.

**Update 2026-07-09:** the "Read" button referenced above has been removed
from `issue.html` entirely (Tez's UI tweak-pass call) — the
`comicvault://read/{id}` link had no handler on a plain desktop browser, so
it did nothing useful outside the Flutter app anyway. This doesn't fix or
worsen this bug (there was never a working web reader either way) — it just
means there's now no reader-related control anywhere in the web UI at all.
See `SPEC.md` §11 and `DECISIONS.md`.

**Impact:** No way to exercise or verify reading-progress behavior from a
desktop/browser context without the Flutter app. Blocked one verification
step for v2.5 Item 3 (confirming `server_kept` visually, beyond the
backend's own scratch tests, which already cover that exact code path).
Not a defect in anything shipped in Item 3 itself.

**Fixed, v2.6 Item 5 (Windows Desktop Reader).** `flutter_app/` was already
one shared Dart codebase targeting both Android and Windows — the `windows/`
platform folder existed but had never been rebuilt/polished/tested since the
V1 initial commit (all live development had been Android-tablet-only). Got
it working properly as a Windows desktop reader rather than porting the old
V1 app separately:
- Guarded the Android-only local-file-picker `MethodChannel`
  (`local_cbz_service.dart`'s `pickFile()`/`resolveSharedUri()`) to no-op on
  non-Android platforms, and hid the "Open local CBZ file"
  button/"Recent files" list in `OfflineLibraryView` on Windows — desktop is
  expected to be on the same LAN as the server, so local file picking was
  descoped there rather than given a Windows-native implementation.
  Confirmed the Android-only immersive-mode `SystemChrome` call in
  `reader_screen.dart` is a harmless no-op on Windows.
- Added keyboard support to the reader (`toolbar_overlay.dart`): arrow keys
  page/scroll, Escape goes back — the reader was touch/mouse-only before.
  Fixed `nextPage()`/`prevPage()` in `comic_page_view.dart` to actually do
  something in Scroll mode too (previously a no-op there, since the
  `PageController` those methods drove wasn't attached to the `ListView`).
- Rebranded the native Windows shell (`windows/runner/main.cpp`,
  `Runner.rc`) from the stock "comicvault" title/metadata to "digib00age",
  matching the app's actual brand elsewhere (favicon, mobile home screen).
  The Windows launcher icon was already current — no change needed there.
- Reviewed `CoverCard`/`BrowseScreen`'s grid/`ShellScreen`'s rail+content
  layout for desktop reflow — all width-adaptive by construction
  (`AspectRatio` + ellipsis text, `SliverGridDelegateWithMaxCrossAxisExtent`,
  `Row`/`Expanded`), no fixed-width assumptions found.
- The web-UI-has-no-reader-page cause above is unaffected — still true,
  still by-design, and tracked separately as the scope of a possible future
  `/issue/{id}` → "open in reader" integration, not reopened here.

**Verified:** Tez ran `flutter run -d windows` and confirmed navigation
(rail → Home/Browse/Series/custom libraries) and reading (Scroll + Page
mode) both work.
