# ComicVault — Roadmap

Paused, deferred, or future work — explicitly out of scope until unblocked or
prioritized. If a request seems to fall under something listed here, flag it rather
than building it; `comicvault-changes-2.1.md` and `comicvault-changes-v2.2.md` (both
closed 2026-06-22) covered the prior active queues — there is no active backlog doc
until Tez creates the next one.

---

## Active build queue

Both `comicvault-changes-2.1.md` and `comicvault-changes-v2.2.md` are fully closed
(2026-06-22). No big item or ride-along queue is currently active — check with Tez
for what's next.

- **Tier 5 (manual, non-dev, still open):** Genre additions (Anthology, Comic,
  Omnibus) via the new admin editor, logo + `.ico`, a personal note to check a
  draw.io visual-mapping skill video.

---

## Follow-up needed (2026-06-23 session)

- **Folder View folder cards — image options.** Found during Tez's full manual test
  pass of v2.2 (2026-06-22), missed during original scoping: folder cards in Folder
  View (`CUSTOM_TABS_SPEC.md` §9.2) currently show a generic folder icon + name +
  recursive issue count, with no cover/representative image. Needs a design
  discussion on options for showing an image from the archives inside that folder
  (e.g. first/representative issue's cover, similar to how the removed 2000 AD
  year-grid showed a first-prog thumbnail per year — see `SPEC.md` §20.9, superseded)
  before deciding backend/frontend changes. Not yet scoped — discuss before building.

---

## Paused indefinitely

- **Mobile Reader changes.** The Flutter reader works as-is (tablet connects, reading
  works). Deferred until all server/web work above is done, and may be skipped
  entirely in favour of a third-party reader app instead.

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

From `SPEC.md` §20.14, corrected 2026-06-20 (two items in the original list — custom
tabs and home strips — have since shipped; removed from here, see `CHANGELOG.md`):

- Multiple scan locations across drives, with per-folder exclude — would allow a clean
  split for folder-scoped custom tabs (e.g. Folder View, shipped v2.2) instead of the
  current path-based fallback.
- Series-level overview field — needs a new XML tag + DB column + editor fields;
  per-issue descriptions cover the need for now.
- Advanced Search page — only worth building if the current inline filter+search
  proves insufficient in real use.
- Login/password protection for `/admin` — no gate currently exists anywhere in the
  app; noted in both `SPEC.md` §20.2 and `EDITOR_SPEC.md` §9 as deferred together.
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
