# ComicVault — ADMIN_SPEC.md

> **How to use this document**
> Paste this file into a Claude Code session alongside `SPEC.md` and `EDITOR_SPEC.md`
> for context on the wider system. This is the single source of truth for the Admin
> page. Record any deviations at the bottom (Change Log), same convention as other
> spec files.
>
> **Status:** All original v2.3 items (1–9) built as of 2026-06-24 and verified via
> manual test pass 2026-06-26 (9 fixes implemented same day — see §12 Change Log).
> §1–§6 (core layout, stats, scan, library folders, pagination) were live from V1.
> All Advanced Settings additions (§7: password protection, remote admin toggle,
> scheduled backup, server port, clear database, clear reading progress),
> Logs/Auto Scan (§8), and Donate (§10) are built and verified — see per-section
> notes for details.
>
> §6 backfilled 2026-06-27 with the Card Size control — built in v2.1 (2026-06-22)
> but never written into this doc when it was created the following day.
>
> Items 10–13 built and code-verified 2026-06-27 (Password Recovery button §7.1.7,
> Scheduled Backup frequency reduction §9, Restore Database §9.2, Card Size +75%
> option §6). Manually tested 2026-06-28: Items 10, 11, 13 passed; Item 12 (Restore
> Database) did not pass — restore completed but DB was not reverted to the backup
> state (BUG-016). **Fixed 2026-07-18** — WAL-checkpoint bug, see §9.2 and
> `archive/bugs-fixed-archive.md`. Item 14 (site-wide header unification) moved to
> `ROADMAP.md` 2026-06-28 — not admin-page scope, blocked on Claude Design
> exploration.
>
> **§11 Processing Tools, folded 2026-07-01** — the standalone
> `admin-spec-section-12-processing-tools.md` scoping file is retired; its
> content lives here as §11.1–§11.4 (renumbered from its own §12.1–§12.4).
> §11.1 File Rename is **built and manually tested (v2.4 Item 10, 2026-07-01; queue
> workflow corrected 2026-07-02)**. §11.2 Convert Archives, §11.3 Convert
> Images, and §11.4 Processing Folder Automation are also **built and
> manually tested (v2.4 Items 12, 13, 16, all 2026-07-01)** — v2.4 closed
> 2026-07-02 with the whole CAPT-tooling cluster verified (`ROADMAP.md`).
> §11.4's third pipeline stage (CT Auto-Tag), its two new toggles, the
> ComicVine API key field, and the Match Ratio Threshold slider (added
> 2026-07-04) are **built and fully tested 2026-07-03/04** (v2.5 Item 1,
> closed) — see `docs/v2.5/progress.md` for the full build narrative,
> including post-build fixes found during Tez's live testing (identify()
> falling back to filename parsing + assuming issue 1 for one-shots, match
> thresholds now user-configurable (80% default), a missing-credits bug in
> the tagging write path, and a misleading-results-summary bug caught
> during a real 5-file low-confidence test pass). A minor open question
> (why Tez's standalone ComicTagger install underperformed ComicVault's own
> matching on that same 5-file test) was investigated but not conclusively
> resolved — not treated as a ComicVault defect, see `v2.5/progress.md`.
>
> **Note on authority:** `SPEC.md` §11 and §20.13 contain earlier admin descriptions.
> Where they conflict with this file, **this file is authoritative** — it consolidates
> and supersedes those entries for admin-page specifics.
>
> **v2.6 Item 1 Phase C1 (2026-07-07):** the Admin page's navigation changed from
> one long scrolling page to a category → sub-item → content-pane structure
> (`docs/v2.6/comicvault-changes-v2.6.md`). §3–4 (Library Stats, Scan Now + scan
> stat cards) stay always-visible at the top; §4's Auto Scan Options, §5, §6, §8,
> and §9 are now reached via **Library Management** / **Library Appearance** in
> the new Settings nav rather than by scrolling. Every field, ID, and behaviour
> described below is unchanged — only how you navigate to it changed. §11
> (Processing Tools) and the rest of §7 (Advanced Settings) are not yet migrated
> — still reached by scrolling, per the old layout — planned for Phase C2.
>
> **v2.6 Item 1 Phase C2a (2026-07-07):** extended the same nav to two more
> categories — **Editor Options** (Genre List, Format List — unlocked, same as
> Phase C1's Home Strips/Libraries) and **Advanced Settings** (Password
> Protection, Change Server Port + Reader Location folded together, Wipe
> Database, Wipe Reading State — all still behind the existing "Unlock advanced
> settings" gate). Every field/ID unchanged, only navigation and the Danger
> Zone→two-separate-sub-items split changed — see §7's intro note above for
> detail.
>
> **v2.6 Item 1 Phase C2b (2026-07-07):** the last category — **Processing
> Tools** (Filename Editor, Converter: Archives & Images, **XML Tagging** [new
> standalone tool, §11.6], Folder Processing, Auto Processing) — is now nav-
> driven too, closing out the Admin IA restructure. Every pre-existing field/ID
> unchanged; the only real behaviour change is CT Auto-Tag's detailed settings
> relocating from Auto Processing's pane to XML Tagging's (shared config, see
> §11.4.4/§11.6.1). The Admin page is fully migrated off the old
> one-long-scrolling-page layout as of this phase.

---

## 1. Access & Design

**URL:** `/admin`

**Access gate:** Password popup, off by default, covering `/admin`, `/editor`, and
their full API namespaces regardless of entry point — see §7.1 for the complete
design. Until a password is set, current V1 ungated behaviour is preserved.

**Design language:** Dark theme, same fonts and card style as the main UI. Admin
page cards are ~25% larger than cards elsewhere in the UI. The purple accent is
reserved for primary actions (e.g. Scan Now); secondary actions (Back, Clear, Remove)
use muted grey — consistent with the Full Editor's styling (`EDITOR_SPEC.md` §5.2).

**Header:** Same fixed top navigation header as all other pages, including the gear
icon.

**Admin cog-link in Full Editor *(built — V2.3 Item 6, 2026-06-24):*** A small
cog/admin icon link in the Full Editor header gives direct navigation to `/admin`,
so a user moving from the editor to trigger a scan doesn't have to navigate away
first. Small convenience, no auth impact. (Built as a bonus alongside the Logout
control while that file was already being touched for the password-protection
session — not a separate Item 9 task.)

---

## 2. Top Action Row

Four buttons spread across the full row width (not grouped):

| Button | Action |
|---|---|
| **Back** | Returns to the main library |
| **User Guide** | Opens a stub page in a new tab (placeholder; full guide is a future addition) |
| **Backup Database** | Triggers `POST /api/admin/backup` — exports a dated copy of `comicvault.db` to the configured backup location. **Superseded by §7 (Scheduled Database Backup)** for the scheduling side; this button remains for on-demand manual backup. |
| **Password Reset** | Placeholder button in V1 (no function). Becomes a real control once password protection (§7.1) ships. |


---

## 3. Stats Section

Individual stat cards, one value per card. **Built (V1).**

| Card | Value |
|---|---|
| Total Files | Grand total of all issues in DB |
| Series | Series count |
| Singles | Singles count |
| Total Read | `read_count / total` — e.g. "1,203 / 5,448 — 22%" |
| In Progress | Issues with status = "reading" |

---

## 4. Scan Section

**Built (V1).**

Stat cards plus one action card:

- **Last Scan:** date of the most recent scan completion (**date only as of
  2026-07-09** — was a full date+time string; the persisted-fallback path also
  used to show `Duration: HH:MM:SS` since it reads straight from the log line —
  Tez's tweak-pass call to keep the summary card simple; full time + duration
  detail is still in the log itself, one "Logs" click away). Persists across
  server restarts (fixed — V2.3 post-test fixes, Fix 7, 2026-06-26): the in-memory
  `ScanProgress.finished_at` resets to `None` on every restart, so the card now falls
  back to the last line of `last_scan_log.md` (via `read_last_scan_timestamp()` in
  `backend/scan_logs.py`) when no live `finished_at` is available, before finally
  falling back to "Never".
- **Files Found:** total files found in last scan.
- **New Files:** new files found in last scan.
- **Scan Now** (action card): triggers `POST /api/scan`; card expands inline to show
  a live progress bar and log output during the scan.
- **Errors (BUGS.md BUG-028, fixed 2026-07-18):** a failed thumbnail-generation
  attempt (e.g. an archive whose leading entries are all unreadable) now counts
  toward `scan_progress.errors` and logs a `THUMBNAIL ERROR: <filename>` line,
  instead of passing silently with `errors=0`. `GET /api/scan/status` returns it
  as `error_files`; the completion text appends `, N errors` when non-zero. Does
  **not** change the file's own `"new"`/`"updated"` result — the row itself still
  scanned correctly, only its derived cover failed.

**Scan log cards (built — V2.3 Item 7, 2026-06-24):** the four scan stat cards above
additionally show per-category log details. See §8 for the log file format,
green-border "new entries" indicator, and per-card Logs button.

### Auto Scan Options (built — V2.3 Item 7, 2026-06-24)

Under the scan cards, a small options area:

- **Scan frequency dropdown:** Every 1 hour / 6 hours / 12 hours / 1 day / 3 days /
  7 days / 1 week / 1 month. Off (default / manual only).
- **Scan on launch:** checkbox — trigger a scan automatically each time the server
  starts (in addition to any scheduled frequency above).

These settings are saved to `config.json` and read by the scanner/tray app.

---

## 5. Library Folders Section

**Built (V1).**

- Lists all configured scan root paths (default: one path from `config.json`).
- Multiple roots supported, each shown as its own row entry.
- **Add folder** — browse/select a folder to add as a scan root. (Currently broken
  — see `BUGS.md` BUG-011: the Add button doesn't open a file dialog.)
- **Remove folder** — remove a root from the scan list.
- **Exclude folders** — per-root exclude list; paths entered here are skipped by the
  scanner (backed by `SCAN_EXCLUDE` in `config.json`).

---

## 6. Pagination Setting

**Built (V1).**

Global page-size selector: **50 / 100 / 200 / 500**, default 50. Set-and-forget —
persists via `localStorage`. Applies to all browse surfaces (Series, Singles, All,
search results). Home page strips are exempt (fixed at 15 covers per strip).

Per `SPEC.md` §20.13: the pagination control lives on the Admin page, not the browse
toolbar; Admin can be opened in its own tab for a quick change.

### Card Size *(built — v2.1 Tier 3, 2026-06-22; missing from this doc until backfilled 2026-06-27)*

A second control in the same Admin area, directly below "Results per page" (same
`.admin-card--spaced` styling). Dropdown: **10% / 25% / 50% / 75% / 100%**
(75% added — V2.3 Item 13, 2026-06-27), persisted via `localStorage`
(`cv_card_size`), driving a `--card-min` CSS variable consumed by `.cover-grid`'s
`grid-template-columns`. `CARD_SIZE_PX` (`frontend/js/app.js`) maps each preset to
a pixel value — 75% sits at `190px`, the midpoint between 50%'s `160px` and 100%'s
`220px`.

**Scope is global** — every cover-grid site-wide resizes together: Series/Singles/
All/search results, Home strips, and — at the time this was built — the 2000 AD
year-picker grid, since superseded by Folder View (`CUSTOM_TABS_SPEC.md` §9). Folder
View's grids should inherit the same `--card-min` mechanism via the shared
`.cover-grid` class, but this hasn't been re-verified against the current Folder
View markup since the 2000 AD removal — worth a quick confirmation next time Code
touches this area.

Originally lived inline in the browse-controls bar; moved here after Tez's
follow-up testing, to sit alongside the other display-density setting rather than
clutter the browse toolbar.

Fifth option **75%** added between 50% and 100% — see
`comicvault-changes-v2.3.md` Item 13.


---

## 7. Advanced Settings

The existing Advanced Settings section is locked by default — a checkbox must be
ticked to enable editing (all fields greyed out until unlocked). **The items below
are additions to this section unless noted.**

**v2.6 Item 1 Phase C1 change:** Custom Tabs (§CUSTOM_TABS_SPEC.md, now labelled
"Add/Remove Libraries" in the UI) and Home Page Strips (§HOME_STRIPS_SPEC.md) are
**no longer part of this locked fieldset** — they moved to the **Library
Appearance** category in the new Settings nav and are directly editable, no
unlock checkbox required. Decided 2026-07-07 (see `DECISIONS.md`) — they graduated
into their own always-visible category, distinct from Advanced Settings, so a
lock tied to a checkbox that now lives in a different part of the nav would have
been a confusing UX regression.

**v2.6 Item 1 Phase C2a change (2026-07-07):** Genre List and Format List moved
out of this locked fieldset too, for the same reason — they graduated into their
own **Editor Options** category, directly editable, no unlock checkbox required
(see `DECISIONS.md`). Reader Location, Server Port, Password Protection, and
Danger Zone (now reached as two separate sub-items, **Wipe Database** and **Wipe
Reading State** — same fields/IDs, just no longer grouped under one heading) stay
in the **Advanced Settings** category and remain locked exactly as before — they
weren't reclassified, so the existing gate still applies.

### 7.1 Password Protection *(built — V2.3 Item 6, 2026-06-24)*

The Admin page, the Full Editor, the Basic Editor (the quick-edit popup on
`/issue/{id}`), and every API endpoint under `/api/admin/*` and `/api/editor/*` are
gated behind a single shared password, regardless of entry point (direct URL, tray
app menu item, link from another page, or raw API call). There is no carve-out for
the Basic Editor — all editing surfaces sit behind the same gate as Admin.

**Default state:** password protection is **off**. No password exists, no gate is
enforced, current V1 behaviour is unchanged until Tez explicitly turns it on.

#### 7.1.1 Enabling protection

Password protection and password-setting are a **single combined action** — there is
no state where the toggle is on with no password, or a password is saved but the
toggle is off. Turning protection on requires entering a new password at the same
time; turning it off clears the enforcement and the stored password hash/salt.

**Disabling requires re-entering the current password (fixed — V2.3 post-test
fixes, Fix 6, 2026-06-26):** previously an already-authenticated admin could
uncheck the toggle and have it take effect immediately with no credential
re-entry. Unchecking the toggle now shows an inline confirmation row (below the
toggle, not a separate modal — keeps it close to the control being changed):
a password field + Confirm/Cancel. Cancel restores the checkbox to checked with no
network call. Confirm POSTs to `POST /api/admin/auth/disable` with
`{ current_password }`; the backend (`admin_auth.py`) verifies it against the
stored hash before clearing protection and returns `403` on mismatch (the toggle
stays on and the confirmation row stays open with an error). On success, Remote
Administration is force-disabled in the same operation as before. The session
itself is *not* auto-logged-out by this action — the user already proved their
identity via the password just entered.

**This action — and any later password change — can only be performed from a local
session (request originates from `127.0.0.1`).** This holds even if the current
session is authenticated via Remote Administration (§7.2) — a remote, logged-in
session cannot flip the gate off or change the password. This is the actual security
boundary: physical/local access to the machine is required to weaken or remove
protection, no matter what's been authenticated remotely.

Turning password protection **off** also force-disables Remote Administration (§7.2)
in the same action — it cannot be left in an "on" state pointing at a gate that no
longer exists.

#### 7.1.2 Login

Unauthenticated requests to a protected **page** (`/admin`, `/editor`, `/issue/{id}`'s
Basic Editor popup trigger) are shown the password popup described in the §1 framing.
Unauthenticated requests to a protected **API** endpoint return `401` with a JSON
error body — the frontend's existing fetch error-handling should surface the popup in
response, rather than the API layer trying to render HTML.

A single password field; on submit, POST to a login endpoint
(`POST /api/admin/login` suggested). On success, the server sets the session cookie
(§7.1.4) and the original request can proceed/retry.

**Compact modal + Cancel button (added 2026-07-09, Tez's tweak-pass call):** the
popup previously had no way to dismiss it short of entering a password. Added a
"Cancel" button (`#loginCancelBtn`) next to "Log In" that calls `hideLoginPopup()`
— now extended to also clear the password field and any error message, so a later
reopen doesn't show stale state from a prior failed/cancelled attempt. The modal
itself (`.login-modal`, shared with the "no password set" dialog below) is now 60%
narrower than the shared `.editor-modal` width (720px → 288px) with a consistent
10px horizontal inset, scoped so the much larger Editor Basic/Full modals — which
also use `.editor-modal` — are unaffected.

**Auto-popup page gating (fixed — V2.3 post-test fixes, Fix 4, 2026-06-26):**
`auth.js`'s `checkAuthStatus()` only auto-opens the popup on page load when the
current path is one of the protected pages (`/admin`, `/editor`) — previously it
fired on every page, including the unauthenticated library (`/`), the moment
password protection was turned on. The 401-interception path (any authenticated API
call that bounces with 401) is unchanged and still surfaces the popup regardless of
page — that's how the Basic Editor popup on `/issue/{id}` still triggers correctly.

**No-password-set explanation dialog (added — V2.3 post-test fixes, follow-on to
Fix 5, 2026-06-26):** clicking Login when password protection is off (so there is
no password to log in with) no longer opens the doomed-to-fail login form. Instead
`auth.js` shows a small info dialog ("Password Protection Not Set Up") explaining
that a password needs to be set in Advanced Settings first, with a single OK button.
The auth button tracks `protection_enabled` (via a `dataset.protectionEnabled`
attribute set in `checkAuthStatus()`) to decide which of the three states applies:
logout, real login form, or this explanation.

#### 7.1.3 Brute-force protection

In-memory, per-IP failed-attempt counter — no new dependency (this follows the same
precedent as dropping `Flask-Limiter` during the editor port: lean, no library where
a few lines suffice).

- **5 failed attempts** from the same IP → that IP is locked out for **10 minutes**
  (suggested defaults — Code/Tez can tune).
- Counter and lockout state reset on server restart. Acceptable for this threat
  model; this isn't defending against a sustained distributed attack, just casual
  guessing on the home LAN once Remote Administration is on.
- A successful login from an IP clears that IP's failed-attempt count.

#### 7.1.4 Session mechanism — stateless signed cookie

No server-side session store (sessions must survive the tray app's health-check
restarts and manual server restarts without forcing every open browser to re-login).

- On first run with password protection enabled, generate a random secret key
  (e.g. `secrets.token_hex(32)`) and store it in `config.json` (e.g.
  `SESSION_SECRET`) — same pattern as every other persistent setting in this app.
- Session cookie value = an expiry timestamp + an HMAC-SHA256 signature of that
  timestamp using `SESSION_SECRET` (stdlib `hmac`/`hashlib`, no new dependency).
  Cookie should be `HttpOnly`; `Secure` is not applicable here since the app runs
  over plain HTTP on the home network.
- Middleware verifies the signature and checks the expiry on every protected
  request. Invalid signature or expired timestamp = treated as unauthenticated.
- **Sliding expiry:** every successful authenticated request reissues a refreshed
  cookie with a new expiry, so an actively-used session never times out, but an
  abandoned one expires on its own. Suggested window: **30 days** of inactivity
  (tune-able).
- Password hash itself: stdlib `hashlib.pbkdf2_hmac` with a random salt, both stored
  in `config.json` alongside `SESSION_SECRET`. No new dependency (avoids pulling in
  `bcrypt`/`argon2` for a single-user home app where the threat model doesn't
  warrant it).

#### 7.1.5 Logout / Login

An auth control sits next to the gear icon in the main header on every page.

**Always-visible, label reflects state (fixed — V2.3 post-test fixes, Fix 5,
2026-06-26):** the button used to be hidden entirely when unauthenticated, which
combined with Fix 4 above left no way to log back in after logging out except by
navigating to `/admin` directly. It's now always visible, labelled "Logout" when
authenticated or "Login" when not (`auth.js checkAuthStatus()`), and the click
handler branches accordingly — logout posts to `/api/admin/logout` and reloads;
login (when a password is set — see the no-password-set case in §7.1.2) opens the
same password popup as the page-load auto-trigger. After a successful login,
`location.reload()` already fires (§7.1.2's existing behaviour), so the button
re-renders with the correct label with no extra wiring needed. No confirmation
needed for logout — logging back in is one password entry away.

#### 7.1.6 Changing password (in-session)

Once logged in, the existing **Password Reset** button (top action row, §2) becomes
live: standard current-password + new-password form. No special handling beyond
normal validation (non-empty, current password must verify before the new one is
accepted).

#### 7.1.7 Forgot-password recovery *(built — V2.3 Item 10, 2026-06-27)*

A **"Forgot Password?"** button sits in the Top Action Row (§2) next to Password
Reset, always available (no auth required to view it — it's instructions, not a
bypass). Clicking it opens a popup explaining the same manual, local-disk-only
recovery procedure as before: stop the server, clear the stored `admin_password_hash`
and `admin_password_salt` fields in `config.json` directly (reverts to "no password
set" / ungated), restart, then set a new password through the UI as normal. No
in-app recovery flow, no script, no backend endpoint — this is already consistent
with the local-access security boundary established in §7.1.1 (you need local machine
access to weaken protection anyway).

This **replaces** the earlier plan to defer documentation to a future User Guide stub
— the popup itself is now the documentation; the guide (once built) can link to it
rather than duplicating the steps.

### 7.2 Remote Administration Toggle *(built — V2.3 Item 6, 2026-06-24; broadened —
v2.4 Item 1, 2026-06-29)*

Advanced Settings → block/allow non-local (non-`127.0.0.1`) access to every route
covered by §7.1 (`/admin`, `/editor`, `/api/admin/*`, `/api/editor/*`).

**Gated: cannot be enabled unless password protection (§7.1) is currently on.**
Enabling Remote Administration while unprotected would expose the entire admin/editor
surface to anyone on the home network with no gate at all.

- The same password covers both local and remote sessions — there is no separate
  remote credential.
- Toggling Remote Administration itself follows the same local-only rule as §7.1.1 —
  only changeable from a `127.0.0.1` session, regardless of where the current
  authenticated session originated.
- If password protection is later turned off, Remote Administration is automatically
  force-disabled in the same action (§7.1.1) — never left enabled with nothing
  backing it.

**Remote Administration off means no function at all for a non-local request —
not just the destructive actions (fixed — v2.4 Item 1, 2026-06-29).** Before this,
the remote block inside `require_admin_auth()` only ran while password protection
was *on*; with protection off (the default state, and the only state Remote
Administration can be in until protection is turned on), the gate no-op'd
entirely, leaving every `/api/admin/*`/`/api/editor/*` endpoint without its own
explicit `is_local_request()` check (stats, logs, cleanup-missing, backup, the
folder-tree browse, the scan trigger) reachable from any device on the LAN. The
handful of destructive actions (Clear Database, Restore Database, the folder/file
dialogs, restart) were never affected by this gap — they carry their own
unconditional `is_local_request()` check regardless of protection/remote-admin
state.

The fix made the remote-admin-disabled check in `require_admin_auth()`
unconditional — it now runs before the protection-enabled check, not after — so
a single change covers every route already wired through that dependency. The
`/admin` and `/editor` page routes themselves (`backend/main.py`) gained the
same check directly, since they were never gated at all (always served the HTML
shell regardless of caller).

**The cog link stays visible but inert for a blocked remote session** — it does
not disappear. `auth.js checkAuthStatus()` toggles a `.settings-btn--disabled`
class (dimmed, `pointer-events: none`) rather than hiding the element, so the
Login/Logout control next to it doesn't shift position. Local sessions are
unaffected in every state.

### 7.3 Server Listening Port *(built — V2.3 Item 8, 2026-06-24; default changed —
v2.4 Item 2, 2026-06-29)*

A manual numeric input field for the server's listening port, default **9424**
via `config.json` (changed from `8000` — v2.4 Item 2). Saving updates
`config.json` and restarts the server. Relevant to `BUGS.md` BUG-004 (port 8000 /
Windows port-exclusion conflict) — moving to a less commonly reserved port is a
workaround for that issue; the v2.4 change moves the *default* itself off 8000
so a fresh install doesn't need to discover the workaround after already hitting
the conflict. 9424 was chosen as a port unlikely to fall inside a typical
WSL2/Hyper-V dynamic port-exclusion range.

**Restarting the server is not the same as restarting the tray app
(observed — v2.4 Item 2 testing, 2026-06-29).** The tray app reads
`reader_port` from `config.json` once, at its own launch, to build its "Open
Library"/"Admin" menu links and to know what port to manage. Stopping the
server from the tray menu does not necessarily kill the underlying process —
if it doesn't, the old process keeps listening on whatever port it started
with, and a second process can end up running on the new port alongside it,
both pointed at the same database. After changing this setting, fully quit
and relaunch the tray app (not just "stop the server" from its menu) so its
cached port and its managed process both pick up the change — don't assume
the menu items or the listening port have updated just because `config.json`
has.

### 7.4 Clear Database *(built — V2.3 Item 9, 2026-06-24 — destructive; full-reset +
restart behaviour added 2026-07-18, BUG-026/BUG-027 fix)*

Advanced Settings. Wipes all **library data** from the DB — issues, genres, credits,
reading progress, and the now-orphaned People rows. **Custom Tabs and Home Strip
configuration are deliberately left untouched** (they're configuration, not library
data — see `DECISIONS.md`). Confirmation uses a plain `confirm()` dialog (same
mechanism as deleting a Custom Tab), not a custom modal, despite this section's
literal "confirmation warning/modal" wording. Gated to local sessions only — same
tier as Restart Server and the backup folder dialog, since a full library wipe is at
least as disruptive as either. Not reversible — pairs with the scheduled backup (§9)
as a "start fresh" option; the confirm() message points at the Backup Database button.

**Full reset scope (2026-07-18):** clearing the DB rows alone left orphaned data
behind and no way to reclaim it (BUG-026), so `clear_database()`
(`backend/routers/admin.py`) also:
- Deletes every file in `backend/thumbnails/` — once the `Issue` rows above are
  gone, every thumbnail is orphaned by definition (`{issue_id}.jpg` naming), so this
  is an unconditional sweep, not a diff against DB rows.
- Resets the four scan log files (`last_scan_log.md`, `changed_files_log.md`,
  `new_files_log.md`, `missing_log.md` — §8) via `scan_logs.clear_all_logs()`.
  Processing Tools logs (Convert, Rename, CT Auto-Tag, etc. — §11) are untouched,
  since they aren't library-scan history.
- Clears `log_last_viewed` and `next_processing_run` in `config.json`. The latter is
  safe to null out — the Processing Folder Automation loop (`scheduler.py`) already
  treats a missing/null value as "recompute on next tick," not "fire immediately."

**Mechanism (restart-after-clear, 2026-07-18):** after the row/file/log cleanup
above, `clear_database()` runs the same `checkpoint_wal()` → `engine.dispose()` →
delete `-wal`/`-shm` sidecars sequence §9.2 uses for Restore Database, then opens a
fresh raw `sqlite3` connection (the SQLAlchemy engine is already disposed at this
point) to run `VACUUM` — reclaiming the freelist pages the bulk deletes created,
which previously left the DB file at its pre-clear size — followed by one more
`PRAGMA wal_checkpoint(TRUNCATE)`. It then calls the same `_schedule_delayed_exit()`
helper §7.3/§9.2 use, so the process exits and the tray app's crash-recovery
relaunches it automatically (frontend shows a toast and reloads the page after
~4s). This is what closes BUG-027: there is no longer any need to stop the server
before wiping — Clear Database is fully self-contained and was never reachable any
other way from the Admin UI in the first place (Stop/Start Server exist only as
tray-menu items, not Admin page controls).

`clear_database()` must be declared `async def` for `_schedule_delayed_exit()`'s
`asyncio.create_task()` call to work — a plain `def` route runs in a worker thread
with no running event loop, which raises `RuntimeError: no running event loop`
(hit during this fix's own verification; `restart_server()`/`restore_database()`
were already `async def` for the same reason).

### 7.5 Clear Reading Progress *(built — V2.3 Item 9, 2026-06-24 — destructive)*

Advanced Settings. Narrower than Clear Database (§7.4) — wipes only reading progress
records, keeps all other data (issues, people, credits, genres, etc.). Same `confirm()`
mechanism and local-only gate as §7.4.

### 7.6 Reader Location *(built — V1)*

Text field pre-populated from `config.json`. Browse/Change button to update. Saves to
`config.json`. Has no functional effect — the field this note originally deferred
to (`ROADMAP.md`'s reader-launch entry) was built 2026-07-14 (v2.6 Item 6) via a
different mechanism: the Windows Flutter reader self-discovers its own exe path
(`Platform.resolvedExecutable`) when registering itself as the `comicvault://`
protocol handler, rather than reading this server-side config field. This field
remains present but still has no functional effect and isn't read by anything.

---

## 8. Logs *(built — V2.3 Item 7, 2026-06-24)*

Two controls in the logs area:

- **View Logs Folder** — a link/button that opens the server's `/logs/` directory in
  Explorer (or reveals its path).
- **Log Size Limit** — configurable numeric input (xMB per log file). Saved to
  `config.json`.

### Scan Log Cards

Each of the four scan stat cards (§4) gains an associated log file and a **Logs**
button that opens it. Log files live in `/logs/`:

| Card | Log file | Log entry format |
|---|---|---|
| Last Scanned | `last_scan_log.md` | `DD/MM/YYYY 00:00 — Duration: 00:00:00` |
| Changed Files | `changed_files_log.md` | `filename.cbz — metadata updated` or `filename.cbz — archive changed (pages: X → Y)` |
| New Files | `new_files_log.md` | `filename.cbz — location` |
| Missing Records | `missing_log.md` | `filename.cbz — last known path — date went missing` |

**"Changed" definition — resolved 2026-06-24 by reading `scanner.py` directly,
updated 2026-07-18 (BUG-013 fix), updated again same day (BUG-029 fix):**
`scan_single_file()` matches files by exact `file_path` first; a path with no
matching row is then checked against `scan_library()`'s `_detect_renames()`
pre-pass, which matches it by `file_size` + `content_hash` against any DB row
currently off-disk (including rows already flagged missing from an earlier
scan) — a match updates that row's `file_path` in place ("moved", logged to
`changed_files_log.md`) instead of inserting a duplicate and orphaning the
original row. This only catches rows whose `content_hash` was already
populated by a prior insert/update since the fix shipped (forward-only, no
retroactive backfill — see `DECISIONS.md`); a rename of a row that predates
this fix and was never re-touched still falls back to the old
insert-new-plus-flag-missing behavior. Within a single unchanged path,
"changed" is flagged on **either** a mtime delta (≥1 second from the stored
`date_modified`) **or** a file-size mismatch (`Issue.file_size`, added for
BUG-013) — previously mtime alone was checked, which meant a same-mtime,
different-file-size re-zip (e.g. one that preserves the original timestamp)
was silently skipped. That gap was `BUGS.md` BUG-013, fixed 2026-07-18 — see
`archive/bugs-fixed-archive.md`.

**Change-type classification (fixed — V2.3 post-test fixes, Fix 8, 2026-06-26):**
the log entry now distinguishes *what* changed, instead of always logging the fixed
literal `"metadata updated"`. `scan_single_file()` compares the existing DB
`page_count` against the freshly-parsed page count (reusing the same zip-read
`_parse_cbz()` already does for every scan — no second zip open) before applying
the new metadata: a page-count mismatch logs
`"archive changed (pages: {old} → {new})"`; otherwise it logs `"metadata updated"`
as before.

**Green border indicator:** a card's border turns green when its corresponding log
file has new entries since it was last viewed (tracked via `log_last_viewed` in
`config.json`). Resets on open.

**Logs modal defaults to the most recent scan only (2026-07-19):** the log file on
disk keeps its full accumulated history — nothing above changed — but the modal
opened by a card's **Logs** button now shows only the entries from the scan that was
just run, not the whole file. Fixes the original UX: as a log grows over many scans,
the entries the user actually came to check (the ones from the scan they just ran)
used to be buried at the bottom, requiring scroll-through of old history to reach
them.

Mechanism: `changed_files_log.md`, `new_files_log.md`, and `missing_log.md` (the
three logs with zero-or-more lines per scan) each get a marker line written at the
very start of every scan run — `## Scan — DD/MM/YYYY HH:MM` — via
`scan_logs.write_scan_markers()`, called from `scan_library()` before its per-file
loop begins. This happens unconditionally, even for a scan that finds no changes, so
a lone marker with nothing under it is still meaningful signal ("a scan ran and found
nothing"), and the boundary is always well-defined going forward. `GET
/api/admin/logs/{log_name}` (`scan_logs.read_recent_log()`) returns only the content
from the last marker onward. `last_scan_log.md` needs no marker — it was already
exactly one line per scan, so "recent" there is just the last line.

**Fallback for pre-existing log files:** a log file written before this change has no
marker lines yet. `read_recent_log()` falls back to returning the full file content
in that case (same as before), rather than hiding history with no way to reach it —
once the next scan runs and adds a marker, recent-scoping starts working normally on
that file. No backfill was done or needed (forward-only, same convention as other
scan-detection fixes — see `DECISIONS.md`).

**Full history unaffected:** the log files themselves are untouched by this change —
still one continuously-growing append-only file each, still viewable in full via any
text editor by following the folder path in Settings → Library Management → Access
Logs (§8 above). Only the in-app modal's default view changed; there is no in-app
"show full history" toggle — reviewing older scans is a text-editor job, by design.


---

## 9. Database Backup

Section heading renamed from "Scheduled Backup" to **"Database Backup"**
(V2.3 Item 12, 2026-06-27) once Restore Database was added alongside it — the
section now covers backup *and* restore, split into two subsections below.

### 9.1 Scheduled Backup *(built — V2.3 Item 8, 2026-06-24)*

Consolidates two previously separate inbox items ("Backup Database Location" and
"Schedule database backup") into one unified control.

**Controls:**
- **Backup folder picker** — opens a native OS folder dialog (not the existing
  library-scoped Custom Tabs/Scan Roots picker — that one is hard-restricted to
  paths under the configured library roots, which doesn't fit a destination
  explicitly meant to live elsewhere). Frontend and backend always run on the
  same machine for this app, so the backend opening a native dialog is
  equivalent to the user opening one themselves; gated to local sessions only,
  since a remote-admin session would otherwise open the dialog on the wrong
  (server) machine. Single destination folder for all backups, saved to
  `config.json`.
- **Backup frequency dropdown *(reduced — V2.3 Item 11, 2026-06-27):*** Off /
  Every day / Every week / Every month / Every 6 months / Every 1 year. Down from
  the original ~20-entry list (every 1hr through 12 months) — Tez's call, excessive
  granularity for a single-user home app. Backend `_BACKUP_FREQUENCY_SECONDS`
  (`backend/scheduler.py`) is unchanged and still recognises the old values
  (`1hr`, `2hr`, `12hr`, etc.) — only the frontend `<select>` options
  (`frontend/admin.html`) were trimmed, so a `config.json` value saved before this
  change keeps working until the dropdown is touched and re-saved with a new value.

**No cloud API integration.** Pointing the destination folder at a cloud-sync
client's local folder (e.g. Google Drive Desktop sync folder) covers cloud backup
without in-app OAuth flows. The folder picker covers local drive, USB, and
cloud-synced folder equally.

The existing **Backup Database** button in the top action row (§2) remains for
on-demand manual backups — it uses the same destination folder once one is set.

**Last Backup indicator + scheduler failure surfacing (fixed — V2.3 post-test
fixes, Fix 9, 2026-06-26):** a "Last Backup" row sits directly under the Backup
Frequency dropdown in this same Scheduled Backup block (not the top action row —
keeps it close to the destination/frequency it describes), showing a localised
datetime string or "Never". `run_database_backup()` (shared by the manual button
and the scheduled loop) writes `last_backup_at` to `config.json` on every
successful copy and clears any `last_backup_error`. If a scheduled backup attempt
fails (`FileNotFoundError`/`OSError` in `scheduler.py`'s `_run_backup_background()`),
`last_backup_error` is set and a red warning line renders under the Last Backup
value until the next successful backup clears it. The manual button stays
exception-surfacing as before (a failed manual backup returns an HTTP error
directly) — this indicator is specifically for catching *unattended* scheduled
failures that would otherwise go unnoticed.

### 9.2 Restore Database *(built — V2.3 Item 12, 2026-06-27)*

Pairs with Scheduled Backup (§9.1) above — its own subsection/card directly below,
inside the same renamed "Database Backup" section.

**Controls:**
- **Backup File picker** — opens a native OS file dialog (`tkinter.filedialog.
  askopenfilename`, same local-machine-sharing justification as the §9.1 folder
  picker), defaulting to the configured backup folder (falls back to the
  database's own folder if unset) but **not restricted** to it — any `.db` file
  the server process can reach is selectable. Local sessions only.
- **Restore Database button** — `confirm()` naming the chosen file by its
  filename, explicitly warning this is a full database replacement (broader than
  Clear Database's §7.4 library-only scope — also overwrites Custom Tabs/Home
  Strips), then posts to `POST /api/admin/restore-database`. Local-only gated,
  same tier as Clear Database.

**Mechanism:** `restore_database()` (`backend/routers/admin.py`) takes a
`source_path`, validates it exists, then:
1. **Safety net** — snapshots the *current* `comicvault.db` first, reusing the
   existing `run_database_backup()` helper (now parameterised with a `prefix`/
   `sep`) to write `pre-restore-{timestamp}.db` into the same backup folder. If
   there's no existing DB to snapshot (`FileNotFoundError`), this step is skipped
   rather than blocking the restore.
2. **WAL checkpoint + sidecar cleanup** (added 2026-07-18, BUG-016 fix) —
   `checkpoint_wal()` (`database.py`) runs `PRAGMA wal_checkpoint(TRUNCATE)` on
   the live engine, then `engine.dispose()` releases the pooled connection's
   file handle (needed on Windows — `TRUNCATE` alone leaves the handle open and
   blocks deletion), then any remaining `comicvault.db-wal`/`-shm` sidecars are
   deleted outright. Without this, SQLite would replay the pre-restore `-wal`'s
   pending writes straight back into the just-restored file on the next open —
   the original BUG-016 failure mode.
3. Copies the chosen file over `comicvault.db` (`shutil.copy2`).
4. Triggers the same delayed-exit relaunch the Server Listening Port control
   (§7.3) and `/admin/restart` use — a full server restart rather than tearing
   down/rebuilding the live DB engine in-process. Factored into a shared
   `_schedule_delayed_exit()` helper used by both.

`run_database_backup()` also calls `checkpoint_wal()` before its own
`shutil.copy2`, so every backup (manual, scheduled, and this restore's own
pre-restore snapshot) captures fully-flushed state — not just restores.

No new dependency — `tkinter` is already used by the §9.1 folder picker.

---

## 10. Donate *(built — V2.3 Item 9, 2026-06-24)*

A Donate button on the Admin page (top action row) opens a popup/modal window
showing "Coming soon." — real content is still TBC and is a pure content edit to
this same modal block when ready, no structural change needed. Frontend-only, no
backend endpoint.

---

## 11. Processing Tools

Reserved section for CAPT's remaining standalone desktop tools, brought into ComicVault
one at a time per `ROADMAP.md`'s "CAPT extra tools" entry. Each tool gets its own
sub-section below (§11.1, §11.2, …) as it's scoped and built. All Processing Tools
sections live at the bottom of the `/admin` page, in the existing single scrolling
layout — not separate pages. (`/admin` as a whole is a placeholder layout pending a
full redesign covered elsewhere; Processing Tools sections will be restyled alongside
everything else when that happens, not before.)

**Shared design notes across all Processing Tools:**

- These tools operate on files **before** they enter the scanned library — typically
  staging areas like `Processing/`, but not restricted to any specific folder. None of
  them write to the database or trigger a rescan; they are pure filesystem utilities
  with a web UI.
- Each tool's section is gated to **local-only sessions** (request originates from
  `127.0.0.1`), same tier as Restart Server / Clear Database / the backup folder
  dialog — these tools perform real, irreversible filesystem mutations. The section is
  greyed out with an explanatory hint when accessed remotely, reusing the existing
  `is_local` flag already returned by `GET /api/admin/auth/status` and the same
  disable/hint pattern §7.1's auth controls use (`authLocalOnlyHint`).
- Source code for all four tools (Rename, Convert, Convert Images, Flatten) lives in
  the original CAPT codebase at `comic_file_editing_toolkit/src/cap_toolkit/`. Each
  tool's logic is being ported, not rebuilt from scratch — the GUI shell (PyQt) is
  discarded, the underlying file-operation logic is reused.

---

### 11.1 File Rename

**Built and manually tested 2026-07-01 — `comicvault-changes-v2.4.md` Item 10.
Queue workflow corrected 2026-07-02 — see §11.1.5.**

Ported from CAPT's standalone File Renamer (`gui/rename_window.py`,
`widgets/rename_options_widget.py`, `utils/rename_logic.py`, `utils/rename_u.py`,
`utils/filename_parser.py`). Batch and single-file renaming of arbitrary files based on
parsed/edited Series, Issue, Title, and Year values.

#### 11.1.1 Scope

- Operates on **any file**, not just comic archives — no extension filter of any kind.
  The tool only ever touches the filename string via a path rename; it never opens a
  file's contents, so it's completely format-agnostic (cbz, cbr, pdf, txt, anything).
  This also means there is nothing to "restrict to CBZ" here — that consideration
  applies to Convert Images/Flatten (§11.3/§11.4), not Rename.
- No restriction to any particular folder (e.g. `Processing/`) — the picker can browse
  anywhere the server process can see, any drive. In practice this will mostly be used
  on pre-ingest staging folders, but nothing in the implementation assumes that.
- Filenames matter to ComicVault only as a fallback parser (`scanner.py`'s
  `_parse_filename()`) used when a file lacks `ComicInfo.xml` — once a file is tagged
  and scanned, the filename is purely cosmetic. Renaming here never touches the DB and
  never needs to.
- **Not part of Processing Folder Automation (§11.4).** Re-scoped 2026-07-01: Rename
  stays a manual-only tool. Automation removes the live-preview safety net Rename
  depends on as its only correction mechanism (no undo — 11.1.6), and the
  ambiguous Series/Title-split cases surfaced during re-scope (11.1.3) specifically
  need a human decision automation can't supply. The "saved naming convention
  template" requirement originally raised by Item 15 (`INBOX.md`, `DECISIONS.md`) is
  dropped along with this — see §11.4's Change Log entry for the corresponding
  pipeline amendment.

#### 11.1.2 File Loading

- **Custom in-app folder-tree picker** — same pattern as the Full Editor's file picker
  (`EDITOR_SPEC.md` §5.1) and the Custom Tabs folder picker (§5 above), **not** a native
  OS dialog (`tkinter`). This is a deliberate choice over the native-dialog pattern used
  by the Scheduled Backup folder picker (§9): the native dialog only works because
  frontend and backend currently share a machine, and breaks conceptually under Remote
  Administration (it would pop open on the server's own screen). The in-app picker is
  pure HTTP/JSON server-side directory listing, so it behaves identically regardless of
  which device is browsing — though committing a rename stays local-gated regardless
  (§11, shared notes).
- **No library-root restriction.** Unlike the Editor's and Custom Tabs' pickers, this
  one is not scoped to `library_root` — it lists any directory the server process can
  reach. Requires a small new backend capability: a "This PC" drive-letter listing,
  reached by navigating **Up** past a drive's root (mirrors the Editor picker's
  Home/Up — **Home** returns to the configured `library_root`, **Up** climbs the tree
  and terminates at a drive-letter list rather than stopping at a fixed root).
- **No recursion.** Selecting a folder loads only the files directly inside it — no
  descent into subfolders (deliberately different from CAPT's original `rglob()`
  behaviour, and from the Editor's recursive folder-add). Loading files from a
  subfolder requires navigating into it and selecting from there. Multi-select
  individual files from within one folder is also supported via the same picker.
- **Per-file removal (added 2026-07-02).** Each row in Loaded Files has its own
  remove control — same pattern and placement as the Queued Files remove control
  (§11.1.5) — to drop a single mis-loaded file without clearing the rest.
- **Clear All (renamed from "Clear Loaded Files" 2026-07-02).** Clears Loaded
  Files, Queued Files, and resets the edit panel (all four field values and their
  File/All checkboxes) back to empty — a full reset, not just an empty file list.

#### 11.1.3 Filename Parsing

Ports `filename_parser.py`'s `parse_comic_filename()` — regex-based extraction of
Series / Issue Number / Year from the current filename, used to pre-populate the edit
panel when a file is selected. Tolerant of scene-release-style tags via
bracket-stripping heuristics, but not exhaustive — this is acceptable because nothing
is committed until the user reviews the live preview (11.1.5) and corrects anything
mis-parsed.

**Re-scoped 2026-07-01** — dedicated session, sample-tested against two real filename
sets (323 periodical-style filenames, 319 creator-prefixed OGN/collection filenames)
before deciding anything. Three concrete bugs found and fixed, output shape decided,
and a firm scope boundary drawn around what the parser is and isn't expected to solve:

- **`present_year` bug (the big one).** `extract_year()` hardcoded
  `present_year = 2025` as its validity ceiling — any year above that was silently
  rejected, which cascaded into series/issue extraction also failing (a rejected year
  leaves its bracket un-stripped, which breaks the issue-number fallback pattern too).
  Sample-tested: this alone broke parsing on 64% of the periodical sample (every
  2026-dated file). **Fix: compute the ceiling dynamically at runtime**, not a
  hardcoded number — this class of bug otherwise just recurs every January.
- **Zero-issue bug.** `issue_num.lstrip('0')` turns an all-zero issue string
  (`"000"`) into `''`, indistinguishable from "no issue found." Fix: only strip
  leading zeros when the result wouldn't be empty.
- **Volume/subtitle whitespace artifact.** Patterns like `Conan the Barbarian v05 -
  Twisting Loyalties` currently leave a double space and dangling dash after the
  `v05` token is stripped (`"Conan the Barbarian  - Twisting Loyalties"`). Fix:
  collapse whitespace after any token/bracket removal, every time, not just once
  up front.
- **No auto-splitting of Series and Title.** Confirmed during re-scope: the parser
  does not, and should not, try to separate an umbrella series name from a sub-title
  or a creator name from a book title (`Cyberpunk 2077 - Chrome`, `Abby Howard - The
  Crossroads at Midnight`) — both are structurally identical strings to a regex, and
  guessing wrong is worse than not guessing. These stay as one glued Series string by
  design. Where the desired final filename genuinely needs a distinct, human-decided
  Title (recurring sub-series titles consistent across a run of issues, e.g. "Dirk
  Gently's Holistic Detective Agency: A Spoon Too Short") — that's a manual entry in
  the Title field, applied via the existing Title→All checkbox once per batch
  (11.1.4). This is the intended tool for that case, not a parser gap.
- **One-shots/OGNs with no issue number in the filename** parse correctly today —
  Series and Year populate, Issue stays empty, and the output template omits the
  `#Issue` segment entirely rather than inventing one.
- **Output separator, decided:** `Series - Title #Issue (Year)`, dash-joined. No
  conditional separator logic — the dash is always present when Title is non-empty,
  omitted along with Title when it's blank.

Sample-tested clean-parse rate once the three bugs above are fixed: ~88% of the
323-file periodical sample requires no manual correction at all. The remaining ~12%
is genuine one-shots (handled correctly, see above) and the ambiguous-split cases
(handled manually, see above) — not a parser deficiency.

#### 11.1.4 Edit Panel

Four fields — **Series, Issue, Title, Year** — each with two independent checkboxes:

| Column | Meaning |
|---|---|
| **File** | Apply this field's typed value to the single currently-selected file only |
| **All** | Apply this field's typed value to every currently loaded file |

**Per-field independence, no column auto-select.** CAPT's original behaviour
auto-selected every File checkbox the moment one was ticked (same for All) — an
all-or-nothing column. This is **not** carried over. Each field's File/All pair is
fully independent of every other field's, matching the convention already established
for the Full Editor's "Apply to: All" checkboxes (`EDITOR_SPEC.md` §5.2, Item 5 of
`comicvault-changes-v2.3.md`) — e.g. Series→All and Issue→File can be set
simultaneously, applying Series across the whole batch while leaving Issue numbers
edited per-file.

**Batch options:**

- **Auto-Increment Issue Numbers** — enabled only when **Issue→All** is checked
  specifically (fixes a bug in the original CAPT, where it was enabled by *any* All
  checkbox regardless of which field). When active, the Issue value typed in is treated
  as the starting number and incremented sequentially down the loaded-files list in its
  current display order (respects drag-and-drop reorder).
- **Case style** — Title Case / All UPPER Case / All lower case, mutually exclusive
  (single-choice group, unchanged from CAPT). Applies only to Series and Title text
  values — Issue and Year are never case-styled.

#### 11.1.5 Queue (also serves as Preview)

**Re-scoped 2026-07-02** — the original 2026-07-01 build used an implicit
auto-accumulate-on-edit model with no explicit "add" gesture and no way to pull a
single file back out (only a whole-list Clear Preview). Manual testing against the
original mockup (`Filename-Editor.pdf`) found this dropped the tool's core intended
workflow, so it's replaced with the explicit queue below.

Editing a field or toggling a File/All checkbox only updates the edit panel's own
state — nothing is sent to the backend yet. An explicit **Add to Queue** button
commits the current edit-panel state:

- **Single-file mode** (any field's File box checked, a file selected) — adds just
  the selected file to the queue, computed from its File-checked overrides plus its
  own parsed baseline for everything else.
- **Batch mode** (any field's All box checked) — adds every currently loaded file to
  the queue in one click, each computed from the shared All-checked values, its own
  File-checked override where applicable, and its own parsed baseline for anything
  else. If Auto-Increment is also on (only available when Issue→All is checked),
  Series/Title/Year still resolve the same per-file way — only Issue is replaced
  with a sequential number computed from the display order at Add to Queue time
  (respects Move Up/Down reordering done *beforehand*, since the queue is a
  one-shot commit, not a live recomputation). **Fixed 2026-07-02** — the initial
  build sent one shared value set for the whole batch when Auto-Increment was on,
  which blanked any field that wasn't All-checked (Series/Title/Year vanished from
  every file's preview, leaving only `#N.ext`) instead of falling back to each
  file's own baseline/File override. Auto-Increment now goes through the same
  per-file resolution as the rest of batch mode, with only the Issue value
  overridden per file.
- Neither box checked — nothing to add; a toast prompts to check a File or All box
  first.

The **Queued Files** list doubles as the preview — each row shows only the resulting
new filename (the old name is already visible at the same row position in Loaded
Files, so it isn't repeated). Repeat Add to Queue per file (single-file mode) to
build up a queue file-by-file, or once in batch mode to queue everything at once —
both can be mixed across separate Add to Queue clicks.

Each queued row has its own remove control to drop just that file back out of the
queue without affecting the rest. **Clear Preview** empties the whole queue at once.
Switching the selected Loaded File without clicking Add to Queue discards the
unsaved edit — this is intentional: Add to Queue is the deliberate commit point.

#### 11.1.6 Apply Rename

Attempts every file currently in the queue. On completion, shows a summary modal
matching the Full Editor's existing Process-error pattern (`feProcessErrorModal`):
"Renamed X of Y files", plus a per-file error list for any failures (permission denied,
filename collision, file no longer present on disk, etc.). Files that succeed clear
from the queue; files that fail remain so the user can retry or adjust. No
partial-silent-failure — every attempted file is accounted for in the summary.

There is **no undo**. This is consistent with the tool's nature (a basic log, not a
transaction system) and matches CAPT's own behaviour — the live preview is the only
safety net before committing.

#### 11.1.7 Audit Log

New `rename_log.md` in `/logs/`, following the existing append-only pattern in
`scan_logs.py` — one line per renamed file:

```
DD/MM/YYYY HH:MM — old_filename.ext → new_filename.ext
```

**Independent 1MB size cap** — not governed by the existing configurable Log Size
Limit setting (§8), which stays scoped to the four scan logs only. Once `rename_log.md`
exceeds 1MB, the oldest entries are dropped first (same truncation mechanism as
`scan_logs.py`'s `_truncate_if_oversized()`, just a fixed ceiling instead of the
configurable one).

#### 11.1.8 Implementation Notes (for Code)

Not binding design, but worth flagging before the build session:

- New backend router (e.g. `backend/routers/rename.py`) mirroring `editor_full.py`'s
  shape: a `browse` endpoint (no `library_root` restriction, lists files *and* folders,
  no extension filter, plus a drive-list endpoint for the "This PC" Up-navigation
  terminus), working-file-list endpoints (add/remove/clear — no recursion, no
  extension filter), and an apply endpoint.
- New `rename_log.py`, parallel to `scan_logs.py`, with its own fixed 1MB ceiling.
- Port `parse_comic_filename()`, `build_filename()`, and the rename-application logic
  from `comic_file_editing_toolkit/src/cap_toolkit/utils/filename_parser.py` and
  `rename_u.py` directly — both are already pure functions with no PyQt dependency.
- This is the **third** near-identical in-app folder-tree picker implementation
  (Editor's `fePicker*`, Custom Tabs' `ctPicker*`, now Rename's). Worth a quick
  judgement call on whether to factor a shared picker component now or carry the
  duplication — not a blocker either way, flagging for awareness only.

---

### 11.2 Convert Archives

**Built and manually tested 2026-07-01 — `comicvault-changes-v2.4.md` Item 12.**
Cross-review fix applied during this build: the picker now excludes `*.bak`
files by filename suffix, same as §11.3 already did — see the Change Log
entry for detail.

Ported from CAPT's standalone Archive Converter (`gui/convert_window.py`,
`processors/arc_convert_worker.py`, `processors/arc_conv_cb_proc.py`,
`processors/arc_conv_pdf_proc.py`, `utils/arc_conv_helpers.py`,
`utils/arc_convert_util.py`). Converts CBR or PDF files into CBZ.

#### 11.2.1 Scope

- **Only two conversion directions are ported: CBR → CBZ and PDF → CBZ.** CAPT's
  other two directions (CBZ → CBR, CBZ → PDF) are dropped entirely, not just
  hidden — there is no UI path to them and their underlying code is not ported.
  This follows directly from Item 5's resolution (`SPEC.md`): CBR is now read
  natively by the scanner, so there's no remaining reason to convert a CBZ down to
  CBR, and PDF was dropped from the scanner/library entirely in favour of always
  converting to CBZ first. The user's only choice is **From format** (CBR or
  PDF) — the target is always CBZ and isn't shown as a separate control.
- Same local-only gating, in-app folder-tree picker pattern, and audit-log
  pattern as §11.1 File Rename — see §11 shared notes above. Same
  pre-ingest/staging positioning (not restricted to any folder).
- Format detection is **content-based**, reused unchanged from
  `arc_convert_util.py`'s `detect_archive_format()` — `.pdf` suffix check, then
  `zipfile.is_zipfile()` / `rarfile.is_rarfile()` magic-byte checks for CBZ/CBR.
  Filenames and extensions are never trusted on their own.

#### 11.2.2 File Loading

- Same in-app folder-tree picker as 11.1.2 — no native dialog, no
  `library_root` restriction, Up climbs to a drive-letter list, no recursion,
  multi-select within one folder.
- **Difference from Rename:** once a From format (CBR or PDF) is selected, the
  picker's file list is filtered server-side to only files whose **detected**
  format matches the selection — content-detected, not extension-filtered.
  Resolved this session (filter, not grey-out): a mislabeled file (e.g. a
  `.zip` renamed to `.cbr`) simply won't appear under "CBR", consistent with
  the format detector's whole purpose of not trusting extensions.

#### 11.2.3 Conversion Options

- **From format** — single choice (CBR or PDF) applied to the whole loaded
  batch, not per-file. Target is always CBZ, shown as a static "→ CBZ" label,
  not a control.
- **No "Delete Original File" checkbox.** Removed 2026-07-01 — superseded by
  the unified backup model (11.2.4, 11.4.6). Original-file disposition is no
  longer a user choice; it's determined automatically by the conversion
  outcome, same as Convert Images (11.3.3 has carried no such checkbox from
  the start, for the same reason).

#### 11.2.4 Conversion Engine

- **CBR → CBZ:** extract via `rarfile` to a temp directory, rezip with
  `zipfile.ZIP_DEFLATED`. Ported from `arc_conv_cb_proc.py`'s
  `convert_archive()` / `FORMAT_MAP['CBR']` branch only — the CBZ → CBR branch
  and its `create_rar_archive()` dependency (shells out to a `rar` CLI /
  requires paid WinRAR) is **not ported**. This confirms RAR creation is never
  required anywhere in ComicVault — consistent with `EDITOR_SPEC.md`'s CBR-edit
  path, which also never writes RAR.
- **macOS AppleDouble sidecars dropped on rebuild (BUGS.md BUG-028, fixed
  2026-07-18).** `._`-prefixed and `__MACOSX/` entries — junk left behind by
  an archive that was ever touched on a Mac, not real page content — are now
  excluded when this step rezips, via the shared `archive_formats.is_macos_junk_entry()`
  predicate. Same fix applied to Convert Images' rebuild (§11.3.4, via the
  shared `flatten_and_zip()`) and CT Auto-Tag/XML Tagging, since both funnel
  through the same rebuild function — so a batch carrying this junk in no
  longer reintroduces it once it passes through any of these tools.
- **PDF → CBZ:** rendered via PyMuPDF (`fitz`), one page per image. New
  **`PDF_RENDER_DPI = 300`** module-level constant (resolved this session,
  print-scan-grade sharpness over CAPT's original 72 DPI), driving
  `fitz.Matrix(PDF_RENDER_DPI / 72, PDF_RENDER_DPI / 72)` in place of CAPT's
  hardcoded `Matrix(1, 1)`. Isolated single-constant change — adjusting DPI
  later needs no other code or schema changes. Pages written as PNG (CAPT's
  existing `page_{i+1:03d}.png` naming retained), then zipped the same way as
  the CBR path.
- **Output path:** same folder, same base filename, `.cbz` extension
  (`Path.with_suffix('.cbz')`) — matches CAPT's default.
- **Backup & Safety — amended 2026-07-01, unified with Convert Images (11.3.5)
  per 11.4.6.** The converted output is staged, then validated (opens as a
  valid archive; image-entry count matches the expected count, accounting for
  any `pages_skipped`). **On successful validation:** the original is renamed
  to `original.ext.bak` (e.g. `Batman #1.cbr.bak`) and the staged output is
  moved into place as `original.cbz`. The `.bak`'s disposition then follows
  11.4.6's unified table: clean success (`pages_skipped = 0`) auto-deletes
  it; success-with-warnings (`pages_skipped > 0`) keeps it permanently, since
  a skipped page means the original is the only recovery path. **On failed
  validation:** the staged output is discarded and the original is left
  completely untouched — no rename, no `.bak` created. **Guard:** if a `.bak`
  already exists for that filename, the run fails for that file with "Backup
  file already exists" — no overwrite, no auto-renaming, same no-silent-clobber
  principle as 11.3.5's equivalent guard. This replaces the old "Output file
  already exists" guard, which checked the wrong thing (the *target* `.cbz`
  colliding) relative to the model Convert Images and Processing Folder
  Automation both already use.
- **CBR CRC errors:** `rarfile`'s tolerant extraction
  (`ignore_crc_errors=True`, ported unchanged from `arc_conv_helpers.py`'s
  `extract_rar_archive()`) is kept — a damaged page is skipped rather than
  aborting the whole file. **Resolved this session — no longer silent:** the
  per-file result now carries a `pages_skipped` count. The conversion still
  counts as a **success** (a CBZ is produced) but is flagged
  success-with-warning in the summary and audit log, e.g. "converted, 2 pages
  missing/corrupted" — differs from CAPT's original fully-silent behaviour.

#### 11.2.5 Progress & Status

- **Resolved this session — background job with live polling, not a blocking
  request like Rename.** Rename is a near-instant string operation; archive
  conversion involves real extract/rezip/rasterize work per file and can take
  meaningful time over a batch, so it follows the **existing scan-progress
  pattern already established in `backend/scanner.py`** (`scan_progress`
  module-level singleton + `GET /api/scan/status`) rather than a new
  architecture.
- New `convert_progress` singleton tracking `running`, `current_file_index`,
  `total_files`, `current_filename`, `finished_at`, and the accumulating
  per-file results list.
- `POST /api/admin/convert/run` starts the batch via FastAPI's
  `BackgroundTasks` and returns immediately (acknowledgement only).
- `GET /api/admin/convert/status` polled by the frontend at the same cadence
  as the existing scan-progress UI, driving a live "Converting file 3 of 20 —
  filename.cbr" label and progress bar.
- On completion: same summary-modal pattern as Rename's `feProcessErrorModal`
  — "Converted X of Y files", per-file status (success / success-with-warning
  / failed) with error or pages-skipped detail. Failed files stay in the
  working list for retry; succeeded files (with or without warning) clear.

#### 11.2.6 Audit Log

New `convert_log.md` in `/logs/`, same append-only pattern and same
independent 1MB cap as `rename_log.md` (11.1.7) — not governed by the
configurable Log Size Limit (§8). One line per attempted file:

```
DD/MM/YYYY HH:MM — old_filename.cbr → new_filename.cbz [OK]
DD/MM/YYYY HH:MM — old_filename.cbr → new_filename.cbz [OK, 2 pages skipped] (backed up to old_filename.cbr.bak)
DD/MM/YYYY HH:MM — old_filename.pdf → FAILED: Backup file already exists
```

**Updated 2026-07-01**, matching the 11.2.4 backup-model amendment: a
success-with-warnings line now notes the retained `.bak` (same format as
`convert_images_log.md`, 11.3.7); the failure example now reflects the
`.bak`-collision guard rather than the retired "output file already exists"
check.

#### 11.2.7 Implementation Notes (for Code)

Not binding design, but worth flagging before the build session:

- New backend router (e.g. `backend/routers/convert.py`). The browse /
  working-file-list endpoints can likely share most of Rename's picker code
  directly — 11.1.8 already flagged the picker as duplicated three times
  (Editor, Custom Tabs, Rename); Convert Archives makes it a fourth. Worth
  factoring into a shared component now rather than carrying it further —
  still not a hard blocker either way.
- Port `detect_archive_format()` from `arc_convert_util.py` unchanged.
- Port the CBR-only branch of `convert_archive()` / `FORMAT_MAP` from
  `arc_conv_cb_proc.py` — drop the CBZ → CBR half and `create_rar_archive()`
  entirely.
- Port `convert_pdf_to_cbz()` from `arc_conv_pdf_proc.py`, swapping
  `fitz.Matrix(1, 1)` for `fitz.Matrix(PDF_RENDER_DPI / 72, PDF_RENDER_DPI / 72)`
  with `PDF_RENDER_DPI = 300` as a module-level constant. Drop
  `convert_cbz_to_pdf()` entirely — not needed.
- New `convert_progress` singleton + status endpoint, modelled directly on
  `backend/scanner.py`'s existing `scan_progress` — reuse the shape rather
  than inventing a new one.
- **Write the core conversion function as a plain, router-independent
  callable** — e.g. `convert_archive_file(source_path, from_format) ->
  ConvertResult` — taking a file path and format, returning a result object,
  with no FastAPI/request coupling. Confirmed 2026-07-01 during Item 15
  scoping as a requirement here too (same pattern 11.3.8 already specified
  for Convert Images) — Processing Folder Automation (§11.4) invokes this
  directly, not through the admin UI's HTTP layer.
- `rarfile` is already a dependency (Item 5, native CBR read support) — no new
  dependency for the CBR side. `PyMuPDF` (`fitz`) and `Pillow` are **new**
  dependencies for the PDF side — confirm both install cleanly in the existing
  Python environment before the build session.
- New `convert_log.py`, parallel to `rename_log.py` / `scan_logs.py`, fixed
  1MB ceiling.

---

### 11.3 Convert Images

**Built and manually tested 2026-07-01 — `comicvault-changes-v2.4.md` Item 13.**

Ported from CAPT's standalone Convert Images tool (`gui/convert_images_window.py`,
`utils/convert_images.py`). Converts supported raster images inside a CBZ or CBR
(jpg/jpeg/tiff/gif/png/bmp) to WebP and repacks the archive.

#### 11.3.1 Scope

- **Pre-ingest staging only** — same positioning as §11.1 Rename and §11.2 Convert
  Archives, not a library-wide bulk-conversion tool. (A future, separately-scoped
  Auto Processing Folder feature is expected to run this same conversion logic
  unattended on files landing in a watched folder — see 11.3.7 — but that doesn't
  change today's scope: this section covers the manually-triggered admin-UI tool
  only.)
- **Both CBZ and CBR accepted as input**, content-detected the same way as 11.2.2
  (`detect_archive_format()`, not extension-trusted). Unlike Convert Archives,
  there's no "From format" selector — the operation (convert images, repack) is
  identical regardless of source container, so both formats simply load into the
  same working list together.
- **CBR is never written.** A CBR source has its images converted exactly like a
  CBZ source, but the rebuilt output is always `.cbz` — same rule as the Editor's
  existing CBR-edit-rebuilds-as-CBZ path (`EDITOR_SPEC.md`, Item 5/11.2.1).
  CAPT's original CBR repack via a `rar` CLI shell-out is **not ported** — it
  depended on a paid WinRAR install, the exact dependency already ruled out
  everywhere else in the app.
- Same local-only gating, in-app folder-tree picker (no `library_root`
  restriction, no recursion, Up climbs to a drive-letter list), and audit-log
  pattern as §11.1/§11.2 — see §11 shared notes.
- **The picker excludes `*.bak` files explicitly**, by filename suffix, not just
  content-detection. A `.bak` backup (11.3.5) is still a structurally valid
  zip/rar by content, so without this exclusion a previous run's backups would
  reappear as convertible inputs in their own right.

#### 11.3.2 File Loading

Same in-app folder-tree picker as 11.1.2/11.2.2. Picker's file list is filtered
to content-detected CBZ or CBR only, minus any `*.bak` files (11.3.1).
Multi-select within one folder, no recursion.

#### 11.3.3 Conversion Options

- **Quality** — user-facing setting at conversion time, applied batch-wide (not
  per-file): a **Lossless** toggle, and when off, a **quality slider** (default
  95, matching CAPT's original value). This replaces CAPT's hardcoded
  `quality=95` and corrects the docstring/code mismatch in the original
  (`"keeping original quality"` vs. an undocumented lossy 95 — CAPT's own
  in-app label even disagreed with itself, saying "90% quality"). Lossless is a
  real option now, not implied by the marketing text.
- No "Delete Original" checkbox — doesn't apply here the way it does to Convert
  Archives. This tool doesn't produce a separate output file the user chooses to
  keep or discard; it rewrites the archive in place under the same filename, with
  its own backup mechanism (11.3.5) standing in for that role instead.

#### 11.3.4 Conversion Engine

- Extract via `zipfile` (CBZ) or `rarfile` (CBR, `ignore_crc_errors=True` —
  already a dependency per Item 5, no new dependency for the CBR side).
- Convert each image whose extension is in `{.jpg, .jpeg, .tiff, .gif, .png,
  .bmp}` to WebP via Pillow, per the quality/lossless setting (11.3.3). Files
  already in `.webp` are left untouched (they simply aren't in the convert set).
  `ComicInfo.xml` and any other non-image entries are extracted and repacked
  unchanged, same as CAPT's original.
- **Per-image failures don't abort the archive.** A corrupted/unreadable image
  is skipped and left in its original format in the rebuilt archive (matches
  CAPT's existing fallback — the only change is making it visible). The result
  is flagged success-with-warning and carries an **`images_skipped`** count,
  same pattern as 11.2.4's `pages_skipped` for Convert Archives.
- **Flatten-and-rebuild reuses the Editor's existing logic**
  (`backend/editor/archive_io.py`'s `_rebuild_archive` flatten step), not
  CAPT's separate flatten implementation. This is a deliberate consolidation,
  not a coincidence — Tez confirmed during scoping that nested-folder archives
  are a known, previously-hit problem (the original reason `_rebuild_archive`
  flattens at all), and having two slightly different flatten implementations
  drift apart over time is exactly the kind of risk worth avoiding up front.
  Code should factor the flatten-and-zip step into something both
  `archive_io.py` and the new Convert Images module can call, rather than
  duplicating it a second time.
- **Known limitation, not addressed:** an animated GIF converts via its first
  frame only (Pillow's default `Image.open` behaviour) — flagged for awareness,
  not expected to matter for comic page content.

#### 11.3.5 Backup & Safety

This tool rewrites the archive's contents in place under the same filename —
structurally different from Rename (only a filename changes, trivially
reversible) and Convert Archives (creates a new file, original only deleted
after the new one's confirmed good). There's no equivalent "kept until you
choose to discard it" margin here unless one is built in explicitly:

- The rebuilt archive is staged in the same directory as the original (matching
  `_rebuild_archive`'s existing same-filesystem-atomic-replace approach), then
  **validated** — confirms it opens as a valid archive and that its image-entry
  count matches the pre-conversion count (accounting for any `images_skipped`
  originals retained in their source format).
- **On successful validation:** the original is renamed to `original.ext.bak`
  (e.g. `Batman #1.cbr.bak`), the staged rebuild is moved into place as
  `original.cbz`, and **the `.bak` is kept — not auto-deleted.** This was
  raised explicitly during scoping: a future Auto Processing Folder feature is
  expected to run this same conversion unattended on files landing in a watched
  folder, with no one necessarily checking results in real time. An
  auto-delete-on-success policy is fine for a human watching the screen, but
  not for a backlog of unattended runs where a silent bad conversion could go
  unnoticed. The `.bak` therefore persists until the user manually deletes it,
  regardless of which trigger (manual admin UI today, or the watched folder
  later) produced it.
- **If a `.bak` already exists** for that filename (e.g. converted twice without
  cleanup), the run fails for that file with "Backup file already exists" —
  no overwrite, no auto-renaming, same no-silent-clobber principle as Convert
  Archives' output-exists guard (11.2.4).
- **On failed validation:** the staged rebuild is discarded, the original file
  is left completely untouched (no rename, no `.bak` created — there was never
  a need to touch the original in the first place), and the failure is reported
  in the summary/audit log.

#### 11.3.6 Progress & Status

Background job with live polling, same reasoning and same shape as 11.2.5 —
per-image extract/convert/rezip work is meaningfully slower than Rename's string
operations and scales with image count, not just file count. New
`convert_images_progress` singleton (own module, not shared with §11.2's
`convert_progress` — separate tools, separate endpoints), tracking `running`,
`current_file_index`, `total_files`, `current_filename`, `finished_at`, and the
accumulating per-file results list (status: success / success-with-warning /
failed, plus `images_skipped` where relevant).

- `POST /api/admin/convert-images/run` starts the batch via `BackgroundTasks`,
  returns immediately.
- `GET /api/admin/convert-images/status` polled by the frontend, same cadence
  and UI pattern as §11.2's live "Converting file X of Y" label.
- On completion: same summary-modal pattern as Rename/Convert Archives —
  "Converted X of Y files", per-file status with `images_skipped` or error
  detail. Failed files stay in the working list for retry.

#### 11.3.7 Audit Log

New `convert_images_log.md` in `/logs/`, same append-only pattern and
independent 1MB cap as `rename_log.md`/`convert_log.md` — not governed by the
configurable Log Size Limit (§8). One line per attempted file:

```
DD/MM/YYYY HH:MM — filename.cbz [OK]
DD/MM/YYYY HH:MM — filename.cbr → filename.cbz [OK, 3 images skipped] (backed up to filename.cbr.bak)
DD/MM/YYYY HH:MM — filename.cbz [FAILED] — Backup file already exists
```

**Corrected 2026-07-01, during the build session.** The clean-success line
above originally read `filename.cbz [OK] (backed up to filename.cbz.bak)` —
stale relative to the unified backup model (§11.4.6): a clean success
auto-deletes the `.bak`, so claiming one exists was wrong. Only the
success-with-warnings line legitimately mentions a `.bak`, since that's the
only outcome that keeps one. Same pattern `convert_log.md` (§11.2.6) already
had right.

#### 11.3.8 Implementation Notes (for Code)

Not binding design, but worth flagging before the build session:

- New backend router (e.g. `backend/routers/convert_images.py`). Picker/
  working-file-list endpoints can share code with §11.1/§11.2's pickers — same
  factoring opportunity already flagged twice now (11.1.8, 11.2.7).
- **Write the core conversion function as a plain, router-independent
  callable** — e.g. `convert_images_in_archive(archive_path, quality, lossless)
  -> ConvertImagesResult` — taking a file path and options, returning a result
  object, with no FastAPI/request coupling. This is a deliberate forward-looking
  call, not speculative gold-plating: a future Auto Processing Folder feature
  (not yet scoped) is expected to invoke this exact logic on files landing in a
  watched folder, and it should be able to call the function directly rather
  than needing to go through the admin UI's HTTP layer.
- Port `convert_images_to_webp()`'s image-loop logic from
  `comic_file_editing_toolkit/src/cap_toolkit/utils/convert_images.py`, but:
  drop the bespoke flatten block in favour of calling into
  `backend/editor/archive_io.py`'s flatten-and-zip step (factor it out as
  shared, per 11.3.4); replace the hardcoded `quality=95` with the
  quality/lossless parameters; drop the CBR repack branch entirely (the `rar`
  CLI shell-out) since CBR sources always rebuild as CBZ now.
- `backend/editor/archive_io.py`'s module docstring currently states "CBR
  support is dropped entirely... library is all-CBZ" — stale relative to
  Item 5's reversal of that decision. Not this item's job to fix (Item 11 — CBR
  support — owns that correction), just flagging so it isn't mistaken for
  current truth while building this.
- New `convert_images_log.py`, parallel to `convert_log.py`/`rename_log.py`,
  fixed 1MB ceiling.
- `Pillow` is already a dependency (thumbnail generation). No new dependency
  for the WebP side — Pillow's WebP support covers both lossy-with-quality and
  lossless via the same `save(..., format="WEBP", lossless=True/False,
  quality=N)` call.

---

### 11.4 Processing Folder Automation

**Built and manually tested 2026-07-01 — `comicvault-changes-v2.4.md` Item 16,
closing out the CAPT-tooling cluster.**

Automates the two ported CAPT tools (§11.2 Convert Archives, §11.3 Convert Images)
against a single configured folder, triggered either on a schedule or on demand via a
"Run Now" button. **§11.1 File Rename is deliberately not part of this pipeline** —
dropped 2026-07-01, see the Change Log entry below and 11.1.1.

#### 11.4.1 Scope

- **Not a file-system watcher.** No real-time monitoring of folder contents — all
  processing is triggered by the configured schedule or by "Run Now". The file-watcher
  model was evaluated during scoping (v2.4 Item 15) and rejected: it requires a new
  `watchdog` dependency, a debounce mechanism (files take time to fully copy before
  they can safely be processed), a persistent work queue to survive server restarts, and
  protection against processing 200 simultaneous arrivals in parallel — meaningful
  architecture cost for a personal staging workflow where batch arrival is the norm. A
  scheduler + "Run Now" covers the real use case with none of that complexity.
- **Three-stage pipeline** — Convert Archives → CT Auto-Tag → Convert Images, fixed
  order, not configurable. Each stage is independently toggleable but the order
  never changes. See 11.4.3 for the dependency rationale. (This was a two-stage
  pipeline — Convert Archives → Convert Images — from 2026-07-01 until CT Auto-Tag
  was added 2026-07-03; before that, a three-stage pipeline that also included
  Rename was dropped 2026-07-01. See Change Log for both.)
- Same local-only gating as all Processing Tools (§11 shared notes). The section is
  greyed out with an explanatory hint for remote sessions.
- Same pre-ingest/staging positioning as §11.1–§11.3. Not restricted to any specific
  folder; not a library-wide bulk tool.

#### 11.4.2 Folder Selection

- Single folder selection — same in-app folder-tree picker as §11.1–§11.3 (no native
  OS dialog, no `library_root` restriction, Up climbs to a drive-letter list, no
  recursion).
- One folder applies to the whole pipeline. There is no per-stage folder override.
- Persisted in `config.json` as `processing_folder_path`.

#### 11.4.3 Pipeline Execution Order

Fixed, always in this sequence:

1. **Convert Archives (§11.2)** — processes CBR and/or PDF files in the folder,
   produces CBZ output. After this stage the folder contains the new CBZ files
   alongside (or replacing, per 11.4.6's backup model) the originals.
2. **CT Auto-Tag (new, 2026-07-03 — see `DECISIONS.md`)** — runs ComicTagger's
   `issueidentifier` (Series/Issue # required at minimum, plus Year/Publisher/Month/
   Issue Count and cover-image hash matching for confidence — see
   `EDITOR_SPEC.md` §9.1/§9.5 for the same field set as it applies to the Full
   Editor's manual Search Online) against each file in the folder, writing
   `ComicInfo.xml` tags for confident matches. Low-confidence matches are governed
   by the Save on Low Confidence toggle (11.4.4): ON writes the best-guess tags and
   sets the `NeedsReview` flag (`EDITOR_SPEC.md` §9.2) for later resolution in the
   Full Editor; OFF skips writing anything for that file, which passes through
   untagged and unflagged. Requires a `comicvine_api_key` (11.4.4) — see that
   section for why.
3. **Convert Images (§11.3)** — processes CBZ and CBR files in the folder (excluding
   `.bak` files), converts images to WebP and repacks. After this stage all processed
   archives contain WebP images.

**Why this order is fixed:** Stage 1 may produce new CBZ files that Stage 2/3 should
then process — running a later stage first would miss them. CT Auto-Tag runs before
Convert Images so tagging always happens on the archive's original images, not
after a lossy WebP pass — not a hard technical requirement (CT can read either
format), but keeps the pipeline's confidence scoring working against the
highest-quality source available. Running the stages in any other order creates a
compounding conflict with no benefit.

**Rename is not part of this pipeline** (dropped 2026-07-01 — see Change Log). Files
land in the processing folder converted and image-optimized; renaming remains a
deliberate manual step via §11.1's admin tool, same as the pre-automation workflow —
Rename's only safety net is the human reviewing its live preview before committing,
which unattended automation would remove.

**Folder-level, not per-file chaining.** Each stage operates on the folder contents
as they exist at that point in the pipeline — it does not receive an explicit list of
files from the previous stage. Each later stage simply picks up whatever CBZ/CBR
files are present after the previous stage finishes. This means:

- A CBR that **failed** Stage 1 (conversion failed, original untouched) will still
  be picked up by Stage 2 (CT Auto-Tag reads CBR natively) and by Stage 3 if
  Convert Images is enabled — §11.3 accepts CBR input and rebuilds as CBZ.
- A file that was already CBZ before the run is ignored by Stage 1 and picked up
  normally by Stages 2 and 3.
- A file CT Auto-Tag skipped (Save on Low Confidence OFF, or the stage disabled
  entirely) is picked up by Stage 3 exactly as if Stage 2 hadn't run on it —
  Convert Images has no dependency on tagging having happened first.

**Per-stage failures do not abort the pipeline.** If a stage fails on a subset of
files, the next stage runs on whatever was left in a valid state. A complete stage
failure (the stage itself errors out, not just individual files) logs the error and
moves to the next stage — the pipeline always runs all enabled stages.

#### 11.4.4 Per-Stage Configuration

Each stage has an **enabled/disabled toggle** and its own settings, all persisted
in `config.json`.

**Convert Archives:**

- Toggle: enabled/disabled (`processing_folder_convert_archives_enabled`)
- From format: CBR or PDF (`processing_folder_convert_archives_from`) — same content-
  detected format choice as 11.2.2. Applied batch-wide to the whole folder run.
- Backup model: see 11.4.6.

**CT Auto-Tag** (new, 2026-07-03 — see `DECISIONS.md`, four entries same date, and
`EDITOR_SPEC.md` §9 for the Full Editor side of this feature):

**v2.6 Item 1 Phase C2b (2026-07-07):** the enable toggle stays here, but the
three detailed settings below (Save on Low Confidence, Match Ratio Threshold,
ComicVine API key) moved to a new standalone **§11.6 XML Tagging** admin-UI
pane — shared `config.json` keys, read by both panes, not duplicated. This
subsection still documents them in full since the underlying config/behaviour
is identical; §11.6 covers only what's new (the standalone folder-run tool
itself).

- Toggle: enabled/disabled (`processing_folder_ct_autotag_enabled`).
- **Save on Low Confidence** toggle (`processing_folder_ct_save_low_confidence`,
  default ON): ON writes the best-guess tags to a low-confidence match and sets
  the `NeedsReview` flag (`EDITOR_SPEC.md` §9.2) for later resolution in the Full
  Editor; OFF skips writing anything for that file — it passes through the stage
  untagged and unflagged, as if the stage hadn't run on it. Deliberately a branch
  inside this stage, not a pipeline-flow change — holding a low-confidence file
  back from continuing to Convert Images/the library was considered and rejected,
  since §11.4 is folder-level, not per-file chaining (11.4.3), and building
  per-file hold-back tracking wasn't judged worth it for this.
- **Match Ratio Threshold** slider (`processing_folder_ct_match_threshold`,
  default 80, range 10–100 in 1% steps) — added 2026-07-04, once Tez had more
  real-world match data than the original 80%-hardcoded default was set from.
  Feeds `IssueIdentifierOptions`' `series_match_search_thresh` and
  `series_match_identify_thresh` (`backend/ct_bridge.py`'s `identify_file()`,
  read from config at call-time), kept tied to one value rather than two
  separate controls, matching CT's own single "match ratio" concept. Auto-saves
  like every other control in this section — every auto-save control here
  (this slider, both toggles above, Convert Archives/Images' controls) shows a
  brief "Saved" toast on change, added 2026-07-04 (`savePfSetting()`,
  `frontend/js/processingTools.js`); the ComicVine API key's Save & Test
  button is still the one control with its own distinct feedback.
- **ComicVine API key** — text field, `comicvine_api_key` in `config.json`
  (plaintext, same trust model already applied to the existing `SESSION_SECRET`).
  Required for this stage to do anything: without a personal key, CT's
  `comictalker` falls back to its own shared default key, rate-limited to 1
  request/10s and 100/hour globally across every ComicTagger install that hasn't
  configured one — a personal key gets 10 req/10s and 200/hour instead (confirmed
  by reading `comictalker/talkers/comicvine.py` directly). A Processing-folder
  batch run on the shared key would stall for hours.
  **Save behaviour:** a **"Save & Test"** button, not auto-save and not a bare
  manual Save — the one deliberate exception to this page's auto-save convention.
  Clicking it always persists whatever's typed to `config.json` immediately, then
  separately calls CT's own `comicvine.py::check_status()` (hits ComicVine's
  `team/1/` endpoint, detects the "Invalid API Key" error) and shows the result as
  pass/fail feedback next to the field — the test does not gate the save, since
  losing a just-typed key to a timed-out test call would be worse than saving a
  key that turns out to be wrong and is easy to re-edit.
- Uses the same shared, router-independent series/issue-search backend function
  as the Full Editor's Search Online button (`EDITOR_SPEC.md` §9.1) — one codepath
  hitting ComicVine, not two.
- Backup model: **does not apply.** This stage only adds/writes XML inside the
  existing archive via the editor core's rebuild path (`EDITOR_SPEC.md` §3.2) — no
  separate output file, no `.bak` to manage; 11.4.6's table is specific to Convert
  Archives/Convert Images' file-replacement model and doesn't extend here.

**Convert Images:**

- Toggle: enabled/disabled (`processing_folder_convert_images_enabled`)
- Quality: lossless toggle or quality slider (default 95) —
  (`processing_folder_convert_images_lossless`, `processing_folder_convert_images_quality`)
  — same options as 11.3.3. Applied batch-wide.
- Backup model: see 11.4.6.

#### 11.4.5 Schedule

- **Options:** Off, Daily (at a configured wall-clock time HH:MM), Weekly (on a
  configured day of the week at a configured HH:MM). Persisted in `config.json` as
  `processing_folder_schedule` (`"off"` / `"daily"` / `"weekly"`),
  `processing_folder_schedule_time` (`"HH:MM"`),
  `processing_folder_schedule_day` (0–6, Monday–Sunday, weekly only).
- **Implementation:** new `processing_folder_loop()` async task in `scheduler.py`,
  registered in `main.py`'s `lifespan` alongside `auto_scan_loop` and `backup_loop`.
  Unlike those two (which use elapsed-time polling), this loop uses **wall-clock
  scheduling**: on each poll cycle it computes the next scheduled run datetime from
  the configured day/time and fires when `now >= next_run`. `next_processing_run` is
  persisted in `config.json` so a server restart does not lose the scheduled time or
  cause a missed run to fire immediately on restart.
- **If a run is already in progress** when the scheduled time arrives: log and skip
  this cycle — same guard as `auto_scan_loop`'s "scan already running" check.
- **Verified 2026-07-02** — investigated a report that scheduled runs weren't firing
  (Weekly, day matching today, time a few minutes out; manual Run Now worked fine).
  Live-reproduced three times against a running server: Daily, Weekly+today's
  weekday, and again via the actual admin UI Save button — all three fired exactly
  on time and correctly rolled `next_processing_run` forward afterward (Daily → next
  day, Weekly → next occurrence of the same weekday). The wall-clock mechanism has
  no bug. The reported non-firing traced to the **Schedule dropdown being left on
  "Off"** while Day/Time were the only fields actually changed — the loop's first
  check (`if schedule not in ("daily","weekly"): continue`) means Day/Time are
  irrelevant whenever Schedule reads Off, matching "Run Now works, scheduled
  doesn't" exactly. At the time, Schedule/Time/Day required a separate explicit
  **Save** click with no "unsaved changes" indicator, unlike every other Processing
  Folder Automation setting on the page — flagged as a `ROADMAP.md` candidate.
- **Fixed 2026-07-19** — Schedule/Time/Day now auto-save on `change`, same as every
  other control on this page (`frontend/js/processingTools.js`'s `saveSchedule()`,
  reusing `savePfSetting()`); the separate Save button was removed. The Day dropdown
  is also now disabled unless Schedule is Weekly, and the Time field is disabled
  when Schedule is Off — `updatePfScheduleFieldStates()`, called on load and on every
  Schedule change — so a field that doesn't apply to the current Schedule value can't
  be edited in the first place, closing off the exact confusion the 2026-07-02
  investigation traced the false-alarm report to.

#### 11.4.6 Unified Backup Model

**Cross-cutting change — written into §11.2 2026-07-01.** §11.3 already matched
this model from its own original scoping; §11.2 was amended to match on the
same date (see that section's 2026-07-01 notes and the Change Log entry below).

The backup policy agreed during Item 15 scoping replaces §11.3's "permanent `.bak`,
never auto-deleted" rationale and §11.2's "Delete Original" checkbox. The unified
model applies to both tools, whether triggered manually or by the automation pipeline:

| Outcome | `.bak` disposition |
|---|---|
| **Clean success** — validated, `pages_skipped = 0` and `images_skipped = 0` | `.bak` is **auto-deleted** |
| **Success with warnings** — validated, but `pages_skipped > 0` or `images_skipped > 0` | `.bak` is **kept permanently** — content was lost in conversion; the original is the only recovery path |
| **Failure** — validation failed or conversion errored | No `.bak` was created; original file is **completely untouched** |

**Why success-with-warnings keeps the `.bak`:** a skipped page or image means the
output is degraded relative to the original. The user may not notice immediately —
particularly in an unattended automation run — and the `.bak` is the only way to
recover the missing content. The cost of a stale `.bak` is a few MB of disk space;
the cost of losing it is unrecoverable.

**§11.2 amendment:** the "Delete Original File" checkbox (11.2.3) is **removed
entirely** — superseded by this model. The "Output file already exists" guard
(11.2.4) becomes "refuse if `.bak` already exists for this file," consistent with
§11.3's existing guard. Both amendments to be written into §11.2 during the
re-scoping session.

**Known limitation:** validation confirms the output opens as a valid archive and
that its entry count matches the expected count (accounting for any skipped items),
but cannot verify visual quality — a WebP conversion could pass validation while
producing visually degraded output. Accepted limitation for both manual and automated
use; noted here for public-release awareness.

#### 11.4.7 Run Now

- Single "Run Now" button — starts the full pipeline immediately using all currently
  enabled stages and the current folder and settings.
- Disabled while any pipeline run is in progress (scheduled or manual).
- Does not affect `next_processing_run` — the scheduled cadence is unchanged.
- Available regardless of whether a schedule is configured (works with schedule set
  to "Off").

#### 11.4.8 Progress & Status

- New `processing_folder_progress` singleton tracking overall pipeline state:
  `running`, `current_stage` (`convert_archives` / `ct_autotag` / `convert_images`),
  and `stage_results` (accumulating per-stage summary).
- The active stage's own progress singleton (`convert_progress`, a new
  `ct_autotag_progress`, `convert_images_progress`) drives the per-file detail
  within each stage — the pipeline does not duplicate that tracking.
- `POST /api/admin/processing-folder/run` — starts the pipeline via `BackgroundTasks`,
  returns immediately.
- `GET /api/admin/processing-folder/status` — polled by the frontend, returns pipeline
  state including current stage, the active stage's per-file progress, and completed
  stage summaries.
- On completion: summary per stage — "Converted X of Y archives", "Tagged X of Y
  files, Z flagged for review", "Converted images in X of Y files" — with per-file
  detail expandable for each stage. Failed files per stage are listed for manual
  follow-up; no automatic retry.

#### 11.4.9 Audit Logs

Each tool's own log captures its entries regardless of trigger source, distinguished
by an `[AUTO]` prefix on log lines produced by the automation pipeline vs. the plain
format used by manual runs:

```
DD/MM/YYYY HH:MM — [AUTO] filename.cbr → filename.cbz [OK]
DD/MM/YYYY HH:MM — [AUTO] filename.cbz [tagged: confident] "Series Name" #12 (2019)
DD/MM/YYYY HH:MM — [AUTO] filename.cbz [tagged: low confidence, NeedsReview set] "Series Name" #12 (2019)
DD/MM/YYYY HH:MM — [AUTO] filename.cbz [skipped: low confidence, Save on Low Confidence off]
DD/MM/YYYY HH:MM — [AUTO] filename.cbz [OK, 3 images skipped] (backed up to filename.cbz.bak)
```

**CT Auto-Tag gets its own new `ct_autotag_log.md`**, same `[AUTO]`-prefix convention
as the other two, rather than folding into either existing log — it isn't a
variant of Convert Archives or Convert Images, distinct enough (confidence outcome,
not a file-format transform) to warrant its own file. Manual, one-file-at-a-time
matches (Full Editor's Search Online, `EDITOR_SPEC.md` §9) are still **not** logged
here — that's an interactive action, not a batch run.

**v2.6 Item 1 Phase C2b (2026-07-07):** `ct_autotag_log.md` is no longer
automation-only. XML Tagging (§11.6) is a second, manual batch-run trigger for
this same log — its lines carry no `[AUTO]` prefix, distinguishing them from
Processing Folder Automation's runs in the same file. `ct_autotag_log.py`'s
`append_entry()` gained an `auto: bool = False` parameter, matching
`convert_log.py`/`convert_images_log.py`'s existing convention — this
subsection's log-format description above is otherwise unchanged.

Manual Convert Archives/Convert Images runs continue to use the existing untagged
format (11.2.6, 11.3.7). `rename_log.md` (11.1.7) never carries an `[AUTO]` line —
Rename isn't triggered by automation. This keeps the existing logs as the single
source of truth for their respective tools while still making automation runs
distinguishable in review.

**Aggregate audit-run summary** ("12 converted, 11 confident, 1 flagged") — confirmed
wanted (`DECISIONS.md`, session 1) but still explicitly deferred, not part of this
build. Would sit alongside these per-tool logs as a run-level rollup, not replace
them.

#### 11.4.10 Implementation Notes (for Code)

Not binding design, but worth flagging before the build session:

- New backend router `backend/routers/processing_folder.py` — run endpoint, status
  endpoint, and settings persistence (read/write `config.json` keys listed in
  11.4.4–11.4.5).
- New `processing_folder_loop()` in `scheduler.py` alongside `auto_scan_loop` and
  `backup_loop`; registered in `main.py`'s `lifespan` startup block. Wall-clock
  scheduling: compute `next_run` from configured day/time on startup and after each
  completed run; persist to `config.json`; on each 60s poll check `now >= next_run`.
- New `processing_folder_progress` singleton — own module or top of
  `backend/routers/processing_folder.py`; not shared with the per-tool singletons.
- All three tool callables — Convert Archives, CT Auto-Tag, Convert Images — are
  invoked **directly** (not via HTTP), same "plain, router-independent callable"
  requirement 11.3.8 specified. CT Auto-Tag's callable is also shared with the Full
  Editor's Search Online endpoint (`EDITOR_SPEC.md` §9.1/§9.4) — one function, two
  callers, not a duplicate implementation on each side.
- The picker/folder-selection endpoint is the **fifth** near-identical in-app picker
  implementation. The shared-component refactor flagged in 11.1.8 and 11.2.7 should
  be treated as a hard prerequisite for this item's build, not optional cleanup — five
  near-identical implementations is the point where duplication meaningfully raises
  maintenance risk.
- `config.json` gains the keys listed in 11.4.4–11.4.5, including
  `processing_folder_ct_autotag_enabled`, `processing_folder_ct_save_low_confidence`,
  and `comicvine_api_key`. No schema migration needed (config is a plain JSON file,
  not the SQLite DB) — new keys default to `"off"` / `false` / `""` on first read,
  same pattern as existing optional config keys.
- New `COMICINFO_TAGS` entry for `NeedsReview` (`backend/editor/xml_parser.py`) is a
  shared prerequisite with `EDITOR_SPEC.md` §9.2 — build once, used by both this
  stage (writes it) and the Full Editor (reads/clears it).

---

### 11.5 Sort by Filename

**Built and manually tested 2026-07-05 — `comicvault-changes-v2.5.md` Item 2.**

Ported from the standalone `create-folders-from-file.py` script. For every CBZ/CBR
file found directly inside a chosen folder, moves it into a new subfolder named
after its own filename with the extension stripped — e.g. `Batman 001.cbz` moves
into `Batman 001\Batman 001.cbz`.

#### 11.5.1 Scope

- **CBZ/CBR only, by extension.** Every other file in the folder — `Thumbs.db`,
  `desktop.ini`, `.bak` files, anything else — is left exactly where it is, not
  folderized. This is a plain extension check, not the content-sniffing
  `detect_archive_format()` other Processing Tools use (§11.2/§11.3) — deliberately
  simpler scope, since this tool only ever moves a file and never opens its
  contents. `.bak` handling is deferred along with §11.2's — not a concern today
  since a `.bak` file never matches the CBZ/CBR extension filter anyway.
- **No recursion.** Only files directly inside the chosen folder are considered.
- Same pre-ingest/staging positioning as §11.1–§11.4. Not restricted to any specific
  folder; not a library-wide bulk tool. No library scan is triggered, no DB write.
- Same local-only gating as all Processing Tools (§11 shared notes).
- **Not part of Processing Folder Automation (§11.4).** Scheduling/pipeline wiring
  is explicitly deferred, not built here (see Change Log) — the `[AUTO]`-log-prefix
  plumbing is already in place for when that lands.

#### 11.5.2 Folder Selection

Single folder selection — same in-app folder-tree picker as §11.1–§11.4 (no native
OS dialog, no `library_root` restriction, Up climbs to a drive-letter list, no
recursion). **Not persisted to `config.json`** — unlike §11.4's Processing Folder,
this tool has no schedule to persist a folder for; the chosen folder lives only in
the admin page's own state until Run is clicked.

#### 11.5.3 Collision Rules

Every file is attempted independently — one file's failure doesn't block any other:

- **Same-basename pair** (e.g. a CBZ+CBR pair sharing a filename) — both move into
  the same folder, no error. The second file's target folder already exists
  (created moving the first) and contains only its own sibling, which isn't treated
  as a conflict.
- **Target folder already exists and holds an unrelated file** (anything whose own
  basename doesn't match the folder name — e.g. a pre-existing folder with some
  other file already in it) — that one file fails with a clear reason
  (`'<folder>' already contains an unrelated file: '<name>'`) rather than being
  dropped in alongside content it doesn't belong with. The file stays in place,
  unmoved.
- **Destination path already occupied** (the exact same filename already sitting in
  the target folder — a re-run scenario) — fails with a clear reason rather than
  silently overwriting.
- **Folder not found / unreachable path** — clean error returned immediately, no
  files attempted, nothing logged as a run.

#### 11.5.4 Run & Result

Single "Run" button — background job + polling progress, same `running`-boolean
guard pattern as §11.4's `processing_folder_progress` (a second Run is rejected
outright while one's in flight; same "reflects actual current state, callers must
check `started` not `running`" contract as the other tools). On completion, a
terse one-line result: `✅ Sorted N files into M folders`, or `⚠️ Sorted N of M
files into K folders — J failed` with an expandable Details list of the per-file
failure reasons, or `❌ Failed: <reason>` for a folder-level failure (not found /
unreachable). No summary modal (§11.1–§11.3's shared `ptSummaryOverlay`) — the
terse inline line plus expandable detail was judged sufficient for a
single-folder, no-preview tool with only one input.

#### 11.5.5 Audit Log

New `filename_sort_log.md` in `/logs/`, same append-only/1MB-cap pattern as the
other three tools' logs:

```
DD/MM/YYYY HH:MM — old_filename.ext → new_folder\old_filename.ext [OK]
DD/MM/YYYY HH:MM — old_filename.ext → FAILED: <reason>
```

`[AUTO]`-prefix support is wired in now (matches `convert_log.py`'s convention)
even though nothing calls it with `auto=True` yet — cheap to add alongside the
tool itself, saves a second pass once automation wiring (deferred, 11.5.1) is
scoped.

#### 11.5.6 Implementation Notes (for Code)

- `backend/filename_sort.py` — `sort_by_filename(folder: str) -> FilenameSortResult`,
  a plain, router-independent callable (same requirement as every other tool's core
  logic, §11.3.8/§11.4.10) — pure filesystem logic, no logging, no router concerns.
- `backend/filename_sort_log.py` — thin wrapper over `tool_logs.py`, parallel to
  `convert_log.py`.
- `backend/routers/filename_sort.py` — `browse`/`drives` (shared `file_picker.py`),
  `run`/`status` mirroring `processing_folder.py`'s shape. No working-file-list
  endpoints — the folder itself is the only input, there's nothing to stage.
- Script name shown as a disabled single-option `<select>` in the admin card rather
  than a plain label — deliberately the **only** script today (per the build
  brief), but a second script (a move-to-library tool, not yet written) is
  expected eventually, at which point this becomes a real dropdown with minimal
  rework.

---

### 11.6 XML Tagging

**Built and manually tested 2026-07-07 — v2.6 Item 1 Phase C2b.**

A standalone, single-folder run of the same CT Auto-Tag matching engine
§11.4's Processing Folder Automation uses (`backend/ct_autotag.py`'s
`ct_autotag_file()`) — pick any folder, run it once, see the result. Added
because `New Admin Layout.md` (the source doc for `admin.jsx`'s Processing
Tools categories) lists it as its own tool, separate from Auto Processing,
and Tez confirmed it's genuinely new functionality, not just a settings
relocation.

#### 11.6.1 Scope

- Folder picker (`mode: 'folder'`, same shared picker every other Processing
  Tool uses) — no working-file-list, the folder itself is the only input,
  same shape as §11.5's Folder Processing.
- Iterates CBZ/CBR files directly inside the folder (`.bak` excluded, same
  filter §11.4's `_ct_taggable_files()` uses), calling `ct_autotag_file()`
  per file exactly as the automation stage does.
- **No new settings of its own.** Match Ratio Threshold, Save on Low
  Confidence, and the ComicVine API Key + Save & Test button physically live
  in this pane (moved out of §11.4's, per Tez's direction) but read/write the
  **same** `config.json` keys (`processing_folder_ct_match_threshold`,
  `processing_folder_ct_save_low_confidence`, `comicvine_api_key`) and the
  **same** existing endpoints (`/api/admin/processing-folder/config`,
  `/api/admin/processing-folder/comicvine-key/test`) Auto Processing already
  used — shared, not duplicated. `ct_bridge.identify_file()` already reads
  `processing_folder_ct_match_threshold` straight from `get_config()`
  itself, so the threshold needs no explicit pass-through at all.

#### 11.6.2 Run & Result

- Single "Run" button, background task + polled `/status`, same
  running/result/error/finished_at shape as §11.5's Folder Processing.
- Result summary: counts of tagged / no match / low confidence skipped /
  failed (of total), with per-file failure detail expandable — mirrors the
  aggregate line Processing Folder Automation's status poll already builds
  for its own CT Auto-Tag stage (`PF_STAGE_LABELS`/`pollPfStatus()` in
  `frontend/js/processingTools.js`).

#### 11.6.3 Audit Log

Shares `ct_autotag_log.md` with Processing Folder Automation's CT Auto-Tag
stage (§11.4.9) — logs here carry **no** `[AUTO]` prefix, distinguishing a
manual XML Tagging run from an automation run in the same file. See
§11.4.9's Phase C2b note for the `append_entry(..., auto: bool = False)`
signature change this required.

#### 11.6.4 Implementation Notes (for Code)

- `backend/routers/xml_tagging.py` — new router, modeled directly on
  `backend/routers/filename_sort.py`'s shape (`browse`/`drives`/`run`/
  `status`, own progress dataclass singleton). No new config or
  ComicVine-key-test endpoints — the frontend pane calls
  `processing_folder.py`'s existing ones directly.
- `_taggable_files()` (CBZ/CBR minus `.bak`) is duplicated locally in
  `xml_tagging.py` rather than imported from `processing_folder.py`'s
  private `_ct_taggable_files()` — keeps the router independent, matching
  `filename_sort.py`'s existing precedent of not importing from
  `processing_folder.py`.
- Registered in `main.py` under `/api/admin` with the same `_auth_gate`
  dependency as every other Processing Tool router.
- Frontend: the three relocated field-rows (`pfCtSaveLowConfidence`,
  `pfCtMatchThreshold`, `pfComicVineKey`/`pfComicVineKeyTestBtn`/
  `pfComicVineKeyResult`) kept their exact IDs when moved — `admin.js`'s
  `loadProcessingFolderConfig()`/`initProcessingFolderTool()` needed zero
  changes, they already bind via `getElementById` regardless of where in
  the DOM the elements physically sit.

---

### 11.7 Move Series Folders / Move Singles Folders

**Built and manually tested 2026-07-18 — v2.6 Item 10.**

Two scripts, ported in as standalone tools sharing §11.5's Folder Processing
card and picker. The final stage of processing before a library scan: moves
folders out of `Processing\Stage 3\series` / `\singles` (or any chosen
folder — not restricted to Stage 3) into their correct place in the library
structure per `SPEC.md` §5.

#### 11.7.1 Scope

- Operates on every **immediate subfolder** of the chosen folder — each one
  treated as a series (or singles title) folder to file. No recursion past
  that first level for deciding *what* to move; the merge itself (11.7.3)
  can recurse further once a match is found.
- Same picker as every other Processing Tool — not restricted to
  `library_root`, fully browsable, no persistence to `config.json` (matches
  §11.5.2's rationale: nothing to persist a folder for, chosen fresh each
  run).
- Same local-only gating as all Processing Tools (§11 shared notes). Not
  part of Processing Folder Automation (§11.4) — manual, on-demand only.

#### 11.7.2 Alpha Bucket

A leading `The `/`A `/`An ` (case-insensitive) is stripped before bucketing
— matches how the library is actually filed (`The 13th Artifact` → `#`, `A
Taste for Blood` → `T`), not a literal first-character rule, which would
contradict both `SPEC.md` §5's own examples and most of the existing
library. After stripping: `A`–`Z` → that letter; a digit, apostrophe, or any
other character → `#`.

**Known gap, not fixed here:** some existing folders are filed by subject
rather than by this rule — e.g. `The Complete Terminal City` sits under `T`
(matching `The Complete Bad Company` under `B`), not `C`. The article-strip
rule alone would send new folders shaped like this to the wrong bucket
relative to that existing convention. Near-miss detection (11.7.4) is the
mitigation — it flags the mismatch for a human decision rather than silently
filing it "correctly" by the mechanical rule.

#### 11.7.3 Collision Rules

Every folder is attempted independently — one failure doesn't block any
other:

- **Series, destination doesn't exist** — moves the whole folder over as a
  new addition (alpha/format-group levels created as needed).
- **Series, destination exists** — merges rather than failing.
  **Recursive and purely structural, no name-based special-casing:** for
  each entry in the source folder, a same-named file at the destination
  fails that one file only (everything else in the batch still attempted);
  a same-named *folder* at the destination is merged into one level
  deeper, recursively, rather than failing outright. This is what makes a
  container-style series (one grouped into sub-folders — a series's issues
  never sitting directly in its own top folder, e.g. one grouped by year)
  merge correctly at whatever depth it already exists in the library,
  without the mover needing to know anything about that series by name.
  Source folder (and any subfolder emptied by the recursion) is removed
  only if left empty — a folder holding even one failed file stays in
  place so the failure is visible, not silently half-cleared.
- **Singles, destination exists** — fails the whole folder outright, stays
  in Stage 3 untouched. Singles are one-CBZ-per-folder by definition, so a
  name collision here means an actual duplicate, not something to merge.
- **Source folder not found / unreachable** — clean top-level error, no
  folders attempted, nothing logged as a run.

**2000 AD needed no special-casing.** Scoped mid-build with a hardcoded
root-level exception in mind (`20000AD` sat outside the A–Z/`#` scheme
entirely, at the time holding everything from progs to megazines to
one-shots). Tez restructured the actual folder instead — renamed to
`2000 AD`, moved under `#\Series\2000 AD`, `2000 AD - YYYY` sub-folders kept
as-is — so it now buckets and files under the ordinary rule like everything
else, and the recursive merge above is what makes moving new `2000 AD -
YYYY` content into it work correctly. See `DECISIONS.md`.

#### 11.7.4 Exact-Duplicate Blocking and Near-Miss Warnings

Two tiers, both checked library-wide within the target format group (not
just the computed destination's own alpha bucket):

- **Exact duplicate (blocking).** A folder name that normalizes identically
  to an existing library folder — same letters/digits once the year suffix
  and all punctuation are stripped, regardless of bracket style — is a
  confident match, not a maybe. Found because Tez flagged that older
  library folders use `Title [YYYY]` where newer Stage 3 output uses `Title
  (YYYY)`; an unprocessed folder under the new convention could otherwise
  duplicate an existing one under the old convention. The move is blocked
  entirely: nothing moves, the folder stays exactly where it is, and it's
  logged as a failure naming the exact existing path it matched. Applies to
  both Series and Singles.
- **Near-miss (warning only, non-blocking).** Everything else — a folder
  that looks like a *probable* variant of an existing one, by similarity
  ratio or substring containment, but isn't a confident match — is reported
  in the result detail and the log, but still moves normally. This is what
  catches cases like `Judge Dredd Megazine` against an existing `2000 AD -
  Judge Dredd Megazines`, or the `The Complete Terminal City` filing gap
  noted in 11.7.2.

#### 11.7.5 Run & Result

Same shared shape as §11.5.4: single "Run" button, background job + polling
progress, one `running`-boolean-guarded progress singleton per script
(Series and Singles can't collide on state, but two Series runs — or two
Singles runs — against the same script still can't overlap). Terse one-line
result (`✅ Moved N of M folders` / `⚠️ Moved N of M — J failed`) with an
expandable Details list combining per-folder failure reasons and any
near-miss warnings.

#### 11.7.6 Audit Log

Two new logs, `series_move_log.md` / `singles_move_log.md`, same append-
only/1MB-cap pattern as every other Processing Tool log. `[AUTO]`-prefix
support wired in now, unused — same rationale as §11.5.5.

#### 11.7.7 Implementation Notes (for Code)

- `backend/library_move.py` — `move_folders(folder, group) ->
  LibraryMoveResult`, `group` is `"series"` or `"singles"`. Plain,
  router-independent callable (same requirement as every Processing Tool's
  core logic). **Also runnable standalone from a terminal** — `python -m
  backend.library_move series|singles <folder>` — per the brief that these
  are ported-in scripts, not admin-page-only functionality.
- **DB sync (defensive, usually a no-op):** `library_move.py` also has
  `sync_moved_paths_to_db(db, result)`, called by the router right after
  `move_folders()` returns. For every successfully-moved folder, it rewrites
  any `Issue.file_path` / `CustomTab.folder_path` / `HomeStrip.folder_path`
  row whose path was under the folder's old location, committing per folder
  so a blocked/failed folder's rows are never touched. In the tool's normal,
  intended use — a Stage 3 Processing folder (scan-excluded, never scanned
  before the move) — no such row exists yet, so this is a no-op; the
  subsequent manual Scan discovers the moved content fresh. It only does real
  work if the tool is pointed at content that's already inside the library
  and already scanned (BUG-025 — see `docs/DECISIONS.md` and
  `docs/archive/bugs-fixed-archive.md`) — not the tool's designed use, but
  the sync keeps that case from silently breaking anyway.
- `backend/series_move_log.py` / `backend/singles_move_log.py` — thin
  `tool_logs.py` wrappers, parallel to `filename_sort_log.py`. `append_entry()`
  also takes `issues_updated`/`db_sync_error` from the sync step above — an
  `[OK]` line shows `N issue(s) re-pointed` when non-zero, or a distinct
  `[OK, DB SYNC FAILED — rescan and check logs]` suffix if the sync itself
  failed (kept separate from a real disk-move `FAILED:` line).
- `backend/routers/library_move.py` — `browse`/`drives` (shared
  `file_picker.py`), `run`/`status` mirroring `filename_sort.py`'s shape,
  `group` passed in the run payload and as a query param on `/status`
  (`library_move_progress` is a dict keyed by group, not a single
  singleton — this is the one structural difference from §11.5's router).
- Frontend: `fsScriptSelect` (previously a disabled single-option
  `<select>`, per §11.5.6's anticipation) is now a live 3-option dropdown.
  `processingTools.js`'s `FS_SCRIPTS` map holds each script's endpoints/
  labels; `runFilenameSort()`/`pollFsStatus()` dispatch off the selected
  option and branch on result shape (`'files' in status.result` for Sort by
  Filename vs. the `folders`/`near_misses` shape for these two).

---

## 12. Change Log

> Record any deviations from this spec here with date and reason.

| Date | Change | Reason |
|---|---|---|
| 2026-07-18 | §7.4 — Clear Database now documents the full reset scope (thumbnails, scan logs, `log_last_viewed`/`next_processing_run`) and the restart-after-clear mechanism (`checkpoint_wal()` → `engine.dispose()` → VACUUM → sidecar delete → `_schedule_delayed_exit()`), reusing §9.2's Restore Database pattern. | BUG-026/BUG-027 fixed — Clear Database left orphaned thumbnails/DB bloat and had no safe reset path since the Admin page and the DB-holding process are the same process; see `docs/DECISIONS.md` and `docs/archive/bugs-fixed-archive.md`. |
| 2026-07-18 | §9.2 — Restore Database mechanism now documents the WAL-checkpoint + engine-dispose + sidecar-delete step (new step 2) that runs before the file copy, and notes `run_database_backup()` also checkpoints before its own copy. Status block corrected: Item 12 restore no longer marked failing. | BUG-016 fixed — restore was silently failing to revert DB state due to WAL replay; see `docs/DECISIONS.md` and `docs/archive/bugs-fixed-archive.md`. |
| 2026-07-18 | §11.7.7 — noted the defensive `sync_moved_paths_to_db()` DB-sync step and its `issues_updated`/`db_sync_error` log fields. | BUG-025 follow-up: re-diagnosed as not-a-bug in the tool's intended Processing→Library workflow, but the sync fix was kept as a safety net for the atypical already-in-library-content case that originally triggered it — see `docs/DECISIONS.md` and `docs/archive/bugs-fixed-archive.md`. |
| 2026-06-27 | Added §11 Processing Tools (new top-level section) and §11.1 File Rename — full scope, picker behaviour, checkbox model, live preview, error handling, and audit log design. Ported from CAPT's standalone File Renamer per `ROADMAP.md`'s "CAPT extra tools" entry, brought in one tool at a time starting with Rename. | Dedicated scoping session 2026-06-27 — CAPT source code and `Processing/` folder structure inspected directly to ground design decisions. |
| 2026-06-30 | Added §11.2 Convert Archives — full scope. Only CBR→CBZ and PDF→CBZ ported (CBZ→CBR/CBZ→PDF dropped, per Item 5's CBR-native-read and PDF-dropped-from-scanner resolutions). Content-based From-format filtering in the picker, `PDF_RENDER_DPI = 300` isolated constant (replaces CAPT's 72 DPI default), CBR CRC errors now surfaced as a `pages_skipped` warning instead of silently dropped, background-job + polling progress modelled on `backend/scanner.py`'s existing `scan_progress` pattern (not a blocking request like Rename), own `convert_log.md` audit log. | v2.4 Item 6 — dedicated scoping session 2026-06-30, CAPT source (`arc_convert_worker.py`, `arc_conv_cb_proc.py`, `arc_conv_pdf_proc.py`, `arc_conv_helpers.py`, `arc_convert_util.py`) and `backend/scanner.py` inspected directly to ground design decisions. |
| 2026-06-30 | Added §11.3 Convert Images — full scope. Pre-ingest staging only (not library-wide). CBZ and CBR both accepted as input; CBR images convert but the archive always rebuilds as `.cbz` (CAPT's `rar`-CLI CBR repack dropped entirely — same WinRAR-dependency problem already ruled out for §11.2). User-facing lossless/quality-slider setting replaces CAPT's undocumented hardcoded `quality=95`. Flatten-on-rebuild reuses the Editor's existing `_rebuild_archive` flatten logic rather than CAPT's separate implementation. New backup model: rebuilt archive validated before replacing, original kept as a permanent `.bak` (never auto-deleted) — raised by Tez because a future, separately-scoped Auto Processing Folder feature will run this same conversion unattended on watched-folder files, where a silent bad conversion with no kept original could go unnoticed. Core conversion logic specified as a router-independent callable for that same future reuse. Background-job + polling progress (own `convert_images_progress` singleton), own `convert_images_log.md` audit log. | v2.4 Item 7 — dedicated scoping session 2026-06-30, CAPT source (`convert_images_window.py`, `utils/convert_images.py`, `widgets/file_management_widget.py`) and `backend/editor/archive_io.py` inspected directly to ground design decisions. |
| 2026-07-01 | Added §11.4 Processing Folder Automation — full scope. Scheduler + Run Now model (file-system watcher rejected — debounce/queue/restart-survival complexity not justified for a personal batch-staging workflow). Single unified pipeline: Convert Archives → Convert Images → Rename, fixed order, independently toggleable. One schedule for the whole pipeline (daily or weekly at a configured wall-clock time), not per-tool schedules. New wall-clock `processing_folder_loop()` in `scheduler.py` (differs from `auto_scan_loop`'s elapsed-time model). Unified backup model agreed: clean success = auto-delete `.bak`; success-with-warnings = keep `.bak`; failure = original untouched. This replaces §11.2's "Delete Original" checkbox and §11.3's "permanent `.bak`, never auto-deleted" policy — both marked ⚠️ for amendment in the re-scoping session. §11.1 Rename also flagged for re-scoping: the CAPT-port model (four fields + checkboxes) is insufficient for automation; needs a template-based naming convention system with save/load, to be expanded before Item 10 is built. `[AUTO]` prefix on log lines distinguishes automation runs from manual runs across all three existing audit logs — no new log file. Shared picker refactor (now fifth duplication) promoted from optional cleanup to hard prerequisite for this item's build. | v2.4 Item 15 — dedicated scoping session 2026-07-01. `backend/scheduler.py` and `backend/main.py` inspected directly to ground scheduling design. File-watcher vs. scheduler trade-off evaluated, file-watcher rejected. Backup model unified across §11.2 and §11.3 as a cross-cutting decision surfaced by this item. §11.1 rename-tool re-scope need surfaced when evaluating what "automation-safe rename" actually requires. |
| 2026-07-01 | §11.1 File Rename re-scoped and §11.4 amended. Three parser bugs found and fixed: hardcoded `present_year = 2025` ceiling in `extract_year()` was silently breaking 64% of a real 323-file sample (every 2026-dated file, cascading into series/issue extraction too) — fixed to compute the ceiling dynamically; `"000"`-style zero-issue numbers were stripped to an empty string — fixed; volume/subtitle patterns (`v05 - Subtitle`) left double-space/dangling-dash artifacts — fixed. Output separator decided: `Series - Title #Issue (Year)`, dash-joined, no auto-splitting of Series/Title. One-shot/OGN handling confirmed: no issue segment when no number is found. **Also decided: Rename is dropped from Processing Folder Automation entirely** — its live-preview review is its only correction mechanism (no undo), which unattended automation removes, and the ambiguous-split cases specifically need a human decision automation can't supply. §11.4 amended to a two-stage pipeline (Convert Archives → Convert Images); Rename's toggle, config keys, and the saved-naming-convention-template requirement are dropped, not deferred. | v2.4 Item 10 re-scope + Item 15 amendment — dedicated session 2026-07-01, sample-tested against two real filename sets (323 periodical-style, 319 creator-prefixed OGN/collection) before any decision was made. |
| 2026-07-01 | §11.2 Convert Archives amended to match the unified backup model. "Delete Original File" checkbox removed entirely. Backup handling moved to a new "Backup & Safety" bullet mirroring §11.3's — stage, validate, rename original to `.bak`, then clean-success auto-delete / warnings keep permanently / failure leaves original untouched (full table: §11.4.6). The old "Output file already exists" collision guard replaced with "refuse if `.bak` already exists" (matches §11.3). Audit-log sample updated to show a retained-`.bak` note on warnings and the new failure wording. Gained the explicit "plain, router-independent callable" requirement already specified for §11.3, confirming Item 15/16 can invoke Convert Archives directly. | v2.4 sanity-check pass ahead of handing the CAPT cluster to Code — this amendment was agreed during Item 15 scoping (previous row, same date) and flagged as outstanding, but never actually written into §11.2 until now. |
| 2026-06-23 | `ADMIN_SPEC.md` created — consolidates `SPEC.md` §11 and §20.13's admin descriptions plus all new admin items scoped in the 2026-06-23 inbox triage session. `SPEC.md` §11/§20.13 are superseded by this file for admin-page specifics. | Inbox triage 2026-06-23; EDITOR_SPEC.md precedent for a standalone admin spec. |
| 2026-06-24 | §7.1 and §7.2 stubs replaced with full design: scope expanded to cover `/editor` and all `/api/admin/*` + `/api/editor/*` endpoints (not just `/admin`); local-only security boundary; stateless signed-cookie session; brute-force lockout; sliding expiry; no-built forgot-password recovery; §7.2 remote toggle dependency tightened. §1 Access gate wording updated to point at §7.1, drop §5.1 reference and "deferred to V2" framing. | Design session 2026-06-24; `comicvault-changes-v2.3.md` Item 6 updated to pointer-only. |
| 2026-06-26 | Post-test fix pass (`docs/2.3-fixes.md`, Fixes 4–9): §7.1.2/§7.1.5 — login popup gated to protected pages only, auth button always visible with Login/Logout label, new no-password-set explanation dialog; §7.1.1 — disabling password protection now requires re-entering the current password via an inline confirm row; §4 — Last Scan card falls back to the persisted log on server restart instead of showing "Never"; §8 — changed-files log now distinguishes "metadata updated" vs. "archive changed (pages: X → Y)"; §9 — new Last Backup indicator + scheduler failure surfacing in the Scheduled Backup block. | Manual test pass 2026-06-26 (`docs/2.3-testing-notes.md`) surfaced all six issues. |
| 2026-06-27 | Added §11 Processing Tools (new section, inserted before the Change Log, which shifts from §11 to §12) and §11.1 File Rename — full scope, picker behaviour, checkbox model, live preview, error handling, and audit log design. Ported from CAPT's standalone File Renamer per `ROADMAP.md`'s "CAPT extra tools" entry, brought in one tool at a time starting with Rename. | Dedicated scoping session 2026-06-27 — CAPT source code and `Processing/` folder structure inspected directly to ground design decisions. |
| 2026-06-27 | Status block corrected — removed stale "manual test pass remaining" (test pass completed 2026-06-26, see Fixes 1–9). §6 backfilled with the Card Size control (built v2.1, 2026-06-22) — never written into this doc when it was created 2026-06-23. Five new items (10–14) queued from inbox triage, noted in the status block. | Doc-consistency scan flagged ISSUE-007 (`doc-scan-issues.md`); extended into a full inbox triage session. |
| 2026-06-27 | §7.1.7 — built the Forgot-Password recovery popup (V2.3 Item 10): "Forgot Password?" button added to the Top Action Row, opens a modal with the manual `config.json` recovery steps. Replaces the prior "none built, defer to future User Guide" text. | `comicvault-changes-v2.3.md` Item 10. |
| 2026-06-27 | §9 — Scheduled Backup frequency dropdown cut from ~20 entries down to 6 (Off/day/week/month/6 months/1 year), V2.3 Item 11. Backend frequency map left untouched (still recognises old values). | `comicvault-changes-v2.3.md` Item 11; Tez's call, excessive list for a single-user home app. |
| 2026-06-27 | §9 renamed from "Scheduled Database Backup" to "Database Backup", split into §9.1 Scheduled Backup (unchanged content) and new §9.2 Restore Database (V2.3 Item 12) — native file picker, `pre-restore-{timestamp}.db` safety snapshot via a now-parameterised `run_database_backup()`, full server restart via a new shared `_schedule_delayed_exit()` helper. | `comicvault-changes-v2.3.md` Item 12. |
| 2026-06-27 | §6 — Card Size dropdown gains a 75% option (between 50% and 100%), V2.3 Item 13. `CARD_SIZE_PX` (`frontend/js/app.js`) maps it to `190px`. | `comicvault-changes-v2.3.md` Item 13. |
| 2026-07-01 | `admin-spec-section-12-processing-tools.md` folded into this file as §11 directly (§11.1-§11.4, renumbered from its standalone §12.1-§12.4), per the resolution plan in `INDEX.md` and the v2.4 build queue's Item 10 entry — the standalone file is retired. §11.1 File Rename built and manually tested (v2.4 Item 10): three filename-parser bugs fixed (dynamic year ceiling, zero-issue stripping, whitespace/dash collapse after token removal), output format `Series - Title #Issue (Year)`, shared in-app picker (`backend/file_picker.py`, `frontend/js/filePicker.js`) built as the foundation for §11.2-§11.4's pickers too. | v2.4 Item 10 build session. |
| 2026-07-02 | §11.1.5/§11.1.6 corrected: the 2026-07-01 build's implicit auto-accumulate-on-edit Preview model is replaced with an explicit **Add to Queue** step (Queued Files list doubles as the preview, new-filename-only per row) plus per-file queue removal. Manual testing against the original mockup (`Filename-Editor.pdf`) found the implicit model had no deliberate "add" gesture and no way to pull a single file back out short of clearing the whole list — a functional regression from what was actually intended, not a design choice. Frontend-only change (`frontend/js/processingTools.js`, `frontend/admin.html`, `frontend/css/style.css`); backend `/rename/preview` and `/rename/apply` unchanged. Layout also reshaped into the mockup's two-row grouping (toolbar + list + edit-panel on top, toolbar + list + batch-options below). | v2.4 Item 10 post-build manual test session, 2026-07-02 — Tez tested against `Filename-Editor.pdf`/`filename-editor-description.txt` and flagged the missing queue workflow. |
| 2026-07-02 | §11.1.2 amended, same-day follow-up: "Clear Loaded Files" renamed **Clear All** and now also resets the edit panel's field values/checkboxes (not just the file/queue lists), and Loaded Files rows gained a per-file remove control matching Queued Files'. | Tez follow-up request same session as the row above. |
| 2026-07-02 | §11.1.5 bug fix: Auto-Increment was sending one shared value set across the whole batch, which blanked Series/Title/Year on every file the moment Auto-Increment was checked (only the incremented `#N` survived in the output filename) instead of falling back to each file's own baseline/File override the way plain batch mode already did correctly. Fixed by routing Auto-Increment through the same per-file `computeRenameFileData` resolution as the rest of batch mode, with only the Issue value overridden per file using a frontend-computed sequential number. | Found by Tez testing against `L:\Comic Archives\Processing\Tagging Done` (Judge Dredd - Day of Chaos v01-03) — screenshots showed the wipe happening specifically when Auto-Increment was toggled on. |
| 2026-07-09 | §7.1.2 — added a "Cancel" button to the login popup (previously no way to dismiss it without entering a password) and compacted the shared `.login-modal` (60% narrower, consistent 10px inset), scoped so the larger Editor Basic/Full modals are unaffected. §4 — Last Scan card shows date only now (was full date+time, and the persisted-restart-survival fallback also showed `Duration:` since it reads the raw log line) — full detail unchanged in the log itself. | Tez's post-redesign UI tweak pass — see `docs/v2.6/progress.md` and `DECISIONS.md`. |
| 2026-07-03 | **§11.4 amended to a three-stage pipeline** — Convert Archives → **CT Auto-Tag (new)** → Convert Images (11.4.1/11.4.3). New CT Auto-Tag stage (11.4.4): enabled/disabled toggle, **Save on Low Confidence** toggle (ON writes best-guess tags + sets `NeedsReview`; OFF skips writing entirely for that file — a branch inside the stage, not a pipeline-flow change, since §11.4 is folder-level/not per-file chaining), and a `comicvine_api_key` field with a **"Save & Test"** button (the one deliberate exception to this page's auto-save convention — validates live via CT's own `check_status()`). Progress/status (11.4.8) and audit logging (11.4.9, new `ct_autotag_log.md`) extended for the third stage; aggregate audit-run summary re-confirmed as wanted but still deferred. Transcribed from `DECISIONS.md` (four 2026-07-03 entries) and `EDITOR_SPEC.md` §9 (the Full Editor side of the same feature) so Code has a build-ready spec on both sides. Also corrected this file's top-of-document status block, which had drifted stale — claimed §11.2–§11.4 were "build in progress (v2.4 Items 12, 13, 16)" when v2.4 had in fact already closed 2026-07-02 with all three built and verified. | v2.5 #1 — four ComicTagger integration scoping sessions 2026-07-03; this pass transcribes the locked decisions into the build-facing spec. |
| 2026-07-04 | **§11.4's CT Auto-Tag stage built and manually verified** (v2.5 Item 1) — see `docs/v2.5/progress.md` for the full narrative. Three real bugs found and fixed during Tez's own live testing: `identify_file()` fell back to filename parsing (via `backend/rename_tool.py`'s tested parser) and defaults the issue number to "1" for one-shots with none in the filename when an archive has no embedded XML, rather than short-circuiting to `no_match` immediately; match thresholds lowered from CT's own CLI defaults (90/91) to 80 to match what Tez had already found worked in his own standalone ComicTagger testing; the tagging write path now does a follow-up full single-issue fetch before mapping fields, since `IssueIdentifier`'s bulk candidate search doesn't carry credits (Writer/Penciller/etc. were silently empty without it). Also carries the same field-mapping-scope correction as `EDITOR_SPEC.md` §9's matching Change Log entry — the automation stage shares `ct_bridge.py`'s mapping function with Search Online, so both surfaces now capture the full CT/ComicVine field set the same way. | v2.5 Item 1 build + Tez's live-testing pass, 2026-07-03/04. |
| 2026-07-04 | **§11.4.4 gained a Match Ratio Threshold slider** (`processing_folder_ct_match_threshold`, default 80, 10–100% in 1% steps), placed after Save on Low Confidence — the previous session's 80% match threshold was hardcoded with no UI; added once Tez had more real-world match data to tune against. Every auto-save control in this section now shows a brief "Saved" toast (`savePfSetting()`) — none had any save confirmation before, ComicVine API Key's Save & Test excepted. **Bug fixed:** Processing Folder Automation's run-complete summary reported "N of M succeeded" by counting any non-`failed` status, which conflates a legitimate `no_match`/skipped-low-confidence outcome (correctly `success=True` — the stage didn't error) with an actual tag write; a 5-file test that tagged 4 and correctly no-matched the 5th reported as "5 of 5 succeeded". Fixed with a CT-Auto-Tag-specific summary breaking out tagged/no-match/skipped-low-confidence/failed counts (the underlying `ct_autotag_log.md` audit log was accurate throughout — UI-only bug). **v2.5 Item 1 closed** — Tez's deferred low-confidence real-world test (a 5-file standalone-ComicTagger-vs-ComicVault comparison) completed; investigated but did not conclusively resolve why the standalone app underperformed (1 of 5 tagged vs. ComicVault's 4 of 5) — not attributed to a ComicVault defect, full detail in `v2.5/progress.md`. | v2.5 Item 1 close-of-session, 2026-07-04. |
| 2026-07-05 | Added §11.5 Sort by Filename — full scope, ported from the standalone `create-folders-from-file.py` script. CBZ/CBR-only by extension (not content-sniffed, unlike §11.2/§11.3 — deliberately simpler since this tool never opens a file). Collision rules refined during build/testing beyond the original brief's literal reading: a same-basename CBZ+CBR pair sharing a target folder is not a conflict, but a target folder that already holds an *unrelated* file (different basename) fails that one file with a clear reason rather than dropping content into it — see `DECISIONS.md` for why the first-pass implementation (an exact-destination-path-exists check only) didn't actually satisfy this. Background job + polling progress (own `filename_sort_progress` singleton, same `running`-boolean guard as §11.4), own `filename_sort_log.md` audit log with `[AUTO]`-prefix support pre-wired (unused until automation is scoped). Automation/scheduling wiring, a second script (move-to-library), and a dirty-folder cleanup tool are explicitly deferred, not built here. | Build brief handed directly to Code (pre-scoped spec, not sourced from `INBOX.md`/`ROADMAP.md`) — logged as `comicvault-changes-v2.5.md` Item 2. Collision-logic correction found via direct scratch-folder testing, before the manual UI pass. |
