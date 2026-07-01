# ComicVault — Inbox

Raw capture only. Jot a line whenever, from whatever device, in whatever shape
it's in — no formatting pressure beyond the tag. Nothing here is a decision;
real classification and placement happens in a triage session with Claude
Chat. This file should never need "getting right" before something goes in it.

**Tag convention** — one of:
- `[bug]` — something that was scoped, planned, and implemented, but doesn't
 work correctly.
- `[change]` — something already in place that should look or behave
 differently (most likely front-end/visual — "add a border colour around X").
- `[feature]` — something new that doesn't exist yet.
- `[unknown]` — not sure which of the above it is yet. Better to mark unknown
 than guess wrong on purpose.

Add a guess at the destination doc if one's obvious (`BUGS.md` /
`comicvault-changes-*.md` / `ROADMAP.md`) — skip it if you don't know, that's
what triage is for.

**Format per line:**
`- [tag] one-liner or short explanation (-> guessed doc, optional)`

**On triage:** the line gets struck through, tag left exactly as originally
entered (even if it turns out wrong — that's the point, see `DECISIONS.md`
if a pattern's worth recording), and annotated with where it actually landed.
Example:

```
- ~~[bug] series cover doesn't update after editor save~~ → added to BUGS.md as BUG-009
```

**Sunday prune:** anything struck through and 7+ days old moves to
`inbox-archive.md`. Untouched/unprocessed lines, regardless of age, stay here
until triaged — only processed lines ever leave.

---

## Unprocessed

(empty — add lines below this heading as they come to you)

[change] Admin page, remove the custom/editable path text input field from Add Custom Tabs. The user has the ability to Choose a folder with the custom folder nav-picker no need for both.

---

## Processed (awaiting Sunday prune)

### Triaged 2026-06-28

- ~~[feature] Add "Password Recovery" button to Admin - simple popup with instructions on restting password through the config.json - this replaces the info in the guide, the guide just points to this button~~ → added to comicvault-changes-v2.3.md as Item 10; ADMIN_SPEC.md §7.1.7 to be amended once built

- ~~[bug] going from All - http://localhost:8000/issue/2769?from=all then back button took to home ?~~ → added to BUGS.md as BUG-014 (regression — see below, two more repro cases merged in)

- ~~[bug] select genre from issue page lists those genres, correct function. there's no way of clearing http://localhost:8000/?surface=fieldview&field=genre&value=Comedy from the UI. the genre dd menu shows genre not comedy so that doesn't reset and selecting a new tab changes the surface but not the url/genre, selecting a different genre from dd menu then resetting by seleting 'Genre' does reset what's displayed to all genres but the url still says comedy so selecting an issue/series then going back resets the list to show Comedy because the back button reads the url~~ → added to BUGS.md as BUG-015

- ~~[change] reduce number of options for db backup frequency to every day, wk,  month, 6 months, 1 yr~~ → added to comicvault-changes-v2.3.md as Item 11; ADMIN_SPEC.md §9 to be amended once built

- ~~[feature] needs a restore database option~~ → added to comicvault-changes-v2.3.md as Item 12; ADMIN_SPEC.md §2/§9 area, not yet scoped

- ~~[change] Add 75% to the card size options in admin~~ → found the underlying Card Size control already existed (built v2.1, 2026-06-22) but was never written into ADMIN_SPEC.md — backfilled §6 this session; the 75% addition itself added to comicvault-changes-v2.3.md as Item 13

- ~~[bug] Issues page: Stars - fixed on Selection (tabs/surface) with X to remove. Ideadlly the fix on the issue page is clicking the star(s) twice removes the rating.~~ → folded into existing BUG-009 as an addendum, not a new entry

- ~~[change] make the main header appear across the whole site inc /series/{id} & /issues/{id} - this should be the same as the home page - 'Search' searches all library unless on a Singles, Series or Custom Tab~~ → added to comicvault-changes-v2.3.md as Item 14; destination spec doc TBC, needs scoping (later moved to ROADMAP.md 2026-06-28, blocked on Claude Design exploration)

- ~~[bug] This issue was fixed - why has it come back, how to fix permenantly - go from series tab - http://localhost:8000/series/2589?from=series - click <- Back it takes me to the home page.~~ → merged into BUG-014 as a second repro case (regression of the Tier 1 back-button fix in `comicvault-changes-2.1.md`)

- ~~[bug] go from singles tab - http://localhost:8000/issue/5478?from=singles - click <- Back it takes me to the home page.~~ → merged into BUG-014 as a third repro case (same regression)

### Triaged 2026-06-23

- ~~There is something that was missed during the original scoping... displaying images from the archives in the folder~~ → overlap with today's v2.3 Folder View card work, no new action needed

- ~~[bug] Clicking on one star after its already highlighted should unhighlight it...~~ → added to BUGS.md as BUG-009

- ~~[bug] from 2000 ad tab - year 1979 - issue/{174} - writer pat mills...lists All 2000 ad progs in list view not just the ones the one pat mills is credited for~~ → added to BUGS.md as BUG-010

- ~~[bug] Admin page - "Scan Roots" 'Add' button currently doesn't open file dialog~~ → added to BUGS.md as BUG-011

- ~~[change] The favorite star added to the cards (top left corner) should be bigger by 5px with a 1px black border~~ → added to SPEC.md (general card behaviour)

- ~~[change] On the issue/{id} page the stars should be the width of the buttons as a row...~~ → added to SPEC.md (general card behaviour)

- ~~[change] The Sort button to a dd menu - to include A-Z, Newest, Recent, # of Issues, # of Pages~~ → added to comicvault-changes-v2.3.md (merged with Ascend/Descend item below; # of Pages restricted to flat issue-list views only, not folder/series cards)

- ~~[change] Admin; Reader Location - placeholder needs to be worked in so that - Read on the issue page works...~~ → merged with item below, parked in ROADMAP.md — needs further scoping (same-machine-only limitation identified), may be dropped

- ~~[change] Connect 'Read' on /issue/{id} to the reader set in Admin - Needs admin and connection to app first~~ → parked in ROADMAP.md (see above)

- ~~[change] Backup Database Location - currently it saves it only to the app folder /backend...~~ → merged into Admin "Schedule database backup" feature, added to ADMIN_SPEC.md (new doc)

- ~~[feature] Add the menu bar that appears in the Flat view to the Folder view (discuss value/function)~~ → merged into new "Unified Menu Bar" feature, new standalone spec doc (name TBC, e.g. MENU_BAR_SPEC.md)

- ~~[feature] The menu bar needs Decend/Ascend button after the sort menu~~ → merged into Unified Menu Bar feature, same new doc

- ~~[feature] Add a user rated dd menu "Rated" 1-5 Stars...~~ → merged into Unified Menu Bar feature, same new doc

- ~~[feature] Add a favorites button to menu - shows all favorites in the selected tab~~ → merged into Unified Menu Bar feature, same new doc

- ~~[change] Cards that have been favorited should also have a thin gold border round the card regardless of read state~~ → added to SPEC.md (general card behaviour)

- ~~[feature] Full Editor: Apply to: All check boxes added to all fields...~~ → added to EDITOR_SPEC.md (default unchecked; issue number excluded, stays auto-increment only)

- ~~Admin page specific new Features [whole block]~~ → split: password popup, remote admin toggle (gated on password being set), Clear Database, Clear Reading Progress, Auto Scan Options, Donate button, server port, view logs+size limit, scheduled backup (merged w/ backup-location item above) all added to new ADMIN_SPEC.md. Genre/Format add-remove line struck as duplicate of existing backlog #1.

- ~~[feature] card = last scanned -> ... missing records -> missing_log.md...~~ → added to ADMIN_SPEC.md. Open TODO flagged for Claude Code: confirm actual scanner change-detection behaviour (XML changes, filename-as-rename, size-change handling) before finalizing "type of change" wording. Missing-records log = filename + path + date went missing.

- ~~[feature] Add the Admin cog-link to the full editor...~~ → added to ADMIN_SPEC.md

- ~~[feature] Tips (mouse over) to be added across the site...~~ → parked in ROADMAP.md, no spec yet

- ~~[feature] Add move up/down option to Genre & Format editing~~ → folded into existing backlog #1 scope (Genre/Format admin-editable lists), no separate entry

- ~~[feature] Add: the Select option to 'Series cards'...~~ → backlog #2 scope amended to include whole-series multi-select; decision (reversal of earlier scoping) recorded in decisions.md

- ~~[feature] Add - OPDS - Need more info but for external readers to be able to connect~~ → parked in ROADMAP.md, merged with Komga-compatibility research note (same underlying goal, needs joint research)

- ~~[feature] Add: Dark/Light theme - match windows theme/over ride?~~ → added to SPEC.md (auto-match Windows theme, manual override toggle available)

- ~~[feature] Add extra CAPT tools - code, logic already done - needs inspecting or bringing in...~~ → parked in ROADMAP.md, needs dedicated planning session

- ~~[feature] Add: New Admin area/fearure - Processing folder settings...~~ → parked in ROADMAP.md, needs dedicated planning session

- ~~[feature] Add: Integrate ComicTagger and ComicVine API...~~ → parked in ROADMAP.md, needs dedicated planning session (per Tez's own "big project, needs planning" note)

- ~~[feature] Build - Windows Installer~~ → duplicate of existing V2 scope item, no new entry

- ~~Work with Claude Design for redesign options...~~ → duplicate of existing parked item, no new entry

- ~~Mobile Reader App **On Hold**... [both sub-items]~~ → folded into existing on-hold Mobile Reader ROADMAP note as future scope detail

- ~~[re-scope] **§12.1 File Rename needs re-scoping before Item 10 is built.** Current spec is a CAPT port (four fields + checkboxes). Automation (Item 15) requires a template-based naming convention system: user defines format (e.g. `{series} #{issue} ({year})`), tests it against real files in the manual tool with live preview, saves it; automation pipeline then applies the saved template. Cloned rename tool available for logic inspection as part of this pass. Default template for automation ("Default Parsing") also needs to be defined. `[AUTO]` prefix log behaviour and `processing_folder_rename_template` config key already specified in §12.4 — §12.1 re-scope must align with those.~~ → re-scoped 2026-07-01: found and fixed three real parser bugs (stale hardcoded year ceiling, zero-issue stripping, volume/subtitle whitespace loss) instead of building a template system. Rename stays manual-only, dropped from Item 15's automation entirely (`DECISIONS.md`, `admin-spec-section-12-processing-tools.md` §12.1.3/§12.4 Change Log)

- ~~[re-scope] **§12.2 Convert Archives backup model amendment.** Item 15 scoping settled a unified backup model that supersedes §12.2's current "Delete Original File" checkbox. Amendments needed: (1) remove "Delete Original File" checkbox (§12.2.3) entirely; (2) replace "Output file already exists" guard (§12.2.4) with "refuse if `.bak` already exists for this file"; (3) add the clean-success/success-with-warnings/failure `.bak` table from §12.4.6. Also confirm core conversion function is specified as a router-independent callable (same requirement as §12.3.8 — needed for Item 15 to invoke it directly).~~ → written into `admin-spec-section-12-processing-tools.md` §12.2/§12.4.6 2026-07-01, during the pre-build v2.4 doc sanity check (all three amendments applied, plus the callable requirement added to §12.2.7)
