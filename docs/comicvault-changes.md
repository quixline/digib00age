# ComicVault — Planning Backlog
> Replaces `comicvault-changes.txt`. Finalized 2026-06-20. This is the planning
> reference going forward — work through it top to bottom.

---

## Status check (confirmed this session)

- V1 (original `SPEC.md`, Phases 1–6): **complete**.
- Editor integration (`EDITOR_SPEC.md`): **complete**.
- Custom Tabs (`CUSTOM_TABS_SPEC.md`), Home Strips (`HOME_STRIPS_SPEC.md`), Taskbar
  App: **all complete**, per `progress.md`. (Taskbar App and the Mobile Reader item
  below were originally tracked in a doc called `v2_1-main-new-features.md`, which no
  longer exists — this file is now the source of truth for both.)
- Mobile Reader changes: **deprioritized, not started.** The reader works as-is
  (tablet connects to the library, reading works fine) — left until everything below
  is done, and may be skipped entirely in favour of using a third-party reader app
  instead. Not part of the active queue.

Everything below is new work, all genuinely additive on top of a finished original
brief — there's no fixed "done" point from here, just an ordered queue.

---

## Build queue — Tier 4 (the big items, in agreed order)

**1. Genre/Format admin editor** — smallest, lowest-risk, build first — **done, 2026-06-20**
- Add Format as a second admin-editable, file-backed list alongside the existing
  Genre mechanism (reverses `EDITOR_SPEC.md`'s "Format = locked constant" decision —
  log as a deviation there once built).
- Surface both in the Admin pages for add/remove.
- No schema change, no data migration.
- **Unblocks:** the manual Genre cleanup below (Tier 5) becomes doable once this ships.
- Built and verified — see `progress.md` "Session — 2026-06-20: Tier 4 Item 1" for
  what shipped and how it was checked (Genre didn't actually have admin UI before this
  either, so both lists got add/remove built, not just Format).

**2. Multi-select + Favorites/Rating** — medium, additive — **done, 2026-06-21**
- Long-press to select a card, further short clicks add more cards to the selection.
- Bulk actions on the selection: Read/Unread, Add to Favorites, Rate (1–5).
- "Read selected" (from the original notes) is part of this.
- New DB fields: `favorites`, `personal_rating` — additive, but turned out to need a
  small one-time `ALTER TABLE` migration after all (see `DECISIONS.md` — `create_all()`
  only creates missing tables, not missing columns on an existing one).
- Scope confirmed before building: multi-select only on cards/rows that map 1:1 to a
  single issue (Singles, series-detail rows, 2000 AD prog cards) — not series-aggregate
  cards. Favorites has no dedicated browse tab yet (deferred, see `ROADMAP.md`).
- Built and verified — see `progress.md` "Session — 2026-06-21: Tier 4 Item 2" for
  what shipped and how it was checked.

**3. Writer/Artist entity dedup + search/link UI** — largest, highest-risk —
**done, 2026-06-21**
- Dedupe people into real entities (one "Alan Moore" row regardless of how many
  issues credit him) — replaces today's raw-CSV writer/artist fields with a people
  table + junction tables.
- Drop the long Writer/Artist filter dropdowns entirely; replace with search +
  click-through linking. **Correction found during build:** the backlog's "same
  pattern as the new Genre links on `/issue/{id}`" doesn't apply — that Tier 2 item
  isn't built yet either (genre tags are still plain non-clickable spans). Item 3's
  click-through is its own new mechanism, just reusing existing `fieldview` plumbing
  for the target page.
- **One-time migration/merge pass — done.** 76 candidate duplicate pairs detected
  (exact-normalization + fuzzy matching) out of 3,738 distinct names across all 6
  credit roles; reviewed and decided one-by-one via a temporary admin page (35
  confirmed merges, 41 correctly kept separate, including a deliberate
  disambiguation pair, "Matt Smith (UK)"/"Matt Smith (US)"). Migration ran for real
  against `comicvault_v2.db` on 2026-06-21.
- **Frontend — done.** Writer/Artist dropdowns removed; credited names on
  `/issue/{id}` are now clickable links to a filtered issue list; editor warns
  (non-blocking) on save if a typed Writer/Penciller name is close to an existing
  one. See `progress.md` "Session — 2026-06-21: Tier 4 Item 3" and "...— Session C"
  for the full build, an incident encountered during editor-save testing (a real
  CBZ's metadata was briefly modified, then fully restored and verified — no data
  lost), and a separate, pre-existing, unrelated bug found as a side effect
  (BUG-007, Basic Editor Summary field line-break doubling — logged, not fixed).
- **Remaining (a later, separate session):** drop the old raw CSV credit columns on
  `Issue` — kept for now as a rollback safety net, once the new system has run for
  real with no issues found over a release cycle.

*(Reasoning for this order, for reference: smallest/lowest-risk first to keep
momentum, defer the schema-changing + real-data-migration item until last.)*

---

## Tier 1 — Bugs (ride along with whichever session is running)
- **List view "Read" row unreadable** — grey text on green background. Copy grid
  view's white/bold styling across to list view.

## Tier 2 — Small UI/cosmetic (ride along, no dependencies)
- Genre tags on `/issue/{id}` → clickable links into All, filtered by that genre
- "Clear" text (appears after a menu change) → fixed small button, same behaviour
- Add "Format" to the Grouping option menu
- Add "mark all read" to the 2000 AD Year page (`/?surface=Series`)
- Admin: pagination — add 25 as an option, keep 50 as default
- Admin: rename "Save Advanced Settings" → "Save Location" (reader exe location only)
- Admin: white border on Scan Now (idle) / green border while scanning
- Admin: green border on Clean Up when there are files pending cleanup
- Admin: reduce dashboard width to align with header width

## Tier 3 — Medium, self-contained (ride along, slightly more design)
- Home page search bar; unify search behaviour/copy with the All tab — "Search All"
  (home + All tab), "Search Singles", "Search Series"
- Card size control — 10% / 25% / 50% / 100% (library view, not admin-only)

## Tier 5 — Manual/non-dev tasks **These are either completed or deferred and can be ignored** 21/6/2026 Tez
- Genre additions: Anthology, Comic, Omnibus — do this once item 1 above ships, as a
  manual edit through the new admin editor, not a separate feature
- Logo + .ico needed
- Check the YouTube AI video re: draw.io skill / visual app-mapping (personal note)

---

## Decisions log (resolved this session)
- Format becomes admin-editable, same mechanism as Genre — deviation from
  `EDITOR_SPEC.md`, log there once built.
- Genre additions deferred to a manual pass after the admin editor ships, not built
  as a feature.
- Home Strips gets an "Auto Saved" message instead of a manual save button — no
  change to the already-specced auto-save behaviour itself.
- Duplicate ComicInfo.xml files found in `thanksgiving.cbz` / `tales of ruination.cbz`
  are pre-editor library debris — folded into `EDITOR_SPEC.md`'s existing multi-XML
  detection feature as real test cases, no separate investigation needed.
- Writer/Artist work has an agreed direction (dedupe + search/link, not a dropdown),
  confirmed as Tier 4 item 3, sequenced last due to migration risk.
- Mobile Reader work parked indefinitely — reader works fine as-is; revisit only
  after all web/server work (i.e. everything above) is done, if at all.

## Change Log
| Date | Change | Reason |
|---|---|---|
| 2026-06-20 | Doc created from raw `comicvault-changes.txt`, conflicts resolved, sequencing agreed (1→2→3) | Initial planning pass, end of session |
| 2026-06-21 | Tier 4 Item 2 (Multi-select + Favorites/Rating) built and verified | See `progress.md` "Session — 2026-06-21: Tier 4 Item 2" |
| 2026-06-21 | Tier 4 Item 3 (Writer/Artist dedup) backend + real migration done; frontend UI deferred | See `progress.md` "Session — 2026-06-21: Tier 4 Item 3" |
| 2026-06-21 | Tier 4 Item 3 frontend (Session C) done — item fully complete. Editor-save testing incident (real CBZ briefly modified, fully restored) and an unrelated bug found (BUG-007) | See `progress.md` "Session — 2026-06-21: Tier 4 Item 3 — Session C" |
