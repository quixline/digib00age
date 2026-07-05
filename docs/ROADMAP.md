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

## Mobile app connectivity fix — closed 2026-07-04 (moved out of "Paused indefinitely" same day)

**The "Flutter reader works as-is" assumption above was wrong** — Tez reported
2026-07-04 that the Flutter app currently failed to connect to the server,
crashed selecting a large CBZ, and still had a broken 2000 AD tab left over
from v2.2. Not new regressions as far as anyone can tell — the app had been
in this state a while, just not caught earlier because all recent attention
was on server/web dev. **All three are now fixed and closed** — `BUGS.md`
BUG-019 (connection failure), BUG-020 (CBZ-select crash), and BUG-008 (2000 AD
tab) — see `archive/bugs-fixed-archive.md` for full detail on each.

This is no longer "paused" — third-party reader connectivity (CDisplayEx/OPDS)
was scoped and ruled out this same session (`DECISIONS.md`), which makes the
Flutter app the only path to reader connectivity going forward, not an
optional one.

**BUG-019, verified on Tez's real Lenovo tablet** — two stacked causes:
`checkConnection()` was hitting an admin-only route that 403s over LAN by
design (fixed with a new unauthenticated `GET /api/ping`), and separately the
tablet's saved server URL had a stale port (8000 instead of 9424), fixed
through the app's own Settings screen.

**BUG-020, verified on the same tablet against a release build** — two
independent causes (an OOM crash on any local CBZ over ~250MB, and a silent
MIME-type mismatch that made some `.cbz` files unselectable — Tez's own "file
association" hunch, confirmed correct). Replaced `file_selector` with a
native streaming picker, then fixed two follow-on memory issues that only
surfaced once the picker itself stopped crashing (redundant full-archive
re-decoding per page, and eager whole-issue page loading). Fix holds in a
release build; a debug build of the same code still struggles with very
large files on this particular 3.7GB-RAM tablet — see the archive entry's
debug-vs-release caveat before assuming a regression in a future debug-mode
test.

**BUG-008, verified on the same tablet** — Tez's explicit call: remove the
broken 2000 AD tab entirely rather than build a Custom Tabs equivalent for
Flutter (not worth building just to replace one tab). Deleted
`two_thousand_ad_screen.dart`, dropped the tab from `library_screen.dart` (4
tabs → 3), removed the dead API calls. 2000 AD issues themselves are
unaffected — still fully browsable via Series/Singles/All like any other
publisher's comics.

**Two previously-noted future-scope items remain parked for whenever they
come up, not committed to:** (1) Reader → Server progress sync (local reading
progress synced back to the ComicVault DB — the local/offline mode has no
progress persistence at all right now, per `SPEC.md`); (2) a "Browse local
files" icon next to search so a user can open a local file without
disconnecting from server view. A Custom-Tabs-equivalent for Flutter is
*not* one of these — BUG-008's fix deliberately chose removal over building
one, so it isn't a parked item unless a real need for it comes up separately.

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
app connectivity fix above (`## Mobile app connectivity fix`) replaced it as
`meta/roadmap.html`'s Now #1, since fixed and closed 2026-07-04; `meta/
roadmap.html` regenerated 2026-07-05 to drop OPDS and reflect the fix.
**v2.5's remaining scope is now just Item 2 below** — the other holding-list
items (user guide, tooltips, installer) were bumped to v2.6 on 2026-07-05, since
UI redesign work (web + mobile) is happening in that version anyway and these
fit better alongside it than as v2.5 stragglers. Queue order confirmed with
Tez 2026-07-05:

1. **Running custom scripts on the Processing Folder — scoped, built, and
   closed 2026-07-05.** Turned out simpler than the "likely worth scoping
   together [with Processing Folder Automation]" framing below suggested —
   once actually scoped it was a single, self-contained tool, not something
   needing Item 15's design revisited. Landed as **Sort by Filename**
   (`ADMIN_SPEC.md` §11.5), ported from the standalone
   `create-folders-from-file.py` script: moves each CBZ/CBR file directly
   inside a chosen folder into its own same-named subfolder. Cowork produced
   the build brief, handed to Code, built and manually verified same day —
   full detail in `docs/v2.5/comicvault-changes-v2.5.md` Item 2 (✅) and
   `docs/v2.5/progress.md`. A collision-rule gap (unrelated existing folder
   content not being caught) was found via scratch testing and fixed before
   the live pass — see `DECISIONS.md`. **This closes v2.5's own scope
   entirely** — the version's only remaining item was this one, everything
   else already moved to v2.6 above. `meta/roadmap.html` regenerated
   2026-07-05 to reflect this (Now #1 card removed).
   Original framing, kept for context: *originally listed alongside
   Processing Folder Automation as "likely worth scoping together" — stayed
   on its own per Tez's explicit call, 2026-06-30, even though Processing
   Folder Automation itself moved forward into v2.4 Item 15.*
2. **Mobile → Server Sync — scoped, built, and closed 2026-07-05.** Sharpened
   from the previously-generic "continue Flutter dev" Now-lane entry — this
   was the specific parked item from the BUG-008 session (`## v2.5 — holding
   list` history above): local/offline reading progress on the Flutter app
   had no persistence back to the ComicVault DB at all (`SPEC.md`). (BUG-017
   — Android had no `.cbz` file association — was a related but separate
   item; fixed and verified on-device 2026-07-05, see
   `archive/bugs-fixed-archive.md`.)

   Full scope doc: `mobile-server-sync-scope.md` (Cowork discovery session,
   2026-07-05). Scoping surfaced a gap the discovery doc hadn't accounted
   for — the Flutter app had no way to download a comic for offline reading
   at all, so there was nothing concrete to sync for the doc's actual
   scenario. Confirmed with Tez to build a proper download-for-offline
   feature as part of this item rather than a heuristic or a deferral.
   Conflict rule locked in as last-write-wins by timestamp (over
   highest-page-wins), matching the scope doc's recommended default. Built
   same session: `GET /api/issue/{id}/download`, `POST /api/sync/progress`
   (last-write-wins, no schema change needed), and the Flutter-side download
   feature + sync engine + trigger wiring + status indicators. **Tez's manual
   test on the real tablet passed** — full detail, including a timezone-skew
   bug caught during review before it reached a device, in
   `docs/v2.5/comicvault-changes-v2.5.md` Item 3 and `docs/v2.5/progress.md`.
   One planned verification step (visually confirming the `server_kept`
   conflict outcome via a second reader) couldn't be run — no working reader
   exists outside the Flutter app right now, tracked separately as `BUGS.md`
   BUG-021, not a defect in this item. `meta/roadmap.html`'s Now #1 card
   removed 2026-07-05 (item complete).
3. **Scope: Web UI Redesign** (v2.6). Replaces the old single "v2.6 UI
   Redesign" placeholder — split 2026-07-05 into web and mobile as two
   separate scoping/design efforts, each needing its own discussion (possibly
   with Claude Design). Covers the header-unification/back-button work noted
   under BUG-014 above, the deferred Admin Custom Tabs field removal, and any
   other web-surface items already parked pending "UI redesign."
4. **Scope: Mobile UI Redesign** (v2.6). The Flutter-side counterpart to #3,
   split out as its own item rather than assumed identical scope/timeline to
   the web redesign.
5. **Add: user guide** (v2.6, moved from v2.5 2026-07-05). Not yet scoped at
   all. `ADMIN_SPEC.md` §7.1.7's Password Recovery popup (v2.3 Item 10) already
   explicitly said the guide, once built, should link to that popup rather than
   duplicating its instructions — worth checking for any other place a spec
   already assumes a guide exists before scoping this from scratch.
6. **Add: tooltips (mouseover) site-wide** (v2.6, moved from v2.5 2026-07-05).
   Low priority, fits naturally alongside the UI redesign work.
7. **Scope: installer — Windows, Mac, and Linux** (v2.6, moved from v2.5
   2026-07-05). Expanded scope, 2026-06-29 — previously Windows-only and
   unprioritized (`SPEC.md` §20.14: "setup is manual, `config.json` +
   `start.bat`"). Cross-platform installer is a meaningfully bigger scoping
   question than a Windows-only one (the app's current setup assumes
   Windows-specific paths/the pystray tray launcher) — flag this scope session
   as likely needing its own dedicated time, not a quick pass.

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
