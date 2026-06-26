# ComicVault — Roadmap

Paused, deferred, or future work — explicitly out of scope until unblocked or
prioritized. If a request seems to fall under something listed here, flag it rather
than building it; `comicvault-changes-2.1.md` and `comicvault-changes-v2.2.md` (both
closed 2026-06-22) covered the prior active queues — current active queue is
`comicvault-changes-v2.3.md`.

---

## Active build queue

`comicvault-changes-v2.3.md` is the current active queue (Status: Active). All 9 items
built — Items 1–5 on 2026-06-23, Items 6–9 on 2026-06-24. Manual test pass remaining
(see the checklist at the bottom of `comicvault-changes-v2.3.md`).

- **Tier 5 (manual, non-dev, still open):** Genre additions (Anthology, Comic,
  Omnibus) via the new admin editor, logo + `.ico`, a personal note to check a
  draw.io visual-mapping skill video.

---

## Follow-up needed (2026-06-23 session)

- **Folder View folder cards — image options. RESOLVED 2026-06-23.** Design
  discussion held; random cached thumbnail approach selected. Full spec in
  `CUSTOM_TABS_SPEC.md` §9.2; build tracked in `comicvault-changes-v2.3.md`.

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

## Deferred — needs dedicated scoping session before building

- **CAPT extra tools** (4–5 tools, code already exists in the original CAPT codebase).
  Needs inspection and integration scoping in a dedicated session before anything is
  added to a build queue.

- **Processing Folder automation** (new Admin area — `ADMIN_SPEC.md` is the future
  home once scoped): scheduled folder monitor; convert-to-cbz via 7zip, custom rename
  pattern, image-to-WebP conversion, flatten archive folders — all four reusing
  existing CAPT tooling. Needs its own dedicated scoping session (trigger conditions,
  conflict handling, action ordering) before going into `ADMIN_SPEC.md`.

- **ComicTagger + ComicVine API integration.** Large project. Tez has flagged this
  explicitly as needing its own planning session before scoping begins.

- **Third-party reader compatibility** — merge the OPDS idea and the existing
  partial-Komga-API-compatibility idea into one research note; both solve the same
  underlying goal (external reader apps connecting to ComicVault) and should be
  evaluated together rather than as two separate efforts. Research-only until the
  web-side work is further along.

---

## Deferred to a future version (not started, no committed timeline)

- **Favorites browse surface/tab.** Tier 4 Item 2 (Multi-select + Favorites/Rating,
  shipped 2026-06-21) added the `favorites` field, a card/row badge, and an issue-
  detail toggle, but no dedicated "Favorites" tab to browse just favorited issues —
  explicitly deferred at build time, not an oversight. See `SPEC.md` §20.15.
- **Drop the old raw CSV credit columns on `Issue`.** Tier 4 Item 3 (Writer/Artist
  dedup, shipped 2026-06-21) kept `writer`/`penciller`/`inker`/`colorist`/`letterer`/
  `cover_artist` as an inert rollback safety net rather than dropping them
  immediately. Drop them in a dedicated later session once the `people`/
  `issue_credits` system has run for real with no issues found over a release cycle.
- **BUG-007 — Basic Editor Summary field line-break doubling.** Found 2026-06-21 as
  a side effect of Item 3's editor-save testing; pre-existing, unrelated to Item 3.
  Not fixed. See `BUGS.md`.

- **Tooltips (mouseover) site-wide.** Low priority. Intended for the end of the main
  dev/design phase once all functional work is settled.

From `SPEC.md` §20.14, corrected 2026-06-20 (two items in the original list — custom
tabs and home strips — have since shipped; removed from here, see `CHANGELOG.md`):

- Multiple scan locations across drives, with per-folder exclude — would allow a clean
  split for folder-scoped custom tabs (e.g. Folder View, shipped v2.2) instead of the
  current path-based fallback.
- Series-level overview field — needs a new XML tag + DB column + editor fields;
  per-issue descriptions cover the need for now.
- Advanced Search page — only worth building if the current inline filter+search
  proves insufficient in real use.
- ~~Login/password protection for `/admin`~~ — **⚠️ FLAG FOR TEZ: this entry is now
  stale.** Full design is written and active — `ADMIN_SPEC.md` §7.1/§7.2; build
  tracked in `comicvault-changes-v2.3.md` Item 6. Should be removed from this
  Deferred list once Tez confirms. Not auto-removed.
- An installer — setup is manual (`config.json` + `start.bat`); not yet prioritized.

---

## Known environmental risk (not a code bug)

- **Port 8000 / Windows port-exclusion conflict (`BUGS.md` BUG-004).** WSL2/Hyper-V's
  networking stack can reserve a TCP port range at boot that happens to include 8000,
  causing uvicorn's bind to fail until `winnat` is restarted. No permanent fix applied
  yet — options noted but not built: move ComicVault off port 8000 to a less commonly
  reserved port, or have `start.bat`/the tray app proactively restart `winnat` before
  launching.

## Known open bug

- **BUG-003 — dead duplicate route** (`GET /api/reading/continue` defined in both
  `progress.py` and `library.py`). No functional impact today; flagged as a
  maintenance hazard, not yet cleaned up. See `BUGS.md` for detail.
