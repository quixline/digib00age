# ComicVault — Changelog

Terse, one-line-per-entry index, newest first. Each line is a pointer into
`progress.md`'s matching section heading — read there for the full narrative,
what was verified, and any gotchas. Bug fixes already logged in `BUGS.md` aren't
repeated here unless they also got their own `progress.md` session entry.

---

- **2026-06-27** — v2.3 Item 10: Admin Password Recovery — added a "Forgot
  Password?" button/popup to the Admin Top Action Row with manual `config.json`
  recovery steps.
- **2026-06-27** — Fixed folder-view card sizing/image-fit mismatch vs standard
  cards (`.folder-card.has-cover` aspect-ratio bug). Fixed BUG-003 (removed dead
  duplicate `GET /api/reading/continue` route in `progress.py`).
- **2026-06-26** — v2.3 post-test fix pass (`docs/2.3-fixes.md`, Fixes 1–9, plus
  two additional steps raised mid-session). Menu bar: collapsed the unintended
  second row into one (status pills moved to the header, secondary filters +
  count merged into the menu-bar row), fixed a CSS shorthand bug that broke
  edge alignment with the header/card grid, widened the search bar, and — per
  Tez's mid-session request — extended secondary filters and the full menu row
  to Folder View (previously Flat-View-only). Multi-select: favourite toggle
  now actually toggles (was add-only), added a rating-clear button (was
  invisible due to a colour-matches-background bug, also fixed). Full Editor:
  Process All errors now open a dismissible modal instead of an unbounded
  inline wall of text. Auth: login popup no longer fires on the unprotected
  library page, the auth button is now always visible with a Login/Logout
  label, disabling password protection requires re-entering the current
  password, and clicking Login with no password set shows an explanation
  dialog instead of a doomed-to-fail form. Admin: Last Scan persists across
  server restarts, the changed-files log now distinguishes metadata-only vs.
  archive(page-count) changes, and a new Last Backup indicator + scheduler
  failure surfacing was added to the Scheduled Backup block. See
  `docs/progress.md` for the full build narrative.

- **2026-06-24** — v2.3 Item 9 (final v2.3 item): Admin destructive actions +
  Donate placeholder. New "Danger Zone" in Advanced Settings — Clear Database
  (wipes issues/genres/credits/reading progress + orphaned People rows, leaves
  Custom Tabs/Home Strips intact) and Clear Reading Progress, both gated
  local-only and confirm()-gated like the existing Delete Tab flow. New
  Donate button + "Coming soon" placeholder modal in the top action row. The
  Full Editor admin cog-link (also part of this item per spec) was already
  built in the Item 6 session. See `docs/progress.md` for the full build
  narrative.

- **2026-06-24** — v2.3 Item 8: Admin scheduled database backup + server
  listening port. New Scheduled Backup section (native OS folder dialog for
  the destination — not the existing library-scoped picker, which can't
  reach paths outside the library — + a 22-option frequency dropdown); the
  existing manual Backup Database button now uses the same destination once
  set. New Server Listening Port field in Advanced Settings — saving
  confirms, then restarts the server (self-exit, relying on the tray app's
  existing crash-recovery to relaunch on the new port). See
  `docs/progress.md` for the full build narrative.

- **2026-06-24** — v2.3 Item 7: Admin scan log cards + Logs area + Auto Scan
  Options. Each of the 4 scan stat cards (Last Scanned, New Files, Changed
  Files, Missing Records) now has a persistent on-disk log in `/logs/`, a
  "Logs" button to view it, and a green-border indicator for unviewed entries.
  New Logs section (folder path display + log size limit) and Auto Scan
  Options (frequency dropdown + scan-on-launch) under Library Scan. Resolved
  the spec's open "what counts as changed" TODO by reading `scanner.py`
  directly — see `DECISIONS.md` and `BUGS.md` BUG-013 for a confirmed
  pre-existing detection gap (size-only changes with an unchanged mtime).
  See `docs/progress.md` for the full build narrative.

- **2026-06-24** — v2.3 Item 6: Admin password protection + Remote Administration
  toggle. Single shared password gates `/admin`, `/editor`, the Basic Editor popup,
  and all `/api/admin/*` + `/api/editor/*` endpoints (off by default, no behaviour
  change until enabled). Stateless signed-cookie sessions, in-memory brute-force
  lockout, local-only enforcement on enable/disable/password-change/remote-toggle.
  See `docs/progress.md` for the full build narrative.

- **2026-06-23** — Full Editor Process All gained a per-field "Apply to: All"
  checkbox (default unchecked) — only checked fields bulk-apply across every
  loaded file; unchecked fields keep each file's own value. Issue Number has
  no checkbox (governed by the existing Increment # mechanism only). Backend
  validation fix alongside it: enforced-field checks (Genre/Format/AgeRating)
  now validate each file's *effective* merged result, not just the partial
  checked-fields payload. See `EDITOR_SPEC.md` §5.2 and v2.3 build plan Item 5.
- **2026-06-23** — Multi-select scope expanded to Series-aggregate cards:
  long-press-selecting a series card now expands to every issue in that
  series server-side before a bulk Read/Unread/Favorite/Rate action runs,
  same meaning as the existing "Mark all read" series-detail button. See
  `SPEC.md` §20.15 and v2.3 build plan Item 4.
- **2026-06-23** — Card behaviour additions shipped: larger favourite-star
  badge with a black border, a thin gold border on favourited cards
  (coexisting with the existing read-state colours), a wider issue-page star
  rating row, and a new light/dark theme system (auto-matches Windows, with
  a manual override in Admin → Appearance). See `SPEC.md` §20.17 and v2.3
  build plan Item 3.
- **2026-06-23** — Unified menu bar (sort dropdown + asc/desc toggle, star
  rating filter, favourites filter, shared grid/list toggle) shipped across
  Flat View and Folder View, replacing the old three-state sort-cycle button.
  Folder View gained full parity — sort/filter now apply there too, including
  a new recursive "any descendant favourited" flag on folder cards. See
  `MENU_BAR_SPEC.md` and v2.3 build plan Item 2.
- **2026-06-23** — Folder View folder cards now show a representative cover
  image: one randomly-selected cached thumbnail from any issue recursively
  under that folder, re-rolled on every request. No new pipeline — reuses
  the existing per-issue thumbnail cache. See `CUSTOM_TABS_SPEC.md` §9.2.
- **2026-06-22** — v2.2 shipped: 2000 AD's hardcoded fixed-tab surface fully
  removed (endpoints, nav button, year-grid UI, all code paths); Custom Tabs
  gained a `view_mode` (`flat`/`folder`) — Folder View generalises 2000 AD's
  old year-grid into a reusable per-tab mode with recursive folder/file
  browsing, real history-backed navigation, depth-agnostic search, and
  recursive Mark All Read. 2000 AD itself becomes an ordinary Folder View
  custom tab post-build. `CUSTOM_TABS_SPEC.md` amended (§9); both
  `comicvault-changes-2.1.md` and `comicvault-changes-v2.2.md` backlogs now
  closed. → `progress.md` "Session — 2026-06-22: v2.2 — Folder View + 2000 AD
  removal"
- **2026-06-22** — Both Tier 3 items done: Home page search bar (copy unified
  with the browse tabs — "Search All"/"Search Singles"/"Search Series"); card
  size control (10%/25%/50%/100%), then reworked into Admin → Pagination and
  extended to Home strips and the 2000 AD year picker (both had been missed
  initially and stayed hardcoded). **`comicvault-changes-2.1.md` backlog now
  fully closed** (renamed from `comicvault-changes.md`). →
  `progress.md` "Session — 2026-06-22: Tier 3 — search bar + card size (+ rework)"
- **2026-06-22** — All 9 Tier 2 ride-along items done: clickable genre tags
  on `/issue/{id}`, restyled "Clear" filter button, Format added to Grouping
  menu, "Mark all read" on 2000 AD Year page, pagination 25 option, Admin
  "Save Advanced Settings" renamed to "Save Location" and moved onto the
  path's row, Scan Now / Clean Up card border states, and an `.admin-main`
  padding shorthand bug fixed (was overhanging the header by 20px each
  side). → `progress.md` "Session — 2026-06-22: Tier 2 — full batch"
- **2026-06-22** — Tier 1 bug fix: All tab, list view — read/part-read cards'
  list-only fields (`.list-genres`, `.list-pub-writer`, `.list-summary`) stayed
  dim grey instead of picking up the white-text override grid view's
  `.cover-title`/`.cover-count`/`.cover-year` already had for those states.
  Added to the same override block. → `progress.md` "Session — 2026-06-22:
  Tier 1 — List view read-state text colour"
- **2026-06-22** — Tier 1 bug fix, second correction: the 2000 AD Years page's
  "All Years" button had the same labeling inconsistency, missed by a silent
  (unflagged) scoping judgment during the prior fix. Label changed to "Back";
  click behavior intentionally left as its existing in-page toggle, not real
  history, since year selection never pushes a history entry. → `progress.md`
  "Session — 2026-06-22: Tier 1 — Back button inconsistency (2000 AD Years
  page)"
- **2026-06-22** — Tier 1 bug fix, corrected: the 2026-06-21 Admin-only fix
  below was incomplete — Issue and Series detail pages had the same guessed-
  destination problem, missed because the prior session was terminated by an
  error before it got there. All three back links now use real
  `history.back()` with a plain "Back" label. → `progress.md` "Session —
  2026-06-22: Tier 1 — Back button inconsistency (full fix)"
- **2026-06-21** — Tier 1 bug fix: Admin's Back link now uses real browser
  history (`history.back()`) with a label derived from where the user came
  from, instead of a hardcoded link to `/`. → `progress.md` "Session —
  2026-06-21: Tier 1 — Back button inconsistency (fix)"
- **2026-06-21** — Tier 4 Item 3 (Session C, frontend): clickable Writer/Artist
  credit links on `/issue/{id}`, dropdowns removed, editor fuzzy warn-on-save.
  Tier 4 Item 3 now fully complete. An incident during testing modified a real
  CBZ's metadata; fully restored and verified, full account + a newly-found
  unrelated bug (BUG-007) in `progress.md`/`BUGS.md`. → `progress.md` "Session —
  2026-06-21: Tier 4 Item 3 — Session C"
- **2026-06-21** — Tier 4 Item 3 (backend + real migration): Writer/Artist entity
  dedup — new `people`/`issue_credits` tables, scanner integration, candidate-
  duplicate detection (76 pairs, 35 confirmed merges), real migration run against
  the live library. Frontend click-through UI deferred to a later session. →
  `progress.md` "Session — 2026-06-21: Tier 4 Item 3"
- **2026-06-21** — Tier 4 Item 2: Multi-select + Favorites/Rating built (long-press
  card selection, bulk Read/Unread/Favorite/Rate toolbar, new `favorites`/
  `personal_rating` Issue fields, standalone favorite/rating controls on the issue
  detail page). → `progress.md` "Session — 2026-06-21: Tier 4 Item 2 — Multi-select +
  Favorites/Rating"
- **2026-06-20** — Tier 4 Item 1: Genre/Format admin editor built (Format reversed
  from locked constant to admin-editable list; both Genre and Format got add/remove
  UI in Admin, neither had one before). → `progress.md` "Session — 2026-06-20: Tier 4
  Item 1 — Genre/Format admin editor"
- **2026-06-19** — BUG-004 investigated: server failed to bind port 8000 after an OS
  restart (Windows/WSL2 port-exclusion conflict, not a code defect). → `progress.md`
  "Session — 2026-06-19: BUG-004, server failed to start after OS restart"
- **2026-06-19** — Tray app menu redesign: split Stop/Start, added Close, dark-mode
  menu, self-service login-autostart toggle. → `progress.md` "V2.1 — Tray App Menu
  Redesign (2026-06-19)"
- **2026-06-19** — Home Strips built (`HOME_STRIPS_SPEC.md`). → `progress.md` "V2.1 —
  Home Strips Built (2026-06-19)"
- **2026-06-19** — Custom Tabs built (`CUSTOM_TABS_SPEC.md`). → `progress.md` "V2.1 —
  Custom Tabs Built (2026-06-19)"
- **2026-06-18** — Full/Basic Editor UI polish pass. → `progress.md` "V2 — Full Editor
  / Basic Editor UI Polish (2026-06-18)"
- **2026-06-18** — Startup failure found and fixed. → `progress.md` "V2 — Startup
  Failure Found and Fixed (2026-06-18)"
- **2026-06-18** — First manual test pass fixes, incl. BUG-002 (Full Editor Queue
  button gating). → `progress.md` "V2 — First Manual Test Pass Fixes (2026-06-18)"
- **2026-06-18** — Full Editor built (batch pre-library tagging). → `progress.md` "V2
  — Full Editor Built (2026-06-18)"
- **2026-06-18** — Basic Editor built (single-issue popup editor). → `progress.md` "V2
  — Basic Editor Built (2026-06-18)"
- **2026-06-18** — Pre-migration data-hygiene report built. → `progress.md` "V2 —
  Pre-Migration Data-Hygiene Report Built (2026-06-18)"
- **2026-06-18** — Editor genres endpoint built. → `progress.md` "V2 — Editor Genres
  Endpoint Built (2026-06-18)"
- **2026-06-18** — Editor core built (shared XML read/merge/write logic, ported from
  CAPT). → `progress.md` "V2 — Editor Core Built (2026-06-18)"
- **2026-06-18** — V2 migration setup complete (repo cloned from V1, BUG-001 scanner
  thumbnail fix applied). → `progress.md` "V2 — Migration Setup Complete (2026-06-18)"
- **2026-06-17** — V1 build and testing complete. → `progress.md` "V1 — Build and
  Testing Complete (2026-06-17)"
- **2026-06-12** — Phase 6: Tray app + Admin page complete. → `progress.md` "Phase 6 —
  Tray App + Admin (Complete)"
- **2026-06-12** — Phases 1–5: Scanner/DB, REST API, Web UI, Issue Detail page, Flutter
  app — V1 core complete. → `progress.md` Phases 1–5
