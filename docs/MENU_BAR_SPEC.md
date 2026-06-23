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
the menu bar row for visual consistency.

---

## 3. Flat View vs. Folder View parity

| Control | Flat View | Folder View |
|---|---|---|
| Sort dropdown | ✅ All criteria | ✅ All criteria except # of Pages |
| Ascend/Descend toggle | ✅ | ✅ |
| Rated filter | ✅ | ✅ (flat file cards only; folder cards unaffected) |
| Favourites filter | ✅ | ✅ (folder shown if any descendant issue is favourited) |
| Search | ✅ | ✅ (existing Folder View search behaviour — depth-agnostic, `CUSTOM_TABS_SPEC.md` §9.3) |
| Grid/List toggle | ✅ | ✅ |

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
