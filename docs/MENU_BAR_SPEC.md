# ComicVault — MENU_BAR_SPEC.md

> **How to use this document**
> Paste this file into a Claude Code session alongside `SPEC.md`, `CUSTOM_TABS_SPEC.md`,
> and `comicvault-changes-v2.3.md` for context on the wider system. This is the single
> source of truth for the unified menu bar. Record any deviations at the bottom
> (Change Log), same convention as other spec files.
>
> **Status:** Built 2026-06-23. Consolidates four previously separate inbox items into one
> coordinated feature. The sort criteria themselves are tracked in
> `comicvault-changes-v2.3.md` (§ Sort control redesign); this spec governs the menu
> bar as a whole.

---

## 1. Goal

The menu bar is a unified, consistent control row that appears across all browse
surfaces — Flat View tabs (Home, All, Singles, Series, custom flat-mode tabs) and
Folder View tabs alike.

**Tez's framing:** Folder View should be functionally equal to Flat View, not a
stripped-down cousin. Currently, in Folder View, "there's just the header then the
cards." That gap should close. Everything in this spec applies to both view modes
unless a specific exception is noted.

---

## 2. Controls

The menu bar contains the following controls, arranged in a single row:

### 2.1 Sort Dropdown + Ascend/Descend Toggle

A dropdown replacing the existing three-state sort cycle button. Full criteria list
and toggle behaviour are defined in `comicvault-changes-v2.3.md` (§ Sort control
redesign). Key constraint: **# of Pages does not apply in Folder View or on
Series/Folder card surfaces** — it must be suppressed or greyed out automatically
when the active view shows aggregate cards rather than flat issue lists.

### 2.2 Rated Filter Dropdown

Filters the current surface to issues at a specific star rating. Options:
1 star / 2 stars / 3 stars / 4 stars / 5 stars. Selecting a rating shows only issues
at exactly that rating; default (no selection) = show all. A second tap/click on the
active rating resets to "all."

Applies to flat issue-list views. In Folder View, it filters the flat file cards
visible at the current folder level (not the folder cards themselves — folder cards
are not rated).

### 2.3 Favourites Filter Button

A toggle button. When active, the current surface shows only favourited items
(issues/series/folders where `favorites = true`). When inactive, all items show.

Applies across both Flat View and Folder View. In Folder View, a folder card should
remain visible if any issue anywhere under that folder is favourited — suppressing a
folder entirely because it has no directly-favourited issues at the root level would
hide content the user might be trying to find.

### 2.4 Search

The existing inline search bar. No functional change — moved into the menu bar to
sit alongside the new controls consistently.

### 2.5 View Toggle (Grid / List)

The existing grid/list toggle (`SPEC.md` §20.5). No functional change — moved into
the menu bar row for visual consistency; **relocated again 2026-07-09** from the
trailing group (next to the title count) to sit right after the sort ascend/
descend toggle, per Tez's tweak-pass direction — see Change Log.

### 2.6 Status Pills — removed (v2.6 Item 1 Phase B, 2026-07-07)

**Superseded.** The `All / Unread / Reading / Read` header pill row described below no
longer exists — see the Change Log. Read-status filtering is now the left sidebar's
Unread/Reading/Read shortcut (`docs/v2.6/comicvault-changes-v2.6.md` Item 1), which
always jumps to the All surface pre-filtered, rather than a per-surface toggle. Left
the original text below as-written rather than editing it, per this doc's own
convention (see `CUSTOM_TABS_SPEC.md`'s change-log preamble for the same pattern) —
this section is the historical record of what changed and why.

~~The `All / Unread / Reading / Read` status pills live in the site header
(`#statusPills`, right after the search bar), not the menu bar itself — they were
originally a separate row inside `.browse-controls` below the menu bar, which produced
an unintended extra row. They're still tied to the same browse-surface visibility as
the menu bar (shown whenever a Flat browse surface is active, hidden on Folder View
and Home).~~

### 2.7 Secondary Filters (Genre / Format / Decade / Year / Rating / B&W)
*(extended to Folder View — V2.3 post-test fixes, additional step alongside Fix 1,
2026-06-26)*

**Publisher removed from this row 2026-07-09** — Tez's tweak-pass call; Publisher
stays available as a `#groupBySelect` grouping option, just not as its own filter
dropdown. See Change Log and `DECISIONS.md`.

The secondary filter dropdowns render in the same single menu-bar row as the
sort/rated/fav/view-toggle controls — previously a separate `.browse-controls` row
below the menu bar, now merged into one row per Tez's direction ("the whole row
needs to be in line with the items above and below"). **Grouping (`#groupBySelect`)
is the one control that stays Flat-View-only** — Folder View already groups by
directory structure, so a second grouping mechanism doesn't apply there.

**Clear button relocated 2026-07-09** — `#filterClear` no longer lives inside
`#browseFilters`; it now sits in the trailing group (`.menu-bar-trailing`), right
before `#browseCount`, the same slot the fieldview banner's own "Clear filter" link
occupies (`renderFieldviewBanner()`, `BUG-015`). Both now share one CSS treatment
(solid accent pill, matching the sidebar's collapsed Library letter-badges) so the
"you're filtered, here's how to clear it" affordance looks and sits identically
regardless of whether the active filter came from a dropdown or a Genre/Writer/
Artist link on an issue/series page. See `DECISIONS.md`.

These filters also apply to Folder View's flat file cards (folders themselves
have no per-field aggregate to filter against, so they stay navigable regardless of
filter state) — closing the gap this spec's §1 framing originally called out.
`renderFolderView()` filters `files` by `genres`/`format`/`age_rating`/`year`
using the same predicates Flat View uses, just against singular issue fields
instead of a series aggregate's plural fields (`publisher` filtering dropped from
this list 2026-07-09 alongside the dropdown's removal). The dropdown options are
populated from a global `/library` fetch the first time any browse surface (flat or
folder) loads — entering directly on a folder tab no longer leaves the dropdowns
empty.

**Vertical divider separators (`.menu-bar-divider`) extended 2026-07-09** — a
hairline divider now sits between every control across the whole row (sort dropdown,
ascend/descend, view toggle, Rated, Favourites, Group by, and each of the six
secondary filters), not just the one divider that previously sat between
Favourites and Group by.

### 2.8 Flagged-for-Review Filter Button (2026-07-15)

A toggle button (`#flagReviewFilterBtn`), sitting right next to the Favourites
button (§2.3) and sharing its exact mechanics: when active, the current surface
shows only issues where `flagged_for_review = true`; when inactive, all items
show. Same Folder View parity rule as §2.3 — a folder card stays visible if any
descendant issue is flagged. Not a dedicated tab, unlike Favourites' optional
`basis_type = 'favorites'` Custom Tab (`CUSTOM_TABS_SPEC.md` §10) — a deliberate
choice (Tez's call) since a permanent nav tab would cost one of the 4
visible-tab slots for something that doesn't need permanent nav presence. See
`EDITOR_SPEC.md` §13 for the full review-queue feature this button surfaces.

---

## 3. Flat View vs. Folder View parity

| Control | Flat View | Folder View |
|---|---|---|
| Sort dropdown | ✅ All criteria | ✅ All criteria except # of Pages |
| Ascend/Descend toggle | ✅ | ✅ |
| Rated filter | ✅ | ✅ (flat file cards only; folder cards unaffected) |
| Favourites filter | ✅ | ✅ (folder shown if any descendant issue is favourited) |
| Flagged-for-review filter (§2.8) | ✅ | ✅ (folder shown if any descendant issue is flagged) |
| Search | ✅ | ✅ (existing Folder View search behaviour — depth-agnostic, `CUSTOM_TABS_SPEC.md` §9.3) |
| Grid/List toggle | ✅ | ✅ |
| Status pills (§2.6) | ✅ | ❌ (no read-status concept for folder cards) |
| Secondary filters (§2.7) | ✅ | ✅ (flat file cards only; folder cards unaffected) |
| Grouping (`#groupBySelect`) | ✅ | ❌ (folder structure already groups by directory) |
| Item/title count | ✅ | ✅ |

---

## 4. Surfaces where the menu bar does NOT appear

Per `SPEC.md` §20.8: the fixed top menu does not appear on `/issue/{id}`.

The menu bar also does not appear on the Admin page or the Full Editor.

---

## 5. Change Log

> Record any deviations from this spec here with date and reason.

| Date | Change | Reason |
|---|---|---|
| 2026-06-23 | `MENU_BAR_SPEC.md` created — consolidates four inbox items (sort dropdown, Rated filter, Favourites filter, Folder View parity) into one unified menu bar spec. | Inbox triage 2026-06-23; Tez's explicit framing that Folder View should be functionally equal to Flat View. |
| 2026-06-23 | Built. Folder cards in Folder View are not individually re-sorted by the sort dropdown (only flat file cards are) — most criteria don't map onto a folder aggregate the way they do a series aggregate. | Scope decision made during build rather than left unspecified; see `DECISIONS.md`. |
| 2026-06-26 | Status pills moved from a separate `.browse-controls` row into the site header (§2.6); secondary filters + item count merged into the single menu-bar row, with `#groupBySelect` kept Flat-View-only (§2.7); secondary filters extended to Folder View's flat file cards, closing this spec's original Folder-View-parity gap. | Post-test fix pass (`docs/2.3-fixes.md` Fix 1) plus an additional step raised mid-session — see `docs/progress.md`. |
| 2026-07-07 | §2.6 Status Pills removed entirely — no per-surface status-pill row anywhere, on any surface. Read-status filtering (`activeStatus`) now only exists as the left sidebar's Unread/Reading/Read shortcut, which always navigates to the All surface first. Clicking it from Series/Singles/a custom tab no longer filters that surface in place. | v2.6 Item 1 Phase B (left sidebar nav) — matches the approved Claude Design reference exactly, not a gap being filled; see `docs/v2.6/progress.md`. |
| 2026-07-09 | Publisher filter dropdown removed from §2.7 (stays as a Group by option only); Grid/List toggle (§2.5) relocated from the trailing count group to sit with sort ascend/descend + Rated; vertical divider separators extended between every control in the row; Clear button (§2.7) relocated from `#browseFilters` into the trailing group next to the title count and unified visually with the fieldview banner's own Clear link. | Tez's post-redesign UI tweak pass — see `docs/v2.6/progress.md` and `DECISIONS.md`. |
| 2026-07-15 | Added §2.8, Flagged-for-Review Filter Button — a new toggle mirroring §2.3's Favourites filter exactly (same mechanics, same Folder View parity rule), part of the new review-queue feature (`EDITOR_SPEC.md` §13, v2.6 Item 8). §3's parity table gained a matching row. | Ad-hoc feature request 2026-07-15, scoped and built same session; see `v2.6/progress.md`. |
