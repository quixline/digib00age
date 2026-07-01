# ComicVault — Roadmap

Paused, deferred, or future work — explicitly out of scope until unblocked or
prioritized. If a request seems to fall under something listed here, flag it rather
than building it; `archive/comicvault-changes-2.1.md` and
`archive/comicvault-changes-v2.2.md` (both closed 2026-06-22) and
`archive/v2.3/comicvault-changes-v2.3.md` (closed 2026-06-29) covered the prior
active queues — current active queue is `v2.4/comicvault-changes-v2.4.md`.

---

## Active build queue

`v2.4/comicvault-changes-v2.4.md` is the current active queue (Status: Active —
scoping phase extended, builds on hold for the CAPT-tooling cluster). 15 items —
revised 2026-06-30 to pull "Processing Folder Automation" forward from the v2.5
holding list as Item 15 (see that doc's header note for the full reasoning).
**Items 1–3 built and manually verified 2026-06-29:**

- Item 1: restrict all admin access for remote users when Remote Administration
  is off — cog stays visible but inert (dimmed, pointer-events: none) for non-local
  sessions; every `/api/admin/*` and `/api/editor/*` endpoint and the `/admin`/
  `/editor` pages now block remote requests unconditionally when the toggle is off,
  not just the handful previously decorated with `is_local_request()`.
- Item 2: default server port changed from 8000 to 9424, resolving the Windows
  port-exclusion conflict at the source. (See "Resolved" section below.)
- Item 3: empty-results `📚` emoji replaced with the ComicVault logo image,
  extended at Tez's call to all 11 empty/error states in `app.js`.

**Scoping phase for the CAPT-tooling cluster is now complete** — Items 4–8
(Favourites, CBR support, Convert Files, Convert Images, Flatten Archive) and
Item 15 (Processing Folder Automation) are all scoped as of 2026-07-01; Item 8
scoped to a drop (superseded by BUG-018), Item 14 (its build counterpart)
dropped with it. Item 15's scoping surfaced a cross-cutting backup-model gap
between §12.2 and §12.3, which was written into the spec 2026-07-01 (pre-build
doc sanity check) — no longer outstanding. The "dedicated cross-review pass
across the whole cluster's specs" originally planned as a separate Chat session
is instead folded into Code's own review-and-Plan-mode pass at the start of the
build session (Tez's call, 2026-07-01) — not skipped, just relocated.

**Remaining to build:** Item 9 (Favourites — no dependency on the cluster,
build-ready), Item 10 (File Rename Tool — build-ready, manual-only), Item 11
(CBR support), Item 12 (Convert Files/Archives), Item 13 (Convert Images), and
Item 16 (Processing Folder Automation — depends on Items 11–13 being built
first, since it orchestrates Convert Archives + Convert Images). Items 8 and 14
are dropped.

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

---

## Paused indefinitely

- **Mobile Reader changes.** The Flutter reader works as-is (tablet connects, reading
  works). Deferred until all server/web work above is done, and may be skipped
  entirely in favour of a third-party reader app instead. Two specific future-scope
  items noted for whenever this is revisited: (1) Reader → Server progress sync
  (local reading progress synced back to the ComicVault DB); (2) a "Browse local
  files" icon next to search so a user can open a local file without disconnecting
  from server view.

- **Reader-launch feature** (`ADMIN_SPEC.md` §7.6 — Reader Location field in
  Advanced Settings + `/issue/{id}` "Read" button wiring). Scoping revealed this
  requires Flutter app changes — the Windows reader EXE doesn't currently accept a
  launch-into-file argument, so the "Read" button can't directly open a specific
  issue in the reader without Flutter work. Also has a same-machine-only limitation
  (browser and server on different machines on the LAN won't work as expected). Parked
  pending further thought on practical usage vs. building out all the edge cases —
  may be dropped rather than built.

---

## v2.5 — scoped for the version after next (not started)

Six items remaining, agreed 2026-06-29 (originally seven — "Processing Folder
automation" moved to `v2.4/comicvault-changes-v2.4.md` Item 15 on 2026-06-30, see
that doc's header note for why). None scoped yet — this is a holding list, not a
build queue; per the version lifecycle in `meta/working-rules.md`, real scoping
won't start until v2.4 closes and a `docs/v2.5/` working folder is created.

- **Scope: ComicTagger + ComicVine API integration.** Large project. Tez has
  flagged this explicitly as needing its own planning session before scoping
  begins.
- **Scope: OPDS — connecting 3rd-party readers.** Merge with the existing
  partial-Komga-API-compatibility idea into one research note; both solve the
  same underlying goal (external reader apps connecting to ComicVault) and should
  be evaluated together rather than as two separate efforts.
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
