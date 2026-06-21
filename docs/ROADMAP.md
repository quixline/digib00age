# ComicVault — Roadmap

Paused, deferred, or future work — explicitly out of scope until unblocked or
prioritized. If a request seems to fall under something listed here, flag it rather
than building it; check `comicvault-changes.md` for what's actually next in the active
queue.

---

## Active build queue (not paused — see `comicvault-changes.md` for detail)

- **Tier 4 Item 3 — Writer/Artist entity dedup + search/link, frontend remaining.**
  Backend (`people`/`issue_credits` tables, scanner integration) and the real
  migration across the live ~5,429-issue library are done (2026-06-21, see
  `progress.md`). Remaining: remove the Writer/Artist filter dropdowns, build the
  click-through UI on `/issue/{id}`, wire the editor's fuzzy warn-on-save, update
  `matches_field()`/`/browse/writers`/`/browse/artists` to resolve against
  `person_id`. Old raw CSV credit columns on `Issue` stay until this ships and runs
  clean for a release cycle.
- **Tier 1 (ride-along bugs):** back button inconsistency (needs repro steps), list
  view "Read" row unreadable (grey-on-green).
- **Tier 2 (ride-along cosmetic):** clickable genre tags on `/issue/{id}`, "Clear"
  button styling, Format in the Grouping menu, "mark all read" on the 2000 AD page,
  admin pagination/styling tweaks (8 items total — see `comicvault-changes.md`).
- **Tier 3 (ride-along, more design):** home page search bar unification, card size
  control, Home Strips "Auto Saved" confirmation message.
- **Tier 5 (manual, non-dev):** Genre additions (Anthology, Comic, Omnibus) via the
  new admin editor, logo + `.ico`, a personal note to check a draw.io visual-mapping
  skill video.

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

From `SPEC.md` §20.14, corrected 2026-06-20 (two items in the original list — custom
tabs and home strips — have since shipped; removed from here, see `CHANGELOG.md`):

- Multiple scan locations across drives, with per-folder exclude — would allow a clean
  split for the 2000 AD library section instead of the current path-based fallback.
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
