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
- **Phase B — queued next.** Left sidebar nav replaces `.surface-nav` top
  tabs (Home/Browse/Series/Issue).
- **Phase C — queued.** Admin page IA restructure (category → sub-item →
  content panes) — the riskiest phase, must preserve every existing
  `admin.js`/`processingTools.js`/`filePicker.js` wiring across ~20
  sections while restyling.
- **Phase D — queued.** Series/Issue detail visual polish (backdrop, issue
  rows, credits layout) per the design reference's `screens.jsx`.

**Status:** Handed to Code 2026-07-07. Phase A built and verified same day.
Phases B–D not yet started.
