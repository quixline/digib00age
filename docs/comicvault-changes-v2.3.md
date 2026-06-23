# ComicVault — v2.3: Build Plan

> **Status: Active.**
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

## Item 6 — Admin: password protection + access controls

**Spec:** `ADMIN_SPEC.md` §7.1, §7.2

Gate `/admin` (and editor access via Admin) behind a password popup. Password
management in Advanced Settings. Remote Administration toggle (block/allow non-local
access to `/admin`) added to Advanced Settings — cannot be enabled until a password
is set.


---

## Item 7 — Admin: scan improvements + auto scan

**Spec:** `ADMIN_SPEC.md` §4 (scan log cards), §8 (logs + auto scan)

Two related scan-area additions:

**Scan log cards:** each of the four scan stat cards (Last Scanned, Changed Files,
New Files, Missing Records) gains its own log file (`/logs/`), a Logs button that
opens it, and a green border indicator when new entries exist since last viewed. Log
formats per `ADMIN_SPEC.md` §8. Note the open TODO: confirm scanner's "changed" flag
definition against `scanner.py` before implementing the Changed Files log format.

**Auto Scan Options:** frequency dropdown (off / 1hr / 6hr / 12hr / 1 day / 3 days /
7 days / 1 month) + "Scan on launch" checkbox. Saved to `config.json`.

**Logs area:** View Logs Folder button + configurable log size limit (xMB) in
`config.json`.

---

## Item 8 — Admin: scheduled backup + server port

**Spec:** `ADMIN_SPEC.md` §7.3, §9

**Scheduled Database Backup:** single folder picker (Explorer, same mechanism as scan
roots) + frequency dropdown. Replaces and supersedes the old one-off Backup Database
button's location field. The top-row Backup Database button stays for manual
on-demand backups, using the same destination folder.

**Server listening port:** manual numeric input in Advanced Settings, updates
`config.json`, restarts server. Addresses BUG-004 (port 8000 Windows exclusion
conflict) as a user-configurable workaround.

---

## Item 9 — Admin: destructive actions + extras

**Spec:** `ADMIN_SPEC.md` §7.4, §7.5, §10, §1 (Admin cog in Full Editor)

- **Clear Database** (Advanced Settings): wipes all DB records including reading
  progress. Confirmation modal required.
- **Clear Reading Progress** (Advanced Settings): wipes progress only, keeps all
  other data. Confirmation modal required.
- **Donate button**: opens a popup modal. Content TBC — build the button + empty
  popup shell now, fill content later.
- **Admin cog-link in Full Editor**: small icon/link in the Full Editor header
  pointing to `/admin`. Nav convenience only.

---

## Manual test pass

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
