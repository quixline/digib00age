# digib00age — Inbox

---

### Unprocessed

- [x] Clear (queue is broken) - fix and move between Process queue and Process all in column 4

- [ ] open web reader with page dimensions - whole thing needs full design review

- [ ] design review - mobile reader UI - get a closer consistency to the web ui, drop the outer glow around cards but keep the inner style and genre/info

- [ ] 

- [ ] do the css refractoring that's been planned

- [ ] **Scanner speedups:** — thumbnails are 53% of the 21.5 min, per-file commits 18%. Batching commits is the easy win (~4 min). Both need scoping; nothing's been attempted.

- [ ] scan code base - clean, removal of dead code, fix linting issues - other useful tasks to clean code base - do in focused sessions or overview then specific

- [ ] stress test - how? scan test - current collection - fake it?

- [ ] plan & build windows install package
  
  
  
  

---

## Processed

_19-07-2026_

* [x] [bug] full editor - load Empire of the Dead 1-15 all listed in correct order - selected #1, changed genre, applied all, increment # yes, process all = filenames dont match the xml issue numbers - #2 = #8 #3 = #9 and so on. check the select all function again. With Series and Processing All - first file selected dictates what is or isn't written to the other issues in the folder (or folders) if All is selected in any field, what is in that field gets written to All, if All is not selected for a particular field in #1 then the values of the other issues aren't changed. Because we dropped the drag n drop for the list view, the auto numbering seems to have failed and only now picked up when editing a larger number of issues.

_18-07-2026_

* [x] full editor needs to parse filenames

* [x] turn the genre ribbon to a href that loads the chosen genre - same as genre links in issue/series

* [x] admin page - reduce width and centre final section, Filename Editor is the only exception, all others can shrink at lease 50%

* [x] home page strips navigation needs to be pushed to the edge of the page removing the small gap

* [x] after a scan - the logs should only show the new entries not the whole log

_17-07-2026_

* [x] make the folder cards to match the others in size, border and image padding + effect

* [x] redesign the list view 1. make it 2 column by default, reducing to one if browser window pushes past the second column. 2. add 10px top padding to the rows and 50px gap between the columns. 3. make the genre tags into links 4. switch the font colour/weight = Issue that is Read has lighter and stronger font than those not read, it should be the other way so the emphsis is on the unread issue. Add the same random bg that the Grid view has

* [x] redesign series view - list and add grid, both should use the same properties that are already set

* [x] All library Grid view cards have a shadow - locate and remove while maintaining the blur glow if poss

* [x] All library Grid view cards - on hover the top glow gets cut off - add more space above

* [x] rename all "YYYY"" folders in 2000 AD dir to "2000 AD - YYYY""

* [x] when an issue is marked as read in the issue page - make the visual changes happen without the need for refreshing the page

* [x] on the issue page add "Read" button under card and before "Mark as Read" - When in the Reading state - change "Read" to "Continue Reading" both open the desktop reader

* [x] issue page - make the bg fit the whole area to the nav bar and header with less of a fade from the top so more of the image can be seen while keeping the same opacity with a slight blur

* [x] when an issue is in the Read state ensure the progress bar doesn't appear - it should only be visible in the Reading state

* ~~after selecting the first card with a double press, then shift + single clicking a card that comes later should select all the cards between the first and last card selected.~~

* ~~after deselecting the last card just deselect it, currently it deselects and opens the issue/series page for that card.~~_

_16-07-2026_

- ~~[bug] cover change in archive takes a long time to show in the library, refresh doesn't speed it up. eg a cover is shown in the library with a double cover/open book cover, archive unpacked, image edited to one page and archive repacked. Library scan detects changed file but doesn't update cover without some wait, when a scan detects the change it also needs to update the UI at a bare minum with f5 (-> BUGS.md, possible regression/duplicate of the 12-7-2026 cover-persist line below marked "not a bug" — this report says refresh doesn't fix it, worth re-checking)~~ → fixed same-session, 2026-07-16, as BUG-023 in `docs/archive/bugs-fixed-archive.md` (confirmed a regression from the 2026-07-13 cover-caching change, not a duplicate of the 12-7 report)

15-7-2026

- ~~[feature] scope - is there a way to tag issues in the library to easily then pull them into the XML editor. eg - various issues in different locations are identified as having incorrect info, I then have to locate each one manually and go through the file selection to get them into the editor~~

- ~~[change] when multiple issues are selected and sent to xml editor - add message - Sending files in the background - add auto refresh on editor window when complete~~

- ~~[change] mobile reader; build release apk for a permanent install~~

- ~~[feature] are there any performace improvements that can be made to speed up the time between clicking Edit XML in /issue/id to when the editor opens?~~

- ~~[change] mobile reader; build release apk for a permanent install~~

- ~~[change] stretch/span header to full width of the available space - site wide~~ → header + main content full-width site-wide, `.container`'s 1440px cap dropped; settled on a 30px L/R gutter after a live iteration (10px → 30px) — see `v2.6/progress.md` "Site-wide layout width, multi-cover background, scrollbars"

- ~~[change] remove/adjust container holding cards, issues, series that sets width, cards/details on all pages should fill the width available - with 10px gap left and right, 5px top - site wide change~~ → same `.container` fix as the header line above (both traced to the same rule) — resolved together, same session

- ~~[change] ajust the main bg that uses a random cover behind the cards and fades from to right to bottom - make it fade from across the top not just the corner but from that same level going down~~ → superseded by a full rework rather than a mask tweak: background now composites up to 4 real covers as a "cloud field" spread across the whole content area (zoned-random placement), fixing the coverage complaint as a side effect of the redesign — see `SPEC.md` §20.19, `DECISIONS.md` "Page background: multiple real covers, not a code-generated gradient"

- ~~[change] apply site wide style change to scroll bars - match the filter scrolls~~ → promoted the filter-dropdown (`.fd-panel`) scrollbar treatment to a global rule, reaching the main app, Admin, and the XML Editor. Found and fixed a same-session regression it caused (Editor's Genre dropdown popup rendering light instead of dark) — see `v2.6/progress.md`

14-7-2026

- ~~[change] the Full Editor has been redesigned using Claude Design - exported to D:\workshop\Claude Design\full editor. Also screenshot of old and new design D:\workshop\comicvault_v2\images~~ → built as v2.6 Item 7 (Full Editor 4-column redesign), 2026-07-14 — see `v2.6/comicvault-changes-v2.6.md` Item 7 / `EDITOR_SPEC.md` §5.4

- ~~[feature] open reader from web library~~

- ~~[bug] since bg change dd menus are displayed behind the cards~~

- ~~[change] rebuild desktop reader with new design~~

13-7-2026

- ~~[change] add pagination to /series/id~~ → built directly this session (no separate triage pass) as v2.6 Item 3 — see `comicvault-changes-v2.6.md`/`progress.md`

- ~~[change] replace taskbar icon with icon-oo.png - keep current green dot for server running, red for stopped - or offer alternative options if available~~ → `icon-oo.png` turned out to be a non-square 166×100 logo lockup, unusable as a tray glyph as-is; used `favicon.png` (square, transparent bg) instead, kept the existing 3-state dot mechanism unchanged — see `DECISIONS.md` "Tray icon base glyph"

- ~~[change] add a slight zoom and 80% white border 'on hover' over the cover image in issue/id~~ → built directly this session (cosmetic, no triage ritual) — `.issue-cover-img:hover` in `frontend/css/style.css`; see `progress.md` "Issue Detail cover: hover zoom + white border"

- ~~[change] add a random cover image to the page (<>container<>) bg on library pages (home, all, singles, series and custom tabs) the image should only be chosen from the current library page so for a custom library like 2000 AD only 2000 AD covers should be shown. The bg image should fill the container div and start at 40% transparancey with 50% blur from the top right fading completely out~~ → built directly this session — see `progress.md` "Random library-page cover background"

- ~~[bug] a performance review was carried out and found bottle necks, find the review and plan the execution~~

- 

12-7-2026

- ~~[bug] the rating from the bottom bar doesn't work when selecting one or multiple cards doesn't change the rating~~

- ~~[bug] if cover is removed from archive, library scan detects change but old cover persists (eg Dusk: Poor Tom)~~ **was not a bug but a page/browser refresh/time is and it's now showing.**
* ~~Project Folder: [change] remove the symlink to docs - google drive isn't required to be in the loop anymore~~

* ~~[bug] investigate missing Design assests - favicon.png, icon-oo.png and other data that was part of the Redesign from Design~~

2026-07-05

- ~~[feature] to scope - in the basic editor only I want to speed up the UX - currently a quick save hits a bottleneck when saving because the editor stays on screen until the archive has been rebuilt with the new xml data - possible solutions? the objective is to have the process running and allow user to navigate away as soon as save is activated~~
* ~~[change] the favourite icon in the top left corner of the cards from a gold star to a red heart with white bg~~
* ~~[change] the pill for number of unread titles after a series has been started, top right corner of the card from blue bg an black text to blue with white text~~
* ~~[feature] add a new pill to the bottom right of the card/cover make the bg of the pill the same as the star pill in the bottom bar with gold stars. have the stars starting from the bottom right going up/increasing in a vertical column~~
* ~~[change] the blue dot in the middle of the 'card selected' in the bottom left of the card to a gold tick with dark grey bg~~
* ~~[change] remove the card outline from Scan Now, Last Scanned and Changed files in the admin area~~

### Triaged 2026-07-05

- ~~[bug] mobile app - doesn't connect to 192.168.0.151:9424~~ → this is BUG-019, already fixed and archived 2026-07-04 (`archive/bugs-fixed-archive.md`) — inbox line lagged the fix.

- ~~[bug] Android: no way to associate .cbz/.cbr files to open in the app (spotted late 2026-07-04)~~ → added to `BUGS.md` as BUG-017, not yet scoped.

### Triaged 2026-07-03

- ~~[change] Admin page, remove the custom/editable path text input field from Add Custom Tabs. The user has the ability to Choose a folder with the custom folder nav-picker no need for both.~~ → deferred to `ROADMAP.md` "v2.6 — UI Redesign" scope, per Tez (2026-07-03) — low-priority polish, picked up alongside that redesign, nothing to build before then.

- ~~[change] Processing Folder Automation's Schedule/Time/Day row needs a separate "Save" click, unlike every other setting on that page (Convert Archives/Images toggles, quality slider) which auto-save on change. Found 2026-07-02 investigating a "scheduled run isn't firing" report — the Schedule dropdown had silently stayed on "Off" while Time/Day were being changed and saved, with no unsaved-changes indicator to catch it. The wall-clock mechanism itself is confirmed correct (ADMIN_SPEC.md §11.4.5). Candidate fix: make Schedule/Time/Day auto-save like the rest of the page, or add a clear unsaved-changes indicator. (-> ROADMAP.md or comicvault-changes-vN.M.md)~~ → deferred to `ROADMAP.md` "v2.6 — UI Redesign" scope, per Tez (2026-07-03) — same call as above, nothing to build before then.

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

- ~~[unknown] ComicTagger integration, session 1 (2026-07-03): does ComicVault's `ComicInfo.xml` scanner/writer round-trip unmapped fields (Story Arc, Series Group, Alt Series, Maturity Rating, etc.) untouched, or does the Editor's save rebuild XML from only the DB's known columns? If the latter, any file CT tags with extra fields will get silently stripped on first Editor save — needs checking before CT write-path is built.~~ → resolved same session by reading `field_merge.py`/`editor_basic.py` directly: `build_xml_from_fields` only touches tags present in the submitted payload, so any field CT writes that isn't in `COMICINFO_TAGS` survives every future Editor save untouched. No fix needed.

- [feature] ComicTagger integration, session 1: ported review UI needs an editable series-search-string field with re-search, not just a passive candidate list — confirmed real workflow (2000 AD "progs" → issue field correction happens routinely, matches CT's own "Specify series search string" + Re-Search). Two-level drill-down also confirmed required: series list (disambiguated by year/publisher/language) → issue list for selected series → confirm. **Full Editor integration question resolved (session 1, second half):** CT's match/review UI folds into the existing Full Editor rather than a separate page (`DECISIONS.md`) — this search dialog is the manual fallback for blank fields after automated Auto-Tag has already run, not a batch-trigger button. **Resolved (session 2, 2026-07-03):** modal overlay, confirmed — full design (both triggers, overwrite semantics, focus trap, shared search backend) locked in `DECISIONS.md`.

- ~~[unknown] ComicTagger integration, session 1: is 2000 AD's "progs" naming pattern predictable enough to fix upstream in the filename parser (auto-relocate to issue field before search), or does it vary too much per-issue to be worth automating? Affects whether the editable-search-field workaround above is the permanent solution or a stopgap. Tez to answer from real usage pattern.~~ → deferred, session 2 (2026-07-03): logged as a `[change]` not a `[bug]` — the Re-Search field already covers this workflow today (re-typing the issue number was already the real habit), nothing is blocked by leaving it. Small parser update to pick up whenever the CT cluster's big work is done (`DECISIONS.md`).

- ~~[unknown] ComicTagger integration, session 2 (2026-07-03): where does the ComicVine API key live? CT's `comictalker` ships a hardcoded shared default key, rate-limited to 1 req/10s / 100/hr (vs. 10 req/10s / 200/hr on a personal key) — confirmed by reading `comicvine.py`. No field for a personal key exists anywhere in ComicVault today; this blocks the CT Auto-Tag automation stage (session 1) as much as the search modal above.~~ → confirmed with Tez: new `comicvine_api_key` field in `config.json`, Admin UI field near Processing Folder Automation (`DECISIONS.md`).

- [change] CAPT: `create_rar_archive()` / CBZ→CBR conversion feature (`arc_conv_helpers.py`) is dead code from ComicVault's perspective per `DECISIONS.md` 2026-07-03 entry — candidate for removal from CAPT, not for porting. Requires real WinRAR CLI on PATH, out of scope permanently.

- [feature] ComicTagger integration, session 1 (second half, 2026-07-03): new `NeedsReview` (name TBD) XML tag, whole-file granularity, confirmed — see `DECISIONS.md`. Needs adding to `COMICINFO_TAGS` (`backend/editor/xml_parser.py`) plus explicit clear-on-save handling in both editor save routes (won't self-clear via the normal `field_merge.py` preservation mechanism, since it's never part of the submitted form payload). **Visual mechanism superseded, session 3 (2026-07-03):** not a §3.5-style badge — a colour-coded card border (reuses the existing favourited-card border convention, `SPEC.md`) plus an inline "N Low Confidence" count in Column 1; full detail in `DECISIONS.md`.

- [re-scope] ComicTagger integration, session 1 (second half, 2026-07-03): when CT integration is actually scoped for build, `ADMIN_SPEC.md` §11.4's automation pipeline becomes three stages, not two — Convert Archives → **CT Auto-Tag (new)** → Convert Images — following the same router-independent-callable/progress-singleton/`[AUTO]`-log-prefix pattern already established for the other two stages. Rename stays excluded from automation (unchanged, already decided) but its place in Tez's manual workflow moves to *after* Full Editor review rather than before. (-> `ADMIN_SPEC.md` §11.4, once this reaches an actual build session)

- [feature] ComicTagger integration, session 1 (second half, 2026-07-03): aggregate audit-run log for the automation stage ("12 converted, 11 confident, 1 flagged") confirmed wanted by Tez, explicitly deferred — not the mechanism the Editor reads (that's the XML tag above), just an operational log alongside whatever job-progress logging the CT automation stage needs. Build alongside that stage, not before.

- ~~[unknown] ComicTagger integration, session 1: mockup/screenshots for the combined Full Editor + CT UI (search dialog placement, loaded-file warning-badge state) not yet done — Tez's stated next step.~~ → superseded, session 3 (2026-07-03): mockup dropped entirely — worked directly from two CT screenshots + source reading instead. Full search/select UI detail locked (`DECISIONS.md`).
