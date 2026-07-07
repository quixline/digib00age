# ComicVault — v2.6: Build Plan

> **Status: Item 1 handed to Code 2026-07-07 — not yet built.** `docs/v2.6/`
> created 2026-07-06, alongside Item 1's handoff, per `ROADMAP.md`'s
> established pattern (working folder created alongside implementation,
> not ahead of it). This redesign was scoped visually in Claude Design
> (canvas exploration + inline annotations), not through a written spec
> pass — exact layout, colour, typography, and spacing values live in the
> Design handoff itself, not duplicated here. This doc tracks scope
> boundaries, decisions, and build status only.
>
> **How to use this document**
> This is the ordered build queue for v2.6. Paste into a Claude Code
> session alongside the Design handoff. Items are marked ✅ when built and
> verified. Bugs and minor fixes are tracked separately in `BUGS.md` —
> don't add them here unless they block a build item.
>
> **Always reference items from other docs as "v2.6 Item N", never bare
> "Item N"** — see `meta/working-rules.md` "Version-qualified references."

---

## Item 1 — Web UI Redesign (navigation, admin page, visual system)

**Feature.** Full visual/structural redesign of the web UI, built in Claude
Design and handed to Code via the Design→Code connector.

**In scope:**
- Navigation relocated from top tabs to a left-side nav.
- "Tabs" reconceived as "Libraries" — side nav supports multiple library
  entries (previously Custom Tabs).
- Full colour palette and typography system overhaul, site-wide.
- Spacing system overhaul, site-wide.
- Admin page: full visual overhaul, including a stats-card redesign.
- Home strips: unchanged — carried over as-is from the current design.

**Full per-screen scope checklist (added 2026-07-07 — the bullets above
and the phase list below are both prose summaries, not an itemised list;
this is the itemised one, cross-checked directly against the Design
project's `screens.jsx`/`parts.jsx`/`admin.jsx`, not just described from
memory. Update this checklist, not just the phase list, if anything else
turns up.):**

| Screen | What changes | Phase |
|---|---|---|
| Header (all pages) | Slim bar: sidebar toggle, brand lockup, search, settings, login/logout | B ✅ |
| Left sidebar (all pages except Admin) | Primary nav, status shortcuts, Libraries list, collapse/expand | B ✅ |
| Home | Strips unchanged | out of scope (unchanged) |
| **Browse (All/Singles/Series/a custom tab's flat listing)** | Filter/sort bar restyled — visual only, every existing field/control kept. Cover grid/card styling itself was out of Phase D's scope (only the filter bar was touched) — still believed close after Phase A's token remap, not independently re-verified against Design this phase. | D ✅ |
| Series detail | Blurred cover backdrop, issue-row treatment, tag/genre chips | E (renumbered from old "Phase D") |
| Issue detail | Cover + action-button column, credits/summary layout | E (renumbered from old "Phase D") |
| Admin | Category → sub-item → content-pane IA restructure | C1 ✅ / C2a ✅ / C2b ✅ — complete |

**Browse filter/sort bar — what's actually different (found in
`screens.jsx`'s `BrowseScreen`, confirmed against the live Design canvas
screenshot, not the possibly-stale handoff bundle):**
- Design's bar: `A–Z` sort dropdown (options include Z–A/Year/Recently
  Added/**Rating** folded in as a sort mode) · sort-direction toggle (↑) ·
  `★ Favourites` toggle · divider · `Genre`/`Format`/`Decade`/`Publisher`/
  `B&W` dropdowns · [spacer] · grid/list toggle · big `N Titles` count.
  Controls are borderless/minimal — no background box, no visible border
  until interacted (`.ds-filter`/`.ds-mb-btn` in `Library.html`'s kit-local
  CSS: `background:none; border:none; color:var(--text-secondary)`,
  active/hover just changes text colour to accent).
- Real app's current bar (`frontend/index.html` `#menuBar`, unchanged by
  Phases A/B): separate `Rated` star dropdown, separate `Year` filter
  *alongside* `Decade`, a `Group by` dropdown, and a `Clear` button — none
  of which appear in the design's `BrowseScreen` at all. Controls are
  boxed pills (`.filter-select` / `.sort-dir-btn` etc. — `background:
  var(--surface-2); border: 1px solid var(--border); border-radius: ...`),
  the pre-redesign visual language, just re-coloured by Phase A's token
  swap, not restructured.

**Resolved 2026-07-07 (was an open question, see `DECISIONS.md` for the
full rationale):** `Group by`, the separate `Year` filter, the separate
`Rated` dropdown, and `Clear` are **not** being dropped. Design was
working from an incomplete snapshot of the app's files and never had
visibility into these controls — their absence from the mockup isn't a
scope decision, it's a gap in what Design saw. **Phase D is a visual
restyle only** — every current field/control in `#menuBar` stays exactly
as-is functionally; only the styling (borderless/minimal controls,
hover/active states, spacing) changes to match the Design output.

**Detail source:** Claude Design canvas + inline annotations, handed to
Code directly via the Design connector — not duplicated into this doc.
Refer to the live Design project for exact layout/spacing/colour values
and any per-element implementation notes.

**Explicitly out of scope for this item (deliberately left for later):**
- BUG-014 (back-button/header unification) — separate pass once this
  lands, not bundled in.
- BUG-015 (genre filter can't be cleared) — parked, revisit after
  redesign is in.
- Mobile/Flutter UI redesign — separate item, scoped independently, not
  started.

**Open question, not blocking handoff:** "Libraries" replacing "Custom
Tabs" in the UI — does this rename ripple into `CUSTOM_TABS_SPEC.md`'s own
terminology, or does the spec keep "Custom Tabs" as the internal/technical
name while the UI surfaces "Libraries"? Decide before post-build spec
updates, not before build starts.

**Also confirmed with Tez, 2026-07-07 (not in the original scope bullets
above):** the design system's own readme frames this as a full visible
brand rename — **digib00age** replaces "ComicVault" in the header logo,
page titles, and favicon. "ComicVault" stays as the repo/internal/codebase
name (DB, API, `config.json`, tray app) — this is UI-visible-copy only.

**Build sequencing (decided 2026-07-07, given the size of this item):**
phased across multiple sessions rather than one continuous build —
- **Phase A — ✅ built 2026-07-07.** Design tokens (colour/typography/
  spacing/elevation) merged into `style.css` site-wide, plus the brand
  rename above. No structural/nav changes. Manually verified in dark and
  light theme across Home/Browse/Series/Issue/Admin — see
  `v2.6/progress.md` for the full build/verify log.
- **Phase B — ✅ built 2026-07-07.** Left sidebar nav replaces the top
  `.surface-nav` tab bar and header status-pills row, across all three real
  pages (index/series/issue — the design's single-SPA-shell assumption
  doesn't hold in the real app). Read-status filtering is now a sidebar
  shortcut that always jumps to All, pre-filtered — not a per-surface
  toggle like before; matches the approved design exactly, documented as a
  deliberate behaviour change in `MENU_BAR_SPEC.md`/`CUSTOM_TABS_SPEC.md`.
  Manually verified in dark and light theme — see `v2.6/progress.md`.
- **Phase C1 — ✅ built 2026-07-07.** Admin page IA restructure, part 1:
  category → sub-item → content-pane nav for **Library Management** and
  **Library Appearance** (the 10 sub-items Design actually built content
  for) — see the mapping table above. Every existing `admin.html` element
  ID preserved; `admin.js`/`processingTools.js`/`filePicker.js` untouched
  except one new additive `bindAdminNav()` function. Home Page Strips and
  Add/Remove Libraries moved out from behind the "Unlock advanced
  settings" gate (`DECISIONS.md`). Manually verified in dark and light
  theme, including one real functional round-trip test (Card Size change
  → localStorage → revert) — see `v2.6/progress.md`.
- **Phase C2a — ✅ built 2026-07-07.** Admin page IA restructure, part 2:
  category → sub-item → content-pane nav for **Editor Options** (Genre
  List, Format List — moved out from behind the advanced-settings lock,
  same treatment as Phase C1's Home Strips/Libraries) and **Advanced
  Settings** (Password Protection, Change Server Port + Reader Location
  folded into one sub-item, Wipe Database, Wipe Reading State — split out
  of the old single "Danger Zone" subsection into two separate sub-items;
  all four stay behind the existing "Unlock advanced settings" gate, not
  reclassified). Every existing `admin.html` element ID preserved;
  `admin.js` extended only by adding two entries to the existing
  `ADMIN_CATEGORIES` array — `bindAdminNav()` itself unchanged. Processing
  Tools section untouched, still old-style always-visible. Manually
  verified in dark and light theme, all 4 new sub-items and the
  lock/unlock gate — see `v2.6/progress.md`.
- **Phase C2b — ✅ built 2026-07-07.** Admin page IA restructure, part 3
  (final category): **Processing Tools** — Filename Editor, Converter:
  Archives & Images (Convert Archives + Convert Images combined into one
  pane), **new standalone XML Tagging tool**, Folder Processing (Sort by
  Filename), Auto Processing (Processing Folder Automation minus the three
  fields relocated to XML Tagging). Real backend work: new
  `backend/routers/xml_tagging.py` modeled on `filename_sort.py`, reusing
  `ct_autotag_file()`/`ct_bridge.*` verbatim; `ct_autotag_log.py`'s
  `append_entry()` gained an `auto: bool = False` param (was
  automation-only, hardcoded `[AUTO]`); registered in `main.py`. The
  ComicVine API key/threshold/save-low-confidence fields moved out of Auto
  Processing's pane into XML Tagging's (same stored config fields, same
  IDs, same existing config/test endpoints — reused, not duplicated); Auto
  Processing keeps its CT Auto-Tag enable checkbox. Every pre-existing
  `admin.html` element ID preserved; `admin.js` extended with one more
  `ADMIN_CATEGORIES` entry. Manually verified in dark and light theme, all
  5 sub-items, plus a real functional round-trip (synthetic scratch CBZ,
  not real library data — XML Tagging run confirmed a non-`[AUTO]` log
  line written alongside untouched `[AUTO]` lines from prior automation
  runs; Save & Test re-verified from its new location) — see
  `v2.6/progress.md`. **Admin page IA restructure (Phases C1/C2a/C2b) is
  now complete** — every category is nav-driven, nothing left on the old
  one-long-scrolling-page layout.
- **Phase D — ✅ built 2026-07-07.** Browse screen filter/sort bar restyle —
  visual only, every current field/control kept exactly as-is (resolved
  2026-07-07, see `DECISIONS.md`). Restyled `.filter-select`/`.sort-dir-
  btn`/`.fav-filter-btn`/`.view-toggle-btn`/`.group-by-select`/`.filter-
  clear` to the borderless/minimal `.ds-filter`/`.ds-mb-btn` treatment,
  fetched directly from the Design project this session (`Library.html`'s
  kit-local CSS, `screens.jsx`'s `BrowseScreen`) rather than relying on
  the prior session's description. Added a vertical divider after
  Favourites and grouped the view toggle with the title count on the
  right, matching Design's layout — pure CSS + one small HTML reorder, zero
  `app.js` changes. **Scope call:** Design's dropdowns are a fully custom
  popup-listbox component (`components/library/Dropdown.jsx`), not a
  native `<select>` — kept the real app's native `<select>` elements and
  restyled only their closed-state trigger appearance, rather than
  rebuilding them as custom widgets (real new interactive-component work,
  not a restyle, and not justified just to reskin a browser-owned popup
  list). Manually verified: every control still filters/sorts/toggles
  identically (Genre filter functional round-trip, Favourites toggle,
  Clear, grid/list view toggle all re-tested), dark and light theme, Flat
  View and Folder View (a Custom Tab's listing) both confirmed, no console
  errors — see `v2.6/progress.md`.
- **Phase D follow-up — ✅ built 2026-07-07.** Styled *open* dropdown panel
  (screenshot-driven request — Design's dropdowns are a custom popup
  listbox, and a native `<select>`'s open state can't be restyled via CSS
  at all, which is exactly the scope call Phase D's own decision entry had
  made). New `frontend/js/filterDropdown.js` layers a custom trigger+panel
  over each `.filter-select` in `#menuBar`, matching
  `components/library/Dropdown.jsx`'s `.ds-dropdown-panel`/`.ds-dropdown-
  opt` styling — the real `<select>` stays in the DOM (hidden, not
  removed) as the single source of truth, so `app.js` needed **zero**
  changes. See `DECISIONS.md` for the sync mechanism this required
  (`Object.defineProperty` on `.value` + a `MutationObserver` on
  `class`/`hidden`).
- **Phase E — queued (renumbered from the old "Phase D").** Series/Issue
  detail visual polish (backdrop, issue rows, credits layout) per the
  design reference's `screens.jsx`.

**Status:** Handed to Code 2026-07-07. Phases A, B, C1, C2a, C2b, and D
(plus its open-dropdown-panel follow-up) built and verified same day (also
a small C2b follow-up polish, see `v2.6/progress.md`) — the Admin IA
restructure is complete and the Browse bar, including its open dropdowns,
now matches the Design reference. Phase E not yet started.
