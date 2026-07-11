# ComicVault v2.6 — Progress Log

## Session — 2026-07-06

- `docs/v2.6/` working folder created.
- Web UI redesign (v2.6 Item 1) scope captured in
  `comicvault-changes-v2.6.md`: nav relocation (top tabs → left nav),
  "Libraries" concept replacing Custom Tabs, full colour/typography/
  spacing overhaul, Admin page stats-card redesign. Home strips confirmed
  unchanged.
- Redesign detail lives in the Claude Design project + inline annotations,
  not duplicated into docs. Handoff to Code planned for 2026-07-07.
- BUG-014 and BUG-015 explicitly deferred — not folded into this item.
- Mobile/Flutter redesign confirmed as a separate, independently-scoped
  item — not started.
- Open question flagged, not blocking: "Libraries" naming vs
  `CUSTOM_TABS_SPEC.md`'s existing "Custom Tabs" terminology — to be
  resolved before post-build spec updates.
- BUG-016 (Restore Database) discussed and deliberately left unfixed for
  now — DB is still in a raw/testing state with nothing worth preserving,
  so a failed restore just means a rescan. Revisit before packaging, not
  before this redesign.

## Session — 2026-07-07 — Web UI Redesign Phase A built

- Pulled the `digib00age` design handoff (Claude Design project
  `7593e236-da17-4d60-8a70-47dbf88acb5c`, folder `design_handoff_v2.6_admin/`)
  into a Code session via the newly-authorized `claude_design` MCP
  (`/design-login`). Read the design system readme, token CSS
  (colours/typography/spacing/elevation/fonts), and the `Library.html`/
  `parts.jsx`/`screens.jsx`/`admin.jsx` click-through prototype before
  planning anything.
- Confirmed two decisions with Tez before building: (1) **phased build** —
  this session does Phase A only (design tokens + brand rename); Phase B
  (left sidebar nav), Phase C (Admin IA restructure), Phase D (Series/Issue
  visual polish) are separate future sessions, each with its own test +
  close ritual. (2) **Visible brand rename to digib00age is in scope** —
  not explicit in this doc's Item 1 bullets, only in the design system's own
  readme, so it needed an explicit yes/no rather than being assumed.
- **Token merge:** kept the existing short CSS variable names
  (`--bg`, `--surface`/`-2`/`-3`, `--accent`, `--text`/`-2`/`-3`, `--border`,
  `--radius`/`-lg`) rather than renaming ~2,193 lines of `style.css` — only
  remapped their *values* to the new dark-first palette (accent blue
  `#0A5FFF`, 4-step surface scale, etc.) and added new semantic aliases
  (`--surface-card`, `--text-secondary`, etc.) plus a large set of additive
  tokens (spacing scale, font tokens, shadow tokens, motion tokens) that
  didn't exist before, so Phases B–D can write new CSS against the design
  reference's own variable names directly.
- Swept `style.css` for hardcoded hex literals that should have been
  variables (`#4caf76` in `.cover-card.state-read`, `#f0c419` favourite gold
  in 7 places) and routed them through the new `--state-read`/`--favourite`
  tokens. Left unrelated ad-hoc colours (editor low-confidence indicator,
  various error/warning reds/ambers) untouched — out of scope, not part of
  the locked read-state/favourite system.
- Added Hanken Grotesk + JetBrains Mono via the design system's Google Fonts
  `@import` — this is the app's first external network dependency (previously
  fully self-hosted/offline-capable). Not blocking; self-hosting the
  `.woff2` files locally is a flagged fast-follow if that ever matters.
- Brand rename: pulled `favicon.png`/`lockup-light.png`/`lockup-dark.png`
  from the design project into `frontend/images/`, added theme-aware
  `.site-logo` markup (swaps lockup variant via `[data-theme]`, same pattern
  as the colour tokens) across all 6 real page shells (index/admin/series/
  issue/editor_full/guide — `editor_basic.html`/`login_popup.html` are
  fragments with no `<head>`, not applicable), updated every `<title>` and
  added `<link rel="icon">`. Caught during manual testing: `app.js` also sets
  `document.title` dynamically on the Series/Issue detail pages (after the
  static `<title>` renders) — missed on the first pass since it's JS, not
  markup; fixed both call sites. Left `readBtn.title = 'Open in ComicVault
  app'` (issue page, links to the `comicvault://` deep link) and the
  `comicvault://` URL scheme itself untouched — the Flutter app is still
  literally named ComicVault and isn't part of this redesign, so renaming
  that tooltip would have been inaccurate, not just cosmetic.
- **Verified manually** — started the real backend (`start_server.py` against
  the actual `L:\Comic Archives` library, read-only browsing, no writes) and
  drove it in a real Chrome tab: Home strips, All/Series browse grids, Series
  detail (backdrop + read-state issue rows), Issue detail (read/favourite
  button states), and the unmodified Admin page, all in both dark and light
  theme (`localStorage.cv_theme` toggle). No console errors. Confirmed Home
  strips are pixel-for-pixel unchanged (explicitly out of scope for all of
  Item 1). Stopped the manually-started dev server afterward so it doesn't
  linger and conflict with the tray app's own instance later
  (`ADMIN_SPEC.md` §7.3 already documents this exact risk).
- `docs/SPEC.md` §1 got a short note explaining the visible-name split
  (digib00age in the UI, ComicVault everywhere else) rather than a rewrite —
  the rest of the doc's "ComicVault" usage is architecture/internal naming,
  correctly unchanged.

## Session — 2026-07-07 — Web UI Redesign Phase B built

- Replaced the top `.surface-nav` tab bar (Home/All/Singles/Series) and the
  header's `.status-pills` row with a collapsible left sidebar
  (`.app-sidebar`, 60px rail / 208px expanded, state in
  `localStorage.cv_sidebar_collapsed`), per the design reference
  (`Library.html`'s `App()` component and `parts.jsx`'s `AppHeader`).
- **Real behaviour change, not just relocation:** read-status filtering
  (Unread/Reading/Read) is no longer a per-surface toggle — it's a sidebar
  shortcut that always jumps to the All surface, pre-filtered. Today you
  could filter Series, Singles, or a custom tab by read-status in place;
  after this phase that's gone, matching the approved design exactly (no
  status-pill row exists anywhere in the reference — `screens.jsx`'s
  `BrowseScreen` filter bar doesn't have one). Confirmed this wasn't an
  oversight by re-checking the design reference before building, not after
  a complaint. Also fixed a latent bug this surfaced: `getFilteredLibrary`'s
  status filter applied unconditionally regardless of `activeSurface` — a
  quick-status jump followed by a plain sidebar click to Series would have
  silently kept filtering Series by the stale status with no visible
  indicator. Fixed by resetting `activeStatus` on every `switchSurface()`
  call unless it explicitly opts in via a new `keepStatus` flag (only the
  quick-status handler sets it).
- The design's `App` component keeps the sidebar mounted across Home/
  Browse/Series/Issue (hidden only on Admin) — the real app doesn't have a
  single SPA shell like the prototype does; `index.html`, `series.html`,
  and `issue.html` are three separate pages sharing one `app.js`. Added the
  same sidebar markup to all three. Series/Issue aren't part of the SPA
  surface-switching machinery, so a sidebar click there is a real
  `location.href` page load back to `index.html` (same pattern the existing
  "← Back" links already use), including `?surface=all&status=unread`-style
  params so a quick-status click from Series/Issue lands pre-filtered.
- `loadCustomTabsNav()` now renders into the sidebar's Libraries section
  (colour-dot + name, cycling `--accent`/`--favourite`/`--state-reading`/
  `--danger`) and runs on all three pages, not just the library page.
- Caught two gaps during implementation, not during testing: forgot the
  `.app-content { flex: 1 1 0%; min-width: 0; }` rule needed for the
  content column to actually fill the space beside the sidebar (would have
  rendered too narrow); referenced a `.ds-eyebrow` class from the design
  reference's own kit-local CSS that was never ported into the real
  `style.css` — swapped for the app's existing near-identical
  `.section-label` class instead of introducing a duplicate.
- **Verified manually** — same method as Phase A (real backend against
  `L:\Comic Archives`, read-only). Confirmed: collapse/expand persists
  across reload; primary items (Home/All/Singles/Series) highlight
  correctly and navigate; Libraries items (2000 AD, Favourites) navigate to
  the right folder-view/flat content with correct active highlighting;
  clicking Unread from inside a custom tab's Folder View correctly jumped
  to All filtered (2,909 of 5,427 titles) with both All and Unread
  highlighted; sidebar renders with nothing active on Series/Issue pages
  (correct — neither maps to a `data-surface`); Admin page unaffected
  (still no sidebar, Phase C territory); dark and light theme; no console
  errors on any page. One process-cleanup gotcha worth remembering: this
  session's `python start_server.py` actually ran as `pythonw.exe`, not
  `python.exe` — the first stop-server attempt filtered on the wrong image
  name and missed it; had to find it via `Get-NetTCPConnection -LocalPort
  9424` instead.
- Updated `MENU_BAR_SPEC.md` §2.6 (status pills — struck through, marked
  superseded, original text kept per the doc's own convention) and
  `CUSTOM_TABS_SPEC.md` §5.2 (nav bar — noted the sidebar move, Libraries
  UI copy vs. unchanged internal "Custom Tabs" naming), both with their own
  Change Log entries, since both docs described behaviour this phase
  changed.

### Follow-up — same day, post-test adjustments (Tez's review of Phase B)

Tez tested live and flagged three fixable items, no show-stoppers:

- **Hamburger toggle now stays fixed at the sidebar rail's x-position; the
  logo shifts right instead** when the sidebar expands — previously both
  sat at a fixed position since the header wasn't responding to sidebar
  width at all. Matches the design reference's `AppHeader` exactly: a
  fixed 60px `.sidebar-toggle-col`, then a `.sidebar-header-spacer` whose
  width is 148px (208px expanded − 60px rail) collapsing to 0 via
  `body.sidebar-collapsed`, sitting between the toggle and the logo.
- **Sidebar now reliably reaches the bottom of the viewport.** Root cause:
  `.site-header` had no explicit height (content-driven, ~55px) while the
  sidebar's sticky `top`/`height` calc assumed the `--header-h` token
  (56px) — a small but real mismatch. Made `--header-h` authoritative by
  giving `.site-header` an explicit `height: var(--header-h)` instead of
  just padding, so the two can never drift apart.
- **Home/All/Singles/Series now render as real icons** (house/grid/single-
  book/stacked-layers, inline SVG matching the existing settings-gear's
  stroke style — `stroke-width: 2`, `currentColor`) instead of the two-
  letter monogram badges ("Ho"/"Al"/"Si"/"Se") from the first pass, which
  weren't what Tez saw in the Claude Design tool.
- **Libraries dot colours** — Tez reported seeing "# A-Z" text instead of
  coloured dots for custom-tab entries (e.g. "#" for 2000 AD, an
  uncoloured "A" for an "Action" tab). Not reproduced after this round of
  fixes: tested dark and light theme, zoomed screenshot confirms proper
  coloured circles (blue for 2000 AD, gold for Favourites), no text
  content in `.app-sidebar-dot` in the current code at all. Possibly a
  stale-cache artifact from before this session's fixes (same browser
  hard-reload gotcha hit during Phase A/B testing — cached `app.js`/
  `style.css` serving old content after an edit). Flagged back to Tez to
  confirm on a hard reload; not independently reproducible, so no code
  change made for this specific item.

### Second follow-up — same day, screenshots from Tez confirm/refute the above

Tez sent three screenshots. Two things changed:

- **Libraries dots — confirmed correct**, not a bug. Both screenshots (rail
  collapsed and expanded) show properly coloured circles (blue 2000 AD,
  gold Favourites) in both states — matches what this session's own testing
  found. No further action.
- **Hamburger alignment — genuinely still broken, screenshot proved it.**
  Root cause was different from what the first fix addressed: the toggle
  button was nested inside `.container.inner` (`max-width: 1440px; margin:
  0 auto`), which centres itself with empty margin on both sides on any
  viewport wider than 1440px — while `.app-sidebar` sits *outside* that
  container, flush to the true left edge. The two were never structurally
  guaranteed to align; the first fix only handled the toggle-stays-put/
  logo-moves *behaviour*, not this positioning bug. Fixed by moving
  `.sidebar-toggle-col`/`.sidebar-header-spacer` to be direct children of
  `.site-header` (itself now the flex row) — siblings of `.container.inner`,
  not nested inside it — so the toggle sits at the true viewport edge like
  the sidebar does, and `.inner`'s own `.container` centring applies only to
  the *remaining* space after it, matching how `.app-content`'s `.container`
  behaves below.
- **"Nav bar doesn't extend to the bottom" — root cause found: `--header-h`
  was never defined.** It was referenced in three places (`.site-header`'s
  height, `.app-sidebar`'s sticky `top`, `.app-sidebar`'s `height: calc(...)`)
  but never added to `:root` — the token additions during Phase A listed a
  "Layout" group (`--container-max`, `--container-pad`, `--header-h`) in
  planning but only the first fix's own new usages of `--header-h` actually
  got written, not a definition. An unresolvable `var()` makes the whole
  property invalid, so `top` silently fell back to `auto` and `height`
  fell back to content-size (~453px) — meaning the sidebar was **never
  actually sticky or full-height at any point in Phase B**, on any page,
  it just happened to look right in short viewports/short pages where the
  natural content height was close enough to viewport height to not be
  obviously wrong. Confirmed via `getComputedStyle` + a direct CSSOM rule
  dump before fixing (`headerHVal: ""`, `computedTop: "auto"`) — a
  scroll-to-bottom test on the 2483-issue "2000 AD" series page (very long
  scroll, ~286,000px) now keeps both the header and the sidebar correctly
  pinned throughout. This was the real, single root cause behind both the
  "hamburger in the wrong place" *symptom Tez saw at a glance* (a stationary
  header reads as "misplaced" when it should be moving with intent) and the
  standalone "doesn't reach the bottom" report — fixing `--header-h` alone
  would very likely have resolved most of the visual wrongness even without
  the container-nesting fix above, but both were real bugs and both are now
  fixed.
- Verified end-to-end after both fixes: scrolled to the bottom of the "All"
  grid (paginated, 5,427 titles) and the 2000 AD series page (2,483 issues)
  at a 1920×1040 window — header and sidebar both remain pinned in every
  case; toggle stays fixed, logo shifts on expand/collapse; dark and light
  theme; no console errors.

### Third follow-up — same day, Libraries markers + width (screenshots from
the live Design canvas, not the handoff files)

Tez sent two screenshots straight from the Claude Design tool (not the
static handoff bundle read during Phase A planning — a later iteration)
and said there should be **no dots in the nav bar at all**, plus asked for
a narrower sidebar:

- **Expanded state:** Libraries items are plain text, no marker of any
  kind — confirmed from the screenshot, not assumed. Removed
  `.app-sidebar-dot` and the per-item colour-cycling
  (`LIBRARY_DOT_COLORS`) entirely.
- **Collapsed state:** Libraries items show a single-letter badge instead
  (accent-blue circle, white letter — same colour for every item, not
  varied) — "#" for 2000 AD (name starts with a digit), "F" for
  Favourites. New `libraryBadgeChar()` (`app.js`) computes it; new
  `.app-sidebar-lib-badge` CSS, hidden by default and shown only via
  `body.sidebar-collapsed`.
- **Width decreased** from 208px to 180px (`.app-sidebar`,
  `.sidebar-header-spacer` recalculated to 120px = 180−60 rail), and
  `.app-sidebar-item`'s icon-to-label gap tightened from `--space-3` (12px)
  to `--space-2` (8px) to match the more compact spacing in the reference.
- Verified live (dark theme, hard-reloaded): expanded Libraries items show
  plain text only; collapsed rail shows the blue letter badges; no console
  errors.

### Fourth follow-up — same day, dynamic sidebar width

Tez confirmed the dots/badge/width changes above and asked for the
expanded width to fit the longest item name dynamically, rather than a
fixed guess (180px) — the real library only has short names ("2000 AD",
"Favourites") right now, but a longer custom-tab name shouldn't get
truncated or force a manual width bump later.

- New `sizeSidebarToContent()` (`app.js`), called at the end of
  `loadCustomTabsNav()` (so it runs after Libraries items are actually in
  the DOM, on all three pages). Measures the sidebar's natural
  `max-content` width with labels forced visible (briefly clears
  `sidebar-collapsed` off `<body>`, measures, restores it — synchronous,
  no `await` in between, so the browser never gets a chance to paint the
  momentarily-uncollapsed state; no visible flash), clamps to 140–320px,
  writes the result to a new `--sidebar-w` custom property on `:root`.
  `.app-sidebar`'s width and `.sidebar-header-spacer`'s width
  (`calc(var(--sidebar-w) - 60px)`) both read from the same variable, so
  they can't drift apart the way the original hardcoded-pixel version
  could have.
- Tested with the real (short) library names — clamps to the 140px floor.
  Tested again by temporarily renaming a Libraries item to a long string
  via the console and re-running the sizing function — grew to 272px,
  clamped correctly, no text clipping, header logo still shifted to the
  right offset. No console errors.

## Session — 2026-07-07 — Phase B closed out; scope-completeness gap found and fixed

Tez confirmed Phase B (nav/hamburger/dots/badges/width) all correct — closing
it out. Before starting Phase C, Tez asked whether `comicvault-changes-v2.6.md`
had a full scope/list of all the changes, since it looked incomplete, and
pointed at a specific example: a filter/sort-bar restyle visible in a Design
screenshot that wasn't mentioned anywhere in the doc.

- Re-fetched `screens.jsx` fresh from the Design project (not relying on the
  earlier Phase A read) and confirmed: yes, `BrowseScreen`'s filter/sort bar
  is a real, distinct design change — leaner control set (no separate Year
  filter, no Group by, no separate Rated dropdown, no Clear button) and a
  fundamentally different visual language (borderless/minimal `.ds-filter`/
  `.ds-mb-btn` controls vs. the real app's current boxed-pill
  `.filter-select`/`.sort-dir-btn` etc., confirmed still untouched by grep —
  Phase A only re-coloured them via the token swap, never restructured them).
- This genuinely wasn't covered by any of the four phases as scoped — Phase D
  was written as "Series/Issue detail visual polish" only, never mentioned
  the Browse listing screen at all. Real gap, not a misunderstanding.
- Fixed `comicvault-changes-v2.6.md`: added an itemised per-screen scope
  table (Header/Sidebar/Home/Browse/Series/Issue/Admin → phase, cross-checked
  against the actual Design files rather than described from memory), a
  written comparison of the current vs. design filter bar, and a new
  **Phase D — Browse screen filter/sort bar** (old Phase D renumbered to E).
- Flagged an open question rather than deciding it: does the design's leaner
  control set mean Group by / Year / Rated / Clear are deliberately dropped,
  or is the mockup just simplified? These are real, separately-motivated,
  working features (`MENU_BAR_SPEC.md` build history) — same class of
  question Phase B's status-pill removal was, which *did* turn out to be a
  deliberate removal once checked directly against the design. Not assuming
  either way this time without asking first.

## Session — 2026-07-07 — Phase C1 built (Admin IA restructure, part 1)

Restructured the Admin page from one long scrolling page into a category →
sub-item → content-pane nav (`admin.jsx`'s pattern), for the two categories
Design actually built content for: **Library Management** and **Library
Appearance** (10 sub-items total). Processing Tools / Editor Options /
Advanced Settings stay in their old always-visible form, queued for Phase C2.

- **Riskiest phase so far** — `admin.html` (891 lines), `admin.js` (1,627
  lines), `processingTools.js` (876 lines), `filePicker.js` (212 lines)
  define 100+ element IDs existing JS binds to directly. Strategy: preserve
  every ID exactly, only reorganise/re-wrap the existing markup and add one
  new additive `bindAdminNav()` function — zero edits to any existing
  function in any of the three JS files.
- Mapped each of the 10 sub-items to its real current `admin.html` section
  (table in `comicvault-changes-v2.6.md`) before touching code, since
  Design's own category/sub-item labels don't cleanly cover the real app
  (confirmed again this session for Processing Tools/Advanced Settings,
  queued for C2, not acted on yet).
- **Real behaviour question surfaced and resolved before building:** Home
  Page Strips and Custom Tabs ("Add/Remove Libraries") used to live inside
  the locked `<fieldset id="advancedFields" disabled>`, gated behind
  "Unlock advanced settings." Once they move into their own Library
  Appearance category, keeping that gate would mean unlocking happens in a
  totally different part of the nav than the content it unlocks — asked
  before deciding; Tez confirmed unlock them, matching `admin.jsx`'s own
  `HomeStripsContent`/`LibrariesContent` (no lock gate at all). Verified
  `toggleAdvanced()` (`admin.js`) only ever does `fieldset.disabled =
  locked` with no other JS-level gating, so moving the two blocks outside
  the fieldset in the HTML was sufficient — no JS change needed.
- Technical approach: each of the 10 target blocks got wrapped in a new
  `<div class="admin-content-block" data-category="..." data-subitem="..."
  hidden>` with its heading promoted to a new `.admin-content-heading`
  class, inner IDs completely untouched. New `bindAdminNav()` renders the
  category cards, contextual sub-item cards, and toggles `hidden` on the
  matching block — mirrors `admin.jsx`'s `selectCategory`/`SubContent`
  logic (click an active category again to collapse it). New CSS:
  `.admin-nav-card`/`.admin-nav-grid`/`.admin-content-heading`, existing
  `.admin-card`/`.admin-field-row`/etc. classes untouched (already close
  enough post-Phase-A).
- **Verified manually** — every one of the 10 sub-items clicked through
  individually, each showing its real persisted data (Card Size "50%",
  Library Folders' real `L:\Comic Archives` root, Home Page Strips' 4 real
  default strips, Add/Remove Libraries' real 2000 AD/Favourites tabs with
  "Add Favourites Tab" correctly disabled since one already exists) — not
  just visually present, genuinely wired to the same `loadX()` calls as
  before. Ran one real functional round-trip test via the console (changed
  Card Size to 25%, confirmed `localStorage.cv_card_size` updated, reverted
  to 50% to restore the real setting). Confirmed the old Advanced Settings
  fieldset no longer contains Home Page Strips/Custom Tabs but still has
  Reader Location/Server Port/Password Protection/Genre List/Format
  List/Danger Zone, all still locked as before. Confirmed Processing Tools
  section fully intact below with real config data (Processing Folder
  `L:\Comic Archives\Processing\testing`, CT Auto-Tag enabled, ComicVine
  key saved). Dark and light theme. No console errors at any point.
- Updated `ADMIN_SPEC.md` with a status note on the new nav (§ intro) and a
  note on §7's lock-gate change for the two relocated sections, plus a
  `DECISIONS.md` entry for the unlock decision and its rationale.

## Session — 2026-07-07 — Phase C2a built (Admin IA restructure, part 2)

Extended the category → sub-item → content-pane nav to the two remaining
"undesigned" categories that don't need backend work: **Editor Options**
(Genre List, Format List) and **Advanced Settings** (Password Protection,
Change Server Port, Wipe Database, Wipe Reading State). Processing Tools
stays old-style, queued for Phase C2b — it needs real backend work (new
standalone XML Tagging tool) so it's being kept separate.

- **New material surfaced before this session's plan was finalised:**
  Tez provided `admin2.PNG` (Design's own screenshot, confirming Processing
  Tools/Editor Options/Advanced Settings were literally "not yet designed in
  this pass"), the source doc Design's `admin.jsx` categories were built
  from (`New Admin Layout.md`, on Google Drive outside the `docs/` junction),
  and 3 CAPT-era reference PDFs. This corrected the Phase C1 plan's guess at
  the Processing Tools mapping: `New Admin Layout.md` lists a **XML Tagging**
  sub-item that doesn't map to any existing section — it's genuinely new
  functionality (own folder picker + Run), not just a relocation. Confirmed
  with Tez: Auto Processing keeps its CT Auto-Tag enable checkbox; only the
  detailed settings (Match Ratio Threshold, Save on Low Confidence,
  ComicVine API Key) move to the new XML Tagging pane. This pushed Processing
  Tools into its own session (Phase C2b) rather than building all three
  remaining categories together as originally assumed.
- **Sequencing decision:** Editor Options + Advanced Settings (C2a) have zero
  backend dependency and use the exact same proven pattern as Phase C1, so
  built now. Processing Tools (C2b) waits for its own plan — splitting
  Auto Processing's field-removal from XML Tagging's field-reception across
  two sessions would leave the ComicVine API key/threshold/save-low-confidence
  genuinely inaccessible in the UI for the gap between them, a real
  regression, not just cosmetic — so all 5 Processing Tools sub-items ship
  together in one atomic C2b session instead.
- **Danger Zone split:** the old single "Danger Zone" subsection (Clear
  Reading Progress + Clear Database together) doesn't match `New Admin
  Layout.md`'s two separate sub-items (Wipe Database, Wipe Reading State) —
  split into two independent `.admin-content-block`s, each with its own
  heading/hint, same buttons/IDs (`clearDbBtn`, `clearProgressBtn`)
  unchanged.
- **Genre List / Format List unlocked** — same treatment as Phase C1's Home
  Strips/Libraries: moved out of the locked `advancedFields` fieldset into
  their own always-visible Editor Options category, since they graduated
  into a category distinct from Advanced Settings and the lock no longer
  made sense once separated from the checkbox that gates it.
- **Advanced Settings sub-items stay locked** — Password Protection, Change
  Server Port (Reader Location folded into the same sub-item — not in
  `New Admin Layout.md`'s list at all, flagged rather than silently
  dropped), Wipe Database, Wipe Reading State all remain inside
  `<fieldset id="advancedFields" disabled>`, gated by the same "Unlock
  advanced settings" checkbox as before — they weren't reclassified, so the
  existing gate still applies. The checkbox + fieldset-open moved out of the
  old `<section class="admin-section"><h2>Advanced Settings</h2>` wrapper
  (redundant now that the category card carries that label) into a bare
  `admin-card` + fieldset pair, physically positioned where the old section
  used to sit (between `#adminContentPane` and Processing Tools) — it's not
  itself gated by category selection (same "always visible, not yet fully
  nav-ified" pattern Processing Tools already uses), so it shows regardless
  of which category is active; only the fields inside it toggle per-subitem.
- Technical approach: identical to Phase C1 — extended the existing
  `ADMIN_CATEGORIES` array in `admin.js` with two new entries (`editor-
  options`, `advanced-settings`), no changes to `bindAdminNav()` itself.
  `admin.html`: 6 blocks wrapped in `.admin-content-block[data-category]
  [data-subitem][hidden]`, inner IDs completely untouched. No CSS changes —
  Phase C1's `.admin-nav-card`/`.admin-content-heading` rules already cover
  the new categories.
- **Verified manually** in the browser (server already running from earlier
  in the session, `localhost:9424/admin`) — all 4 category cards render;
  Editor Options → Genre List shows real data (Crime 534 issues, Superhero
  131 issues, etc.), unlocked with no checkbox gate; Advanced Settings → all
  4 sub-items render correctly and independently (Password Protection
  greyed out until unlock checkbox ticked, then editable; Change Server
  Port shows the real listening port 9424 and real Reader Location
  `L:\Comic Archives` together; Wipe Database and Wipe Reading State render
  as two separate isolated blocks, confirming the Danger Zone split
  worked). Library Management (Phase C1) re-checked, still fully
  functional, unaffected by the new array entries. Processing Tools section
  scrolled past, confirmed still fully intact and untouched below the new
  content. Dark and light theme (toggled via `localStorage.cv_theme`, then
  reset back to dark). No console errors on a fresh page load. Did not
  click Save & Restart / Clear Database / Clear Reading Progress — those
  are real, irreversible actions against the live server and out of scope
  for a rendering/wiring verification pass.
- Updated `ADMIN_SPEC.md` (top status note + §7 intro note covering the
  unlock/lock split and the Danger Zone sub-item split) and
  `comicvault-changes-v2.6.md` (Phase C2 split into C2a ✅ / C2b queued,
  checklist table, status line).

## Session — 2026-07-07 — Phase C2b built (Admin IA restructure, part 3 — Processing Tools, final category)

Extended the category → sub-item → content-pane nav to the last remaining
category, **Processing Tools** — closing out the Admin IA restructure that
started with Phase C1. Unlike C1/C2a, this phase had real backend work: a
genuinely new standalone tool, **XML Tagging**.

- **Re-verified the earlier backend research against live code** before
  building anything (a memory claim isn't the same as current truth) —
  confirmed `ct_autotag_file()`, `ct_bridge.identify_file()`,
  `processing_folder.py`'s helpers, `ct_autotag_log.py`, and
  `filename_sort.py`'s pattern all still matched what was recalled from
  earlier in the session, plus one detail not previously noted:
  `ct_bridge.identify_file()` (`ct_bridge.py:303`) already reads
  `processing_folder_ct_match_threshold` straight from `get_config()`
  itself — not passed in by the caller — so the threshold needed zero
  plumbing to be automatically shared between Auto Processing and the new
  XML Tagging pane.
- **Backend — the only real new code in this item:**
  - `ct_autotag_log.py`'s `append_entry()` gained an `auto: bool = False`
    parameter (`prefix = "[AUTO] " if auto else ""`), matching
    `convert_log.py`/`convert_images_log.py`'s existing convention. Its
    docstring previously claimed CT Auto-Tag "only ever runs... never as a
    standalone admin-UI tool" — no longer true, docstring corrected.
    `processing_folder.py`'s one existing call site updated to pass
    `auto=True` explicitly, preserving today's behaviour exactly (verified
    via the log itself post-build — see below).
  - New `backend/routers/xml_tagging.py`, modeled directly on
    `filename_sort.py`'s shape: `browse`/`drives` (shared `file_picker.py`),
    `run`/`status` (background task + polled progress dataclass singleton).
    `_taggable_files()` (CBZ/CBR minus `.bak`) duplicated locally as a
    5-line function rather than imported from `processing_folder.py`'s
    private `_ct_taggable_files()` — keeps the router independent, matching
    `filename_sort.py`'s existing precedent. **No new config or
    ComicVine-key-test endpoints** — confirmed the existing
    `/api/admin/processing-folder/config` and
    `/api/admin/processing-folder/comicvine-key/test` endpoints already
    handle the three shared fields generically, so XML Tagging's frontend
    pane just calls those directly. This was the literal "shared, not
    duplicated" behaviour Tez asked for, achieved with zero new backend
    surface for settings.
  - Registered `xml_tagging.router` in `main.py` under `/api/admin`, same
    `_auth_gate` dependency as every other Processing Tool router.
  - Import-checked (`python -c "import backend.main"`) before touching the
    frontend — caught nothing, but cheap insurance given a real new module
    was added.
- **Frontend — `admin.html` restructure:**
  - Dropped `#processingToolsSection`'s old `<section><h2>Processing
    Tools</h2>` wrapper (redundant once the category card carries that
    label — same move as Phase C2a's Advanced Settings), kept the `id` on
    a plain `<div>` so `refreshProcessingToolsLocalGate()`
    (`processingTools.js`) still finds and disables every descendant when
    accessed non-locally, unchanged.
  - Five `.admin-content-block[data-category="processing-tools"]` blocks:
    Filename Editor (File Rename, unchanged), **Converter: Archives &
    Images** (Convert Archives + Convert Images combined into one block,
    each keeping its own nested `.admin-subsection` — the existing
    `border-top` separator CSS already reads well for two stacked
    subsections), **XML Tagging** (new folder-picker + Run + progress
    markup, `xt*`-prefixed IDs mirroring Sort by Filename's `fs*`
    convention, plus the three relocated field-rows), Folder Processing
    (Sort by Filename, unchanged), Auto Processing (Processing Folder
    Automation minus the three relocated fields — the old CT Auto-Tag
    field-row split in two: the enable checkbox stays with a new "Detailed
    settings in XML Tagging" hint, Save on Low Confidence's checkbox moved
    out).
  - Category card order follows `New Admin Layout.md`'s own sequence —
    Processing Tools inserted as the 3rd card (between Library Appearance
    and Editor Options), not appended last.
- **Frontend — JS:** `admin.js` gained one more `ADMIN_CATEGORIES` entry
  (`processing-tools`, 5 sub-items) — `bindAdminNav()` itself unchanged.
  `processingTools.js` gained `openXtBrowse()`/`renderXtResult()`/
  `runXmlTagging()`/`pollXtStatus()`/`initXmlTaggingTool()`, modeled 1:1 on
  the existing `fs*` Sort by Filename functions, called from
  `initProcessingTools()`. **No changes needed** to
  `loadProcessingFolderConfig()`/`initProcessingFolderTool()` — both kept
  working unchanged against the relocated field IDs regardless of new DOM
  position, the same insight already validated for Genre/Format List in
  C2a.
- **Verified manually** in the browser (restarted the backend server to
  pick up the new router — `Stop-Process` on the listening PID, confirmed
  the port was free, relaunched `python start_server.py`, confirmed clean
  startup log with no import errors):
  - All 5 category cards render in the right order; Processing Tools shows
    all 5 sub-items; Filename Editor / Converter / Folder Processing behave
    exactly as before, just relocated; Auto Processing shows CT Auto-Tag as
    enable-only with the real saved Processing Folder path
    (`L:\Comic Archives\Processing\testing`) and no threshold/key fields;
    XML Tagging shows the real saved Match Ratio Threshold (70%) and masked
    ComicVine API key, proving the relocated fields still load from the
    same shared config.
  - **Hit a stale-browser-cache false alarm mid-verification** — after
    editing `processingTools.js`, the new functions weren't found on
    `window` even though `node --check` had passed and a fresh `fetch()` of
    the same URL showed the new code was being served correctly. A hard
    reload (Ctrl+Shift+R) fixed it immediately — the browser had cached the
    old script and hadn't revalidated it across several soft
    navigations/reloads. Not a real bug; noted here in case it recurs.
  - **Real functional round-trip, scratch data only** (per `CLAUDE.md`
    Section 6 — never touched the real library or `Processing` folder):
    generated a synthetic 1-page CBZ in a scratch job-tmp folder (not
    inside the repo or the real library), ran XML Tagging against it via
    the actual `runXmlTagging()` UI function, polled to completion (real
    ComicVine lookup happened — result came back `low_confidence`, correct
    given the file has no real match). Confirmed `ct_autotag_log.md` got a
    new line with **no `[AUTO]` prefix** sitting directly below several
    pre-existing `[AUTO]`-prefixed lines from real prior automation runs —
    proof both that the new `auto=False` standalone path and the untouched
    `auto=True` automation path are both correctly wired. Scratch file
    deleted immediately after.
  - Re-clicked Save & Test on the relocated ComicVine API key field (same
    real key, non-destructive) — "The API key is valid" confirmed the
    button still hits the existing endpoint correctly from its new
    location.
  - Dark and light theme, no console errors on a fresh page load.
- Updated `ADMIN_SPEC.md` (§11.4.4/§11.4.9 notes on the field relocation
  and the log's `auto` param change, new §11.6 XML Tagging section, top
  status note) and `comicvault-changes-v2.6.md` (Phase C2b marked ✅,
  checklist table, status line — Admin IA restructure now complete).

### Follow-up — Phase C2c: "Unlock advanced settings" moved into the sub-item nav row

Tez asked for a small layout fix right after C2b: the "Unlock advanced
settings" checkbox was sitting in its own full-width row below the content
panes (visually right under the sub-item cards, since everything above it
collapses to zero height when hidden) — moved it up into the same row as
the Advanced Settings sub-item cards (Password Protection / Change Server
Port / Wipe Database / Wipe Reading State), as a compact "☐ Unlock" element
at the end of that row, rather than its own separate row.

- `admin.html`: wrapped `#adminSubitemNav` and a new compact
  `#advancedLockWrap` label (same `#advancedLock` checkbox `<input>` node,
  unmoved — critical, since `toggleAdvanced()`'s change listener is bound
  once at init and would be lost if the node were destroyed/recreated) in
  a shared `.admin-subitem-row` flex container. Removed the old standalone
  `<div class="admin-card">` wrapper the checkbox previously lived in.
  Label text shortened from "Unlock advanced settings" to just "Unlock"
  per Tez's request, since the category card above it already says
  "Advanced Settings."
- `admin.js`: `bindAdminNav()`'s `renderSubitems()` now also toggles
  `#advancedLockWrap`'s `hidden` attribute (`activeCat !== 'advanced-
  settings'`) — the only logic change; `toggleAdvanced()` itself untouched.
- `style.css`: new `.admin-subitem-row` (flex row, subitem grid takes
  remaining space) and `.admin-lock-label--compact` (fixed intrinsic
  width via `flex: 0 0 auto`, bordered/backgrounded to match the compact
  nav-card style used elsewhere in this row, same 24px bottom margin as
  the grid it sits beside so the row's bottom edge lines up).
- **Verified manually**: checkbox renders compact and inline with the 4
  sub-item cards only when Advanced Settings is the active category;
  correctly disappears when switching to any other category (checked
  Processing Tools specifically — 5 cards fill the row cleanly with no
  stray checkbox); unlock toggle still enables/disables the fieldset
  exactly as before. Dark and light theme, no console errors.
- Noted but not investigated further: the very first click on a category
  card immediately after a `location.reload()` sometimes produced no
  visible change (category showed active/highlighted but no sub-item row
  rendered), while a second click always worked correctly. Reproduced 3
  times, always specifically right after a scripted reload, never during
  normal interaction — reads as a reload/click race in the browser
  automation tooling itself (the click landing on the pre-reload DOM a
  moment before navigation completes), not a real product bug. Flagging
  here in case it turns up again.

## Session — 2026-07-07 — Phase D built (Browse filter/sort bar restyle)

Restyled the Browse screen's filter/sort bar (`#menuBar`,
`frontend/index.html`) to match the Design reference — the last visual gap
identified in the itemised per-screen checklist. Scope had already been
settled (`DECISIONS.md`, same day): visual restyle only, every current
field/control stays.

- **Read the Design project directly rather than relying on the prior
  session's description of it** — fetched `Library.html` (kit-local
  `.ds-filter`/`.ds-mb-btn` CSS), `screens.jsx` (`BrowseScreen`'s actual
  JSX layout), and the compiled `Dropdown` component source
  (`components/library/Dropdown.jsx`, bundled into `_ds_bundle.js` — had
  to extract the JSON tool result's `content` field to a real `.js` file
  on disk first to grep it usefully, since the raw tool output is one
  giant escaped-JSON line).
- **Scope-narrowing finding, made before writing any code:** Design's
  filter dropdowns aren't native `<select>` elements — `FilterSelect` in
  `screens.jsx` renders a fully custom popup-listbox component with its
  own open/close state, click-outside handling, and a themed
  `.ds-dropdown-panel` for the open list. Rebuilding that is real new
  interactive-component work, not a restyle, and reskinning a
  browser-owned native `<select>`'s open popup isn't achievable via CSS
  anyway (and isn't visually comparable across browsers). **Decision:**
  kept the real app's native `<select>` elements, applied `.ds-filter`'s
  *closed-trigger* styling only — matches the already-resolved "restyle,
  don't rebuild" scope from the `DECISIONS.md` entry, without needing to
  ask again.
- Also found: Design groups the grid/list view toggle *with* the "N
  Titles" count in one trailing right-aligned cluster, and has one vertical
  divider after Favourites, before the filter dropdowns — details not
  captured in the prior session's textual description, only visible by
  reading `screens.jsx` directly.
- **Technical approach — CSS-only + one small HTML reorder, zero `app.js`
  changes** (confirmed via grep first: nothing in `app.js` depends on
  DOM order/position for any of these elements, everything is
  `getElementById`-bound):
  - `style.css`: rewrote `.filter-select` and `.sort-dir-btn`/
    `.view-toggle-btn`/`.fav-filter-btn` from boxed pills
    (`background:var(--surface-2); border:1px solid var(--border)`) to
    borderless/minimal (`background:none; border:none`), muted text that
    brightens on hover and turns accent-coloured on focus/`.active` —
    existing `--dur`/`--ease` transition tokens reused, no new tokens
    needed. Restyled `.filter-clear` the same way for visual consistency
    (Design has no equivalent control, but it sits in the same row).
    Added `.menu-bar-divider` (1px hairline) and `.menu-bar-trailing`
    (flex group, `margin-left:auto`, replaces `.browse-count`'s own
    `margin-left:auto`).
  - `index.html`: inserted `<span class="menu-bar-divider">` after
    `favFilterBtn`; moved the existing `viewToggle` button (unchanged —
    still one button, one behaviour, not split into two Design-style
    grid/list buttons, since that would be a functional UI change beyond
    restyle scope) into a new `.menu-bar-trailing` wrapper alongside
    `browseCount`. Every other element — `sortSelect`, `sortDirBtn`,
    `starRatingFilter`, `favFilterBtn`, `groupBySelect`,
    `#browseFilters` and its 7 children — untouched, same IDs, same
    position.
- **Verified manually** in the browser (Browse "All" surface and a Custom
  Tab's Folder View listing — "2000 AD", confirming the shared bar works
  correctly in both Flat View and Folder View, and that Folder View
  correctly has no Group by dropdown, unchanged): divider renders (subtle
  hairline, matches Design's intent); Favourites toggle filters correctly
  and turns accent-coloured while active, Clear appears/disappears exactly
  as before; Genre filter round-tripped via a real `change` event (3,325
  of 5,427 titles, active state turned accent blue); grid/list view toggle
  re-tested after an initial missed click (coordinates shifted once Clear
  toggled visibility mid-sequence — not a bug, just needed a precise
  re-click) — confirmed both the icon swap and the actual grid↔list layout
  change still work. Dark and light theme. No console errors.
- Updated `comicvault-changes-v2.6.md` (Phase D marked ✅, checklist table,
  status line) — deliberately did **not** claim the cover grid/card
  styling was re-verified, since Phase D's scope was the filter bar only;
  left that checklist note honestly scoped to what was actually checked
  this session, not what Phase A's remap is merely believed to already
  cover.

## Session — 2026-07-07 — Phase D follow-up built (styled open-dropdown panel)

Tez shared a screenshot (`D:\workshop\images\digib00age\open-dd-menu.PNG`)
of the *open* Genre dropdown, asking for the open-menu styling to be
adjusted — directly reversing Phase D's own scope call from earlier the
same session ("kept native `<select>` filter dropdowns", `DECISIONS.md`):
a browser's native `<select>` popup can't be restyled via CSS at all, so
matching the screenshot required actually building the custom listbox
component that decision had ruled out.

- **Reused Phase D's own research** — `components/library/Dropdown.jsx`
  (fetched from the Design project earlier the same session, still fresh)
  is the exact reference the screenshot matches: `.ds-dropdown-panel`
  (themed card surface, border, radius, shadow) and `.ds-dropdown-opt`
  (padding, hover highlight, accent-tinted selected row). Confirmed every
  CSS variable needed already exists in `style.css` (`--surface-card`,
  `--shadow-pop`, `--radius-md`, `--accent-tint`, `--accent-text`) — zero
  new tokens, though one referenced token turned out not to actually
  exist (`--radius-sm` — only `--radius-xs`/`--radius`/`--radius-md`/
  `--radius-lg` are defined; caught before shipping, used `--radius-xs`
  instead).
- **Constraint-first design, before writing code:** grepped `app.js` for
  every way it touches the 10 `.filter-select` elements — `change`
  listeners (the actual filter logic), **programmatic** `.value =`
  (`clearAllFilters()`, sort's "Pages"-option suppression), dynamically
  rebuilt option lists (`addOpts()`, Genre/Format/Decade/Year/Publisher/
  Rating are populated from live library data, not static HTML), and
  `groupBySelect.hidden` toggled per-surface. All four had to keep working
  with zero changes to `app.js` itself.
- **Approach — hidden native `<select>` + custom overlay
  (`frontend/js/filterDropdown.js`, new file):** the real `<select>` stays
  in the DOM (visually hidden via `opacity:0`, not removed) as the single
  source of truth. A custom trigger `<button>` (reuses `.filter-select`'s
  exact CSS class for identical Phase D look) and an initially-hidden
  `.fd-panel` sit alongside it. The panel's rows are rebuilt **fresh from
  `select.options` every time it opens** — not cached at init — which is
  what makes dynamically-populated option lists and per-option
  `hidden`/`disabled` (the Pages-option case) work automatically with no
  `app.js` changes: the panel always reflects whatever the real select
  currently contains. Selecting a row sets `select.value` and dispatches a
  real `change` event, so every existing `app.js` listener fires exactly
  as if the native popup had been used.
- **The one genuinely new trick, and the one bug it took a round to find:**
  `app.js` sets `.value =` and toggles `.active`/`.hidden` as *separate*
  statements in places like `clearAllFilters()` (`.value = ''` then a
  distinct `.classList.remove('active')` on the next line) — a plain
  `change`-event listener can't see scripted `.value =` at all, so the
  trigger needs its own hook. First attempt: intercepted `.value`'s setter
  via `Object.defineProperty` (delegating to the original
  `HTMLSelectElement.prototype` descriptor) to resync the trigger's label,
  and derived the trigger's accent "active" look from a blanket
  `select.value !== ''`. That second part was wrong — it made the sort
  dropdown (`sortSelect`, which always has a real value like `"alpha"` and
  which `app.js` never toggles `.active` on) permanently accent-coloured,
  a visible regression from Phase D's actual look (plain/muted until a
  real filter is chosen). Fixed by not guessing at "active" from value at
  all: added a `MutationObserver` watching the select's `class`/`hidden`
  attributes (both real, observable DOM mutations, unlike `.value`) and
  mirroring `select.classList.contains('active')`/`select.hidden`
  verbatim onto the trigger/wrapper — self-consistent regardless of
  statement ordering inside functions like `clearAllFilters()`, and exactly
  matches original behaviour for every element (including the two,
  `sortSelect`/`groupBySelect`, that `app.js` never marks `.active` at all).
- **Second bug, found the same way (build → check against the real app,
  not just against the plan):** the custom trigger button initially also
  turned permanently accent-coloured after being clicked once, even with
  the fix above. Cause: the trigger shares the `filter-select` CSS class
  for its base look, and the existing rule `.filter-select:focus { color:
  var(--accent) }` was written to target *any* element with that class —
  including the new trigger `<button>`, which (unlike a native `<select>`)
  never loses browser focus after a click. Fixed by tag-qualifying that
  selector to `select.filter-select:focus`, so it only ever matches the
  real (now-hidden, harmless) `<select>` elements, never the visible
  trigger button.
- Capped `.fd-panel`'s height (`max-height:320px; overflow-y:auto`) after
  seeing the real Genre list (~30 real values, vs. the Design mockup's
  6-item placeholder list) run off the bottom of the viewport — not
  something the Design reference's own short list would ever have
  surfaced.
- **Verified manually**, per the plan's checklist: every dropdown (sort,
  Rated, Group by, Genre, Format, Decade, Year, Publisher, Rating, B&W)
  opens with the themed panel matching the screenshot; Genre selection
  round-tripped (filtered to 3,325 of 5,427, trigger turned accent-blue);
  **Clear correctly reverted the trigger to its plain placeholder text and
  colour** (the specific case that proves the `class`/`hidden`
  `MutationObserver` sync works, not just the simpler `change`-event
  path); clicking outside a panel closes it and lets the click pass
  through to whatever was underneath (matches Design's own `Dropdown.jsx`
  behaviour — confirmed by accident when a stray outside-click during
  testing navigated into an issue page); Escape closes without changing
  selection; switched to the Series surface and confirmed the sort
  dropdown's "Pages" option is correctly absent (proves the live-rebuild-
  from-`select.options` respects `.hidden`); switched to the "2000 AD"
  Custom Tab (Folder View) and confirmed `groupBySelect`'s wrapper
  correctly stays hidden there too. Dark and light theme, both Flat View
  and Folder View. No console errors on a fresh load.
- Updated `DECISIONS.md` — added a follow-up note on the original Phase D
  "kept native select" entry pointing at this session's reversal, plus a
  new entry documenting the sync mechanism (`Object.defineProperty` +
  `MutationObserver`) as its own non-obvious call.

**Follow-up fix, same session:** Tez flagged a stray *horizontal*
scrollbar showing up on every panel (screenshot: `filter-dd-menu-open.PNG`,
the Year dropdown) — Design's own mockup never surfaces this since its
fake data is short, but the real Year/Genre lists are long enough to need
the `.fd-panel` vertical scroll added earlier this session, and that
triggered it. Root cause: `.fd-panel` set `overflow-y: auto` without also
setting `overflow-x` — per the CSS Overflow spec, when one axis is scrollable
and the other is left `visible`, the browser computes the `visible` one to
`auto` too, so the vertical scrollbar's own width was enough to tip the
panel into horizontal overflow and show a second, unwanted scrollbar with
its own left/right arrow buttons. Fixed with one line
(`overflow-x: hidden`) — reloaded and re-checked Year and Genre, both
clean, only the intended vertical scrollbar remains. No other files
touched.

## Session — 2026-07-08 — Design-vs-implementation scan + CoverCard selection circle built

Tez asked whether Phase D was "all the changes based on Design's docs" and
requested a full scan comparing the Design project against the real app,
having already spotted one gap himself (a small circle in the bottom-left
corner of cover images on hover — screenshot: `D:\workshop\images\
digib00age\selection-dot.PNG`).

- **Scan approach:** rather than re-describing Design from memory, pulled
  the remaining component sources directly from the Claude Design
  project's compiled bundle (`_ds_bundle.js` — same JSON-extraction trick
  as Phase D's Dropdown research: save the tool result's `content` field
  to a real `.js` file so it's actually greppable) — `CoverCard.jsx`,
  `parts.jsx` (`AppHeader`, `Strip`), `Badge`/`StatCard`/`Tag`/
  `StatusButton`. Compared each against the real app's corresponding CSS/
  JS.
- **Confirmed already matching (no action needed):** CoverCard's read-
  state colouring (fully-read green tint, part-read black+gradient) —
  matches to the literal RGB value; favourite badge, unread badge,
  progress bar + bottom feather gradient; hover-lift (`--lift:
  translateY(-3px)` is even the same token name in both); Home Strip's
  hover-reveal scroll arrows (pre-existing V1 feature, not something Phase
  A/B introduced, already matched Design's edge-aware behaviour); Admin
  `StatCard` padding/typography; header logo height/search/settings
  button. This confirmed Phase A's token remap was genuinely thorough, not
  just spot-checked.
- **Confirmed gap:** Design's `CoverCard.jsx` has a `canSelect`-gated
  select circle (`.ds-select-circle`) the real app never got — 14×14px,
  white ring, `bottom:11/left:8`, hidden until hover (`opacity:0→1`),
  stays visible once selected with an inner 6px accent dot, grid-view-only
  by default (`!isList`). The real app's selection was long-press-only
  (`makeSelectable()`, 500ms) with zero visual hint it was possible until
  already mid-gesture.
- **Out of scope, correctly not flagged as a new finding:** Series/Issue
  detail differences (`StatusButton`, backdrop, issue rows, `Tag` layout)
  — already tracked as Phase E, not started, not a Phase D/A/B/C gap.

**Built the fix**, plan approved before touching anything:

- Traced exactly where `.cover-card` elements get built in `app.js`:
  `buildCoverCard()` (Browse grid) and `buildFolderFileCard()` (Folder
  View flat files) both already call `makeSelectable()` — these two get
  the new circle. `buildStripCard()` (Home) does **not** call
  `makeSelectable()` at all — Home has no selection feature, so no circle
  there (confirmed via a real page check: 45 strip cards, 0 select-dots).
- `app.js`: extracted the 2-line `if (!selectionActive) enterSelectionMode
  (...) else toggleSelected(...)` branch already living inside
  `makeSelectable()`'s long-press timer into a named `selectOrToggle(id,
  kind)` helper, called from both the timer callback (unchanged behaviour)
  and a new `buildSelectDot(id, kind)` helper (`e.preventDefault();
  e.stopPropagation();` then `selectOrToggle`) used by both card-building
  functions. Zero changes to `enterSelectionMode`/`toggleSelected`/
  `exitSelectionMode`/the toolbar — the circle is a new entry point into
  the exact same state machine, not a parallel one.
- `style.css`: new `.select-dot` — the inner filled dot is a
  `::after` pseudo-element gated purely by the ancestor `.cover-card.
  selected` class already toggled by the existing `toggleSelected()`, so
  no extra DOM node or JS needed for that part. `.cover-grid.list-view
  .select-dot { display: none; }` for the grid-only default.
- **Verification hit real automation friction, worth recording:** the
  first couple of real-mouse clicks via the browser tool either navigated
  straight into the issue page or hit nothing at all — alarming at first,
  since it looked like `preventDefault()`/`stopPropagation()` weren't
  working. Root-caused by dispatching the *exact* event cascade a real
  click fires (`pointerdown` → `pointerup` → `click`, matching what
  `makeSelectable()`'s own long-press listeners also observe) directly via
  JS at the dot's measured `getBoundingClientRect()` center: selection
  worked correctly, toolbar appeared, **no navigation**, every time. The
  earlier failures were the automation tool's coordinate targeting on a
  14×14px element, not a real bug — confirmed by also testing a
  plain synthetic `click`-only dispatch (which skips pointerdown/pointerup
  entirely) versus the full cascade, both landing on the same correct
  result once the coordinates were right.
- **Verified manually**, per the plan: hover reveals the circle
  (screenshotted, matches the shared reference image); click selects
  without navigating (confirmed via the full pointerdown/pointerup/click
  cascade dispatch, both on Browse and Folder View — `#folderGrid` file
  cards, 45 of 45 got a dot); list view hides all dots
  (`getComputedStyle().display === 'none'`); Home strips have zero dots
  among 45 strip cards; Cancel correctly resets selection state; dark and
  light theme (white ring renders identically in both, matching Design's
  fixed `rgba(255,255,255,0.95)` regardless of theme); no console errors.
  Did not exhaustively re-test the long-press gesture itself since the
  refactor only extracted its existing 2-line branch into a named
  function with identical behaviour, no logic change.
- Updated `comicvault-changes-v2.6.md` (new checklist-table row for
  CoverCard, cross-cutting bullet in the phase list, status line) — logged
  as its own item since it doesn't map to a single lettered phase
  (Browse + Folder View, not tied to Phase D's filter-bar-only scope).

## Session — 2026-07-08 — Phase E built (Series/Issue detail visual polish) — v2.6 Item 1 complete

Tez said "kick off Phase E" — the last item on the build queue, described
since it was first written as "blurred cover backdrop, issue-row
treatment, tag/genre chips" (Series) and "Cover + action-button column,
credits/summary layout" (Issue).

- **Scanned before building, same discipline as the CoverCard work**: read
  Design's actual `screens.jsx` (`SeriesScreen`/`IssueScreen`) — already
  fetched earlier this session for other research — plus, newly this
  session, `elevation.css` and `colors.css` (the actual token source,
  never read directly before now; `--shadow-modal` was the only elevation
  token previously confirmed). Compared every rule against the real
  `style.css`/`app.js`.
- **Confirmed already matching (no action needed) — this phase turned out
  much smaller than the checklist framing implied, a third time this
  session:** issue-row treatment (coloured left border per read-state,
  tinted background for "reading", circular status button with matching
  border/fill colours) — already present, matches Design's `issueRow()`/
  `StatusButton` almost exactly. Genre tag chips, credits grid
  (`grid-template-columns: auto 1fr`, same gap values), `.meta-section`'s
  divider — `margin-top:20px; padding-top:16px; border-top:1px solid
  var(--border)` is **literally identical** to Design's `Section`
  component, not just close. Rating stars (already tuned per a prior
  SPEC.md pass), status/favourite toggle buttons, `.cover-card.selected`'s
  ring (uses the exact same formula as Design's `--ring-selected` token).
  Series backdrop's blur (`3px`, exact token match) and dark overlay
  (`rgba(0,0,0,0.45)`, exact token match) were also already correct —
  hardcoded to the same literal values Design's tokens resolve to, just
  not expressed as tokens yet.
- **Two real, confirmed gaps:**
  1. **A genuine bug**, not a missing feature: `.series-backdrop-img {
     opacity: 1.5; }` — CSS clamps this to `1.0`, so the backdrop rendered
     at full strength instead of Design's intended `0.28` subtle wash.
     Probably the single biggest reason the series page read as "off"
     relative to Design despite everything else already matching.
  2. **The Issue detail page had no backdrop at all** — `buildIssueDetail()`
     never built one. Design gives Issue its own variant: taller (440px),
     much fainter (`opacity: 0.18` vs Series' `0.28`), fading via a
     4-stop gradient mask rather than a flat dark overlay, so it reads as
     barely-there texture behind the two-column layout rather than a
     focal element.
- **Built the fix:**
  - Formalized `--blur-backdrop` (`3px`), `--backdrop-opacity` (`0.28`),
    `--backdrop-overlay` (`rgba(0,0,0,0.45)`) as real `:root` tokens
    (values copied directly from Design's `elevation.css`, identical
    across both themes — Design doesn't override them for light).
  - Series: swapped `.series-backdrop-img`'s `opacity`/`filter` and
    `.series-hero-wrap::before`'s `background` to reference the new
    tokens instead of the old hardcoded literals — fixes the opacity bug
    and makes both backdrops (series + the new issue one) share one
    source of truth.
  - Issue: `buildIssueDetail()` (`app.js`) now prepends an `.issue-
    backdrop` (image + a `linear-gradient(to bottom, var(--bg) 0%,
    var(--bg) 8%, transparent 55%, var(--bg) 100%)` fade div) before
    building its existing content, then wraps that existing content
    (the two-column layout + prev/next nav, completely unchanged) in a
    new `.issue-content` (`position:relative; z-index:1`) so it stacks
    above the backdrop. Added `#issueContent { position: relative; }` so
    the backdrop's `position:absolute` anchors correctly. No changes to
    `issue.html`'s static markup.
  - **Deliberate scope call, flagged rather than silently done or
    scope-crept:** Design's backdrop extends behind the "← Back" button
    too, but the real app's back button (`#backLink`) is static markup in
    `issue.html`, a DOM sibling *before* `#issueContent` — not something
    `buildIssueDetail()` builds. Restructuring static markup to move it
    into the backdrop's stacking context wasn't worth it for a few pixels
    of cosmetic overlap; the backdrop starts just below the back button
    instead. Logged as its own `DECISIONS.md` entry.
- **Verified manually**: opened a busy-cover series ("2000 AD") — backdrop
  now visibly subtle/washed-out compared to before, cover art recognisable
  as texture, not competing with the title/genre-tags text for attention.
  Opened issue #1 of the same series — new faint backdrop visible behind
  the top of the page (title art readable as a watermark), fading out by
  roughly the credits section; two-column layout, badges, credits,
  ratings, toggle buttons, prev/next nav all rendered exactly as before,
  no regression from the new wrapper div. Repeated both checks in light
  theme — backdrop reads correctly against the light background too, no
  contrast issues introduced. No console errors on a fresh load.
- Updated `comicvault-changes-v2.6.md` (checklist table rows for Series/
  Issue detail, Phase E phase-list bullet, both status notes — including
  the top-of-doc header, stale since the item was first handed off and
  still saying "not yet built") — **v2.6 Item 1 (Web UI Redesign) is now
  fully complete**, every phase A through E plus both cross-cutting
  follow-ups built and verified.

## Session — 2026-07-08 — BUG-014 fixed (back-button regression)

- Not part of Item 1 — BUG-014 was explicitly deferred out of the redesign
  (see 2026-07-06 entry above); this was its own standalone session, done
  now that Item 1 is closed out.
- Full diagnostic pass before any code change, per Tez's request: two
  parallel Explore agents independently re-read `app.js`/`issue.html`/
  `series.html` against current (post-redesign) code rather than trusting
  the 2026-06-27 diagnosis already in `BUGS.md`, then live browser testing
  against the running dev server actually reproduced the bug.
- **Key finding:** the identical action (All → issue → Back) produced two
  different outcomes across two live attempts — once correctly landing back
  on "All" (Chrome's back/forward cache silently restored the previous
  page's live JS state), once landing on Home (a real reload occurred,
  hitting the actual defect). This explains why the same bug class survived
  two prior "fixes" (2026-06-21, 2026-06-22) without ever being caught as
  still-broken — bfcache was randomly masking it in manual testing.
- **Root cause:** `switchSurface()` in `app.js` only called `pushState` for
  Folder View custom tabs; the four main browse surfaces (Home/All/Singles/
  Series) never wrote to the URL, so `history.back()` from a detail page
  fell through to bare `/`, which defaulted to Home. A second bypass,
  `redirectHomeSearchToAll()`, had the same defect independently.
- **Fix:** extended Folder View's already-working `pushState`/`popstate`
  convention app-wide — `switchSurface()` now writes the URL on every
  branch, `redirectHomeSearchToAll()` now routes through `switchSurface()`
  instead of duplicating its logic, `initLibrary()` and the `popstate`
  listener now share one `parseSurfaceState()` parser (previously two,
  independently drifting) and restore `field`/`value`/`folder`/`status` in
  addition to `surface`/`path`, and the first page load now gets a
  `history.replaceState()`. Removed the now-fully-dead `from=` query-param
  plumbing in the same session (deferred until after verification passed,
  per Tez's call, so cleanup and behavioral fix didn't get conflated).
  Admin page's independent back-link (`admin.js`) reviewed and left
  unchanged — structurally unrelated to this bug (never routed through
  `switchSurface()`), per Tez's call.
- **Verified manually**, live against the dev server (`:9424`), each case
  run twice — a plain Back click, and a forced hard-reload-then-Back to
  guarantee a bfcache miss, since that's the scenario that actually broke
  before: All→issue→Back, Series→series-detail→Back,
  Series→series-detail→issue→Back→Back, Home-search→All→issue→Back, and
  Folder View's existing 2-level drill-down→Back→Back (confirmed the new
  `{replace}` option on `pushFolderViewUrl()` didn't regress it). All land
  on the correct origin surface. Full account, including the exact live
  repro sequence that caught the bfcache nuance, in `BUG-014`'s entry in
  `archive/bugs-fixed-archive.md`.
- `docs/BUGS.md` updated — BUG-014 moved to `archive/bugs-fixed-archive.md`;
  BUG-015 annotated noting this fix incidentally clears stale `field=`/
  `value=` from the URL on surface switch as a side effect, but does not
  fix BUG-015 itself (dropdown/clear-control gaps remain open).

## Session — 2026-07-08 — BUG-015 fixed (fieldview filter had no clear/indicator)

- Standalone session, same day as BUG-014, not part of Item 1.
- Tez's initial proposed fix was a "Clear" first row in the Genre dropdown.
  Investigation found this only covers the genre case — fieldview is also
  reached via writer/artist credit links and admin-configured home strips
  (publisher/format/decade/year/rating/B&W), none of which have a dropdown
  to attach a clear-row to. Presented the gap and an alternative to Tez via
  the plan-mode question flow; Tez approved the alternative.
- **Root cause:** the Genre dropdown (`activeGenre`) and the fieldview
  mechanism (`viewField`/`viewFieldValue`) are two fully separate,
  unrelated pieces of state that happened to share the word "Genre."
  Fieldview itself showed zero context — no banner, no indicator, a
  generic "N Titles" count with no mention of what was filtering it.
- **Fix:** generalized the Series detail page's existing BUG-010 banner
  pattern ("Showing X of Y — filtered by Z. View full series") for the
  fieldview surface generically — a new `renderFieldviewBanner()` reads
  `"{count} Titles — {FieldLabel}: {value}"` with a real-navigation "Clear
  filter" link to `/?surface=all` (real navigation, not a JS state reset —
  deliberately avoiding the class of bug BUG-014 just closed). Writer/
  artist values are a `Person.id`, not human-readable — added a `label=`
  URL param, threaded through the same shared `parseSurfaceState()`/
  `buildSurfaceUrl()`/`writeSurfaceUrl()` path BUG-014 established, plus a
  new `field_value_label` field resolved server-side in
  `backend/routers/home.py` for the one link-construction site (admin
  home-strip links) that doesn't have the person's name client-side.
  `hasActiveFilters()`/`clearAllFilters()` deliberately left blind to
  fieldview state (commented why — blanking it in place would empty the
  grid via a cache-miss, not unfilter it).
- **Bonus (Tez's call):** Genre dropdown now cosmetically mirrors an active
  genre fieldview's value, synced once per surface switch (not on every
  re-render) so it doesn't fight a user's own manual dropdown selection.
- **Robustness fix found live:** `renderFieldviewBanner()` initially had no
  null-check on its DOM element — crashed the whole render pipeline (stuck
  "Loading…") when a stale cached `index.html` (predating this fix) was
  served alongside a fresh `app.js`, a realistic deploy-skew scenario, not
  just a testing artifact. Added a guard.
- **Verified manually**, live against the dev server (`:9424`): genre tag,
  writer credit link (label survives hard refresh and Back/Forward), a
  temporary admin-configured writer-basis home strip (confirming the new
  backend `field_value_label` round-trips — "4 Titles — Writer: A. J.
  Lieberman"), Clear filter link, cleanup-on-navigate-away, a secondary
  Format-dropdown filter layered on a fieldview (banner count updates,
  global Clear only clears the Format narrowing), and decade/B&W value
  formatting. Test home-strip scaffolding removed after verification —
  hit a native `confirm()` dialog blocking Claude-in-Chrome automation on
  the admin Delete button, asked Tez to click it manually. Full account in
  `BUG-015`'s entry in `archive/bugs-fixed-archive.md`.
- `docs/BUGS.md` updated — BUG-015 moved to `archive/bugs-fixed-archive.md`.

## Session — 2026-07-09 — Post-redesign UI tweak pass

Not a formal v2.6 build-queue item — Tez went through the live web app page by
page, flagging spacing/positioning/consistency issues and a few small feature
asks against the (already-complete) redesign. Verified live throughout by Tez
against the running dev server on `:9424` (a Code-managed preview server
couldn't be started — the port was already bound by Tez's own tray-app
instance pointed at the real library, so all verification this session was
Tez's own manual refresh-and-check, not a Claude Code browser session).

- **Header login/logout drift (`issue.html`, `series.html`):** both pages were
  missing the settings-cog `<a class="settings-btn">` markup index.html has —
  the cog's `margin-left: auto` is what pushes itself *and* the Logout button
  after it to the header's right edge; without it, Logout just sat right
  after the logo. Added the missing markup to both pages. (`guide.html` has
  the same gap but Tez confirmed it isn't visibly broken there — left alone.)
- **2000 AD "Mark all read" spacing:** `.folder-view-nav` had no bottom
  margin, so the button/breadcrumb row butted straight up against the cover
  grid below with zero gap — unlike Flat View's `.menu-bar`, which uses
  `margin-bottom: 12px` for the same purpose. Added `margin-bottom:
  var(--space-3)` (12px) to `.folder-view-nav` only, matching the design
  system's existing spacing scale — not the shared `.back-nav` class Issue
  detail's breadcrumb also uses.
- **Folder View back button:** replaced the `Root / 1981 / …` clickable
  breadcrumb with a real "← Back" button, reusing the exact
  `history.back()`-when-possible / `href="/"`-fallback pattern Series/Issue
  already use — safe now that BUG-014 (2026-07-08) made real-history
  navigation reliable app-wide. `renderFolderBreadcrumb()` deleted along with
  `#folderBreadcrumb`. Caught a dependency while removing it: Folder View's
  search box used to write its "Search results for…" message into that same
  breadcrumb element — gave it its own `#folderSearchLabel` span instead so
  search still shows what you searched for. See `DECISIONS.md`.
- **Grid/List toggle relocated:** moved from the trailing group (next to the
  title count) to sit right after the sort ascend/descend button, before
  Rated — `A–Z | ↑ | ⊞ | Rated | ★ Favourites`.
- **"|" separators throughout the menu bar:** `.menu-bar-divider` (already
  used once, between Favourites and Group by) extended between every control
  in the row — sort dropdown, ascend/descend, view toggle, Rated,
  Favourites, Group by, and each of the six secondary filter dropdowns.
- **Dropdown scrollbars restyled:** `.fd-panel` (the custom popup list
  `filterDropdown.js` builds over every native `<select>`) had the default
  OS scrollbar, which didn't blend with the dark theme. Added thin
  `scrollbar-color`/`::-webkit-scrollbar-thumb` styling using `--surface-3`/
  `--text-3` tokens — applies to every filter dropdown site-wide since they
  all share this one class, and adapts automatically in light theme too via
  the existing CSS variables.
- **Fieldview banner deduped:** the banner (shown when arriving via a Genre/
  Writer/Artist link) used to open with its own "{count} Titles" text, which
  duplicated the count already shown in `.menu-bar-trailing`. Moved the
  banner element into `.menu-bar-trailing` itself (before `#browseCount`)
  and dropped the duplicate count from its text — now just
  "Genre: Thriller Clear Filter   3,301 Titles" in one row rather than two
  rows repeating the number.
- **Publisher filter removed** from the secondary filters dropdown row
  (`#browseFilters`) — every reference to `activePublisher` removed from
  `frontend/js/app.js` (pool filter, Folder View filter, `hasActiveFilters()`,
  `clearAllFilters()`, `bindSelect()`, `populateFilterDropdowns()`'s
  `addOpts()` call, which has no null-guard and would have thrown on load if
  left pointing at a removed element). Publisher stays available as a Group
  by option (`#groupBySelect`), a separate, untouched control. See
  `DECISIONS.md`.
- **"Read" button removed from Issue detail** — the `comicvault://read/{id}`
  deep-link button, non-functional on a plain desktop browser (no web reader
  exists — `BUG-021`). `buildStatusToggle()`'s "Mark as Read" button is
  separate and untouched. `SPEC.md` §11 and `BUGS.md` BUG-021 updated to
  match. See `DECISIONS.md`.
- **Series detail Genre tags fixed to be real links** — were plain `<span>`,
  not `<a>`, unlike Issue detail's genre tags (which already link to
  `/?surface=fieldview&field=genre&value=…`). Matched the Issue detail
  pattern exactly.
- **Clear Filter pill unified — two rounds of fixes:**
  1. Restyled `#filterClear` from a plain text link to a solid accent pill
     (`var(--accent)` background, `var(--on-accent)` text) matching the
     collapsed sidebar's single-letter Library badges — Tez's reference for
     what an "active" filter control should look like.
  2. Discovered the fieldview banner's own "Clear filter" link
     (`.fieldview-banner-clear`) was a *second*, differently-styled and
     differently-positioned "clear the filter" control — plain text link,
     sitting inline in the banner text rather than as a pill next to the
     count. Gave both elements the same CSS rule and moved `#filterClear` out
     of `#browseFilters` into `.menu-bar-trailing` (the fieldview banner's own
     slot), so both trigger paths — a dropdown selection or a Genre/Writer/
     Artist link — now land the pill in the exact same place. Text
     capitalization matched too ("Clear Filter" both places). Deliberately
     did not add a "Field: Value" label to the dropdown case — see
     `DECISIONS.md` for why.
- **Login popup — compact + Cancel:** `.login-modal` (shared with the "no
  password set" dialog, not the larger Editor Basic/Full modals) narrowed
  60% (720px → 288px shared `.editor-modal` width) with a consistent 10px
  horizontal inset. Added a "Cancel" button — there was previously no way to
  dismiss the popup without entering a password. `hideLoginPopup()` extended
  to clear the password field and any error message on close, so a later
  reopen doesn't show stale state.
- **Full Editor toolbar:** "Search Online" renamed **"Search ComicVine"**
  (it's specifically a ComicVine search) and moved out of the header into a
  new row directly above the three-column layout, sharing `.fe-layout`'s
  exact `340px / 1fr / 368px` grid template so it sits centred over the XML
  Editor column at any window width — not an eyeballed margin. Added a new
  **"Search GoodReads"** link alongside it in the same row/group — a plain
  `target="_blank"` link to goodreads.com, no field wiring, Tez's addition.
- **Admin "Last Scan" card — date only:** was showing a full date+time
  string (`toLocaleString()`), and the persisted-restart-survival fallback
  (`scanState.last_scan_persisted`, read straight from `last_scan_log.md`'s
  last line) also showed a trailing `Duration: HH:MM:SS` since that log line
  format bundles both. Switched the live path to `toLocaleDateString()` and
  split the persisted fallback string on its first space to keep just the
  date. The log file itself is untouched — full time + duration detail is
  still one "Logs" click away. Caught via a browser-cache false alarm: the
  first refresh after this fix still showed the old format, traced to a
  stale cached `admin.js` (FastAPI's static file serving sends no explicit
  cache-control headers) — a hard refresh confirmed the fix was correct all
  along.

**Docs updated same session:** `SPEC.md` §11 (Read button removed, deep-link
section note), `MENU_BAR_SPEC.md` §2.5/§2.7 + Change Log, `CUSTOM_TABS_SPEC.md`
§9.2/§9.6 + Change Log, `EDITOR_SPEC.md` §9.4 + Change Log, `ADMIN_SPEC.md`
§7.1.2/§4 + Change Log, `BUGS.md` (BUG-021 annotated), `DECISIONS.md` (six new
entries).

## Session — 2026-07-09 — First performance-diagnostics baseline (not a build-queue item)

Tez asked for a diagnostics-only pass — no benchmarks existed yet, no fixes or
functional changes in scope, just finding and quantifying real bottlenecks,
with the USB-attached (bus-powered, no wall adapter) library drive `L:\Comic
Archives` called out explicitly as a variable to isolate. Zero application
code was touched; every measurement came from standalone read-only scratch
scripts (outside the repo, per `TESTING.md`'s existing convention) against the
already-running live server/DB, or read-only OS-level inspection.

- **Two hard, numbers-backed N+1 findings, confirmed identically in-process,
  over HTTP, and in a real browser:** `GET /api/library` (the main
  browse/listing endpoint, hit on nearly every navigation) fires **7,508 SQL
  queries** and takes ~4s — caused by `i.genres` being accessed per-issue via
  a lazy relationship with no `joinedload`/`selectinload` anywhere in the
  codebase, plus one extra `ReadingProgress` query per unique series (2,080
  series). `GET /api/series/{id}` for the library's largest series ("2000
  AD", 2,483 issues) fires **4,969 queries** (~2.6s) from one
  `ReadingProgress` query per issue with no batching — a normal 25-issue
  series (Postal) takes only 53 queries (~30ms) for comparison, confirming
  clean linear N+1 scaling. Both were reproduced as genuine multi-second
  waits in an actual browser click-through, not just synthetic numbers.
- **Cover images never honor cache revalidation:** confirmed live that a
  byte-exact `If-None-Match` still gets a 200 with the full body back (0/15
  sampled covers ever got a 304); no `Cache-Control` header is set anywhere
  in `reader.py`. A full "All library" grid view re-transfers all ~80MB of
  visible thumbnails from local disk every single time, even when nothing
  changed.
- **Reader page-serving has zero caching, proven end-to-end:** flipping to a
  never-before-read page and re-flipping to an already-viewed page cost the
  same (22.8ms vs 22.7ms median) — `_sorted_pages()` re-opens the archive and
  re-parses the whole ZIP central directory on every single
  `/api/page/{id}/{n}` call (cold `archive_namelist()` alone costs a median
  42.5ms, vs 0.6ms warm), while raw sequential disk throughput for the same
  files is healthy (91.4MB/s median) — confirms this is app-level overhead,
  not the drive.
- **USB drive itself is not the bottleneck** — raw sequential throughput
  measured healthy and consistent (75-95MB/s across ~130 sampled files, two
  independent test passes). A genuine cold-idle probe (drive left untouched
  12 minutes, then a fresh never-touched file read) came back inconclusive:
  one of two valid samples showed roughly half the expected throughput for
  its size, the other was normal — not enough to confirm or rule out a
  USB-power-management effect; flagged as an open follow-up rather than
  overclaimed. (First idle-probe attempt re-read the *same* file after 12
  minutes and got an impossible 1,718MB/s — proved Windows' RAM file cache
  survives well past 12 minutes regardless of drive state, not a spin-down
  finding; corrected the method to always use a fresh file per rep.)
- **Found and corrected a red herring in the session's own tooling, not the
  app:** an early HTTP-timing pass hitting literal `localhost:9424` showed a
  uniform +2000-2700ms floor on *every* endpoint, including one whose actual
  DB work takes under 1ms. Root cause (confirmed via a raw socket test):
  Windows resolves `localhost` to IPv6 (`::1`) first, the server binds IPv4
  only, and the refused IPv6 attempt takes ~2000ms before falling back —
  not a ComicVault bug, and real browsers are unaffected (Happy Eyeballs
  races IPv4/IPv6 rather than trying sequentially). Re-ran everything against
  `127.0.0.1` for accurate numbers; documented for any future scripts on this
  host.
- **Not measured this pass, flagged as follow-ups:** Full Editor's
  page-preview endpoint (admin-auth-gated; code inspection alone flags it as
  the highest-risk unmeasured area — full-resolution, base64-in-JSON, no
  caching), scanner behaviour at real scale (all 18 historical log entries
  were near-no-op incremental runs, not representative of processing a real
  batch of new files), and a true cold-server-restart baseline (stayed
  warm-only against the already-running tray-app server, per Tez's call).
- Wrote up the full baseline, ranked findings table, raw data, and a reusable
  methodology as a new standing doc, **`docs/PERFORMANCE.md`** (parallel to
  `TESTING.md`, for speed/load rather than correctness) — added to
  `docs/INDEX.md`'s active/authoritative table. No `BUGS.md`/`ROADMAP.md`/
  build-queue entries this session — triaging which findings to actually act
  on, and when, is a deliberately separate later decision.
- **Packaged the methodology as a reusable skill**, `.claude/skills/
  perf-diagnostics/`, at Tez's request before closing the session — a
  future re-run (after a fix, or just to check for regressions) shouldn't
  have to rediscover the gotchas this pass hit the hard way (the `localhost`
  IPv6-fallback artifact, the cold-idle probe's cache-reuse mistake). The
  skill folder holds the ground rules, known gotchas, phased methodology,
  and the six actual working scripts from this session (plus a new
  `0_find_targets.py` helper to refresh the hardcoded series/issue/tab IDs
  those scripts target, since those will drift as the library changes).
  `docs/PERFORMANCE.md` now points to the skill instead of expecting a
  future session to re-derive the method from its own prose.

## Session — 2026-07-11 — Inbox cosmetic pass (5 items)

Worked through `INBOX.md`'s cosmetic/change items first, per Tez's request at
session start. All five are pure visual restyles of existing card elements
plus one small new pill — no build-queue item, no `DECISIONS.md` entry, no
bug ticket, per `CLAUDE.md` Section 5's cosmetic threshold.

- **Favourite badge → red heart, white bg** (`style.css`): swapped the `★`
  content for `♥`, gold → `#e02424` red, translucent-black bg → solid white.
  Border/size/position unchanged.
- **Unread badge text → white**: `.unread-badge`'s `color: #000` → `#fff`.
- **Personal-rating pill (new)**: added `.card-rating-pill`/`.rating-star`
  CSS (bg/border matching the existing `.selection-rate` bottom-toolbar
  pill) and a `buildRatingPill()` helper in `app.js`, called from both grid
  card builders (`buildCard` for Series/Singles/All, `buildFolderFileCard`
  for Custom Tab Folder View) whenever `personal_rating > 0` — renders a
  vertical stack of gold stars, one per rating point, bottom-right of the
  cover, growing upward. Confirmed `personal_rating` is already present on
  the API payloads both builders consume (`/api/library`, `/library/tab/
  {id}/folder`) — no backend change needed. Not added to the flat issue-list
  row or Home Strip cards (neither shows the favourite/unread badges either,
  so this follows the same existing precedent).
- **Card-selected dot → gold tick, dark grey bg**: `.select-dot`'s selected
  state now sets a dark grey (`#333`) circle background with a `✓` gold
  (`var(--favourite)`) glyph, replacing the small solid blue dot.
- **Admin Scan cards — outline removed from 3 of 6**: added `id`s
  (`lastScanCard`, `changedFilesCard`) alongside the existing `scanNowCard`
  in `admin.js`'s `renderScanSection()`, then `border: none` on those three
  IDs in `style.css`. Files Found / New Files / Missing Records intentionally
  keep the default `.stat-card` border — only the three named in the inbox
  line change.
- **Verified manually** in a real Chrome tab against the live tray-app
  server (`localhost:9424`, hard-reloaded to bypass a stale-cache false
  start where the old star/black-badge briefly still showed): favourite
  heart and rating pill both confirmed on real favourited/rated titles
  (`2000 AD Presents Sci-Fi Thrillers`, `Neuromancer`, `110 Per¢`); unread
  badge's white text confirmed on a partially-read series; selected-card
  gold tick confirmed by actually selecting a card via the multi-select
  flow; Admin page confirmed Scan Now/Last Scan/Changed Files borderless
  while Files Found/New Files/Missing Records keep theirs. No console
  errors at any point.
- `docs/SPEC.md` §20.18 added (all five behaviours). `INBOX.md`'s five
  lines struck through with destination annotations. No spec update needed
  for `ADMIN_SPEC.md` §4 — it never claimed anything about card borders, so
  nothing there was made inaccurate.

**Same-session follow-up, after Tez's review:**

- **Favourite heart badge was egg-shaped** (screenshot: `fav.PNG`) — the `♥`
  glyph's own metrics aren't square like the `★` star's were, so sizing the
  badge by content+padding alone stretched the `border-radius:50%` circle
  into an oval. Fixed with explicit `width:20px; height:20px;` and flex
  centring, so the circle is a true circle regardless of glyph shape.
- **Admin card outline fix corrected — scope was wrong, not the styling.**
  Tez: "I should've said make all the card outlines the same" — the first
  pass stripped the border from only 3 of the 6 Scan-section cards, leaving
  a visibly inconsistent row (plus `#scanNowCard` already had its own
  distinct default white border, pre-dating this session, that the first
  pass didn't touch). Reworked: removed the per-ID `border: none` overrides
  and the now-unnecessary `lastScanCard`/`changedFilesCard` IDs in
  `admin.js`; changed `.stat-card`'s own base border to `1px solid
  transparent` (not `border: none`, so the border box still exists for
  state overrides to colour in) — applies uniformly to all six Scan cards
  *and* the five Library Stats cards above them, one rule instead of an
  ID allowlist. Removed `#scanNowCard { border-color: #fff; }`'s special
  default so it matches the rest at rest. Left `#scanNowCard.is-scanning`'s
  and `.has-pending`'s green `border-color` overrides untouched — those are
  real status indicators (scan in progress / unread log entries, §8), not
  decorative outline, and only set colour so they still render correctly
  against the new transparent baseline.
- **Verified manually** again after both fixes: heart badge zoomed-in
  screenshot confirms a true circle; Admin page confirms all six Scan cards
  plus the five Library Stats cards share the same borderless idle look,
  with the green "unviewed log entries" indicator still showing correctly
  on Last Scan (real pending state, not a bug). No console errors.
- `docs/SPEC.md` §20.18 updated in place for both corrections rather than
  appending a second entry, since the earlier description was simply wrong,
  not superseded.

## Session — 2026-07-11 — Basic Editor async save (INBOX.md, second item worked this session)

`POST /api/editor/{issue_id}` used to run field validation, XML merge, the
full archive rebuild, and a single-file rescan all synchronously — the
popup stayed open ("Saving…") for the whole round trip, dominated by the
archive rebuild (extract-all → rebuild-zip-from-scratch → atomic replace,
scales with page count, not XML size). Tez wanted to navigate away as soon
as Save is clicked. Planned in Plan Mode first (two Explore-agent research
passes covering the current save flow and the codebase's existing
background-job pattern, then a Plan agent to work out the concrete diff)
before writing any code — see the approved plan for the full design
rationale.

- **Backend (`backend/routers/editor_basic.py`):** split
  `save_editor_fields()` — validation + XML merge stay synchronous (still
  422s immediately on bad input); the archive rewrite + rescan moved into a
  new `_finish_save()` background-task worker, mirroring
  `admin.py`'s `_run_scan_background()` (fresh `SessionLocal()`, since the
  request-scoped session and the `issue` ORM object loaded from it are both
  gone by the time a `BackgroundTasks` callback runs — the worker re-queries
  `Issue` by id instead of being passed the original ORM object). Progress
  tracked per-issue (`dict[int, EditorSaveProgress]`, not a single global
  singleton like the Processing Tools use), since the Basic Editor can be
  opened against different issues from different tabs. New `409` guard
  against a second concurrent save on the same issue (set
  `running=True` synchronously before queuing, closing the race window
  between two fast back-to-back POSTs). New `GET .../save-status` polling
  endpoint. `GET /api/editor/{issue_id}` gained a `saving` flag so the popup
  can detect and block a conflicting edit if a save for that issue is still
  finishing.
- **Frontend (`frontend/js/editor_basic.js`):** `onEditorSubmit()` now
  closes the modal immediately on `pending: true` instead of waiting for
  the rebuild, shows a "Saving in background…" toast, and starts a
  self-rescheduling `setTimeout` poll of the new status endpoint (same
  pattern as `processingTools.js`'s `pollXtStatus()`) — on completion,
  toasts "Saved" and calls the existing `onSaved()` callback
  (`initIssue()`) so the issue page picks up the new data; on error, toasts
  the failure and leaves the page as-is. New `showEditorToast()` reuses the
  existing `.admin-toast` CSS classes directly (`style.css` is loaded
  globally, not just on the Admin page — only `admin.js` itself is
  Admin-only) rather than duplicating that CSS. `openEditorModal()` now
  reads the `saving` flag and, if true, shows a neutral notice
  (`.editor-error--notice`, new CSS, reuses `var(--accent)` instead of the
  base rule's red) and disables the form fields + Save — Cancel/Close stay
  enabled either way, so the notice never traps the user in the modal.
- **Accepted trade-off, confirmed with Tez before building:** if a
  background save fails after the user has already navigated away, it's
  silent — no new cross-page/persistent notification system, discoverable
  only by reopening the editor and seeing the edit didn't take. Safe either
  way since the archive rewrite only replaces the original file via an
  atomic `os.replace()` after the new file is fully staged, so a failure
  never corrupts anything. Full rationale in `DECISIONS.md`.
- **Verified manually**, real backend, scratch data only — never touched
  `L:\Comic Archives` (`CLAUDE.md` §6). Registered a temporary `Issue` row
  in the live DB pointing at a scratch multi-page CBZ built in the session
  scratchpad (first 60 pages/38KB — rebuilt too fast to observe the
  in-flight window at all once the OS file cache warmed up; regenerated at
  120 pages/34.5MB of random-noise JPEGs, ~3.7s cold-cache rebuild, for the
  timing-sensitive checks), confirmed via direct DB query afterward that
  cleanup removed it and the real library was never touched.
  - **Discovered mid-session: the live server doesn't hot-reload**
    (`reload=False` in `start_server.py`) — the first pass of testing was
    silently exercising the *old* synchronous code the whole time (matching
    response shape gave it away: `series`/`number` fields with no
    `pending` key). Asked Tez before restarting the tray app's server via
    the local-only `/api/admin/restart` endpoint (same one used in prior
    sessions for this exact purpose) rather than doing it unprompted, since
    it's Tez's live personal server and could interrupt something he's
    doing on another device — confirmed, restarted, re-tested against the
    real new code from there.
  - Real click-through: edit a field, Save — modal closed near-instantly,
    "Saving in background…" toast, page auto-refreshed with the new value
    once the background task finished; confirmed the *archive itself* (not
    just the DB) had the new XML and all pages intact by reading the CBZ
    directly afterward, across three separate saves.
  - 409 guard: two concurrent `POST`s (fired via `Promise.all` in the
    browser) — first got `200 {pending: true}`, second got `409`.
  - In-flight `saving` flag: a same-script POST-then-immediate-GET (no
    round trip in between) showed `saving: true`/`running: true` right
    after a `pending: true` response, and the poll loop correctly resolved
    to `running: false` once the background task finished.
  - Frontend notice rendering: a UI-click-based attempt to catch this live
    kept missing the window (background rebuild finishing faster than the
    browser-automation tool round trips once the scratch file was
    OS-cache-warm) — switched to intercepting `window.fetch` to force a
    `saving: true` response and confirmed the notice, disabled fields, and
    disabled Save render correctly, with Cancel/Close staying enabled. Hit
    the project's known stale-browser-cache gotcha once during this
    (`progress.md`'s Phase C2b precedent) — a hard reload fixed it; the
    first "the notice doesn't render" result was the browser serving a
    cached pre-edit copy of `editor_basic.js`, not a real bug.
  - Validation still blocks synchronously: an intentionally incomplete
    payload (Summary only, no Genre/Format/AgeRating) got `422` with the
    expected enforced-field errors, no background task queued.
  - Toast styling: both the neutral "Saving…" and the red `--error` variant
    confirmed visually correct.
  - No console errors at any point across the session.
- `docs/EDITOR_SPEC.md` §6.1 rewritten for the new async shape + Change Log
  entry; `docs/DECISIONS.md` entry for the silent-failure trade-off;
  `docs/CHANGELOG.md` one-liner.
