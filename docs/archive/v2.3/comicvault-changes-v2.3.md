# ComicVault — v2.3: Build Plan

> **Status: Items 1–13 built; Items 10–13 manually tested 2026-06-28 — one failure.**
> Items 1–9 built, verified, and manually tested (2026-06-24/26). Items 10–13 built
> and code-verified 2026-06-27. Manual test pass run 2026-06-28: Items 10 (Password
> Recovery), 11 (Backup frequency), 13 (Card Size 75%) passed; Item 12 (Restore
> Database) did not pass — restore completes but DB is not reverted to backup state.
> Logged as BUG-016. **Item 14 is parked**, not queued — see its own entry below for why.
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

Built 2026-06-27. **Spec:** `ADMIN_SPEC.md` §7.1.7 **Manual Test: Passed, Tez, 28-6-26**

Added a real "Forgot Password?" button/popup to the Admin page's Top Action Row —
shows simple step-by-step instructions for clearing the password hash/salt directly
in `config.json` to recover from a forgotten password. This **replaces** §7.1.7's
plan to rely on a future User Guide stub — the popup itself becomes the
documentation; the guide (once built) just links to it rather than duplicating the
instructions.

---

## ✅ Item 11 — Admin: reduce Scheduled Backup frequency options

Built 2026-06-27. **Spec:** `ADMIN_SPEC.md` §9 **Manual Test: Passed, Tez, 28-6-26**

Cut the existing frequency dropdown (was 1hr through 12 months, ~20 entries) down
to: **Off / Every day / week / month / 6 months / 1 year**. Tez's call — the
original list was excessive for a single-user home app.

---

## ✅ Item 12 — Admin: Restore Database option 

Built 2026-06-27. **Spec:** `ADMIN_SPEC.md` §9.2 **Manual Test: Not Passed, Tez, 28-6-26. Backed-up db with only 2000 AD custom tab in place, Added new tab - 'testdb', changed Read status on 1 issue. Restored DB, testdb tab and read status unchanged.

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

Built 2026-06-27. **Spec:** `ADMIN_SPEC.md` §6 (Card Size subsection) **Manual Test: Passed, Tez, 28-6-26**

Existing control (built v2.1, 2026-06-22) offered 10% / 25% / 50% / 100%. Added
**75%** as a fifth option, between 50% and 100% — `frontend/admin.html`'s
`#cardSizeSelect` gained the `<option>`, and `frontend/js/app.js`'s
`CARD_SIZE_PX` map gained `'75': '190px'` (midpoint between 50%'s 160px and
100%'s 220px).

---

## Item 14 — Site-wide: unify the main header across Series/Issue detail pages

**Moved to `ROADMAP.md`** ("Blocked on Claude Design UI redesign exploration")
2026-06-28 — it shares the same blocking dependency as that exploration, so it no
longer belongs in an active build queue. All findings (header markup gap, BUG-014
sequencing, search-scope question) preserved there, not lost.
