# ComicVault — v2.3: Build Plan

> **Status: Active.** Items 1–9 built, verified, and manually tested (2026-06-24/26).
> Items 10–14 added 2026-06-27 from inbox triage — queued, not yet built.
>
> **How to use this document**
> This is the single ordered build queue for v2.3. Paste into a Claude Code session
> alongside the referenced spec files. Work top to bottom. Items are marked ✅ when
> built and verified. Bugs and minor fixes are tracked separately in `BUGS.md` —
> don't add them here unless they block a build item.
>
> **Specs to paste for most sessions:** `SPEC.md`, `CUSTOM_TABS_SPEC.md`,
> `MENU_BAR_SPEC.md`, `ADMIN_SPEC.md`, `EDITOR_SPEC.md` as relevant per item.

---

## ✅ Item 1 — Folder View: folder card images

Built 2026-06-23. Full spec: `CUSTOM_TABS_SPEC.md` §9.2.
Random cached thumbnail per subfolder, re-randomised on every request, falls back to
plain folder icon when count = 0. No new pipeline or scanner changes.

---

## ✅ Item 2 — Menu bar redesign

Built 2026-06-23. **Spec:** `MENU_BAR_SPEC.md` + this item's bullet list below (the
"sort controls section below" referenced here pointed nowhere — resolved by treating
this item's bullets as the full sort spec, see `DECISIONS.md` 2026-06-23 entry).

Replace the existing three-state sort cycle button with a unified menu bar across all
surfaces (Flat View and Folder View). Controls:
- Sort dropdown (A–Z / Newest / Recent / # of Issues / # of Pages) + Ascend/Descend toggle
- Rated filter dropdown (1–5 stars)
- Favourites filter toggle button
- Existing search bar (moved into bar for consistency)
- Existing grid/list toggle (moved into bar)

**# of Pages** is suppressed on surfaces showing Series or Folder aggregate cards.
Folder View gets full parity — see `MENU_BAR_SPEC.md` §3 for the full surface matrix.


---

## ✅ Item 3 — Card behaviour additions

Built 2026-06-23. **Spec:** `SPEC.md` §20.17

Four visual changes, all frontend:
1. Favourite star (card top-left): +5px size, 1px solid black border.
2. Issue page star rating row: increase star size + reduce inter-star spacing so the
   row fills the button row width (reduces blank margin either side).
3. Favourited cards: thin gold border around the full card outline, coexisting with
   the existing amber/green read-state gradient.
4. Dark/Light theme: auto-match Windows system theme; manual override toggle in
   Settings.

---

## ✅ Item 4 — Multi-select scope expansion

Built 2026-06-23.

**Spec:** `DECISIONS.md` (multi-select scope correction, 2026-06-23)

Extend the existing long-press multi-select to include Series and Singles aggregate
cards (previously excluded per `SPEC.md` §20.15). Same bulk actions (read/unread/
favourite/rate) apply. Existing machinery — bulk endpoints already exist, frontend
`makeSelectable()` needs extending. `SPEC.md` §20.15's exclusion text is superseded
by the `DECISIONS.md` entry.

---

## ✅ Item 5 — Full Editor: Process All per-field checkbox

Built 2026-06-23.

**Spec:** `EDITOR_SPEC.md` §5.2 (amended note) + §12 change log

Add an "Apply to: All" checkbox to every field in the Full Editor's XML Editor
column. Default: unchecked. Process All only bulk-applies checked fields; unchecked
fields keep their per-file values. Issue Number gets no checkbox (auto-increment only,
unchanged). This changes the existing default-everything behaviour.

---

## ✅ Item 6 — Admin: password protection + access controls

Built 2026-06-24. **Spec:** `ADMIN_SPEC.md` §7.1, §7.2 — full design there; this item is a pointer only.


---

## ✅ Item 7 — Admin: scan improvements + auto scan

Built 2026-06-24. **Spec:** `ADMIN_SPEC.md` §4 (scan log cards), §8 (logs + auto scan)

Two related scan-area additions:

**Scan log cards:** each of the four scan stat cards (Last Scanned, Changed Files,
New Files, Missing Records) gains its own log file (`/logs/`), a Logs button that
opens it, and a green border indicator when new entries exist since last viewed. Log
formats per `ADMIN_SPEC.md` §8. The open TODO (confirm scanner's "changed" flag
definition against `scanner.py`) was resolved by direct code reading — see
`DECISIONS.md` and `BUGS.md` BUG-013 for a confirmed pre-existing detection gap.

**Auto Scan Options:** frequency dropdown (off / 1hr / 6hr / 12hr / 1 day / 3 days /
7 days / 1 month) + "Scan on launch" checkbox. Saved to `config.json`.

**Logs area:** View Logs Folder button + configurable log size limit (xMB) in
`config.json`.

---

## ✅ Item 8 — Admin: scheduled backup + server port

Built 2026-06-24. **Spec:** `ADMIN_SPEC.md` §7.3, §9

**Scheduled Database Backup:** single folder picker (native OS dialog — not the
library-scoped Custom Tabs/Scan Roots picker, which can't reach paths outside the
library; see `DECISIONS.md`) + frequency dropdown. Replaces and supersedes the old
one-off Backup Database button's location field. The top-row Backup Database button
stays for manual on-demand backups, using the same destination folder.

**Server listening port:** manual numeric input in Advanced Settings, updates
`config.json`, restarts server. Addresses BUG-004 (port 8000 Windows exclusion
conflict) as a user-configurable workaround.

---

## ✅ Item 9 — Admin: destructive actions + extras

Built 2026-06-24. **Spec:** `ADMIN_SPEC.md` §7.4, §7.5, §10, §1 (Admin cog in Full Editor)

- **Clear Database** (Advanced Settings): wipes library data (issues, genres,
  credits, reading progress, orphaned People rows) — Custom Tabs/Home Strips
  configuration intentionally untouched, see `DECISIONS.md`. Confirmed via the
  existing `confirm()` mechanism (same as Delete Tab), local-only gated.
- **Clear Reading Progress** (Advanced Settings): wipes progress only, keeps all
  other data. Same `confirm()`/local-only mechanism as above.
- **Donate button**: opens a "Coming soon." popup modal. Content TBC, no backend.
- **Admin cog-link in Full Editor**: already built during the Item 6 session
  (bundled in while that file was touched for the Logout control).

---

## Manual test pass **Completed 1-9**

After all items above are built, run a full manual test pass covering:
- Menu bar on each surface (Home, All, Series, Singles, custom flat tab, Folder View)
- Each sort criterion + asc/desc, including # of Pages suppression on aggregate views
- Rated filter + Favourites filter in both Flat and Folder View
- Card visual changes (favourite star, gold border, read-state coexistence, theme)
- Multi-select on Series and Singles aggregate cards
- Full Editor Process All with mixed checked/unchecked fields
- Admin password gate, remote toggle dependency, all new Admin controls
- Scan log cards: trigger a scan, confirm log files written, green borders appear
- Scheduled backup: set a destination, confirm backup runs, confirm manual button uses same destination
- Destructive actions: confirm modal gates, confirm correct scope (DB vs. progress only)

---

## ✅ Item 10 — Admin: Password Recovery button

Built 2026-06-27. **Spec:** `ADMIN_SPEC.md` §7.1.7

Added a real "Forgot Password?" button/popup to the Admin page's Top Action Row —
shows simple step-by-step instructions for clearing the password hash/salt directly
in `config.json` to recover from a forgotten password. This **replaces** §7.1.7's
plan to rely on a future User Guide stub — the popup itself becomes the
documentation; the guide (once built) just links to it rather than duplicating the
instructions.

---

## ✅ Item 11 — Admin: reduce Scheduled Backup frequency options

Built 2026-06-27. **Spec:** `ADMIN_SPEC.md` §9

Cut the existing frequency dropdown (was 1hr through 12 months, ~20 entries) down
to: **Off / Every day / week / month / 6 months / 1 year**. Tez's call — the
original list was excessive for a single-user home app.

---

## ✅ Item 12 — Admin: Restore Database option

Built 2026-06-27. **Spec:** `ADMIN_SPEC.md` §9.2

Pairs with the existing Backup Database (§2) and Scheduled Backup (§9.1). §9 was
renamed "Database Backup" and split into two subsections/cards (Scheduled Backup,
Restore Backup) to host both. Scoped 2026-06-27:

- **Source:** native OS file dialog (same local-machine-sharing justification as the
  existing Backup folder picker §9), opening in the configured backup folder by
  default but not restricted to it.
- **Mechanism:** copy the chosen file over `comicvault.db`, then a full server
  restart — reuses the existing restart plumbing from §7.3 (port changes) rather
  than tearing down/rebuilding the live DB engine in-process.
- **Safety net — confirmed 2026-06-27:** auto-snapshot the *current* DB via the
  existing `run_database_backup()` helper (already shared by manual + scheduled
  backup) immediately before the swap, saved as `pre-restore-{timestamp}.db` into
  the same backup folder. Tez's call — cheap extra safety step, worth it regardless
  of how good the main confirmation dialog is.
- **Confirmation:** `confirm()` naming the chosen backup file's date, explicitly
  warning this is a full DB replacement (broader than Clear Database's library-only
  scope — also overwrites Custom Tabs/Home Strips), local-only gated same tier as
  Clear Database §7.4.

**Built as scoped, one wording deviation:** the confirm() names the file by its
*filename*, not a separately-parsed date — backups created by ComicVault's own
naming convention (`comicvault_backup_{timestamp}.db`) already encode the date in
the filename, and the picker allows choosing *any* `.db` file (not just ones
ComicVault created), so there's no reliable date to extract from an arbitrary
file. Filename is the practical equivalent Tez's confirmation intent called for.

---

## ✅ Item 13 — Admin: Card Size — add a 75% option

Built 2026-06-27. **Spec:** `ADMIN_SPEC.md` §6 (Card Size subsection)

Existing control (built v2.1, 2026-06-22) offered 10% / 25% / 50% / 100%. Added
**75%** as a fifth option, between 50% and 100% — `frontend/admin.html`'s
`#cardSizeSelect` gained the `<option>`, and `frontend/js/app.js`'s
`CARD_SIZE_PX` map gained `'75': '190px'` (midpoint between 50%'s 160px and
100%'s 220px).

---

## Item 14 — Site-wide: unify the main header across Series/Issue detail pages

**Status: parked, last in queue — Tez is not actioning this yet.** A separate
exploration with Claude Design (UI redesign direction) may change or supersede this
header work entirely — check there before scoping further. Findings below are kept
so nothing is lost in the meantime.

**Spec:** none yet — destination doc TBC (likely `SPEC.md` or `MENU_BAR_SPEC.md`,
whichever currently governs header layout; confirm during scoping)

`/series/{id}` and `/issue/{id}` currently use a different header treatment than
Home/the browse tabs. Make them consistent with the Home page header. Search scope:
"Search" should search the full library by default — except when already on a
Singles, Series, or Custom Tab surface, where it stays scoped to that surface (same
behaviour as `SEARCH_PLACEHOLDERS`/`updateSearchPlaceholder()` already established
for Home vs. All vs. Singles vs. Series, per `progress.md` "Session — 2026-06-22:
Tier 3"). Open question for whoever picks this back up: what should the search bar
search *from* an issue/series detail page itself, since it isn't "on" any surface
— proposed default is full-library (same as Home), not yet confirmed with Tez.

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

**Related but separate — likely root cause of BUG-014, found while reading the same
code:** the issue/series back-links already use real `window.history.back()` (a
code comment there says this replaced the old `from=` param logic). But the four
main surface tabs (Home/All/Singles/Series, `bindSurfaceNav()`) never call
`pushState` — switching tabs only updates a JS variable, the URL stays bare `/`.
Folder View *does* call `pushState` on every drill-down
(`pushFolderViewUrl()` — already explicitly documented in `app.js` as "a deliberate
departure from the simpler `history.back()`-only pattern used elsewhere"). So: user
on All (URL still `/`) → opens an issue → real navigation pushes `/issue/123` onto
history → Back → browser correctly returns to the literal previous entry, bare `/`
→ page loads defaulting to Home. The `?from=all`/`?from=series`/`?from=singles`
params still being attached when building card links (`buildCoverCard()` etc.) are
dead code — already ignored by both detail pages. **Recommended fix for BUG-014:**
extend Folder View's existing `pushState` pattern to the four main surface tabs;
once in place, Item 14's nav links on the detail pages can just point at
`/?surface=all` etc. and back-navigation works correctly for free. Sequence
BUG-014's fix just before or alongside this item, not independently — same
mechanism. Full write-up in `BUGS.md` BUG-014.

Needs a quick scoping pass to confirm current header variants before Code starts,
whenever this gets picked back up.
