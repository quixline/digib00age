# ComicVault — Progress Log (v2.4)

Narrative build history for v2.4 — per-session detail, what was actually built,
verification notes. Append-only, written by Claude Code at the close of each
session. Full project history through v2.3's close lives in
`archive/v2.3/progress.md` — not duplicated here.

---

## Session — 2026-06-29: v2.4 Item 1 — restrict all admin access for remote users when Remote Administration is off

**Goal.** Close the gap flagged going in: today's gating only blocked remote
requests from the handful of endpoints explicitly decorated with
`is_local_request()` (Clear Database, Restore Database, the folder/file
dialogs, `/admin/restart`). Every other `/api/admin/*` and `/api/editor/*`
endpoint — stats, logs, cleanup-missing, backup, the folder-tree browse, the
scan trigger — was reachable from any LAN device whenever password protection
was off, which is the **default** state. So in practice most installs were
wide open remotely despite "Remote Administration" reading as off.

**What was found.** `require_admin_auth()` (`backend/auth.py`) no-op'd
entirely — including its remote-block check — whenever
`is_protection_enabled()` was false. The remote check only ever ran in the one
case (protection on, remote admin off) that already worked correctly. The
`/admin` and `/editor` page routes (`backend/main.py`) had no gating of any
kind — always served the HTML shell to anyone, local or remote.

**What changed.**
- `backend/auth.py` `require_admin_auth()` — moved the
  `is_local_request()` / `is_remote_admin_enabled()` check ahead of the
  protection-enabled early return, so it now applies unconditionally. This
  alone fixes every route already wired through the `_auth_gate` dependency
  in `main.py` (all of `admin.router`, `editor_basic.router`,
  `editor_full.router`) — not just the destructive actions.
- `backend/main.py` — `GET /admin` and `GET /editor` now run the same
  local-or-remote-admin-enabled check before serving the page, so a blocked
  remote request gets a 403 instead of a functional-looking HTML shell.
- `frontend/js/auth.js` `checkAuthStatus()` + `frontend/css/style.css` — the
  cog icon **stays in place** for a non-local session when Remote
  Administration is off (no layout shift to the Login/Logout button next to
  it), but gets a `.settings-btn--disabled` class: dimmed and
  `pointer-events: none`, so it's visibly inert rather than removed. First
  pass hid the icon outright with `hidden`, which both shifted the Login
  button left and didn't match the intended behaviour — corrected same
  session before doc close, per the manual-test-first rule this session
  added to `CLAUDE.md`/`working-rules.md`.

Local sessions (the owner, at `127.0.0.1`) are unaffected in every state —
this only closes the remote-access gap, V1 local behaviour is unchanged.

**Verified.** Unit-level check (`unittest.mock.patch` on
`is_protection_enabled` / `is_remote_admin_enabled`, scratch script, not
committed) against `require_admin_auth()` directly, covering all four
relevant (protection, remote_admin, local) combinations. **Manual test by
Tez: passed** (2026-06-29) — confirmed after the cog-icon correction above.
No real `config.json` or library data touched.

**Docs.** `ADMIN_SPEC.md` §7.2 updated to describe the broadened gate.
`meta/roadmap.html`'s Now lane updated — Item 1's card removed, remaining 13
cards renumbered 1–13 (those are display-order badges, not the `comicvault-
changes-v2.4.md` Item numbers, which never renumber — see
`meta/working-rules.md` "Version-qualified references").

---

## Session — 2026-06-29: v2.4 Item 2 — default server port → 9424

**Goal.** Resolve the recurring Windows port-exclusion conflict (`BUGS.md`
BUG-004) at the source by changing the default `reader_port` from `8000` to
`9424`, rather than relying on the existing user-configurable port field
(`ADMIN_SPEC.md` §7.3) only being discovered after a fresh install already
hits the conflict.

**What changed.**
- Default fallback (used when `reader_port` is missing from `config.json`):
  `backend/main.py`, `backend/config.py`, `backend/routers/admin.py`
  (`/admin/config` GET fallback) — `8000` → `9424`.
- `config.example.json` — template default for new installs.
- `config.json` (the real, live config) — updated directly to `9424`, since
  it had `reader_port` set explicitly and an explicit value shadows the code
  default; nothing would have changed on restart otherwise.
- Stale port mentions in comments/docs-adjacent text: `start_server.py`,
  `README.md`.
- Flutter app placeholder/default server URL (`api_service.dart`,
  `settings_service.dart`, `settings_screen.dart`) — example text only, no
  functional change, updated for consistency.
- **Not touched (scoping miss, caught during testing):** `tray/tray_app.py`'s
  "Open Library"/"Admin" menu links read `READER_PORT` from `config.json` at
  the tray app's own launch — they update automatically once the tray app is
  restarted, no code change needed there. Flagged here so it's not mistaken
  for an oversight next time this comes up.

**Verified — manual test by Tez: passed (2026-06-29).** Library reachable at
`http://localhost:9424` after restart.

**Found during testing, not a regression from this change:** stopping the
server from the tray menu did not actually terminate the old process — it kept
listening on 8000 with `config.json` still showing the new 9424 in memory-cache
for the *new* process the tray then started, leaving two live server instances
against the same `comicvault.db` simultaneously (confirmed via `netstat`/
`Get-Process`: PID 10520 on 8000, started before the edit; PID 15232 on 9424,
started after). Resolved by fully quitting and relaunching the tray app rather
than using its "stop" action alone. Documented as a standing caution in
`ADMIN_SPEC.md` §7.3 so it's not rediscovered the same way next port/config
change.

**Docs.** `ADMIN_SPEC.md` §7.3 updated (default value + the tray-app-restart
caution). `ROADMAP.md`'s "Resolved (kept for context)" port-8000 note tightened
to reflect the new default. `meta/roadmap.html`'s Now lane updated — Item 2's
card removed, remaining 12 cards renumbered 1–12.

---

## Session — 2026-06-29: v2.4 Item 3 — empty-results icon → logo image

**Goal.** Replace `<div class="empty-icon">📚</div>` on the no-matching-results
state ("No comics match these filters.") with the logo image at
`images/logo1.png`, per the item as scoped.

**What changed.**
- `images/logo1.png` was confirmed present but not web-reachable — the
  project-root `images/` folder isn't under any static mount (only `/static`
  → `frontend/` exists). Copied the file to `frontend/images/logo1.png`
  (the root copy is untouched) so it's served at `/static/images/logo1.png`
  through the existing mount, rather than adding a new one for a single file.
- `frontend/js/app.js` line ~906 — swapped the `📚` `empty-icon` div for
  `<img class="empty-logo" src="/static/images/logo1.png" alt="">` on the
  "No comics match these filters." state, as scoped.
- `frontend/css/style.css` — added `.empty-logo` alongside the existing
  `.empty-icon` (emoji) class rather than overloading one class for both.
  Went through two corrections from manual testing before settling:
  first pass used fixed `width`/`height` (56×56), which squashed the logo's
  non-square aspect ratio into a box; fixed by switching to
  `height: 56px; width: auto`. Centering also needed `display: block;
  margin: 0 auto` rather than relying on the parent's `text-align: center`,
  since an `<img>` doesn't center the same way inline text does.
- **Expanded beyond the item's original scope, at Tez's explicit call after
  seeing it work:** the same `.empty-icon` emoji pattern (`⚠️` and one more
  `📚`) appeared in 10 other empty/error states across `app.js` — home strips
  init failure, "No content yet.", server-unreachable, tab/view no-longer-
  available, folder-load failure, search failure, series-not-found,
  issue-not-found. All 10 were switched to the same `<img class="empty-logo">`
  markup for visual consistency, since the fix (file location, sizing,
  centering) was already proven working on the first one. See
  `DECISIONS.md` for the rationale entry — this is a judgment call (logo
  standing in for warning/error icons too, not just "no content") worth a
  paper trail since it wasn't in the original item text.

**Verified — manual test by Tez: passed (2026-06-29).** Confirmed across the
filtered-empty state and re-checked after both CSS corrections.

**Docs.** `DECISIONS.md` — new entry for the scope expansion. `meta/
roadmap.html`'s Now lane updated — Item 3's card removed, remaining 11 cards
renumbered 1–11.

---
