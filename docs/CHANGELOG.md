# ComicVault — Changelog

Terse, one-line-per-entry index, newest first. Each line is a pointer into
`progress.md`'s matching section heading — read there for the full narrative,
what was verified, and any gotchas. Bug fixes already logged in `BUGS.md` aren't
repeated here unless they also got their own `progress.md` session entry.

---

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
