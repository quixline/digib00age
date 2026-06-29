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
> Database) did not pass — restore completes but DB is not reverted to the backup
> state (BUG-016, open). Item 14 (site-wide header unification) moved to `ROADMAP.md`
> 2026-06-28 — not admin-page scope, blocked on Claude Design exploration.
>
> §11.1 File Rename scoped 2026-06-27 — design complete, build not yet started.
>
> **Note on authority:** `SPEC.md` §11 and §20.13 contain earlier admin descriptions.
> Where they conflict with this file, **this file is authoritative** — it consolidates
> and supersedes those entries for admin-page specifics.

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

- **Last Scan:** date/time of the most recent scan completion. Persists across server
  restarts (fixed — V2.3 post-test fixes, Fix 7, 2026-06-26): the in-memory
  `ScanProgress.finished_at` resets to `None` on every restart, so the card now falls
  back to the last line of `last_scan_log.md` (via `read_last_scan_timestamp()` in
  `backend/scan_logs.py`) when no live `finished_at` is available, before finally
  falling back to "Never".
- **Files Found:** total files found in last scan.
- **New Files:** new files found in last scan.
- **Scan Now** (action card): triggers `POST /api/scan`; card expands inline to show
  a live progress bar and log output during the scan.

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

### 7.4 Clear Database *(built — V2.3 Item 9, 2026-06-24 — destructive)*

Advanced Settings. Wipes all **library data** from the DB — issues, genres, credits,
reading progress, and the now-orphaned People rows. **Custom Tabs and Home Strip
configuration are deliberately left untouched** (they're configuration, not library
data — see `DECISIONS.md`). Confirmation uses a plain `confirm()` dialog (same
mechanism as deleting a Custom Tab), not a custom modal, despite this section's
literal "confirmation warning/modal" wording. Gated to local sessions only — same
tier as Restart Server and the backup folder dialog, since a full library wipe is at
least as disruptive as either. Not reversible — pairs with the scheduled backup (§9)
as a "start fresh" option; the confirm() message points at the Backup Database button.

### 7.5 Clear Reading Progress *(built — V2.3 Item 9, 2026-06-24 — destructive)*

Advanced Settings. Narrower than Clear Database (§7.4) — wipes only reading progress
records, keeps all other data (issues, people, credits, genres, etc.). Same `confirm()`
mechanism and local-only gate as §7.4.

### 7.6 Reader Location *(built — V1)*

Text field pre-populated from `config.json`. Browse/Change button to update. Saves to
`config.json`. Has no functional effect in V1 (present for a future configurable
reader). Deferred — see `ROADMAP.md` (reader-launch entry).

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

**"Changed" definition — resolved 2026-06-24 by reading `scanner.py` directly:**
`scan_single_file()` matches files by exact `file_path` and flags "changed" purely
on mtime delta (≥1 second from the stored `date_modified`) — it cannot distinguish
*why* the mtime changed. A filename change is confirmed to produce a separate
new-row insert + missing-flag on the old row (not a "change") — `file_path` is the
sole, unique match key. A same-mtime, different-file-size change (e.g. a re-zip
that preserves the timestamp) is confirmed **not** detected at all — logged as
`BUGS.md` BUG-013, out of scope to fix here.

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
2. Copies the chosen file over `comicvault.db` (`shutil.copy2`).
3. Triggers the same delayed-exit relaunch the Server Listening Port control
   (§7.3) and `/admin/restart` use — a full server restart rather than tearing
   down/rebuilding the live DB engine in-process. Factored into a shared
   `_schedule_delayed_exit()` helper used by both.

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

#### 11.1.3 Filename Parsing

Ports `filename_parser.py`'s `parse_comic_filename()` unchanged — regex-based
extraction of Series / Issue Number / Year (Title is left blank; CAPT never parsed it
out either) from the current filename, used to pre-populate the edit panel when a file
is selected. Tolerant of scene-release-style tags via bracket-stripping heuristics, but
not exhaustive — this is acceptable because nothing is committed until the user reviews
the live preview (§11.1.5) and corrects anything mis-parsed.

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

#### 11.1.5 Live Preview

No explicit "Preview Changes" button. The Preview list updates immediately on every
field edit or checkbox change. Single-file edits **accumulate** across file
selections — select File A, tick a field, edit it; select File B, tick a different
field, edit it; both A and B now sit in the Preview list simultaneously, each carrying
only its own edited field(s) with everything else left as originally parsed. This
matches CAPT's existing accumulation behaviour exactly, just without the manual Preview
button. Switching into a batch ("All") edit, or pressing **Clear Preview**, resets the
list. Clear Preview button is retained.

#### 11.1.6 Apply Rename

Attempts every file currently in the Preview list. On completion, shows a summary modal
matching the Full Editor's existing Process-error pattern (`feProcessErrorModal`):
"Renamed X of Y files", plus a per-file error list for any failures (permission denied,
filename collision, file no longer present on disk, etc.). Files that succeed clear
from the Preview list; files that fail remain so the user can retry or adjust. No
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

## 12. Change Log

> Record any deviations from this spec here with date and reason.

| Date | Change | Reason |
|---|---|---|
| 2026-06-23 | `ADMIN_SPEC.md` created — consolidates `SPEC.md` §11 and §20.13's admin descriptions plus all new admin items scoped in the 2026-06-23 inbox triage session. `SPEC.md` §11/§20.13 are superseded by this file for admin-page specifics. | Inbox triage 2026-06-23; EDITOR_SPEC.md precedent for a standalone admin spec. |
| 2026-06-24 | §7.1 and §7.2 stubs replaced with full design: scope expanded to cover `/editor` and all `/api/admin/*` + `/api/editor/*` endpoints (not just `/admin`); local-only security boundary; stateless signed-cookie session; brute-force lockout; sliding expiry; no-built forgot-password recovery; §7.2 remote toggle dependency tightened. §1 Access gate wording updated to point at §7.1, drop §5.1 reference and "deferred to V2" framing. | Design session 2026-06-24; `comicvault-changes-v2.3.md` Item 6 updated to pointer-only. |
| 2026-06-26 | Post-test fix pass (`docs/2.3-fixes.md`, Fixes 4–9): §7.1.2/§7.1.5 — login popup gated to protected pages only, auth button always visible with Login/Logout label, new no-password-set explanation dialog; §7.1.1 — disabling password protection now requires re-entering the current password via an inline confirm row; §4 — Last Scan card falls back to the persisted log on server restart instead of showing "Never"; §8 — changed-files log now distinguishes "metadata updated" vs. "archive changed (pages: X → Y)"; §9 — new Last Backup indicator + scheduler failure surfacing in the Scheduled Backup block. | Manual test pass 2026-06-26 (`docs/2.3-testing-notes.md`) surfaced all six issues. |
| 2026-06-27 | Added §11 Processing Tools (new section, inserted before the Change Log, which shifts from §11 to §12) and §11.1 File Rename — full scope, picker behaviour, checkbox model, live preview, error handling, and audit log design. Ported from CAPT's standalone File Renamer per `ROADMAP.md`'s "CAPT extra tools" entry, brought in one tool at a time starting with Rename. | Dedicated scoping session 2026-06-27 — CAPT source code and `Processing/` folder structure inspected directly to ground design decisions. |
| 2026-06-27 | Status block corrected — removed stale "manual test pass remaining" (test pass completed 2026-06-26, see Fixes 1–9). §6 backfilled with the Card Size control (built v2.1, 2026-06-22) — never written into this doc when it was created 2026-06-23. Five new items (10–14) queued from inbox triage, noted in the status block. | Doc-consistency scan flagged ISSUE-007 (`doc-scan-issues.md`); extended into a full inbox triage session. |
| 2026-06-27 | §7.1.7 — built the Forgot-Password recovery popup (V2.3 Item 10): "Forgot Password?" button added to the Top Action Row, opens a modal with the manual `config.json` recovery steps. Replaces the prior "none built, defer to future User Guide" text. | `comicvault-changes-v2.3.md` Item 10. |
| 2026-06-27 | §9 — Scheduled Backup frequency dropdown cut from ~20 entries down to 6 (Off/day/week/month/6 months/1 year), V2.3 Item 11. Backend frequency map left untouched (still recognises old values). | `comicvault-changes-v2.3.md` Item 11; Tez's call, excessive list for a single-user home app. |
| 2026-06-27 | §9 renamed from "Scheduled Database Backup" to "Database Backup", split into §9.1 Scheduled Backup (unchanged content) and new §9.2 Restore Database (V2.3 Item 12) — native file picker, `pre-restore-{timestamp}.db` safety snapshot via a now-parameterised `run_database_backup()`, full server restart via a new shared `_schedule_delayed_exit()` helper. | `comicvault-changes-v2.3.md` Item 12. |
| 2026-06-27 | §6 — Card Size dropdown gains a 75% option (between 50% and 100%), V2.3 Item 13. `CARD_SIZE_PX` (`frontend/js/app.js`) maps it to `190px`. | `comicvault-changes-v2.3.md` Item 13. |
