# ComicVault — Roadmap

Paused, deferred, or future work — explicitly out of scope until unblocked or
prioritized. If a request seems to fall under something listed here, flag it rather
than building it; `archive/comicvault-changes-2.1.md` and
`archive/comicvault-changes-v2.2.md` (both closed 2026-06-22),
`archive/v2.3/comicvault-changes-v2.3.md` (closed 2026-06-29), and
`archive/v2.4/comicvault-changes-v2.4.md` (closed 2026-07-02) covered the prior
active queues. No active build queue right now — `docs/v2.5/` hasn't been created
yet; real scoping starts whenever that triage session happens (see "v2.5" below).

---

## v2.4 — closed 2026-07-02

All 16 items resolved: Items 1–7, 9–13, 15–16 built and manually verified; Items 8
and 14 (Flatten Archive, scope + build) dropped, superseded by BUG-018 (fixed
off-cycle 2026-07-02, after this close-out — tracked independently in `BUGS.md`,
never blocking the close-out since bug fixes aren't version-scoped; see
`archive/bugs-fixed-archive.md`). Items 1–3 (remote-admin gating, default port 9424,
empty-state logo) verified 2026-06-29; the CAPT-tooling cluster (Favourites, CBR
support, File Rename, Convert Archives, Convert Images, Processing Folder
Automation — Items 4–7/9–13/15–16) scoped through 2026-07-01 and built/verified
2026-07-01–02, including two post-test fixes to File Rename (the "Add to Queue"
workflow and an Auto-Increment field-wiping bug) found during the manual test
pass. Full detail archived at `archive/v2.4/comicvault-changes-v2.4.md`;
`archive/v2.4/progress.md` holds the full session narrative.

**v2.3 closed 2026-06-29.** Items 1–9 built (Items 1–5 on 2026-06-23, Items 6–9 on
2026-06-24) and verified via the manual test pass on 2026-06-26 (9 fixes same day).
Items 10–13 built and Code-verified 2026-06-27; manually tested 2026-06-28 — Items
10 (Password Recovery), 11 (Backup frequency), and 13 (Card Size 75%) passed; Item
12 (Restore Database) did not pass — restore completes but DB is not reverted to
the backup state (`BUGS.md` BUG-016, open — root cause confirmed, fix not yet
built). Item 14 moved out of v2.3's queue 2026-06-28 — see "Blocked on Claude
Design UI redesign exploration" below. Full detail archived at
`archive/v2.3/comicvault-changes-v2.3.md`; `archive/v2.3/progress.md` holds the full
project narrative through v2.3's close.

---

## v2.6 — UI Redesign (blocked on Claude Design exploration)

Two items share the same blocking dependency — a parked exploration with Claude
Design on overall UI redesign direction, not yet started. Both should be revisited
together once that direction exists, since either could change what the other needs
to do.

**v2.3 Item 14 — Site-wide: unify the main header across Series/Issue detail pages**
(moved here 2026-06-28, originally scoped 2026-06-27)

`/series/{id}` and `/issue/{id}` currently use a different header treatment than
Home/the browse tabs. Make them consistent with the Home page header. Search scope:
"Search" should search the full library by default — except when already on a
Singles, Series, or Custom Tab surface, where it stays scoped to that surface (same
behaviour as `SEARCH_PLACEHOLDERS`/`updateSearchPlaceholder()` already established
for Home vs. All vs. Singles vs. Series, per `progress.md` "Session — 2026-06-22:
Tier 3"). Open question for whoever picks this back up: what should the search bar
search *from* an issue/series detail page itself, since it isn't "on" any surface
— proposed default is full-library (same as Home), not yet confirmed with Tez.

**Spec:** none yet — destination doc TBC (likely `SPEC.md` or `MENU_BAR_SPEC.md`,
whichever currently governs header layout; confirm during scoping).

**Status pills excluded from scope, confirmed 2026-06-27:** the Unread/Reading/Read
filter pills were deliberately moved up into the site header (out of
`.browse-controls`) during the 2026-06-26 menu-bar fix pass, to make room once the
menu bar picked up more controls (see `progress.md` "Session — 2026-06-26", Fix 1).
They're list filters and don't apply to a single issue or series detail page —
header unification here means nav tabs + search + admin-gear link + logout only.

**Code-reading findings, 2026-06-27 (read `issue.html`/`series.html`/`index.html`/
`app.js` directly before scoping):**

- `issue.html` and `series.html`'s headers currently contain **only the logo and a
  hidden Logout button** — no surface-nav tabs, no search bar, no admin gear-icon
  link at all. This is a bigger gap than "different styling" — the markup itself is
  missing, not just hidden. `index.html` has all of it (`bindSurfaceNav()`,
  `bindSearchEvents()`, the `/admin` gear link).
- Recommend factoring the header bindings into one shared init routine all three
  pages call, rather than duplicating `bindSurfaceNav()`/`bindSearchEvents()`/the
  admin-link wiring a third time.

**`BUG-014` (back-button regression) — sequence with Item 14, not independently:**
the issue/series back-links already use real `window.history.back()` (a code
comment there says this replaced the old `from=` param logic). But the four main
surface tabs (Home/All/Singles/Series, `bindSurfaceNav()`) never call `pushState` —
switching tabs only updates a JS variable, the URL stays bare `/`. Folder View
*does* call `pushState` on every drill-down (`pushFolderViewUrl()` — already
explicitly documented in `app.js` as "a deliberate departure from the simpler
`history.back()`-only pattern used elsewhere"). So: user on All (URL still `/`) →
opens an issue → real navigation pushes `/issue/123` onto history → Back → browser
correctly returns to the literal previous entry, bare `/` → page loads defaulting to
Home. The `?from=all`/`?from=series`/`?from=singles` params still being attached
when building card links (`buildCoverCard()` etc.) are dead code — already ignored
by both detail pages. **Recommended fix:** extend Folder View's existing `pushState`
pattern to the four main surface tabs; once in place, Item 14's nav links on the
detail pages can just point at `/?surface=all` etc. and back-navigation works
correctly for free. Full write-up in `BUGS.md` BUG-014.

Needs a quick scoping pass to confirm current header variants before Code starts,
whenever this gets picked back up.

**Two more items folded in, 2026-07-03 (Tez's call, `INBOX.md` triage):** both are
low-priority Admin-page polish, deferred here rather than built standalone —
(1) remove the redundant custom/editable path text input from Add Custom Tabs
(the folder nav-picker already covers this); (2) Processing Folder Automation's
Schedule/Time/Day row needs to either auto-save like the rest of that page or
get a clear unsaved-changes indicator (found 2026-07-02 investigating a
"scheduled run isn't firing" report — the wall-clock mechanism itself is fine,
see `ADMIN_SPEC.md` §11.4.5). Neither blocks anything before v2.6 starts.

---

## Paused indefinitely

- **Reader-launch feature** (`ADMIN_SPEC.md` §7.6 — Reader Location field in
  Advanced Settings + `/issue/{id}` "Read" button wiring). Scoping revealed this
  requires Flutter app changes — the Windows reader EXE doesn't currently accept a
  launch-into-file argument, so the "Read" button can't directly open a specific
  issue in the reader without Flutter work. Also has a same-machine-only limitation
  (browser and server on different machines on the LAN won't work as expected). Parked
  pending further thought on practical usage vs. building out all the edge cases —
  may be dropped rather than built.

---

## Next session — Mobile app connectivity fix (moved out of "Paused indefinitely" 2026-07-04)

**The "Flutter reader works as-is" assumption above was wrong** — Tez reported
2026-07-04 that the Flutter app currently fails to connect to the server and
crashes when selecting a CBZ on the tablet. Not a new regression as far as
anyone can tell — it's been in this state a while, just not caught earlier
because all recent attention was on server/web dev. Full detail: `BUGS.md`
BUG-020 (CBZ-select crash, still open); BUG-019 (connection failure) is fixed
and closed — see `archive/bugs-fixed-archive.md`.

This is no longer "paused" — third-party reader connectivity (CDisplayEx/OPDS)
was scoped and ruled out this same session (`DECISIONS.md`), which makes fixing
the Flutter app the only path to reader connectivity going forward, not an
optional one. Also folded into the same fix pass: BUG-008 (Flutter's 2000 AD
tab still calls endpoints removed in v2.2) — reactivated now that Flutter dev
is actually starting, and likely to involve real UI changes since the fixed
2000 AD tab has since been replaced web-side by user-defined Custom Tabs
(`CUSTOM_TABS_SPEC.md` §9), which the Flutter app has no equivalent of yet.

**BUG-019 closed 2026-07-04 (later same day), verified on Tez's real Lenovo
tablet** — two stacked causes: `checkConnection()` was hitting an admin-only
route that 403s over LAN by design (fixed with a new unauthenticated
`GET /api/ping`), and separately the tablet's saved server URL had a stale
port (8000 instead of 9424), fixed through the app's own Settings screen. Full
detail in `archive/bugs-fixed-archive.md`.

**Not scoped yet — still a lot here.** Next session starts with root-causing
BUG-020 (the CBZ-select crash — still no stack trace or repro detail beyond
"select a CBZ, it crashes"; BUG-019's fix didn't touch that code path, so it
isn't expected to be incidentally resolved), then scoping whatever UI changes
fall out of replacing the hardcoded 2000 AD tab with a Custom Tabs equivalent.
Two previously-noted future-scope items remain parked for whenever they come
up, not part of this fix: (1) Reader → Server progress sync (local reading
progress synced back to the ComicVault DB — the local/offline mode has no
progress persistence at all right now, per `SPEC.md`); (2) a "Browse local
files" icon next to search so a user can open a local file without
disconnecting from server view.

---

## v2.5 — holding list (v2.4 closed 2026-07-02; Item 1 closed 2026-07-04, rest not yet scoped)

Six items agreed 2026-06-29 (originally seven — "Processing Folder automation"
moved to `v2.4/comicvault-changes-v2.4.md` Item 15 on 2026-06-30, see that doc's
header note for why). One of the six — ComicTagger + ComicVine — has since gone
all the way through scoping, build, and testing; the remaining five are still an
unscoped holding list, not a build queue. `meta/roadmap.html`'s Now lane moved
the first three items here (ComicTagger + ComicVine, OPDS, Processing Folder
custom scripts) up from Next on 2026-07-02; per the version lifecycle in
`meta/working-rules.md`, real scoping (and a `docs/v2.5/` working folder for
them) still needs its own triage session before any of the remaining five move
to an actual build queue.

**ComicTagger + ComicVine API integration — built, fully tested, and closed
2026-07-04.** Tracked as `docs/v2.5/comicvault-changes-v2.5.md` Item 1 (✅);
full build/test/fix narrative in `docs/v2.5/progress.md`, spec detail in
`EDITOR_SPEC.md` §9 and `ADMIN_SPEC.md` §11.4. `meta/roadmap.html`'s Now lane
card removed 2026-07-04 (item complete).

**OPDS — connecting 3rd-party readers — scoped and ruled out, 2026-07-04.**
Research found CDisplayEx (the target reader) doesn't support OPDS at all —
only Komga/Kavita's own proprietary REST APIs — so this wouldn't have delivered
what it was scoped for. Combined with this being a single-connection use case
and a preference for maintaining ComicVault's own client apps over supporting
third-party readers even in a future public-release scenario, both OPDS and the
partial-Komga-API-compatibility idea are dropped, not just deferred. Full
reasoning in `DECISIONS.md`. Removed as a v2.5 holding-list item — the mobile
app connectivity fix above (`## Next session`) is `meta/roadmap.html`'s Now #1
replacement once Code regenerates it.
- **Scope: running custom scripts on the Processing Folder.** Originally listed
  alongside Processing Folder Automation as "likely worth scoping together" —
  stays here in v2.5 on its own (Tez's explicit call, 2026-06-30) even though
  Processing Folder Automation itself moved forward into v2.4 Item 15. Revisit
  whether this still makes sense to scope together once Item 15's design exists.
- **Add: user guide.** Not yet scoped at all — first mention. `ADMIN_SPEC.md`
  §7.1.7's Password Recovery popup (v2.3 Item 10) already explicitly said the
  guide, once built, should link to that popup rather than duplicating its
  instructions — worth checking for any other place a spec already assumes a
  guide exists before scoping this from scratch.
- **Add: tooltips (mouseover) site-wide.** Low priority within v2.5 itself, but
  now has a version attached rather than "end of main dev/design phase" with no
  target.
- **Scope: installer — Windows, Mac, and Linux.** Expanded scope, 2026-06-29 —
  previously Windows-only and unprioritized (`SPEC.md` §20.14: "setup is manual,
  `config.json` + `start.bat`"). Cross-platform installer is a meaningfully bigger
  scoping question than a Windows-only one (the app's current setup assumes
  Windows-specific paths/the pystray tray launcher) — flag this scope session as
  likely needing its own dedicated time, not a quick pass.

---

## Deferred to a future version (not started, no committed timeline, no version assigned)

- **Drop the old raw CSV credit columns on `Issue`.** Tier 4 Item 3 (Writer/Artist
  dedup, shipped 2026-06-21) kept `writer`/`penciller`/`inker`/`colorist`/`letterer`/
  `cover_artist` as an inert rollback safety net rather than dropping them
  immediately. Drop them in a dedicated later session once the `people`/
  `issue_credits` system has run for real with no issues found over a release cycle.

---

## Resolved (kept for context, not actionable)

- **Port 8000 / Windows port-exclusion conflict.** A user-configurable server port
  (`ADMIN_SPEC.md` §7.3) was added 2026-06-27 as a workaround — Tez confirmed this
  resolves it in practice. **Resolved at the source 2026-06-29 (v2.4 Item 2):**
  the default itself moved from 8000 to 9424, so a fresh install no longer needs
  to discover the workaround after already hitting the conflict. Original defect:
  `archive/bugs-fixed-archive.md` BUG-004.
- **BUG-003 — dead duplicate route.** Fixed 2026-06-27. See
  `archive/bugs-fixed-archive.md`.
