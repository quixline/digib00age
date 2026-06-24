# ComicVault — ADMIN_SPEC.md

> **How to use this document**
> Paste this file into a Claude Code session alongside `SPEC.md` and `EDITOR_SPEC.md`
> for context on the wider system. This is the single source of truth for the Admin
> page. Record any deviations at the bottom (Change Log), same convention as other
> spec files.
>
> **Status:** Partially built. §1–§4 (core layout, stats, scan, library folders,
> pagination) are live as of V1 (2026-06-17 build close-out). §5 (Advanced Settings)
> is partially live — the existing Locked section is built; most new items in §5 are
> not yet built. §6 (Logs), §7 (Scheduled Backup), §8 (Auto Scan), §9 (Donate) and
> all password/access items are **not yet built** — see status notes per section.
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

**Admin cog-link in Full Editor:** A small cog/admin icon link in the Full Editor
header gives direct navigation to `/admin`, so a user moving from the editor to
trigger a scan doesn't have to navigate away first. Small convenience, no auth impact.

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

- **Last Scan:** date/time of the most recent scan completion.
- **Files Found:** total files found in last scan.
- **New Files:** new files found in last scan.
- **Scan Now** (action card): triggers `POST /api/scan`; card expands inline to show
  a live progress bar and log output during the scan.

**Scan log cards (not yet built — see §6):** the four scan stat cards above will
additionally show per-category log details once §6 ships. See §6 for the log file
format, green-border "new entries" indicator, and per-card Logs button.

### Auto Scan Options (not yet built)

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
time; turning it off clears the enforcement (the stored password hash may remain on
disk, but is no longer checked against anything).

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

#### 7.1.5 Logout

A **Logout** control sits next to the gear icon in the main header on every page,
visible only when an authenticated session is active. Clears the session by setting
an already-expired cookie. No confirmation needed — logging back in is one password
entry away.

#### 7.1.6 Changing password (in-session)

Once logged in, the existing **Password Reset** button (top action row, §2) becomes
live: standard current-password + new-password form. No special handling beyond
normal validation (non-empty, current password must verify before the new one is
accepted).

#### 7.1.7 Forgot-password recovery — none built

If the password is forgotten entirely, recovery is **manual, local-disk-only**: stop
the server, clear the stored password hash/salt fields in `config.json` directly
(reverts to "no password set" / ungated), restart, then set a new password through
the UI as normal. No in-app recovery flow, no script — this is already consistent
with the local-access security boundary established in §7.1.1 (you need local
machine access to weaken protection anyway).

This needs to be **documented in the project docs now**, and **added to the future
User Guide** (currently a stub page per §2) once that's built — flagging both so it
isn't lost.

### 7.2 Remote Administration Toggle *(built — V2.3 Item 6, 2026-06-24)*

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

### 7.3 Server Listening Port *(not yet built)*

A manual numeric input field for the server's listening port (currently hardcoded to
8000 via `config.json`). Saving updates `config.json` and restarts the server.
Relevant to `BUGS.md` BUG-004 (port 8000 / Windows port-exclusion conflict) — moving
to a less commonly reserved port is a workaround for that issue.

### 7.4 Clear Database *(not yet built — destructive)*

Advanced Settings. Wipes all records from the DB, including reading progress. Requires
an explicit confirmation warning/modal before executing. Not reversible — pairs with
the scheduled backup (§9) as a "start fresh" option.

### 7.5 Clear Reading Progress *(not yet built — destructive)*

Advanced Settings. Narrower than Clear Database (§7.4) — wipes only reading progress
records, keeps all other data (issues, people, credits, genres, etc.). Requires a
confirmation warning/modal before executing.

### 7.6 Reader Location *(built — V1)*

Text field pre-populated from `config.json`. Browse/Change button to update. Saves to
`config.json`. Has no functional effect in V1 (present for a future configurable
reader). Deferred — see `ROADMAP.md` (reader-launch entry).

---

## 8. Logs *(not yet built)*

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
| Changed Files | `changed_files_log.md` | `filename.cbz — type of change` |
| New Files | `new_files_log.md` | `filename.cbz — location` |
| Missing Records | `missing_log.md` | `filename.cbz — last known path — date went missing` |

**"Changed" definition — open TODO for Claude Code:** confirm against the actual
scanner logic what currently gets flagged as a changed file before finalising the log
format. Working assumption: XML content changes are already flagged; a filename change
should be logged as a new + missing pair (not a "change"); file-size-only change
behaviour is untested and needs checking. Do not implement the log format without
first verifying this against `scanner.py`.

**Green border indicator:** a card's border turns green when its corresponding log
file has new entries since it was last viewed. Resets on open.


---

## 9. Scheduled Database Backup *(not yet built)*

Consolidates two previously separate inbox items ("Backup Database Location" and
"Schedule database backup") into one unified control.

**Controls:**
- **Backup folder picker** — opens Explorer (same mechanism as the Scan Roots Add
  button / Full Editor's path picker). Single destination folder for all backups.
  Saved to `config.json`.
- **Backup frequency dropdown:** Every 1 hour / 2 hours / 4 hours / 6 hours /
  12 hours / 24 hours / 1 day / 2 days / 3 days / 4 days / 5 days / 6 days /
  7 days / 1 week / 2 weeks / 3 weeks / 4 weeks / 1 month / 2 months / 3 months /
  6 months / 12 months.

**No cloud API integration.** Pointing the destination folder at a cloud-sync
client's local folder (e.g. Google Drive Desktop sync folder) covers cloud backup
without in-app OAuth flows. The folder picker covers local drive, USB, and
cloud-synced folder equally.

The existing **Backup Database** button in the top action row (§2) remains for
on-demand manual backups — it uses the same destination folder once one is set.

---

## 10. Donate *(not yet built)*

A Donate button on the Admin page opens a popup/modal window. Details of the popup
content are TBC. For the initial build: the button and a functional (but empty/
placeholder) popup shell are sufficient — content is filled in later.

---

## 11. Change Log

> Record any deviations from this spec here with date and reason.

| Date | Change | Reason |
|---|---|---|
| 2026-06-23 | `ADMIN_SPEC.md` created — consolidates `SPEC.md` §11 and §20.13's admin descriptions plus all new admin items scoped in the 2026-06-23 inbox triage session. `SPEC.md` §11/§20.13 are superseded by this file for admin-page specifics. | Inbox triage 2026-06-23; EDITOR_SPEC.md precedent for a standalone admin spec. |
| 2026-06-24 | §7.1 and §7.2 stubs replaced with full design: scope expanded to cover `/editor` and all `/api/admin/*` + `/api/editor/*` endpoints (not just `/admin`); local-only security boundary; stateless signed-cookie session; brute-force lockout; sliding expiry; no-built forgot-password recovery; §7.2 remote toggle dependency tightened. §1 Access gate wording updated to point at §7.1, drop §5.1 reference and "deferred to V2" framing. | Design session 2026-06-24; `comicvault-changes-v2.3.md` Item 6 updated to pointer-only. |
