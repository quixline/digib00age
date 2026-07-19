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

## Session — 2026-07-12 — Removed the docs/ Google Drive junction, retired Cowork's nightly doc-scan

- **Goal:** Tez no longer needs Google Drive/Cowork in the loop for
  `docs/`. Removed the Windows directory junction and replaced it with a
  real folder in the repo containing the same files, then checked and
  updated everything that assumed the junction existed.
- **Migration:** confirmed via `fsutil reparsepoint query` that `docs/`
  was a genuine NTFS junction (Mount Point) into
  `C:\Users\tezdr\My Drive (quixlinedesign@gmail.com)\Dev_Folders\Workshop\
  comicvault_v2\project_docs`, and that git already tracked the real file
  content directly (`core.symlinks=false`, blobs are plain `100644`
  files) — so removing the junction changes nothing from git's
  perspective. Robocopied all 44 files (31 git-tracked + 13 gitignored
  Cowork/meta files) from the junction-resolved path into a staging
  folder, removed the junction with `rmdir` (link only, target untouched
  — verified the original Drive folder still has all 44 files
  afterward), renamed staging into place as `docs/`, cleared a stray
  inherited ReadOnly attribute, and confirmed write access. `git status`
  and `git ls-files docs` were byte-for-byte identical before and after
  (same 31 tracked files, same two pre-existing modified files —
  `INBOX.md`, `meta/roadmap.html` — untouched by the swap).
- **Impact check surfaced a second, bigger thing:** Cowork's nightly
  doc-scan automation (drift/contradiction checking across the doc set)
  was built entirely on top of that junction — `meta/working-rules.md`
  and `meta/cowork-doc-scan-instructions.md` described it, logged to
  `doc-scan-issues.md`, tracked state in `doc-scan-state.md`. With the
  junction gone, Cowork has no path into these docs anymore. Asked Tez
  whether to retire that workflow or leave it for a separate
  Cowork-side reconfiguration — **Tez chose retire**.
- **Retirement done:** moved `doc-scan-state.md` and
  `meta/cowork-doc-scan-instructions.md` (both gitignored, never
  git-tracked) into `docs/archive/` as point-in-time records, alongside
  the already-archived `cowork-notes.md` and `doc-scan-issues.md`/
  `doc-scan-issues-archive.md`. Added a retirement note to
  `meta/working-rules.md` and rewrote `INDEX.md`'s "Doc-scan automation
  (Cowork)" section to match. Left `DECISIONS.md`/`ROADMAP.md`'s
  historical entries mentioning Cowork's nightly scan untouched — those
  are rationale/narrative log, describing what was true when written,
  not live claims.
- **Docs updated:** `CLAUDE.md` §2 (junction description → plain-folder
  description, gitignored so not part of this commit), `README.md`
  (dropped the junction pointer line), `docs/INDEX.md` (folder-structure
  section, doc-scan-automation section, archive table, the 2026-06-27
  known-gap note marked moot), `docs/meta/working-rules.md` (archive
  description, Inbox-workflow bullet, new retirement note — gitignored,
  not part of this commit).
- **Not touched, flagged for later:** the broader "Chat/Cowork → docs →
  Design → Code → docs → git workflow" phrase in `CLAUDE.md` §5 and
  `working-rules.md`'s structural-change threshold — that's about
  Cowork's planning role generally, a separate question from the
  nightly-scan mechanism this session retired.

## Session — 2026-07-12 (same day, follow-up) — Confirmed scan cancellation is permanent; Claude Code is now master controller

- Tez followed up on the item flagged above: the nightly scan wasn't left
  open as "no replacement yet" — it's cancelled outright, won't run again.
  Tez also clarified the bigger picture the flagged item was gesturing at:
  Claude Code is now the **master controller** for this project — planning,
  triage, build, and docs all happen in a Code session — with one
  exception: outside planning docs (a Design mockup, notes from a Chat
  conversation) still get dropped into the repo as reference material when
  they exist, just not as a required upstream stage Code waits on.
- Also clarified how session continuity works now that the scan is gone:
  a `SessionEnd` hook captures a plain-text conversational summary into
  `the_brain` (personal, cross-project record, separate from this repo)
  every time a Claude Code session ends — additional to, not a substitute
  for, this project's own doc updates (`progress.md`, `CHANGELOG.md`,
  `DECISIONS.md`) which still happen exactly as `working-rules.md` and
  `CLAUDE.md` describe.
- **Docs updated:**
  - `docs/meta/working-rules.md` — added a "Master controller" section up
    top; reworded the structural-threshold bullet, the Inbox-triage
    bullet, the roadmap.html wholesale-regen note, and the version-lifecycle
    bullet to point at Code instead of "Chat"/"Chat triage pass"; firmed up
    the Cowork-retirement note from "no replacement mechanism yet" to
    "cancelled for good."
  - `CLAUDE.md` — §2's citation of the old scan-issues file repointed to
    its new `archive/` path; §4 (roadmap.html bullet) repointed the
    placement-decision call from "a triage session with Chat" to Code as
    master controller; §4 gained a note distinguishing the `SessionEnd`
    hook from this project's own close-of-session doc updates; §5's
    Structural bullet reworded to drop the "Chat/Cowork → docs → Design →
    Code" pipeline language in favour of Code-as-master-controller, with
    outside planning docs as optional reference input.

## Session — 2026-07-12 (same day, follow-up) — Performance fixes Phase 1: `/api/library` N+1

- Found and triaged `docs/PERFORMANCE.md`'s 2026-07-09 baseline — nothing
  from it had been queued anywhere yet. Ranked the fixable findings by
  impact, agreed with Tez to track the work as v2.6 Item 2 (folder stayed
  open for follow-ups per `INDEX.md`) and to close each phase out (build →
  manual test → commit) before starting the next, rather than batching all
  fixes into one test pass.
- **Phase 1 built:** `backend/routers/library.py`'s `get_library()`
  (`GET /api/library`) had two N+1s — `Issue.genres` accessed per-issue via
  a lazy relationship across ~5,400 issues, and a `ReadingProgress` query
  re-run once per unique series (2,080 series) instead of batched. Fixed
  with `selectinload(Issue.genres)` on the initial query and one
  `ReadingProgress` query across every issue in scope, built into a
  `read_map` before the per-series loop instead of inside it.
- **Verified:** in-process query-count check (same methodology as
  `PERFORMANCE.md` Phase B) confirmed 7,508 → 13 queries, 3.9-4.1s →
  ~0.63-0.67s median. The live reader-server subprocess doesn't autoreload
  (plain `subprocess.Popen`, no `--reload`), so it needed a restart to pick
  up the change — Tez restarted it via the tray app and confirmed live: All
  Library loads visibly faster, no console errors.
- **Docs updated:** `v2.6/comicvault-changes-v2.6.md` (new Item 2, Phase 1
  marked done, Phases 2-5 scoped), this file, `CHANGELOG.md`,
  `PERFORMANCE.md` (Phase 1 re-baseline appended to §1).
- **Next:** Phase 2 — `GET /api/series/{id}` N+1 for large series, same
  `ReadingProgress`-batching pattern Folder View's `progress_map` already
  uses.

## Session — 2026-07-12 (same day, follow-up) — Performance fixes Phase 2: `/api/series/{id}` N+1

- **Phase 2 built:** `backend/routers/library.py`'s `get_series()`
  (`GET /api/series/{issue_id}`) had `_progress_for(iss.id, db)` called once
  per issue in the loop building `issue_list` — one `ReadingProgress` query
  per issue in the series (finding #2's named root cause). Fixed with a
  batched `progress_map` built once across `issues_sorted`, same pattern as
  Folder View's existing `progress_map` and Phase 1's library fix.
- **Found along the way, not named in the original baseline:** the
  series-wide `all_genres` aggregation (`for i in issues for g in i.genres`)
  was a second, separate N+1 — the query-count math in the original baseline
  (4,969 for a 2,483-issue series) only adds up as *two* per-issue queries
  (progress + genres), not one. Fixed with `selectinload(Issue.genres)` on
  the `all_issues` query, same pattern as Phase 1.
- **Verified:** in-process query-count check — 2000 AD (2,483 issues):
  4,969 → 9 queries, 2.5-2.7s → ~0.33-0.42s median. Postal (25 issues, the
  baseline's "typical series" comparison point): 53 → 5 queries. Tez
  restarted the reader server via the tray app and confirmed live: 2000 AD
  loads fast, no console errors.
- **Docs updated:** `v2.6/comicvault-changes-v2.6.md` (Item 2 Phase 2 marked
  done), this file, `CHANGELOG.md`, `PERFORMANCE.md` (Phase 2 re-baseline
  appended to §1, and the finding #2 root-cause note amended to mention the
  genres N+1 it didn't originally catch).
- **Next:** Phase 3 — reader page-serving (findings #4/#5), cache the
  sorted page list per issue instead of re-parsing the ZIP central
  directory on every page request.

## Session — 2026-07-13 — Performance fixes Phase 3: reader page-serving cache

- **Phase 3 built:** `backend/routers/reader.py`'s `_sorted_pages()` re-parsed
  the CBZ/CBR's ZIP central directory (`archive_formats.archive_namelist()`)
  on every call — hit by `/api/page/{id}/{n}`, `/api/issue/{id}/pages`, and
  the cover fallback path alike, with zero caching benefit even for
  re-flipping to an already-viewed page (findings #4/#5). Added an
  in-process cache keyed on `archive_path → ((mtime, size), sorted_pages)` —
  an `os.stat()` check (cheap) gates a cache hit, and a changed file on disk
  (rescan/replace) invalidates automatically since its `(mtime, size)` key
  changes.
- **Verified:** in-process check on issue 11 (Four Horsemen #1, the same
  file the original baseline's Phase D2 used): cold parse 5,483ms this run
  (this specific file was genuinely cold-disk, consistent with finding #9's
  known cold-idle drive variance — not a regression from this change) →
  warm cache-hit 0.08-0.13ms. Tez restarted the reader server and read
  through several pages of a comic live, no console errors.
- **Docs updated:** `v2.6/comicvault-changes-v2.6.md` (Item 2 Phase 3
  marked done), this file, `CHANGELOG.md`, `PERFORMANCE.md` (Phase 3
  re-baseline appended to §1).
- **Next:** Phase 4 — cover image caching (finding #3): `Cache-Control`
  headers + honoring conditional `If-None-Match` GETs in
  `backend/routers/reader.py`.

## Session — 2026-07-13 (same day, follow-up) — Performance fixes Phase 4: cover Cache-Control/ETag/304

- **Phase 4 built:** `GET /api/cover/{issue_id}` (`backend/routers/reader.py`)
  had no `Cache-Control` header and never honored conditional GET — root
  cause (finding #3): Starlette's `FileResponse` computes and sends an
  `ETag`/`Last-Modified` automatically, but has no logic anywhere to check
  an incoming `If-None-Match` against it, so a `304` was never possible even
  though the ETag was already present in every response. Added an explicit
  `Cache-Control: public, max-age=86400` header, computed the ETag manually
  (same md5(mtime+size) formula `FileResponse` already used, so any
  previously-cached client ETag stays valid), and check
  `request.headers["if-none-match"]` before building the `FileResponse`,
  returning a bare 304 with no body on a match. The rare CBZ-extraction
  fallback path (thumbnail missing — ~0% of requests, coverage is ~100%)
  got the `Cache-Control` header too, without the conditional-GET logic
  (not worth the complexity for a path that's essentially never hit).
- **Verified:** `TestClient` in-process check — fresh request 200 with
  `Cache-Control`/`ETag`, matching `If-None-Match` → 304 with empty body,
  stale `If-None-Match` → full 200. Re-confirmed against the live,
  already-restarted server over direct HTTP (same result). Tez confirmed
  live in the browser: All Library loads faster, no console errors. A
  scripted browser reload via Claude-in-Chrome didn't show 304s in its
  network log on a same-URL `navigate()` — traced to a browser-automation
  cache-revalidation quirk (scripted navigation doesn't exercise HTTP cache
  revalidation the way a real user reload does), ruled out as a server
  issue by the direct-HTTP check against the identical running process.
- **Docs updated:** `v2.6/comicvault-changes-v2.6.md` (Item 2 Phase 4
  marked done), this file, `CHANGELOG.md`, `PERFORMANCE.md` (finding #3 and
  Phase 4 re-baseline).
- **Next:** Phase 5 — Full Editor page-preview (finding #6), unmeasured in
  the original baseline (admin-auth-gated); needs a real measurement pass
  through an authenticated browser session before deciding whether/what to
  fix.

## Session — 2026-07-13 (same day, follow-up) — Performance fixes Phase 5: Full Editor page-preview

- Finding #6 was the one baseline finding never actually measured (code
  inspection only, deliberately avoiding a scripted admin login with the
  real password). Tez temporarily disabled admin password protection so
  this session could measure it live via Claude-in-Chrome, without ever
  handling the password directly (still off-limits per the credential
  rule even with permission granted).
- **Measured:** loaded the 1,220-page "East of West: The End of Times
  Compendium" into the Full Editor (`http://127.0.0.1:9424/editor`,
  `file_id=5`). Direct HTTP timing against the live server:
  `/api/editor/full/files/5/page/{n}` took 25-330ms per page, transferring
  up to 3.7MB of base64-encoded JSON, with **zero improvement on repeat
  requests** to the same page (page 0: 68ms→65ms, page 1: 30ms→25ms) —
  confirmed the same root cause as findings #4/#5 (the ZIP central
  directory re-parsed on every call), just living in
  `backend/routers/editor_full.py`, a separate module from `reader.py`
  that doesn't share its Phase 3 cache.
- **Scope decision (Tez):** fix only the page-list N+1, not the
  full-res/base64 image encoding itself — the latter is a bigger, more
  invasive change with real editor-UX tradeoffs (image quality) that
  wasn't part of this pass.
- **Phase 5 built:** added `_cached_image_list()` to
  `backend/routers/editor_full.py` — same `(mtime, size)`-keyed cache
  pattern as Phase 3's `_sorted_pages()` — and pointed both
  `get_file_preview()` and `get_file_page()` at it instead of each
  independently re-calling `archive_formats.archive_namelist()`.
- **Verified:** re-added the same compendium after Tez restarted the
  server, re-timed via direct HTTP: repeat page requests now show a real
  cache benefit (page 0: 153ms→53ms, page 1: 91ms→16ms) instead of the
  pre-fix flat/no-improvement pattern. Cleared the editor's working-file
  list via the API afterward to leave no residue (no library/DB writes
  occurred at any point — this endpoint only reads from working-set files
  outside the library).
- **Docs updated:** `v2.6/comicvault-changes-v2.6.md` (Item 2 Phase 5
  marked done, Item 2 marked complete overall), this file, `CHANGELOG.md`,
  `PERFORMANCE.md` (finding #6 and Phase 5 re-baseline). **v2.6 Item 2
  (Performance fixes) is now complete** — all 5 phases from the
  2026-07-09 baseline built and verified.
  - `docs/INDEX.md` — retirement section reworded to state the scan is
    cancelled permanently, not paused; "Code and Chat" read-access line for
    `archive/` simplified to "Code."
  - `docs/DECISIONS.md` — new entry ("Claude Code as master controller;
    Cowork's scan cancellation confirmed permanent") capturing this
    session's clarification, kept separate from yesterday's
    retire-vs-reconfigure entry rather than editing it in place.
- **Not touched:** `docs/DECISIONS.md`/`docs/ROADMAP.md`'s pre-existing
  historical entries that mention Cowork's nightly scan or a Chat triage
  session — those describe what was true when written and stay as
  narrative record, same reasoning as the prior session's entry.

## Session — 2026-07-12 (same day, second follow-up) — Stale-cover false alarm investigated; bulk star-rating bug found and fixed (BUG-022)

Tez reported a Singles issue (`Dusk - Poor Tom (2000)`, id 3414) showing the
wrong cover after a bad duplicate-named file was removed from the archive and
a rescan ran. Investigated read-only first, in plan mode.

- **Stale-cover report — not a real bug, confirmed by direct evidence, not
  just theory.** Extracted the archive's current front-cover entry
  (`bu_Dusk_00fc.jpg`, no more duplicate names) and the cached
  `backend/thumbnails/3414.jpg`, compared them visually — identical, correct
  cover. Thumbnail file's mtime (18:43:20) is after the archive's mtime
  (18:41:53), proving the scanner's unconditional `_generate_thumbnail()`
  call (`backend/scanner.py`) did regenerate it correctly. DB row, cached
  JPEG, and archive were already fully consistent — Tez confirmed live it
  was resolved by a browser refresh. No code change, no `BUGS.md` entry
  (not a real defect). Worth remembering for next time: `/api/cover/{id}`
  has no `Cache-Control` header and no versioned URL, so a browser can serve
  a stale copy after any cover regeneration — flagged as a latent
  perf/correctness improvement, not acted on since nothing is actually
  broken today (only surfaces as a confusing false alarm, as here).
- **New bug found via the same investigation session:** selecting card(s)
  and applying a star rating from the bottom multi-select toolbar didn't
  update the card(s) — no visible change, looked like a persistence bug.
- **Root cause:** `frontend/js/app.js`'s bulk-action toolbar
  (`ensureSelectionToolbar()`) routes every button through
  `runBulkAction(path, extraBody, applyFn)`, which only patches the DOM/
  cache if a third `applyFn` argument is passed (`applyReadStateToDom`,
  `applyFavoriteToDom` both do this). The two rating call sites (clear +
  5 stars) never passed one — a gap left over from `.card-rating-pill`
  (`SPEC.md` §20.18) being added 2026-07-11, after the original bulk-toolbar
  code, with no equivalent `applyRatingToDom` ever added. The backend write
  itself (`POST /api/progress/bulk/rate`) was correct throughout — this was
  purely a client-side reflection gap, confirmed by reading the single-issue
  rating control (self-patches its own state, unaffected) and by a scratch
  DB read showing the rating persisted correctly even before the fix.
- **Fixed:** added `applyRatingToDom(ids, rating)` / `_patchRatingInCaches`
  (mirrors `applyFavoriteToDom`/`_patchFavoritesInCaches`) and wired them as
  the `applyFn` for both rating call sites.
- **Verified live** against the running dev server (`localhost:9424`, real
  library, read/write-safe scratch verification only) — drove the actual UI
  functions (`selectOrToggle`, real `.click()` on the toolbar's star/clear
  buttons) on a real browse-grid card: `.card-rating-pill` appeared/updated/
  disappeared immediately with no reload, cache (`allLibrary`) patched
  correctly, and cross-checked against the live DB (`personal_rating`
  column) at each step to rule out a cache-only false positive.
- **Docs:** logged directly to `docs/archive/bugs-fixed-archive.md` as
  BUG-022 (found-and-fixed in one session, per `CLAUDE.md`'s allowance for
  that) rather than round-tripping through `BUGS.md` first.
- **Also noted:** `docs/INDEX.md` currently claims "no active version folder
  right now" for v2.6, but `docs/v2.6/progress.md` (this file) has been the
  live, current log since 2026-07-06 — `INDEX.md` is stale on this point.
  Flagged to Tez rather than silently corrected, since `CLAUDE.md` treats
  `INDEX.md` as the authority on doc status and this is exactly the kind of
  drift that's caused problems before (`archive/doc-scan-issues.md`).

## Session — 2026-07-13 (same day, follow-up) — Series Detail page pagination (v2.6 Item 3)

- From `INBOX.md`: "add pagination to /series/id" — the Series Detail
  page's issue list rendered every issue in the series flat, unpaginated,
  unlike every other browse surface (`SPEC.md` §20.13 already specified
  page-number navigation "on browse pages" but the Series Detail page had
  never picked it up).
- **Built:** `frontend/js/app.js` — `initSeries()` now caches the full
  `/api/series/{id}` response (`seriesPageData`) and renders through a new
  `renderSeriesIssuePage()`, which slices to the current page
  (`seriesCurrentPage`) using the same global `pageSize` setting Browse
  already reads from `cv_page_size`. Pulled Browse's existing
  `renderPagination()` click/render logic out into a shared
  `renderPaginationControls(container, current, totalPages, onPageChange)`
  helper — both Browse and Series Detail now call the same function, so the
  page-number control (`‹ 1 2 3 … N ›`) is guaranteed identical rather than
  a second copy that could drift. `/api/series/{id}` is unchanged — still
  returns the full issue list in one response; slicing is client-side, same
  pattern Browse already uses for its filtered library.
- **Verified live** against the running dev server (`localhost:9424`, real
  library, read-only — no destructive actions, no data mutated): 2000 AD
  (series id 79, 2,483 issues) correctly paginates into 50 pages of 50, last
  page (50) ends at issue #2484 with exactly 33 rows and `›` disabled;
  Postal (series id 4616, 25 issues, under one page) renders all 25 with an
  empty pagination container, matching Browse's own single-page behaviour.
  No console errors on either page load.
- **Docs:** `SPEC.md` §20.6 and §20.13 updated to note the Series Detail
  issue list is now paginated. `INBOX.md` line struck through and annotated.

## Session — 2026-07-13 (same day, follow-up) — Tray icon base glyph now reuses favicon.png

- From `INBOX.md`: "replace taskbar icon with icon-oo.png - keep current
  green dot for server running, red for stopped". Investigated first
  (Explore agent) rather than doing a literal swap: `icon-oo.png` (and the
  byte-identical `logo1.png`) is a 166×100 horizontal logo lockup pulled
  into `frontend/images/` generically during the v2.6 redesign (commit
  `77a0dc0`) — not square, not built as a tray asset, and would look wrong
  as-is at tray size.
- Checked `favicon.png` instead: 136×127, RGBA, transparent background
  around a solid blue rounded-square "oo" mark — square-shaped and already
  proven at small size (it's the live web favicon). Confirmed with Tez this
  was worth using despite cutting against the 2026-07-07 decision that the
  tray app stays outside the v2.6 digib00age rebrand — resolved as a
  narrow, visual-only exception (see `DECISIONS.md` "Tray icon base
  glyph"): the tray app's process/menu/log name stays "ComicVault"
  unchanged, only the icon's base artwork changed.
- **Built:** `tray/tray_app.py` — `make_icon_image()` now composites the
  existing 3-state coloured dot (green/amber/red, bottom-right corner,
  unchanged position/colours) over `favicon.png` instead of the old
  programmatically-drawn purple book glyph. New `_load_base_icon()` loads
  and letterboxes the favicon onto a transparent 64×64 canvas once, cached
  in `_base_icon_cache` (same per-call cost as before — the previous
  version also drew the full glyph fresh on every call).
- **Verified:** syntax-checked (`py_compile`), then imported the actual
  edited module (not a copy) and called `make_icon_image()` for all three
  states directly, rendering each to a scratch PNG and visually confirming
  the dot overlay reads cleanly against the favicon's blue glyph in all
  three colours. Did **not** launch a second live tray app instance to
  check it in the real system tray — the real one already owns port 9424
  and manages the actual reader subprocess; restarting it to see the new
  icon live is Tez's to do, not something to interrupt mid-session for.
- **Docs:** `SPEC.md` §3 updated (icon base glyph note). `DECISIONS.md` new
  entry. `INBOX.md` line struck through and annotated.

## Session — 2026-07-13 (same day, follow-up) — Issue Detail cover: hover zoom + white border

- From `INBOX.md`: "add a slight zoom and 80% white border 'on hover' over
  the cover image in issue/id". Cosmetic-only (hover state on an existing
  element, no layout/nav change) — per `CLAUDE.md`'s cosmetic/structural
  threshold, built directly without a `DECISIONS.md` entry or build-queue
  item.
- **Built:** `frontend/css/style.css` — `.issue-cover-img` gets a
  `3px solid transparent` border (reserves the space so hover doesn't
  shift layout) and a `transform`/`border-color` transition using the
  existing `--dur`/`--ease` motion tokens (respects
  `prefers-reduced-motion` automatically, same as every other hover effect
  site-wide). `:hover` scales to `1.04` and sets the border to
  `rgba(255, 255, 255, 0.8)`.
- **Verified live** against the running dev server (`localhost:9424`,
  read-only): loaded `/issue/4616` (Postal #1), confirmed no layout shift
  from the new transparent border, hovered the cover and confirmed the
  zoom + white border both render as expected (zoomed screenshot). No
  console errors.

## Session — 2026-07-13 (same day, follow-up) — Random library-page cover background

- From `INBOX.md`: "add a random cover image to the page (container) bg on
  library pages (home, all, singles, series and custom tabs)... only from
  the current library page... fill the container div... 40% transparency
  with 50% blur from the top right fading completely out."
- Read `frontend/index.html` first rather than guessing at "container" —
  Home, Browse (All/Singles/Series), and Folder View/flat custom tabs all
  render inside the same single `<main class="container">`, so one shared
  background layer there covers every listed surface with no per-page
  duplication.
- **Built:** `frontend/index.html` — new `#pageBg`/`#pageBgImg` markup,
  first child of `<main class="page-main">`. `frontend/css/style.css` —
  `.page-bg-img` fills the container (matches `.series-backdrop`'s
  image/blur recipe) with a `radial-gradient(circle at top right, …)`
  mask so it's visually anchored to the top-right corner and fades fully
  transparent by ~70% of the radius; 0.4 opacity, 28px blur (both
  calibrated judgment calls — "50% blur"/"40% transparency" aren't literal
  CSS units, picked what read well against real covers, same as the hover-
  effect task's border opacity call). `frontend/js/app.js` — new
  `setPageBackground(pool)` picks one random `cover_path` from whatever
  pool is passed in and shows/hides `#pageBg`; wired into three call
  sites so the pool is always scoped to what that surface actually shows:
  `renderBrowse()` (`getFilteredLibrary()` — covers Home's "All" redirect,
  Browse, and flat custom tabs), `loadHome()` (union of all loaded strip
  items), `renderFolderView()` (`[...folders, ...files]` for the current
  directory only). Picked once per surface-entry, not on every filter/
  pagination re-render, so it doesn't flicker while browsing within a
  surface.
- **Verified live** against the running dev server (`localhost:9424`,
  read-only): confirmed via `getBoundingClientRect()`/computed-style
  inspection that the element renders with the right opacity/blur/mask
  values and a real `cover_path`-derived `src`; visually confirmed the
  top-right glow on the "All" surface (clearly visible while loading,
  subtler once the grid fills the space — expected, matches the existing
  backdrop pattern's "wash, not a dominant graphic" intent). Confirmed
  scoping on the 2000 AD Folder View tab (`tab-3`) at both the year-folder
  level and inside a year (file level) — background pool is built directly
  from that fetch's own `folders`/`files` arrays, so it's scoped by
  construction, not by a filter that could leak. Checked light theme (no
  visual breakage, reverted the theme override after testing). No console
  errors on any surface.
- **Docs:** `SPEC.md` §20.19 added.

## Session — 2026-07-13 (same day, follow-up) — Random cover background: full-width + reduce blue cast

- Tez flagged two problems from a real screenshot (wide viewport): (1) the
  background was clipped to the centered 1440px `.container` column,
  leaving plain flat gutters on either side on any screen wider than that
  — should cover the full content area instead; (2) the wash read too
  blue.
- **Full-width fix:** `.page-bg` changed from `position: absolute` (sized
  to `.page-main`'s box) to `position: fixed`, pinned to the actual
  viewport — `top: var(--header-h)`, `left: var(--sidebar-w)` (with a
  `body.sidebar-collapsed` override matching the sidebar's own 60px
  collapsed width), `right: 0`, `bottom: 0`. This also means it no longer
  scales with page height the way the old absolute-inside-`.page-main`
  version did (relevant for Home, which can get tall with many strips).
  Needed `#homeView`/`#browseView`/`#folderView`/`.menu-bar` all elevated
  to `position: relative; z-index: 1` (menu-bar didn't need this before —
  it never spatially overlapped the old container-scoped bg — but does
  now that the bg spans the full content area including the menu-bar row).
- **Blue-cast fix:** added `saturate(0.6) sepia(0.15)` to `.page-bg-img`'s
  filter, muting any strong colour cast (many covers skew cool/blue) into
  a more neutral warm-grey wash rather than trying to hand-tune per-image.
  Another judgment call on ambiguous units, same as the original 40%/50%
  figures — ready to adjust if it reads wrong.
- **Verified live:** resized the browser to 1920px wide, confirmed the
  glow now extends to the real right edge of the viewport (not stopping
  at the old ~1440px column boundary) and reads a muted warm-grey instead
  of blue. Confirmed the sidebar (both expanded and collapsed states) and
  header stay completely clean — no bleed-through — and that the menu
  bar's filter dropdowns/count still render crisply above the now-full-
  span background. No console errors.

## Session — 2026-07-13 — Mobile UI Redesign built (v2.6 Item 4)

Built the Flutter-side counterpart to Item 1 — full rail-based scaffold
redesign of the tablet app, per `design_handoff_tablet_app/README.md`
(options 2a portrait / 2b landscape). Split out from Item 1 as its own item
on 2026-07-05 (`ROADMAP.md`); this is that item, built and closed.

- Read the design handoff (README, `Flutter App Redesign.dc.html` sections
  2a/2b, `tokens/*.css`, `data.js`) plus the existing Flutter app
  (`lib/screens/library_screen.dart`, `series_screen.dart`,
  `services/api_service.dart`, models) and the relevant backend routes
  (`backend/routers/library.py`, `home.py`, `progress.py`) before planning —
  confirmed every piece of data the design needed already existed
  server-side (`/api/nav/config`, `/api/home/strips`,
  `/api/library?tab_id=/field=/value=/q=`, the bulk favourite/rate
  endpoints) so this item needed **zero backend changes**.
- Asked Tez how to source the design's "Hanken Grotesk everywhere" font
  requirement, given the app has real offline-reading functionality
  (unlike the web app, which already made this same call for Item 1's
  Phase A) — confirmed `google_fonts` package over a bundled-asset or
  system-default fallback. See `DECISIONS.md`.
- Entered plan mode given the scope (new theme system, 4 new screens, 8 new
  widgets, model/API extensions, 2 file deletions) — plan approved before
  any code was written.
- **Built:** `lib/theme/tokens.dart` (`AppColors`/`AppSpacing`/`AppText`/
  `buildAppTheme()`, dark-only); `lib/models/custom_tab.dart`; extended
  `Series` (`readCount`, `readingCount`, `favorites`, `personalRating`,
  `pageCount`, `writers`, plus `readState`/`progressPercent` getters
  mirroring `frontend/js/app.js`'s `seriesReadState()` exactly) and `Issue`
  (`favorites`, `personalRating`); extended `ApiService` (`getNavConfig()`,
  `getHomeStrips()`, `toggleFavorite()`, `setRating()`, `getLibrary()`
  threaded with `tabId`/`field`/`value`/`q`). New screens:
  `shell_screen.dart` (root — persistent rail + nested `Navigator` for
  Home/Browse/Series/Issue, replaces `LibraryScreen` at route `/`),
  `home_screen.dart`, `browse_screen.dart`, `series_detail_screen.dart`,
  `issue_detail_screen.dart`. New widgets: `nav_rail.dart`, `app_top_bar.dart`,
  `cover_card.dart` (grid + list variants), `status_button.dart`,
  `blurred_backdrop.dart`, `comic_search_delegate.dart` and
  `offline_library_view.dart` (both extracted from the old
  `library_screen.dart` verbatim, reused unchanged). Deleted
  `library_screen.dart`/`series_screen.dart` — fully superseded. Read-state
  filters (Unread/Reading/Read) and card taps (single → Issue Detail
  direct, series → Series Detail) mirror the web app's existing logic
  rather than inventing new rules.
- **Copied logo assets** (`lockup-light.png`) from `frontend/images/` into
  `flutter_app/assets/logo/` (the real asset set already existed there from
  Item 1's brand-rename work — the design handoff bundle only shipped one
  of the three files).
- **Verified via real on-device testing**, not just `flutter analyze` —
  built a debug APK, installed and drove it via `adb` on Tez's actual
  Lenovo tablet against the real library/server (the same device
  `BUG-019`/`BUG-020` were originally found and fixed on). This surfaced
  three real bugs `flutter analyze` and a simulator wouldn't have caught:
  1. Cover cards overflowed their allotted height on Home strips and
     Browse grid — the sizing math (strip row height, grid
     `childAspectRatio`) was short for a 2-line title + meta. Fixed by
     recomputing both against the actual cover-image-height + text-block
     math instead of a guessed constant.
  2. Series Detail eagerly built every issue row into one `Column` inside
     a `SingleChildScrollView` — fine for a small series, but 2000 AD
     (2,483 issues) froze on an empty spinner for ~8 seconds before
     anything painted. Switched header + issue list to a `CustomScrollView`
     with the issues in a lazy `SliverList.separated` — the header now
     renders instantly regardless of series size.
  3. The nastiest one: `_IssueRow`'s card decoration combined a
     non-uniform `Border` (a status-coloured 3px left edge — green/blue/
     grey depending on read state — against a plain grey elsewhere) with a
     `borderRadius`. Flutter's `BoxDecoration` silently refuses to paint
     that combination — no red error banner, nothing in `adb logcat`
     unless a live Dart console is attached via `flutter run` (the
     `FlutterError` only surfaces there, as "A borderRadius can only be
     given on borders with uniform colors"). The practical symptom: every
     issue row in every series rendered as a blank grey box, no text, no
     cover — reproduced identically whether reached via a small or a huge
     series, so it wasn't a lazy-loading artifact. Found by attaching
     `flutter run` directly to the tablet instead of `flutter build apk` +
     `adb install`, which is what actually surfaced the exception text.
     Fixed by layering the coloured left edge as a separate `Positioned`
     strip inside a `ClipRRect`/`Stack`, rather than folding it into the
     card's own border.
  - Also confirmed working end-to-end on the real device: grid↔list
    toggle: Browse "All" (2,080 titles) in both views, no overflow;
    Series→Issue drill-in and back-stack unwind; mark-as-read/favourite/
    5-star-rating on Issue Detail, all optimistic-then-persisted (verified
    by navigating back to Browse and seeing the same issue's favourite
    ring/read-state reflected from a fresh `/api/library` fetch, not just
    the optimistic local state); Unread/Reading/Read filters (2,066/…/…
    of 2,080, matching the client-side filter mirrored from `app.js`);
    portrait↔landscape rotation — rail correctly defaults
    collapsed/expanded and shows Tez's real custom libraries (2000 AD,
    Favourites, All the A's) as text when expanded.
- **Two follow-up fixes from Tez's own manual pass, same day:** (1) Browse
  had lost the header (logo/search/settings) — the design prototype's HTML
  shows this exact same header block on both its Home and Browse sections,
  and `browse_screen.dart` simply never got it built in; extracted the
  block from `home_screen.dart` into a shared `lib/widgets/app_top_bar.dart`
  used by both screens now. (2) The nav rail rendered vertically centered
  in the middle of the screen instead of pinned to the top —
  `shell_screen.dart`'s `Row(children: [NavRail(...), Expanded(...)])` had
  no `crossAxisAlignment` (defaults to `center`), and the rail's own height
  is just its content's intrinsic height, so it floated in the middle of
  the full-height `Row`. Fixed with `crossAxisAlignment:
  CrossAxisAlignment.stretch`. Both re-verified on the real tablet after
  rebuilding.
- **Tez confirmed the full manual pass on the real tablet** — this is the
  close-of-session gate (`CLAUDE.md` Section 4). Asked to update docs and
  push.
- **Fourth bug, found during doc-writing, after Tez's confirmation —
  nothing reached the Reader.** A final code review pass before writing
  these docs (checking every screen for a `/reader` route) found that
  Home, Browse, and Series Detail all route a tap through to Issue Detail,
  and Issue Detail itself had no button, cover-tap, or any other path to
  actually open a comic — a genuine dead end, since the design mockup's
  Issue Detail button list (Mark as Read/Add to Favourites/rating stars)
  never included a read-entry-point, and the old direct issue→reader tap
  from `library_screen.dart`/`series_screen.dart` was removed along with
  those files. Fixed by adding a `_PrimaryButton` ("Start Reading" /
  "Continue Reading" / "Read Again", label keyed off `readStatus`) plus a
  tap on the cover image itself, both pushing `/reader` on the *root*
  navigator (not the shell's nested one) with the issue's own id — same
  pattern the search delegate and offline-view already use to reach the
  fullscreen, no-rail reader route. First attempt used a `▶`/`↻` glyph
  prefix on the button label; Android renders `▶` as a coloured emoji
  glyph (not the plain monochrome triangle intended), visually
  inconsistent with the plain-text `Mark as Read`/`★ Add to Favourites`
  buttons beside it — dropped the glyphs, plain text only. Also gave the
  button its own `_PrimaryButton` (accent-blue fill) rather than reusing
  `_SecondaryButton`, since it's the page's actual main action, not a
  toggle alongside Mark as Read/Add to Favourites. Verified on-device:
  tapped through to a series issue (w0rldtr33 #17), "Start Reading"
  rendered as a clean solid accent button, tapped it, the Reader opened
  and rendered page 1 correctly. **Tez subsequently confirmed both Start
  Reading and Continue Reading work correctly** (2026-07-13, next
  session).
- **Scope decisions** (full rationale in `DECISIONS.md`): Home strip cards
  don't show the favourite ring/unread badge (issue-level `/api/home/strips`
  data lacks those fields — only `/api/library`'s series-level cards have
  them); a single tapped anywhere goes straight to Issue Detail rather than
  a "series of one" page; the old manual "sync now" button/snackbar is
  dropped (not in the new design, background sync still runs
  automatically); house/grid/book/layers icons use Material
  `Icons.*_outlined` rather than adding the `lucide_icons` package; light
  theme isn't built this pass (dark-first, matching Item 1's own approach).
- Cleaned up all scratch screenshots/APKs from `flutter_app/build/` after
  verification — nothing left behind, and `build/` is gitignored regardless.

## Session — 2026-07-13 (same day, follow-up) — Browse title counts didn't match the web

Tez reported a real discrepancy after the above: mobile Browse "All" showed
2,080 titles against the web's 5,427 for the same library; "Singles" showed
1,870 against the web's 1,862.

- **Root-caused against the live server directly** rather than guessed at —
  fetched `/api/library`, `/api/library?group=Singles`, and
  `/api/library?group=Series` from the running dev server
  (`localhost:9424`) and diffed them in a scratch Python script. Two
  distinct, unrelated causes, both real:
  1. **Count semantics.** `frontend/js/app.js`'s `_renderBrowsePage()`
     (`isFlatSurface()`) shows the *grand total of individual comics* —
     `filtered.reduce((sum, s) => sum + (s.issue_count || 1), 0)` — for
     All, a custom library, and the read-state shortcuts (all of which
     operate on the same "All" pool), but a plain *card count*
     (`filtered.length`) for Series/Singles. `SPEC.md` §20.1/§20.3 already
     documented this distinction for the web; `browse_screen.dart` just
     hadn't implemented it, using `_items.length` uniformly everywhere.
  2. **Singles/Series fragmentation, the more interesting bug.**
     `browse_screen.dart` was filtering via the backend's
     `GET /api/library?group=` query param
     (`backend/routers/library.py::get_library`), which filters at the
     *individual issue* level (`query.filter(Issue.format_group == group)`)
     **before** grouping issues into series-name cards. Found 8 real series
     where this matters — e.g. "Nowhere Men" (12 issues, `format_group`
     `Series` for the series as a whole) has exactly one issue individually
     tagged `format_group=Singles` (a special/annual sharing the series
     name). `group=Singles` picks up just that one stray issue and builds a
     *phantom extra 1-issue "Singles" card* for it, on top of the real
     12-issue "Series" card the same series already has — the "Singles"
     browse tab was showing genuine multi-issue series as if they were also
     separate one-shots. The web app never hits this because it fetches the
     full ungrouped library exactly once (`allLibrary`, no `group` param)
     and filters *client-side* by each series-group's own single
     representative `format_group` (the cover issue's, chosen by lowest
     issue number) — a mixed-tag series always resolves to exactly one
     card that way, whichever format its cover issue happens to carry.
     Confirmed the other direction has no gap (nothing in `group=Singles`
     is missing from the full library, and nothing in the full library's
     Singles-tagged entries is missing from `group=Singles` — the bug is
     purely extra phantom entries, not lost ones).
- **Fix:** `browse_screen.dart`'s `_load()` now fetches `getLibrary()`
  unfiltered for every kind except a custom Library tab (which stays a
  genuine server-scoped fetch — folder/favourites-scoped, not a subset of
  the "All" pool, so the backend `tab_id` param is correct and unaffected
  by this bug), then filters client-side by `s.formatGroup` for
  Series/Singles — mirroring `frontend/js/app.js`'s `getFilteredLibrary()`
  exactly instead of leaning on the backend's issue-level `group=` filter.
  Added `_isFlatCount` (mirrors `isFlatSurface()`'s exact surface list:
  All/Library/Unread/Reading/Read are flat, Series/Singles are card-count)
  and updated `_countLabel()` to sum `issueCount` when flat.
- **Verified the fix against the live server's actual data before
  rebuilding** — computed what the new logic would produce from the same
  three JSON fetches used to diagnose the bug: All = 5,427, Singles =
  1,862, Series = 218, all matching the web exactly. Rebuilt, reinstalled,
  and re-confirmed on the real tablet: "All" now reads "5,427 Titles",
  "Singles" now reads "1,862 Titles". "2000 AD Sci-Fi Special" (one of the
  8 previously-fragmented titles) no longer appears twice.
- **Tez confirmed both Start Reading and Continue Reading work correctly**
  (see the fourth-bug entry above) and the count fix.

## Session — 2026-07-13 (same day, follow-up) — App icon: favicon.png (digib00age mark)

Cosmetic change, per `CLAUDE.md`'s cosmetic/structural threshold — no
build-queue item or `DECISIONS.md` entry needed. Tez asked for the
Flutter app's launcher icon (Android + Windows) to use `favicon.png`,
same mark already used for the tray icon (`DECISIONS.md`, 2026-07-13) and
the web favicon.

- Added `flutter_launcher_icons` (dev dependency) rather than hand-editing
  each Android mipmap density + the Windows `.ico` — generates every
  required size from one source image consistently.
- `favicon.png` is 136×127 (not square) — padded to a transparent 1024×1024
  square (centering the existing artwork, no distortion) via a scratch
  Pillow script, saved as `assets/logo/app_icon.png`, the actual
  `flutter_launcher_icons` source image. Configured in `pubspec.yaml`
  (`flutter_launcher_icons:` block — Android + Windows, `min_sdk_android:
  21`, no adaptive-icon layers since the existing icon setup didn't use
  them either).
- Ran `dart run flutter_launcher_icons` — regenerated all 5
  `android/app/src/main/res/mipmap-*/ic_launcher.png` densities and
  `windows/runner/resources/app_icon.ico`.
- **Verified on-device:** rebuilt the debug APK, reinstalled, pressed Home
  and located the app's icon in the taskbar dock — cropped/zoomed the
  screenshot to confirm it's the digib00age "oo" mark (blue rounded
  square, Android's adaptive-icon mask applied automatically around it),
  not a stale cached icon.

## Session — 2026-07-14 — Filter dropdowns rendering behind cover cards (bug fix)

From `INBOX.md`: "since bg change dd menus are displayed behind the cards"
(screenshot showed the Genre/Format/Decade/Year `.fd-panel` dropdown
rendering under the cover grid instead of over it).

**Root cause:** the random library-page cover background feature
(2026-07-13) added `#homeView, #browseView, #folderView, .menu-bar {
position: relative; z-index: 1; }` to `frontend/css/style.css`. `.menu-bar`
and `#browseView` are sibling elements (both direct/indirect children of
`.app-content`) — giving them equal `z-index: 1` makes each its own
stacking context, and sibling stacking contexts of equal z-index paint in
DOM order. `#browseView` comes after `.menu-bar` in `index.html`, so it
painted fully on top regardless of the dropdown's own `z-index: 40`
(`.fd-panel`) — that z-index only ranks within `.menu-bar`'s own stacking
context, and never gets to compete with `#browseView`'s.

**Fixed:** split the rule so `.menu-bar` gets its own `z-index: 2`, higher
than the content views' `z-index: 1` — its stacking context (and the
dropdown inside it) now always paints on top regardless of DOM order.

**Verified:** live against the running dev server (`localhost:9424`) via
Claude-in-Chrome — reproduced the exact bug screenshot's page (Browse →
All, "101 Other Uses For A Condom" visible), opened the Genre dropdown,
confirmed it now renders over the cover grid correctly.

## Session — 2026-07-14 — Windows Desktop Reader built (v2.6 Item 5)

From `INBOX.md`: "rebuild desktop reader with new design" (`BUGS.md`
BUG-021, now closed — moved to `archive/bugs-fixed-archive.md`). Tez's
framing going in was that the V1 Windows reader had been "dropped" and
needed recreating from scratch; research (two parallel Explore agents, one
each on `D:\workshop\cBook_Server\flutter_app` and the current
`comicvault_v2\flutter_app`) found a narrower story — `flutter_app/` already
shares one Dart codebase across Android and Windows (the `windows/` platform
folder has been present since the V1 initial commit), it just had never
been rebuilt, tested, or polished for desktop since then; all live
development including Item 4's rail redesign was Android-tablet-only.
Confirmed with Tez to extend the existing shared codebase rather than port
from the old V1 app — same rail nav/reader/browse/home/series/issue screens
as mobile, by construction, not a second implementation to keep in sync.

Also confirmed separately: third-party/OPDS reader integration (the
"external readers" Tez recalled being explored and dropped) was a distinct,
already-closed decision (`DECISIONS.md`, 2026-07-04) — unrelated to this
task, not competing with it.

**Scope decisions confirmed with Tez before building** (see plan file):
server-mode only on Windows (no Windows-native local-file picker — desktop
is expected to be on the same LAN as the server); `comicvault://` URI-scheme
registry registration deferred entirely to a future web
`/issue/{id}` → "open in reader" integration task; verification via
`flutter run -d windows` only, no installer/`flutter build windows` release.

**Built:**
- `local_cbz_service.dart`: `pickFile()`/`resolveSharedUri()` no-op on
  non-Android platforms instead of invoking the Android-only
  `MethodChannel('comicvault/local_file_picker')`, which has no Windows-side
  implementation and would otherwise throw.
- `offline_library_view.dart`: hid the "Open local CBZ file" button and
  "Recent files" list on Windows (gated on `Platform.isAndroid`) — the
  server-unreachable retry banner and the "Downloaded" section (reads via
  `DownloadService`, not the picker) are unaffected.
- `comic_page_view.dart`: `nextPage()`/`prevPage()` in both
  `ComicPageViewState` and `LocalComicPageViewState` were no-ops in Scroll
  mode (the `PageController` they drove was never attached to the
  `ListView` in that mode) — fixed to animate the scroll position by one
  viewport instead, needed so keyboard paging (below) means something in
  Scroll mode too. `LocalComicPageViewState` had no `ScrollController` at
  all before this; added one, matching `ComicPageViewState`'s existing one.
- `toolbar_overlay.dart` / `reader_screen.dart`: added keyboard support —
  Left/Up = prev, Right/Down = next, Escape = back — via a `Focus` wrapping
  the existing tap-zone `Stack`. Purely additive: existing tap/mouse
  behaviour untouched.
- `windows/runner/main.cpp` (window title) and `Runner.rc`
  (`FileDescription`/`ProductName`): rebranded from the stock "comicvault"
  to "digib00age", matching the brand used elsewhere. Confirmed live via
  `Get-Process | Select MainWindowTitle` → "digib00age". The Windows
  launcher icon was already current (`app_icon.ico` regenerated 17:07,
  after the 17:05 logo update — see the App icon session above) — no change
  needed.
- Confirmed the Android-only immersive-mode `SystemChrome` call in
  `reader_screen.dart` is a harmless no-op on Windows (two clean
  rebuild/launch cycles, no exceptions).
- Reviewed `CoverCard`, `BrowseScreen`'s grid delegate
  (`SliverGridDelegateWithMaxCrossAxisExtent`, width-adaptive column count),
  and `ShellScreen`'s `Row`/`Expanded` rail+content layout for desktop
  reflow — all adaptive by construction, no fixed-width assumptions found.

**Verified:** `flutter analyze` clean throughout. Baseline `flutter run -d
windows` on the unmodified app confirmed a clean launch with no startup
exceptions; two further rebuild/launch cycles after the code changes and
after the native (`main.cpp`/`Runner.rc`) changes were equally clean.
Tez manually ran `flutter run -d windows` and confirmed navigation (rail →
Home/Browse/Series/custom libraries) and reading (both Scroll and Page
mode) work.

**Note on process:** an early attempt to screenshot the running desktop
window via a hand-rolled PowerShell/Win32 script went wrong twice — once
capturing an unrelated window on Tez's screen (a stale window handle/rect),
once failing on a `GetWindowTextW` marshaling bug. Both screenshots were
deleted immediately without being examined further; no further automated
desktop-screenshot attempts were made. Visual/reflow confirmation was left
to Tez's manual pass instead, which is where this repo's verification
standard (`CLAUDE.md` §6) puts it anyway.

## Session — 2026-07-14 (same day, follow-up) — Open Issue Detail cover in the Windows desktop reader (v2.6 Item 6)

From `INBOX.md`: "open reader from web library — open the selected
issue/id from the web library in the desktop reader" — the natural next
step right after Item 5 made the Windows reader actually work. Closes out
`ROADMAP.md`'s long-parked "Reader-launch feature" entry.

Researched via an Explore agent reading the `app_links-6.4.1` package
source directly (not just its docs) before planning anything: the Flutter
app's own `comicvault://read/{id}` deep-link parsing (`main.dart`) already
worked correctly and always had — the "Read" button removed 2026-07-09
(`DECISIONS.md`) failed because nothing on Windows had ever registered a
handler for the scheme, not because the Dart-side handling was broken. Two
real gaps: (1) no Windows Registry entry for the protocol — `app_links`
ships the cold-start argv-parsing and a `WM_COPYDATA` live-forwarding
listener, but registry registration itself only exists in the package's
`example/` folder, not its public API; (2) no single-instance
forwarding — a second `comicvault://` click while the reader was already
open would spawn a second exe process, since nothing detected the existing
window or forwarded the link into it.

Two decisions confirmed with Tez before building (`AskUserQuestion`):
scope is the Issue Detail page's cover only (Browse/Series grid cards keep
their normal navigation); protocol registration is an explicit "Register
as this PC's comic reader" button in Settings, not silent/automatic on
every launch — a registry write should be a visible, deliberate action.

**Built:**
- Added `win32`/`ffi` to `flutter_app/pubspec.yaml`.
- New `flutter_app/lib/services/protocol_handler_service.dart` —
  register/unregister/read-back against
  `HKEY_CURRENT_USER\Software\Classes\comicvault`, adapted from
  `app_links`'s own example (`windows_protocol.dart`), using
  `Platform.resolvedExecutable` to self-discover the exe path rather than
  relying on Admin's inert "Reader Location" field (`ADMIN_SPEC.md` §7.6).
  Fixed a couple of API mismatches while adapting the example's pattern
  (`WIN32_ERROR.ERROR_SUCCESS` isn't a real symbol in this win32 package
  version — it's a plain top-level `ERROR_SUCCESS` int constant; `nullptr`
  needed an explicit `dart:ffi` import alongside `package:ffi/ffi.dart`) —
  caught immediately by `flutter analyze`, not left for runtime.
- New "Windows Reader" section in `flutter_app/lib/screens/
  settings_screen.dart` (Windows-only), register/unregister toggle.
- `flutter_app/windows/runner/main.cpp`: added `SendAppLinkToInstance()`
  (adapted from `app_links`'s example) — finds an existing
  `"digib00age"`-titled window before creating a new one, forwards the
  link via `SendAppLink()` (already linked via
  `generated_plugin_registrant.cc`, just needed the header include),
  restores/foregrounds it, exits without a second window. Fixed a real bug
  found in the reference example while adapting it — its
  `SetWindowPos(0, HWND_TOP, ...)` call passed a null window handle
  instead of `hwnd`.
- `frontend/js/app.js`'s `buildIssueDetail()`: wrapped `.issue-cover-img`
  in `<a href="comicvault://read/{id}">`; `frontend/css/style.css` added
  `.issue-cover-link { display: block; }` so the wrap doesn't disturb
  layout — no changes needed to the existing `:hover` effect, which
  targets the `<img>` itself.

**Verified:**
- Registry read/write logic confirmed correct via a standalone `dart run`
  script run from inside `flutter_app/` (temporary, deleted after) —
  `register()` → `isRegistered()` true → `unregister()` → `isRegistered()`
  false, confirmed against the real Windows registry
  (`reg query HKEY_CURRENT_USER\Software\Classes\comicvault` empty
  afterward — left unregistered, since that test run's own
  `Platform.resolvedExecutable` was `dart.exe`, not the real app).
- Cover-link markup confirmed live via Claude-in-Chrome's DOM inspection
  (`href="comicvault://read/1"` on Issue #1's page) and a hover screenshot
  confirming the existing zoom/white-border effect still fires through the
  new `<a>` wrap — deliberately did **not** click the link myself, since
  doing so triggers a real browser "Open ComicVault?" dialog and launches
  a native app, which is Tez's action to take, not something to automate.
- `flutter analyze` clean throughout; native rebuild/launch cycles clean,
  no exceptions.
- Tez completed the full manual loop: registered via Settings; cold-start
  (reader fully closed, clicked a cover, accepted the browser prompt,
  landed straight in that issue's reader); warm-start (reader already
  open, clicked a different issue's cover, existing window came to front
  and navigated there rather than spawning a second process); confirmed
  Browse/Series grid cover clicks are unaffected. All passed.

## Session — 2026-07-14 — Full Editor 4-column redesign (v2.6 Item 7)

- **Inbox `[change]`:** the Full Editor was redesigned in Claude Design
  (`D:\workshop\Claude Design\full editor`, `4-Column Full Editor.dc.html`
  + old/new screenshots in `images/`). Took `/editor` from its 3-column
  layout to a **4-column workspace + footer status bar**, same
  Design→Code pattern as Item 1.
- **Approach:** reproduced the export's *visual design* only, using the
  app's existing CSS token system (already a near-exact match to the
  design-system tokens) + vanilla JS. **No `x-dc` prototype runtime
  ported; every `/api/editor/full/*` endpoint reused** — a layout +
  interaction reskin, not a backend change.
- **Why a rebuild:** first built by a cloud Ultraplan session, but its
  container had no git remote and a GitHub-blocking egress policy, so it
  could never push; the patches never reached the PC and their URLs are
  auth-gated (`temp/build-not-deployed.md`). Tez chose to rebuild locally
  on the current `main` rather than chase the stranded artifacts
  (`DECISIONS.md`).
- **Scope decisions locked with Tez:** Column 1 = render the loaded
  working set as a folder→series→issue tree (keep the existing modal
  intake), not a live library browser; viewer gains Fit + Fullscreen +
  lazy thumbnail strip but **no Rotate**; one-pass build. All three in
  `DECISIONS.md`.
- **Built (4 files):** `frontend/editor_full.html` (4-col grid + footer,
  Search moved to header, all 4 modals + scripts preserved, all 16
  apply-to-all `data-field`s intact); `frontend/js/editor_full.js`
  (`renderFileTree`/`buildFileTree`/`naturalCompare`, genre chips, queue
  cards, viewer `fitViewer`/`toggleFullscreen` + lazy `renderThumbStrip`,
  `updateStatusBar`); `frontend/css/style.css` (4-col layout + footer,
  `--control-md`, tree/chips/apply-column/viewer/thumb/queue/status-bar
  styles); `backend/routers/editor_full.py` (additive `?w=` thumbnail
  downscale on the page endpoint). `EDITOR_SPEC.md` §5.4 added (supersedes
  §5.2 layout).
- **Data-path parity confirmed:** all 16 `Apply to All` `data-field`s
  present and unique → Process All unchanged; genre chips read/write the
  same comma-joined `Genre` value the checkbox grid did; every JS
  `getElementById` cross-checks to an HTML id; Python parses.
- **Verified live** (Claude-in-Chrome against Tez's running tray server,
  read-only): loaded *Before the Incal* + *Benjamin* from
  `L:\Comic Archives\B\Series` — tree grouped folder→series→issue with
  count/XML badges + correct stats (9/9/0) + natural sort; issue-click
  loaded editor + viewer; genre chips seeded from XML and add/remove
  (removed genre returns to the dropdown); footer read the selected file +
  "Valid ✓"; viewer showed the real cover (page 1/51) with a working lazy
  thumbnail strip; queue card + "counts differ" + Queued=1. Console clean;
  no archive files written; working set + queue cleared afterward.
- **Post-build tweaks (Tez, cosmetic):** density pass so the Main tab fits
  without scrolling (input height 34→30px, tighter row/label gaps, form
  padding, textarea min-height); then three fixes — genre rendered as a
  single bordered control (removed the inner double-border via
  `select.fe-genre-add` specificity), Summary's apply checkbox centred on
  the textarea, and `Increment #`'s label moved in front of its checkbox
  with the checkbox aligned in the apply column.
- **Manual test:** Tez ran a single file end-to-end through to adding it to
  the library (core write path). Series/multi-file path + the tightened
  layout left as Tez's own follow-up hand-test.
- **Deploy gotcha noted in specs:** static assets have no `cache-control`,
  so `/editor` needs Ctrl+F5 after a deploy to pick up new HTML/CSS/JS (hit
  this repeatedly during verification — a normal refresh served the stale
  old editor). The `?w=` param needs a tray-server restart; the strip works
  without it (full-size images, heavier). Flagged asset-versioning as a
  possible small follow-up.
- Committed on branch `full-editor-4col-redesign` and pushed to origin.

## Session — 2026-07-15 — Site-wide layout width, multi-cover background, scrollbars

Three `INBOX.md` cosmetic `[change]` items, worked through together in one
session since each touched the same shared, non-version-scoped surface
(`style.css`'s global rules) — see `CLAUDE.md` §5's cosmetic/structural
threshold, all three qualify as cosmetic (visual only, no nav/IA change).

- **Full-width header + content, site-wide.** `.container` (`style.css`) was
  capped at `max-width: 1440px; margin: 0 auto`, boxing the header
  (logo/search/settings) and every page's main content into a centred column
  with dead space beyond it on wide viewports — root cause of two separate
  inbox lines at once ("stretch/span header to full width" and "remove/adjust
  container holding cards… fill the width available"), since both trace back
  to the same `.container` rule. Dropped the cap entirely; `.container`
  now sets only the L/R gutter + 5px top. `.site-header .inner` (which also
  used `.container`) gets its own `padding: 0 <gutter>` override since the
  header is a fixed-height, vertically-centred bar, not a top-padded content
  block. **Gutter iterated live with Tez:** first cut used 10px L/R (matching
  his stated spec), tried live, then widened to **30px L/R** per his
  follow-up ("that's better") — mobile (`@media max-width:640px`) kept
  separately at 10px so small screens don't lose 60px to margins. Verified:
  `.container` is used in exactly three places (header inner, menu-bar inner,
  main content wrapper) — no modal/popup uses it, so the change is safe
  site-wide. `guide.html`'s narrow prose column is unaffected — it pins its
  own inline `max-width: 720px` on `<main>`, only its *header* went
  full-width. Verified live across Home/All/Series/Issue/Admin/XML Editor,
  Ctrl+F5, both themes.
- **Multi-cover "cloud field" page background** — rebuilds the 2026-07-13
  random-cover background (`SPEC.md` §20.19). Tez likes the effect
  ("colourful blurred clouds… gives the site an alien feel") but the single
  top-right-corner radial mask "doesn't cover enough" (`INBOX.md`, also the
  open "fade from across the top not just the corner" line — superseded by
  this, full coverage being a superset of that ask). Discussed whether a
  code-generated gradient would be lighter on memory instead of real cover
  art — confirmed it isn't a real factor (the background already reuses the
  same cached 300px `/api/cover/{id}` thumbnail the card grid fetches, no
  extra load either way) — see `DECISIONS.md`. Chosen direction: keep real
  cover art, composite several at once. `setPageBackground()` (`app.js`) now
  picks up to 4 *distinct* random covers from the active surface's pool
  (never padded with repeats on a small surface) and renders each as a
  `.page-bg-blob` `<img>` — soft circular mask (radial-gradient, transparent
  past 68%) so it reads as a cloud not a rectangle, positioned via inline
  `--x`/`--y`/`--s` custom props seeded from one of four shuffled quadrant
  anchors + random jitter/scale, so coverage spreads across the whole area by
  construction rather than clustering. Two new `:root` tokens for live tuning
  — `--pagebg-blur` (30px) and `--pagebg-blob-opacity` (0.32) — dropped the
  old `saturate(0.6) sepia(0.15)` grey-mute in favour of `saturate(0.9)` so
  real colour comes through. `#pageBg` itself and its fixed
  content-area-pinned positioning (sidebar-width tracking etc.) are
  untouched — only its contents changed from one `<img>` to N. Verified live:
  full coverage on Home/Browse/Folder View, re-randomises per surface entry,
  a single-publisher tab still only shows its own covers, small surfaces
  degrade gracefully, no console errors, "loads quick" (Tez) — same cached
  thumbnails, no new endpoint.
- **Site-wide scrollbars, matching the filter-dropdown look, including the
  XML Editor.** `INBOX.md`: "apply site wide style change to scroll bars -
  match the filter scrolls." The filter-dropdown panel (`.fd-panel`) already
  had a custom scrollbar treatment (`scrollbar-width: thin`, 8px WebKit bar,
  transparent track, `--surface-3` thumb → `--text-3` on hover) that nothing
  else on the site matched. Promoted it to a global rule (bare
  `::-webkit-scrollbar*` + `:root`'s `scrollbar-width`/`scrollbar-color`, both
  inheritable/global by construction) placed right after the base resets, so
  it reaches every scroll container in one page — main library, Admin, and
  the XML Editor (`editor_full.html`, which links `style.css` — confirmed).
  The Basic Editor modal (`editor_basic.html`) is a fragment injected into
  pages that already link `style.css`, so it inherits it too, no separate
  link needed. More-specific existing rules (the 4px `.continue-strip` home
  strip bar, the hidden strip-track scrollbar) stay more specific and were
  unaffected — confirmed by CSS specificity, not just assumption.
  - **Regression found and fixed same session, reported by Tez:** the XML
    Editor's Genre "Add genre" dropdown (`select.fe-genre-add`) started
    rendering its open popup light/washed-out while Format and Age Rating
    (plain `.fe-field select`s) stayed correctly dark. Root cause: once a
    page defines custom `::-webkit-scrollbar` rules, Chromium renders any
    native `<select>` popup that's long enough to need a scrollbar in **CSS
    mode** instead of native OS-chrome mode — and CSS-mode popups paint using
    the select's own `background-color`. Genre's list is long/scrollable
    (forced into CSS mode) and had `background: transparent` (deliberate, so
    the closed control reads seamless inside its `.fe-genre-wrap` box, no
    inner rectangle) — transparent-on-CSS-mode painted light. Format/Age
    Rating have short, non-scrolling lists, so they stayed in native mode
    and were never affected. Fix: `select.fe-genre-add`'s background changed
    from `transparent` to `var(--surface-2)` — same colour as the wrap it
    sits in, so the closed look stays seamless while the open popup now gets
    a real dark background like the other two. Verified live: Genre popup now
    matches Format/Age Rating; closed control still shows no visible inner
    box.

## Session — 2026-07-15 — Legacy credit-column cleanup + roadmap triage

Executed `ROADMAP.md`'s deferred "Drop the old raw CSV credit columns on
`Issue`" item, then closed out the roadmap's `Later` lane triage that
followed from it.

- **Investigated before touching anything, found the docs were wrong.**
  `ROADMAP.md`/`SPEC.md` described all 6 columns (`writer`/`penciller`/
  `inker`/`colorist`/`letterer`/`cover_artist`) as "written by the scanner
  but no longer read" — safe to drop outright. Traced every usage in
  `backend/` and `frontend/js/app.js` and found that's only true for 4 of
  the 6. `writer`/`penciller` are still genuinely read server-side, powering
  three live things: the library search box (`path_utils.matches_search()`),
  "Group by Writer" (confirmed still present in `#groupBySelect`), and the
  series-card meta line (`library.py`'s per-series `writers`/`artists`
  aggregate). Only `_issue_to_dict()`'s dead JSON serialization and the
  already-migrated Issue Detail credit links matched the "no longer read"
  claim.
- **Talked through the finding with Tez** — the full fix (migrate those 3
  live consumers onto `people`/`issue_credits`, then drop all 6) is real,
  working-code territory he couldn't easily verify himself. His call: only
  remove what's genuinely dead, leave anything live completely untouched.
  `writer`/`penciller` folded into his own already-queued `INBOX.md`
  "scan code base - clean, removal of dead code" item as the right home for
  that follow-up, rather than deciding it in a rush here.
- **Built (reduced scope — 4 columns only):** `backend/scanner.py` — removed
  the 4 dead write assignments, `writer`/`penciller` untouched.
  `backend/routers/library.py` — removed the 4 dead keys from
  `_issue_to_dict()`'s JSON response. `backend/models.py` — removed the 4
  dead `Column` defs from `Issue`. `backend/database.py` — new
  `_drop_legacy_credit_columns()`, an idempotent `DROP COLUMN` migration
  (mirrors `_add_missing_issue_columns()`'s guarded-`ALTER TABLE` pattern),
  wired into `init_db()`.
- **Verified against scratch copies of the real DB only** (per `CLAUDE.md`
  §6 — real DB never touched): confirmed SQLite 3.49.1 (well above the 3.35
  minimum for `DROP COLUMN`); ran the actual shipped
  `_drop_legacy_credit_columns()` function (not a re-implementation) against
  a scratch copy — exactly the 4 target columns dropped, `writer`/
  `penciller` byte-identical before/after, idempotent on a second call;
  confirmed the `Issue` ORM class and the real `_issue_to_dict()` function
  both work cleanly against the migrated schema (no `AttributeError`, no
  dead keys in the response); grepped the whole backend/frontend for any
  other reference to the 4 dropped fields — none found, aside from
  `scanner.py`'s XML-parsing `meta` dict still reading the tags into local
  variables that are simply never persisted now (harmless, dict keys not
  attribute access, flagged as minor residue for the future cleanup
  session rather than touched here). Confirmed the real DB file was
  untouched throughout, before and after.
- **Tez manually tested the real app** after a restart — library loads,
  search, Group by Writer, and the series-card writer/artist display all
  confirmed working.
- **Roadmap triage, same session:** Tez confirmed the other two `Later`-lane
  items were separately ruled out — Advanced Search page (existing inline
  filter+search already cover the need) and multiple scan locations across
  drives + the bundled series-level overview field idea (single-location
  app/workflow, judged not worth the complexity; per-issue descriptions
  already cover the overview-field need). With all three `Later` items now
  resolved, removed the `Later` lane from `docs/meta/roadmap.html` entirely
  (3-column grid: Now/Next/Launch) — see `ROADMAP.md`'s "Resolved" section
  and `DECISIONS.md` for full rationale on each.
- **Found and fixed a doc bug while appending this entry:** the previous
  session's append (2026-07-15, "Site-wide layout width, multi-cover
  background, scrollbars") had accidentally displaced a pre-existing
  "Committed on branch `full-editor-4col-redesign` and pushed to origin."
  line — it belonged to the earlier Full Editor Item 7 session but had been
  pushed down to the end of the file by that edit's insertion point,
  making it misleadingly read as if it described the layout/background/
  scrollbar session (which was committed to `main`, not that branch, and
  explicitly not pushed per Tez's instruction). Moved back to its correct
  position.

## Session — 2026-07-15 (same day, follow-up) — Basic Editor popup-open perf fix

Tez asked whether anything could be done about the delay between clicking
"Edit XML" on `/issue/{id}` and the Basic Editor popup opening.

- **Traced the full click-to-open path** (frontend `editor_basic.js` +
  backend `editor_basic.py`/`archive_io.py`) and found `GET
  /api/editor/{issue_id}` opened the same archive file **3 separate times**
  per request — `find_xml_in_archive()`, `extract_xml_from_archive()`, and a
  separate `get_archive_page_count()` call, each independently re-parsing the
  ZIP central directory. Same redundant-reopen anti-pattern as
  `PERFORMANCE.md` findings #4/#5 (`reader.py`) and #6 (`editor_full.py`),
  just never applied to the Basic Editor's `archive_io.py` path.
- **Measured before fixing** (in-process, `PERFORMANCE.md` §2 methodology):
  the dominant cost is actually the *first* cold disk touch on a
  rarely-opened archive (211-313ms observed) — inherent USB HDD seek
  latency, not fixable in code, consistent with existing findings #8/#9. The
  redundant 2nd/3rd opens were already cheap once the OS file cache warmed
  from the first open, so the fix's guaranteed win is smaller than initially
  expected: ~1ms on a typical single issue, ~9-10ms on a large compendium
  (954MB, 1024 pages: 14.2-15.0ms for 3 opens → 5.2-5.9ms for 1).
- **Built:** `backend/editor/archive_io.py` — new
  `read_xml_and_page_count()`, one archive open instead of three.
  `backend/routers/editor_basic.py` — both the `GET` (popup load) and `POST`
  (save) handlers now use it via `_read_original_xml()`. `frontend/js/
  editor_basic.js` — `populateStaticSelects()`'s one-time-per-page-load
  `GET /api/editor/formats` + `GET /api/editor/genres` fetches now run
  concurrently (`Promise.all`) instead of sequentially.
- **Verified:** in-process timing before/after (above); a scratch-copy
  save-path round-trip (never the real file) confirmed the refactored read
  path doesn't change save behaviour; confirmed the real library file used
  for comparison was untouched throughout. **Tez manually tested live**
  after a server restart: popup opens and saves correctly, no console
  errors, and confirmed the diagnosis matches the felt experience — the
  first archive opened in a session has a noticeable lag (audible drive
  spin-up), subsequent archives open the editor immediately.
- Full before/after numbers and root-cause writeup added to
  `docs/PERFORMANCE.md` as a new finding (#11) with its own re-baseline
  entry, rather than duplicating the detail here.

## Session — 2026-07-15 (same day, follow-up) — Review Queue: flag issues + batch-send to Full Editor (v2.6 Item 8)

Ad-hoc feature request: various issues scattered across different series/
folders turn out to have incorrect metadata; fixing them meant manually
re-locating each one through the Full Editor's file picker. Wanted a way to
flag issues wherever noticed, then batch-pull them into the editor.

- **Investigated first** — confirmed `NeedsReview` (`EDITOR_SPEC.md` §9) is
  an unrelated flag (ComicTagger low-confidence, XML-only, Full-Editor-only
  visual, never persisted/queryable). No existing "flag for later batch
  action" mechanism. Closest precedent: `Issue.favorites` — a boolean DB
  column + bulk multi-select toolbar action + menu-bar filter toggle. This
  feature mirrors that pattern closely.
- **Confirmed with Tez before building:** flag auto-clears on save in either
  editor (matches `NeedsReview`'s existing behaviour); viewing flagged
  issues is a filter toggle within the current view, not a dedicated nav
  tab (avoids spending one of the 4 visible-tab slots `CUSTOM_TABS_SPEC.md`
  caps); a single-issue toggle belongs on `/issue/{id}` too, not just bulk
  multi-select; and — the one real architectural fork — saving a
  review-queue issue inside the Full Editor should trigger the same DB
  rescan the Basic Editor already does, a scoped, confirmed exception to
  Full Editor's deliberate "never touches the DB" rule (`EDITOR_SPEC.md`
  §5), since it's now handling already-catalogued files too. Files with no
  matching `Issue` row (the original pre-library use case) stay completely
  untouched.
- **Built:** new `Issue.flagged_for_review` column (mirrors `favorites`,
  guarded `ALTER TABLE` migration); single-issue + bulk flag/unflag
  endpoints (`backend/routers/progress.py`, mirroring the existing
  mark-read/favorite patterns); `flagged_for_review` added everywhere
  `favorites` is already serialized in `library.py` (no new query
  architecture — filtering is client-side, same as Favourites); new
  `POST /editor/full/files/add-by-issues` (resolves `Issue.id` →
  `file_path`, reuses `add_files()`'s validation via a new shared
  `_add_path_to_working_set()` helper); the confirmed DB-sync exception in
  `process_batch()`; the Basic Editor's save path clearing the flag
  synchronously; and the full frontend surface — Issue Detail toggle button
  (mirrors `buildStatusToggle`'s single-issue-endpoint style), a bulk
  toolbar button (mirrors `★ Favorite`), a "→ Send to Full Editor" bulk
  action, the `#flagReviewFilterBtn` menu-bar toggle (mirrors
  `#favFilterBtn` exactly, including Folder View parity), and card
  badge/ring styling (bottom-left corner — the one free corner among
  favourite/unread/rating/progress-bar).
- **Verified:** backend logic (flag set/clear, path resolution, both
  `process_batch` DB-sync branches) exercised in-process against scratch
  copies of the real DB and a real CBZ, never the originals — confirmed the
  matched-issue case rescans + auto-clears, and the unmatched/pre-library
  case makes zero DB writes.
- **Bug found during Tez's manual verification, fixed same session:** after
  using a Genre filter to find mismatches, sending several issues to the
  Full Editor, saving, and refreshing the library page, Tez hit "Failed to
  initialise. Cannot read properties of null (reading 'addEventListener')."
  Root cause: `bindFilterEvents()`'s new `flagReviewFilterBtn` lookup had no
  null-guard, and Tez's browser had served a stale cached `index.html` (from
  before this button existed) alongside already-fresh `app.js` — a classic
  deploy-time cache mismatch, not a logic bug (clicking "Home" in the nav,
  which forced a genuinely fresh fetch, self-resolved it). Fixed by
  null-guarding the new lookup specifically. Five pre-existing unguarded
  lookups in the same function (`favFilterBtn`, `sortSelect`, `sortDirBtn`,
  `starRatingFilter`, `groupBySelect`, `viewToggle`) have the identical
  fragility and were flagged, not fixed — out of this item's scope. Same
  underlying class of gap Item 7's own verification notes already flagged
  (static assets served with no `Cache-Control`, needing a hard-refresh
  after any frontend deploy) — not a new problem this item introduced.
- **UX addition, same session, after initial verification passed:** "Send to
  Full Editor" now opens the `/editor` tab immediately (must happen
  synchronously with the click for the popup blocker) with a "Sending files
  in the background…" toast, since resolving+adding a large selection can
  take a moment; that same tab auto-reloads once the background add
  completes, so it shows the populated working set instead of an empty one.
  Reuses `editor_basic.js`'s `.admin-toast` styling under a new
  `libraryToast` element id.
- **Tez manually verified the full loop live, twice** (once before the
  cache-bug fix, once after): filtered by Genre to find mismatches,
  multi-selected across series, sent to Full Editor, edited and saved,
  confirmed the flag cleared and the DB updated, confirmed a normal
  pre-library Full Editor session is unaffected, confirmed the Basic
  Editor's save path clears the flag too, and confirmed the toast +
  auto-refresh addition. All passed.
- Full detail in `EDITOR_SPEC.md` §13, `MENU_BAR_SPEC.md` §2.8,
  `docs/v2.6/comicvault-changes-v2.6.md` Item 8, and `DECISIONS.md`.

## Session — 2026-07-15 (same day, follow-up) — Card redesign: grid, Home Strips, Folder View (v2.6 Item 9)

Ad-hoc feature request: a new card design (`D:\workshop\Claude Design\new card
design`, `CollectorCard.dc.html` — a mockup/design-tool export, not portable
code) needed translating into the real app and fine-tuning live. Two rounds,
both driven directly against the running app with Tez rather than by
description alone.

**Round 1 — main library grid + Issue Detail cover.** Built the initial
translation (ornate bezel look from the mockup), then went through many live
fine-tune passes as Tez compared the running app against the mockup
screenshot and against his own evolving intent:
- Simplified away the mockup's multi-layer metal bezel/foil/noise-texture
  chrome entirely — "over-ambitious", too many competing borders.
- Moved the card's colour ring from wrapping just the cover image to wrapping
  the whole card (cover + info block), after a cover-only ring only showed as
  a thin line at the image/text boundary.
- The progress bar went through two real bug fixes before it worked: a
  legacy `.cover-info` gradient rule and a legacy cover-bottom "feather"
  pseudo-element were both still painting over the new dark card face/the
  new bar respectively, silently inherited from pre-redesign CSS that didn't
  have enough selector specificity to be overridden by the new rules. Also
  found that the Singles-card progress math (`read_count/issue_count`) could
  only ever show 0% or 100% — never a real mid-point — because
  `current_page` wasn't in the `/library` response at all; added it.
- Redesigned the progress bar's shape entirely, twice: first as a flush
  full-width line (matching the mockup), then — once Tez saw it working — as
  an inset floating pill with its own tinted track, since he'd been
  picturing a distinct overlay element, not a border-adjacent stripe.
- Favourite went from a stacked dual-ring (state colour + gold) back to a
  single ring that just turns gold outright — the two-ring version "looked
  off". Border colour then got removed entirely in a later rewind (below).
- Genre ribbon: added as a new element (data was already in the API, just
  unread by the frontend for Series cards), then reworked from a solid
  colour fill to off-white text (matching the sidebar nav's text colour) with
  the read-state colour narrowed down to just a 2px bottom border, after the
  solid fill visually clashed with the new white card border.
- **Border rewind:** after seeing the accumulated result at 100% card size
  against the original mockup, Tez asked to strip it back to one simple
  border — removed all read-state/favourite colour from the border, moved
  read-state colour to the genre ribbon only, favourite to the heart badge
  only. Several more rounds tuned the exact border weight/opacity/blur
  (60%→45% white, 2px→1px, blur 3px→5px) and the cover's inset "matte gap"
  from the border (10px→5px).
- Flag-for-review went from an emoji tag to a real inline SVG flag icon
  matching the sidebar nav's stroke-icon style, per Tez's specific ask; the
  legacy rule giving flagged cards a red border also got removed the same
  way favourite's did.
- Repeated caching friction throughout: static assets have no
  `Cache-Control`, so a normal reload — even in a fresh automated browser
  tab — sometimes still served stale JS/CSS. Worked around per-round via a
  cache-busted `<link>`/`<script>` swap; confirmed each fix against real
  `getComputedStyle()`/DOM inspection, not just screenshots, after one round
  where a genuine fix looked identical to the broken state in a screenshot
  purely from a stale render.
- **Tez confirmed each round live** before moving to the next; final state
  is what's documented in `SPEC.md` §20.20.

**Round 2 — extended to Home Strips + Folder View**, after Tez noticed the
new look hadn't reached the Home page and asked whether one uniform
treatment across every grid-format card was feasible. Two research passes
(backend field completeness, frontend structural comparison) found:
- Folder View's flat file cards already had every field needed
  (`genres`/`personal_rating`/`favorites`/`flagged_for_review`) — zero
  backend work, same `.cover-grid`-based sizing as the main grid.
- Home Strips were missing all four fields in `_issue_card()`
  (`backend/routers/home.py`) — added, pure serializer change, no new
  queries (the `Issue` objects were already loaded).
- Home Strip cards were flex-pinned to ~90-120px wide, meaningfully
  narrower than the main grid's cards — the redesign's fixed-size badges
  would crowd/overlap there. Asked Tez: scale the badges down, or widen the
  cards? He chose to widen (`max(var(--card-min), 160px)`), a deliberate
  Home-page layout change (fewer cards per strip before scrolling), not a
  scaled-down variant.
- Folder View's subfolder tiles (`buildFolderCard()`) and Series Detail's
  issue rows (`buildIssueRow()`) confirmed explicitly out of scope — neither
  is a single-issue portrait card structurally.
- Built both: `buildStripCard()` and `buildFolderFileCard()` gained the
  `.cover-card--redesign` class, the bottom-anchored meta-row layout, the
  new SVG flag badge, and the inset progress pill — reusing the exact same
  CSS already written for the main grid (nothing new needed there beyond
  the strip-width/grid-gap rules), confirming the modifier-class approach
  from Round 1 was the right call for exactly this reason. Home Strips also
  had a real bug: `.continue-strip` had no left/right padding, so the new
  border's box-shadow bleed was clipped at the scroll container's left
  edge — fixed with padding + a matching negative margin to keep the first
  card's visual position unchanged. Card gap bumped to 19px on the main
  grid, Folder View's grid (`#folderGrid`, needed its own rule — different
  ID from the main grid's `#coverGrid`), and Home Strips, for consistency
  across all three.
- **Verified:** Home Strips confirmed live across all strip types at the
  new width, correct spacing, border no longer clipped. Folder View's code
  changes mirror the exact same proven pattern and needed no backend work,
  and couldn't be live-verified same-session (no Custom Tabs existed in the
  environment) — **Tez confirmed live in a same-day follow-up**, re-adding
  custom folders and checking Folder View, Flat view, and the Favourites
  tab: all consistent with the rest of the redesign. Folder View's
  subfolder tiles correctly render outside the new card format, as scoped
  (they're a different kind of card entirely, not a bug).
- Full detail in `SPEC.md` §20.20, `docs/v2.6/comicvault-changes-v2.6.md`
  Item 9, and `DECISIONS.md`.

## Inbox triage paused (process change, not a build item)

- 2026-07-16: Tez asked that `INBOX.md` go back to capture-only, effective
  immediately and until he says otherwise — no session type (Chat, Cowork,
  or Code) triages it on its own initiative anymore, including Code doing
  so opportunistically mid-session. Triage resumes only when Tez explicitly
  opens a Code session for that purpose. Updated `docs/meta/working-rules.md`
  "Inbox workflow" and the `docs/INBOX.md` header to reflect the hold; logged
  in `DECISIONS.md`.

## Session — 2026-07-16 — BUG-023: stale library cover after archive edit + rescan

- Tez reported: editing a comic's cover inside its CBZ (unpack → replace page →
  repack) and rescanning didn't update the cover shown in the library grid —
  neither F5 nor Ctrl+Shift+R fixed it, delay reported as minutes.
- Diagnosed live against a real affected issue (id 5469): scanner was working
  correctly the whole time — archive mtime, DB `date_modified`, and the
  regenerated thumbnail on disk all matched within ~2 minutes of the edit. Root
  cause was the browser's HTTP cache: v2.6 Item 2 Phase 4 (2026-07-13) added
  `Cache-Control: public, max-age=86400` to `GET /api/cover/{id}` to stop
  re-transferring unchanged thumbnails, but the URL never changed, so a browser
  that had already fetched a cover was entitled to reuse it for a full 24h with
  no way for any reload gesture to force a re-fetch of images set via JS after
  page load (how every cover in this app renders). A regression of the caching
  win, not a scanner bug — matches Tez's own suspicion in the INBOX note.
- Considered forcing revalidation on every request (`Cache-Control: no-cache`)
  first, and built it as an interim fix — but Tez asked whether that adds
  per-request overhead and whether invalidation could instead ride on the
  scanner's own change detection. It can, and it's strictly better: added
  `path_utils.cover_url(issue)`, which appends a `?v=` stamp from
  `Issue.date_modified` (the same mtime the scanner already records the moment
  it detects and applies a change) to every cover URL. Unchanged covers keep the
  original zero-request 24h cache; changed covers get a structurally different
  URL the instant a rescan updates that row, so the browser cache-misses
  automatically. Reverted `reader.py`'s cache header back to a long
  `"public, max-age=86400, immutable"`, now safe. All 9 call sites across
  `library.py`/`home.py` that built the raw `/api/cover/{id}` string switched to
  the new helper, including a data-shape change in Folder View's subfolder-cover
  pick (`subfolder_issue_ids` now retains `Issue` objects, not bare ids, so
  `.date_modified` is available with no extra query).
- **Verified live:** built a scratch two-page CBZ (red cover), scanned it in as
  an isolated test issue (id 5502, real library/DB otherwise untouched),
  confirmed the served cover was red with a version-stamped URL. Repacked the
  same archive with a green cover, rescanned, confirmed the version stamp
  changed and the new URL served the green cover immediately — no delay, no
  reload needed. Test issue, thumbnail, and scratch files deleted afterward.
  Tez confirmed fixed live in his own browser against the real library.
- Full detail in `docs/archive/bugs-fixed-archive.md` BUG-023.

## Session — 2026-07-17 — Hanken Grotesk not rendering; Admin scan-card green borders removed

- Tez noticed Hanken Grotesk (installed at the OS level) wasn't showing
  anywhere in the UI despite the Phase A font port. Root cause: `body`
  (`style.css`) hardcoded `font-family: system-ui, -apple-system,
  BlinkMacSystemFont, "Segoe UI", sans-serif` directly instead of using the
  `--font-sans` token (`'Hanken Grotesk', system-ui, ...`) defined alongside
  it — the Google Fonts `@import` was loading the font correctly, but no
  rule anywhere ever referenced it, so every element inherited `body`'s
  hardcoded fallback stack. Grepped the rest of the file to confirm this was
  the only hardcoded `Segoe UI`/`system-ui` stack — `--font-mono` was already
  wired up correctly at every technical-text call site. Fixed by changing
  `body`'s `font-family` to `var(--font-sans)`.
  - **Verified live:** confirmed via `getComputedStyle(document.body).fontFamily`
    (resolved to `"Hanken Grotesk", system-ui, ...`) and `document.fonts` (the
    four weights actually used — 400, 400 italic, 600, 700 — report
    `status: "loaded"`); zoomed screenshot of Home confirms the letterforms
    match Hanken Grotesk, not Segoe UI.
- Tez also asked to remove the green borders appearing on several Admin →
  Library Scan cards (screenshot: `15-07-2026_210200_digib00age-admin.png`
  showed it on Last Scan/Changed Files/Missing Records, absent on Files
  Found/New Files). Traced to `.has-pending`/`#scanNowCard.is-scanning`
  (`style.css`, added 2026-07-11) — both just `border-color: var(--green)`,
  toggled by `admin.js` per-card when a log has unread entries or a scan is
  actively running. Removed both CSS rules (cosmetic only — left the
  class-toggling JS untouched, it just has no visual effect now) and
  tightened the now-stale comment above `.stat-card` that referenced them.
  - **Verified live:** hard-reloaded `/admin` — all six Scan section cards
    (Scan Now, Last Scan, Files Found, New Files, Changed Files, Missing
    Records) render with the uniform dark card style, no green borders,
    Library Stats/Settings cards unaffected (never had the rule).
- Both changes are cosmetic (colour only, no nav/routing/IA change) per
  `CLAUDE.md` §5 — no `DECISIONS.md`/build-queue entry needed.

## Session — 2026-07-17 — Bulk-select toolbar: actions no longer clear the selection

- Tez reported that applying one bulk action (e.g. Favorite) to a selection
  immediately cleared it, so combining two actions on the same cards (e.g.
  favorite *and* rate) required long-pressing and re-selecting the same
  cards a second time.
- Root cause: `runBulkAction()` and the `→ Send to Full Editor` handler
  (`frontend/js/app.js`) both unconditionally called `exitSelectionMode()`
  after firing, on every action, success or failure.
- Fix: removed the trailing `exitSelectionMode()` call from both
  `runBulkAction()` (covers Mark Read/Unread, Favorite, Flag for Review,
  Rate) and the Send to Full Editor handler, so the selection and toolbar
  now stay live after an action fires — multiple actions can be applied to
  the same selection in sequence. Added an explicit **Deselect** button to
  the toolbar's end group (alongside the existing Cancel/Done, which were
  already functionally identical to each other) so clearing the selection
  is now a deliberate action rather than a side effect of every button
  click.
- **Verified live:** selected 2 cards in the "All" grid, applied Favorite
  (both favorited, selection and toolbar stayed active, "2 selected" still
  shown), then without re-selecting applied a 4-star rating to the same
  pair (applied correctly, selection still persisted), then clicked
  Deselect (cleared the selection/hid the toolbar, applied favorite/rating
  values remained on the cards). No console errors during the flow.
  Reverted the test favorite/rating values afterward so the real library
  data matches its pre-test state.
- Cosmetic/behavioural fix within the existing toolbar, no new nav/routing/
  IA change, no backend/data-model change — no `DECISIONS.md` entry needed
  per `CLAUDE.md` §5.

## Session — 2026-07-17 — Bulk-select toolbar: rating patch fixed (stale cover badge, unchanged info row)

- Follow-up bug surfaced by the previous session's fix (screenshot:
  `17-07-2026_003428_digib00age.png`): applying a new rating via the
  toolbar's star widget made an unrated-looking star badge reappear
  overlaid on the cover art, while the actual rating display under the
  card's issue/page count (the info block) stayed on its old value.
- Root cause: `applyRatingToDom()` (`frontend/js/app.js`) still patched
  `.card-rating-pill` — a cover-overlay badge from before the 2026-07-07
  redesign — inside `.cover-img-wrap`. No card builder has created that
  element since the redesign moved ratings into `.card-rating-row`,
  rendered in the info block's count row (`buildCoverCard()`/
  `buildFolderFileCard()`, via `buildRatingRow()`). The patch function was
  never updated to match, so every bulk-rate action added a legacy pill the
  redesign had already replaced, and left the real, visible rating row
  untouched.
- Fix: `applyRatingToDom()` now swaps `.card-rating-row` in place inside a
  new `.cover-count-row` marker class (added to `buildCoverCard()`'s and
  `buildFolderFileCard()`'s count/pages row, the same row `buildRatingRow()`
  is appended into at initial render) instead of touching `.cover-img-wrap`.
  Removed the now-dead `buildRatingPill()` function and its
  `.card-rating-pill` CSS (`style.css`) — nothing has rendered that markup
  since the redesign.
- **Verified live:** searched the real library for "4 Kids Walk Into A
  Bank" (an already-3-star-rated series card), selected it, rated it 5 —
  cover art showed no stray badge and the info-row rating updated to 5
  stars immediately — then rated it back to 3 via the toolbar to restore
  the real value. No console errors. Folder View's flat file cards
  (`buildFolderFileCard()`) weren't live-tested (long-press doesn't
  simulate cleanly via browser automation) but use the identical
  `.cover-count-row`/`.card-rating-row` structure now shared with
  `buildCoverCard()`, so the same fix applies.
- Cosmetic/behavioural bug fix, no nav/routing/IA change, no backend/
  data-model change — no `DECISIONS.md` entry needed per `CLAUDE.md` §5.

## Session — 2026-07-17 — Bulk-select toolbar: rating stars now toggle-to-clear like the issue page

- Tez pointed out the issue-detail page's rating control lets you clear a
  rating by clicking its already-selected star again (BUG-009 behaviour),
  but the bulk-select toolbar's rating stars didn't match — clicking a star
  equal to the selection's current rating just re-applied the same value
  instead of clearing it.
- Fix: the toolbar's per-star click handler (`ensureSelectionToolbar()`,
  `frontend/js/app.js`) now checks, before firing, whether every selected
  card's rendered `.card-rating-row` (inside its `.cover-count-row`) already
  has exactly `i` stars; if so the click clears the rating (0) instead of
  re-setting it to `i` — mirrors the Favorite/Flag-for-Review buttons'
  existing "all already set → toggle off" pattern in the same toolbar.
- **Verified live:** selected "4 Kids Walk Into A Bank" (real 3-star rating),
  clicked "Rate 3" — rating cleared to unrated; clicked "Rate 3" again —
  restored to 3 stars. No console errors.
- Cosmetic/behavioural fix within the existing toolbar — no `DECISIONS.md`
  entry needed per `CLAUDE.md` §5.

## Session — 2026-07-17 — Selection toolbar's Done pill: black text fixed to white

- Follow-up from the Deselect-button work: the toolbar's "Done" pill
  (`.selection-done-btn`, `style.css`) had `color: #000` — black text on
  its solid accent-blue background — which had been asked for earlier but
  not actually applied. Changed to `color: #fff`.
- **Verified live:** selected a card, confirmed the Done pill now renders
  white text on the blue background.
- Cosmetic colour-only change per `CLAUDE.md` §5 — no `DECISIONS.md` entry.

## Session — 2026-07-17 — Selection toolbar: removed the redundant Cancel button

- Tez pointed out Cancel and Deselect did the exact same thing (both just
  call `exitSelectionMode()`) — no reason to keep both. Removed the Cancel
  button from `ensureSelectionToolbar()` (`frontend/js/app.js`); Deselect
  and Done remain.
- **Verified live:** selected a card, confirmed the toolbar's end group now
  shows only Deselect and Done. No console errors.
- Cosmetic/UI-simplification change per `CLAUDE.md` §5 — no `DECISIONS.md`
  entry needed.

## Session — 2026-07-17 — Deselect pill restyled to match the other toolbar pills

- Tez asked for Deselect to visually match the other action pills (Mark
  Read, Favorite, etc.) — darker pill background, same hover behaviour —
  instead of its previous transparent/muted-text look inherited from the
  removed Cancel button.
- Switched Deselect's class from `.selection-cancel-btn` to the shared
  `.selection-action-btn` (`frontend/js/app.js`), which already carries the
  `var(--surface-2)` background, `var(--text-2)` text, and accent-border/
  text hover state every other pill uses. Removed the now-unused
  `.selection-cancel-btn` CSS rule (`style.css`) since nothing referenced
  it anymore after Cancel's removal.
- **Verified live:** selected a card, confirmed Deselect renders with the
  same dark pill background as Mark Read/Favorite/etc., and its hover
  state matches (accent border + brighter text). No console errors.
- Cosmetic colour/style-only change per `CLAUDE.md` §5 — no `DECISIONS.md`
  entry needed.

## Session — 2026-07-17 — Issue detail page: Summary text too wide on large screens, paragraph breaks lost

- Tez reported that on the issue detail page (`/issue/{id}`, served via
  `issue.html`), the Summary paragraph stretched to fill the full window
  width on a maximized/large browser window — a side effect of the
  2026-07-15 INBOX decision to drop `.container`'s 1440px cap site-wide
  (`style.css` line ~210). That full-width policy was meant for card grids,
  not a single prose paragraph, so at wide viewports the summary line
  length became uncomfortably long. Separately, ComicInfo.xml `Summary`
  fields containing blank-line paragraph breaks (`\n\n`) were rendering as
  one run-on paragraph — `_text()` in `backend/scanner.py` preserves
  internal newlines from the XML (only strips/leading trailing whitespace),
  and the API passes `issue.summary` straight through, but the frontend
  wrote it via `textContent` (`app.js` `initIssue()`) into a plain `<p>`,
  and default CSS `white-space` collapses newlines on display.
- Fix, both in `.summary-text` (`frontend/css/style.css`): added
  `max-width: 640px` to cap the paragraph's line length regardless of
  window width, and `white-space: pre-line` so embedded `\n`/`\n\n` from
  the XML render as line/paragraph breaks instead of being collapsed. No
  JS or backend change needed — the data already carried the newlines.
- **Verified live:** loaded issue id 5 (`30 Days of Night Deluxe Edition
  #1`, a Summary with two embedded blank-line breaks) at both 1920px and
  1280px window widths. Summary now wraps at ~640px regardless of window
  width and renders as four distinct paragraphs matching the XML's blank
  lines. No console errors, no other page elements affected.
- Cosmetic typography/sizing change per `CLAUDE.md` §5 — no `DECISIONS.md`
  entry needed.

## Session — 2026-07-17 — Issue detail page: cover card frame — thicker metal bezel, thinner state ring, embossed cover inset

- Tez asked, staying on the issue detail page's cover card
  (`.issue-cover-link--redesign` in `frontend/css/style.css`), for three
  adjustments to the layered box-shadow "frame" around the cover: increase
  the metal-grey bezel ring's thickness by 3px, reduce the inner
  read-state ring (blue=unread/green=read) by 1px, and add a border
  directly on the cover image's edge so it reads as dropped/embossed into
  the frame rather than flush with it. Explicitly scoped to the issue page
  only, not the browse/home grid cards.
- The frame is a stack of concentric `box-shadow` rings on
  `.issue-cover-link--redesign`: state ring → dark gap → metal bezel ring
  → dark gap → drop shadow. Widened the state ring's spread from 2px to
  1px (2px→1px thick) and the bezel ring's spread from 6px to 8px (2px→5px
  thick, +3px), shifting the two dark-gap rings outward by the same
  amounts so their own 2px thickness is preserved and nothing overlaps.
  Confirmed via `grep` that the browse/home grid's cover cards use a
  separate, differently-named class (`.cover-card--redesign`, its own
  box-shadow block elsewhere in `style.css`) — `.issue-cover-link--redesign`
  only ever applies to the issue detail page's single big cover, so this
  change can't leak into grid cards.
- Replaced `.issue-cover-link--redesign .issue-cover-img { box-shadow:
  none; }` with an inset box-shadow (a 1px dark inset ring plus a soft
  inward blur along the top) so the cover image itself now shows a
  recessed/embossed edge inside the bezel frame, instead of sitting flush
  against it.
- **Verified live:** loaded issue id 5 (state: read, green ring) and issue
  id 2886 (state: unread, blue ring) at the issue detail page, zoomed into
  the cover card corner on both — confirmed the thinner state ring, the
  visibly thicker metal bezel, and the embossed inset line around the
  cover image. Loaded the home grid separately and confirmed grid cover
  cards are visually unchanged (flush corners, no bezel frame) — the
  redesign-class scoping held. No console errors.
- Cosmetic sizing/decorative change per `CLAUDE.md` §5 — no `DECISIONS.md`
  entry needed.

## Session — 2026-07-17 — Issue detail page cover card: widened black gap before state ring, tried offset-shadow recipe for the embossed inset

- Tez shared a screenshot (`Pictures/Screenshots/17-07-2026_092546_top-10-
  digib00age.png`) of the issue page's cover card pointing out the black
  gap between the cover art and the blue/green state ring was too thin
  (a 1px inset ring from the previous session), and asked to try adapting
  a generic drop-shadow recipe they had — `.image-with-shadow { box-shadow:
  5px 5px 15px rgba(0,0,0,0.4); }` (horizontal/vertical offset + blur, not
  a symmetric ring) — into this frame to see if it gave a better dropped/
  embossed effect.
- Widened the solid inset ring on `.issue-cover-link--redesign
  .issue-cover-img` from 1px to 3px (`inset 0 0 0 3px rgba(0,0,0,0.75)`)
  — this is what actually renders as the black gap between the cover art
  and the state ring outside it, since the state ring sits on the parent
  `.issue-cover-link--redesign` element with zero offset from the image's
  edge. Adapted Tez's snippet as a second **inset** shadow layer (`inset
  5px 5px 15px rgba(0,0,0,0.4)`) rather than a regular one — a
  non-inset shadow on the image would extend outward past the parent's
  own concentric box-shadow rings unpredictably, whereas inset keeps the
  directional darkening contained within the cover itself, reading as a
  subtle bottom-right-weighted shadow inside the recess.
- **Verified live:** reloaded issue id 5, cropped/upscaled screenshots of
  the top-left corner before and after — confirmed the black gap is now a
  clearly visible solid band instead of a near-invisible hairline, and the
  directional inset shadow adds a soft depth cue without any visible
  artifacts or clipping. Full-page screenshot checked for regressions —
  none. Change is still scoped to `.issue-cover-link--redesign
  .issue-cover-img`, so grid/browse cards remain untouched.
- Cosmetic/decorative, exploratory per Tez's request ("see if this gives
  us the effect we want") — flagged as open to further iteration, not a
  finished design decision. No `DECISIONS.md` entry.
- **Follow-up same session:** Tez reported not seeing any difference.
  Checked the server was serving the edited file (`curl .../style.css`)
  and the computed style in a live tab (`getComputedStyle` via
  `javascript_tool`) — both confirmed the 6px inset box-shadow was
  correctly applied, so the gap was rendering, just too soft/blurred to
  read clearly at normal (non-zoomed) viewing size, especially against a
  dark cover. Switched from a blurred inset `box-shadow` ring to a real
  `border` (`border-width: 6px; border-color: rgba(0,0,0,0.9);` on
  `.issue-cover-link--redesign .issue-cover-img`, on top of the
  pre-existing `border: 3px solid transparent` base rule already reserving
  that space) — a border has no blur/anti-aliasing softness, so it reads
  as a crisp, unmistakable dark gap even unzoomed. Kept the directional
  inset shadow layer for depth. **Verified live:** hard-reloaded, screenshot
  at normal size (no zoom) now clearly shows the gap, confirming the border
  approach reads far better than box-shadow did at real viewing size.
- **Follow-up same session:** Tez confirmed the border thickness now looks
  right and asked to also add "the box-shadow effect" to the cover — i.e.
  the literal `.image-with-shadow` recipe as a real (non-inset) offset
  drop shadow, not the inset-adapted version from earlier. Changed
  `.issue-cover-link--redesign .issue-cover-img`'s `box-shadow` from
  `inset 5px 5px 15px rgba(0,0,0,0.4)` to the plain (non-inset) `5px 5px
  15px rgba(0,0,0,0.4)` — since the image is a child of
  `.issue-cover-link--redesign` (which paints its own ring stack first),
  the child's outer shadow paints on top of the parent's rings where they
  overlap, so it now visibly casts onto the metal bezel below/right of the
  cover, reading as the cover being lifted/dropped rather than flush.
  **Verified live:** hard-reloaded, confirmed via cropped screenshot that
  the shadow spills onto the bezel in the bottom-right corner as intended,
  with the border still providing the crisp gap on all sides.

## Session — 2026-07-17 — Issue-page cover: "collector card" slab redesign

- Tez supplied a finished design mockup (`D:\workshop\Claude\Claude Design\new
  issue cover card\CollectorCard.dc.html` and its `-print` variant, both
  Claude Design exports) and asked to integrate it into the issue page's
  cover card, replacing the flat box-shadow-ring bezel from the earlier
  sessions above with a proper graded-card "slab" look.
- The old `.issue-cover-link--redesign` approach faked a bezel with stacked
  solid-colour `box-shadow` rings — box-shadow can't fill with a gradient,
  so it couldn't reproduce the mockup's metallic chrome bezel, its coloured
  mat, or either layer's noise texture. Rebuilt as three real nested `div`s
  instead (`.cc-frame-outer` → `.cc-frame-mat` → `.cc-frame-inner`, added in
  `buildIssueDetail()`, `frontend/js/app.js`), each painting its own
  gradient/noise/highlight background, wrapping the existing
  `.issue-cover-img`. Values (gradients, noise SVG data-URIs, shadow
  stacks) ported near-verbatim from the mockup, scaled down for the site's
  200px cover column instead of the mockup's 408px preview frame.
- **Kept, didn't drop, the existing state-colour signal:** the old ring
  swapped blue (unread) / green (reading·read) via CSS class — same
  grouping preserved on the new `.cc-frame-mat`'s gradient (`state-unread`
  override; green is the default, matching the old rule's `state-part-read,
  state-read` grouping). The mockup itself has no state concept — this
  mapping was Code's call, not spelled out in the design, made to avoid
  losing an already-shipped piece of information density.
- **Favourite badge:** the mockup shows a heart badge overlaid on the art
  itself (dark translucent circle, red ❤), not the site's existing
  white-circle grid-card badge style. Added as `.cc-favorite-badge` inside
  `.cc-frame-inner`, always present in the DOM and toggled via the
  `hidden` attribute (not a CSS class) so `buildFavoriteToggle()` can sync
  it live — passed the badge element into `buildFavoriteToggle(data,
  badgeEl)` and added one line to its existing `sync()` closure. The
  standalone "☆ Add to Favorites" / "★ Favorited" button below the cover
  is unchanged and still the actual control; the badge is a read-only
  mirror of its state, same relationship the grid card already has.
- Hover: mockup's `translate(-3px,-9px)` "lift off the mat" effect on the
  art itself, scaled down slightly to `translate(-3px,-8px)`, replacing the
  old `scale(1.04)` zoom-on-hover.
- Mobile (`≤640px`): old rule fixed `.issue-cover-img` to `120×180px`
  (overriding its `aspect-ratio: 2/3`). Since 120:180 reduces to exactly
  2:3, the fixed height was redundant — replaced with
  `.issue-cover-link--redesign { width: 120px; flex-shrink: 0; }` so the
  whole frame (not just the innermost image) shrinks together, and the img
  keeps using its normal `aspect-ratio: 2/3` at every breakpoint instead of
  a special-cased override.
- **Verified live:** confirmed the running dev server (port 9424, already
  owned by Tez's tray app) was serving the edited `style.css` via `curl`
  before troubleshooting further — it was; the first screenshot round
  showed no visible change only because of a stale browser cache, resolved
  with a hard reload. After that: checked issue 28 (favourited, unread) —
  metallic bezel, blue mat, dark inner frame, and the heart badge all
  rendered correctly; checked issue 26 (read, not favourited) — green mat,
  no badge, progress bar under the cover unaffected. Clicked "Add to
  Favorites" on issue 26 live and confirmed the overlay badge appeared
  immediately without a reload, then clicked it again to restore the
  original (unfavourited) state — confirmed via `/api/issue/26` that
  `favorites` was back to `false`. No console errors. Did not do a full
  visual pass at the `≤640px` mobile breakpoint (window-resize in the
  browser-automation tool didn't change the captured viewport) — the
  mobile CSS change is a direct, dimensionally-equivalent substitution
  (120:180 ⇔ 2:3) rather than new layout math, so risk is low, but this is
  a real gap if Tez wants it double-checked by hand on a narrow window.
- Cosmetic per `CLAUDE.md` §5 (colour/spacing/visual restyle of an existing
  card, no navigation/IA change) — no `DECISIONS.md` entry, direct build.
- **Follow-up same session:** Tez compared the live result against a
  closer reference screenshot (`issue-card-design.PNG`) and flagged that
  the gap between the image's black border and the state-colour mat line
  should carry a soft blur, not sit flat — the mockup's dark inner frame
  (`.cc-frame-inner`) had been ported as an opaque flat panel with no
  colour bleed. Traced this back to the original `CollectorCard.dc.html`:
  it has an inset `box-shadow: 0 0 10px rgba(80,220,120,.18) inset` glow
  layered on the mat div itself, mostly hidden behind the opaque dark
  frame nested inside it — porting the layer literally wouldn't have
  reproduced the visible effect Tez pointed at. Added the glow directly to
  `.cc-frame-inner` instead (`0 0 16px 3px rgba(63,184,119,.4) inset`,
  state-coloured — green default, blue `state-unread` override matching
  the mat's own colour split), so it reads as a soft light bleeding in
  from the mat edge and fading toward the black border, before the crisp
  mat line itself. **Verified live:** hard-reloaded issue 26 (green/read)
  and issue 28 (blue/unread), cropped zoom screenshots on both confirm the
  blurred colour transition now sits between the black border and the
  mat line, matching the reference. No console errors.
- **Follow-up same session:** Tez asked for three more adjustments: (1)
  give the card more real estate, +25% — `.issue-layout`'s cover column
  went `200px` → `250px`, and the `≤640px` mobile frame width went `120px`
  → `150px` (same 25%) so both breakpoints scale together; (2) drop the
  hover lift effect entirely — removed
  `.issue-cover-link--redesign:hover .issue-cover-img`'s
  translate+box-shadow rule and the now-unused `transition` off
  `.issue-cover-img`, so the card is fully static, matching the rest of
  the page's non-hover cards; (3) thicken the image border and the three
  frame layers by 5px each — `.issue-cover-img` border `3px → 8px`,
  `.cc-frame-outer` padding `6px → 11px`, `.cc-frame-mat` padding
  `4px → 9px`, `.cc-frame-inner` padding `7px → 12px`. Border-radii left
  unchanged — not asked for, and the thicker frame still reads cleanly
  against them. **Verified live:** hard-reloaded issue 28, confirmed the
  card is visibly larger with a heavier frame and the blur glow from the
  prior follow-up still reads correctly at the new size; hovered over the
  cover and confirmed no transform/shadow change fires. No console errors.
- **Follow-up same session:** Tez felt the 8px black border from the prior
  step was too heavy and asked to revert it, while still growing the
  cover art and tightening the dark gap before the mat line. Reverted
  `.issue-cover-img` border `8px → 3px`; shrank `.cc-frame-inner` padding
  `12px → 5px` (this is literally the gap between the black border and the
  mat — shrinking it both tightens the gap and hands the freed space to
  the image); grew `.cc-frame-mat` padding `9px → 12px` so the
  state-coloured ring itself reads thicker/more prominent now that it
  sits closer to the art. Net effect on cover-art size: +9px of image per
  side (border -5, inner gap -7, mat +3). **Verified live:** hard-reloaded
  issue 28 (unread/blue) and issue 26 (read/green), zoom screenshots on
  both confirm a thin black border, larger art, a tighter blurred gap,
  and a visibly thicker mat ring. No console errors.

## Session — 2026-07-17 — Issue-page cover: root cause of the recurring "Blur" struggle found — `::before` doesn't render on `<img>`

- Tez reported still not getting the intended blur/glow effect right, despite
  several rounds above, and supplied a targeted recipe from Design (`D:\workshop\
  Claude\Claude Design\new issue cover card\issue-cover-glow-recipe.css`) —
  the exact same box-shadow + blurred `::before` glow layer already present in
  the original `CollectorCard.dc.html` mockup (line 56-59: the innermost element
  wrapping the cover art, *inside* `cc-frame-inner`), isolated on its own so the
  "split it exactly like this" structural gotcha would be unmissable.
- Root cause: `.issue-cover-img` in `frontend/js/app.js`/`style.css` is the
  actual `<img>` element itself, not a wrapping `<div>`. `::before`/`::after`
  don't render on replaced elements (`<img>`, `<video>`) in browsers — so every
  earlier attempt to add a blurred glow layer directly to `.issue-cover-img`
  was silently a no-op, independent of any box-shadow/overflow-clipping
  interaction. This was never diagnosed in the earlier sessions above because
  the symptom (no visible blur) looked identical to a shadow/clip conflict.
- Fix: added a new wrapper `<div class="cc-cover-glow">` in `buildIssueDetail()`
  between `.cc-frame-inner` and the `<img class="issue-cover-img">`, matching
  the recipe's two-element split — `.cc-cover-glow` carries the box-shadow
  (moved off the img, values unchanged) and the blurred `::before` gradient
  glow (`inset: -3px`, `filter: blur(5px)`, white-top-to-black-bottom); the img
  keeps its border/border-radius/`overflow: hidden` (added) as the clipping
  layer. Radii scaled down from the recipe's 14px/17px (mockup's 408px preview
  frame) to 9px/12px to match the site's existing 6px `.issue-cover-img`
  radius. **Did not reintroduce the recipe's hover-lift transform** — Tez
  explicitly asked to remove all hover interaction on this card two sessions
  ago (see "collector card slab redesign" above, follow-up 2), so only the
  static shadow + glow were ported, not the hover state.
- **Verified live:** hard-reloaded issue 28 (unread/blue, favourited) and issue
  26 (read/green, not favourited). Confirmed via `getComputedStyle` in a live
  tab that `.cc-cover-glow::before` actually has `filter: blur(5px)` and the
  gradient background applied (not just present in the stylesheet — actually
  computed on the rendered `::before`, ruling out the img-pseudo-element dead
  end recurring). Temporarily scaled `.cc-frame-outer` 4× via `transform:
  scale(4)` in a live tab (reverted after) to inspect the corner at high
  resolution — confirms a visible soft light-to-dark blurred band between the
  black inner-frame border and the cover art on both states, matching the
  recipe. No console errors on either issue page.
- Cosmetic/decorative fix to an existing card per `CLAUDE.md` §5 — no
  `DECISIONS.md` entry needed.
- **Follow-up same session:** Tez asked to push `.cc-frame-inner` (and
  everything inside it — the glow wrapper, the image) a few more pixels away
  from the `.cc-frame-mat` edge. Since `.cc-frame-inner` is a direct child of
  `.cc-frame-mat` with no gap of its own, that spacing is entirely
  `.cc-frame-mat`'s own `padding` — increased `12px → 16px`. Net effect: the
  state-coloured mat ring reads thicker/more prominent, inner frame + art
  shrink slightly to make room. **Verified live:** hard-reloaded issue 28
  (unread/blue), zoomed on the corner and confirmed a visibly wider mat band
  before the dark inner frame starts. No console errors.

## Session — 2026-07-17 — Desktop reader: Scroll mode never reported or resumed reading progress

- Tez reported the web UI's "Reading" left-nav filter showed nothing after
  opening an issue (Wordless), reading partway, and closing it — traced the
  whole chain (`frontend/js/app.js` nav filter → `GET /api/library`
  `reading_count` → `ReadingProgress.status` → `POST /api/progress/{id}`)
  and found the web frontend and backend both correct and consistent with
  each other. The actual gap was upstream in the Flutter desktop reader
  (`flutter_app/lib/widgets/comic_page_view.dart`): the reader's two modes,
  Scroll (continuous vertical scroll) and Page (swipe), only wire
  `onPageChanged` in Page mode via `PageView.builder`'s built-in callback.
  Scroll mode's `_buildScrollMode()`/local-file equivalent used a plain
  `ListView.builder` with no listener reporting page position at all — so
  scrolling through an entire issue never called `onPageChanged`, never hit
  `POST /api/progress/{id}`, and `ReadingProgress.status` never left
  `"unread"`. Scroll is the default reading mode
  (`settings_service.dart:39`), so this hit the out-of-the-box experience,
  not an edge case — confirmed present since the reader was first built
  (V1), not a recent regression.
- **Fix (progress reporting):** added a `ScrollController` listener
  (`_handleScrollProgress()`) to both `ComicPageViewState` (server-mode
  reader) and `LocalComicPageViewState` (local/offline CBZ reader) that
  estimates the current page from `scrollController.position.pixels /
  maxScrollExtent` and calls the existing `widget.onPageChanged(page)`
  callback only when the rounded page index changes — reusing the exact
  same downstream path Page mode already had (`ReaderScreen._onPageChanged`
  → `ApiService.updateProgress` / `SyncStore.recordProgress`), no backend or
  `reader_screen.dart` changes needed. One correctness wrinkle: server-mode
  scroll builds a pre-reversed `urls` list for manga
  (`widget.pageUrls.reversed.toList()`), unlike `PageView`'s `reverse:` flag
  (which only flips scroll *direction*, not item order), so the raw
  scroll-fraction index has to be remapped (`count - 1 - localPage`) back to
  the original index for `reversePages` issues — otherwise manga progress
  would have saved backwards relative to what Page mode saves. The
  local-file reader needed no such remap (its scroll-mode `itemBuilder`
  already keeps position `i` as the logical page number, only flipping
  which page's bytes get fetched per position).
- **Tez confirmed this half working**, then asked to also fix the
  resume-position half of the same `INBOX.md` line ("desktop reader not
  reporting read state or resuming read state") in the same session.
- **Fix (resume position):** Scroll mode also never jumped to
  `widget.initialPage` on open (unlike `PageController(initialPage: ...)`,
  a plain `ScrollController` has no "start at item N" concept) — reopening
  an issue in Scroll mode always started at the top regardless of saved
  progress. Added `_jumpToInitialPage()`, run once via
  `WidgetsBinding.instance.addPostFrameCallback` after first layout (when
  the Sliver's extrapolated `maxScrollExtent` becomes available), reusing
  the same fraction-based estimate in reverse: `jumpTo((page / (count - 1))
  * maxExtent)`. This is a pixel estimate, not exact — comic pages have
  slightly different heights depending on aspect ratio, and network images
  resolve their real height asynchronously after the initial layout
  estimate — so "lands roughly where you left off" is the intended
  behaviour, not frame-exact resume. Considered an exact approach (tracking
  each item's real rendered extent, or pulling in a package like
  `scrollable_positioned_list`) but the fraction estimate needed no new
  dependency and comic pages are close enough to uniform aspect ratio that
  the approximation is good enough in practice — see `DECISIONS.md`.
- **Found and fixed alongside (same root cause, not separately requested):**
  the bottom-bar page slider's `jumpToPage()` was silently a no-op in Scroll
  mode for the server-mode reader, and would have thrown ("ScrollController
  not attached to any scroll views") in Scroll mode for the local-file
  reader, since it unconditionally called the unattached `PageController`.
  Both now call a shared `_scrollToPage()` helper (factored out of
  `_jumpToInitialPage()`, same math) when in Scroll mode.
- Deliberately **not** fixed in this session, flagged to Tez and declined:
  nothing further — Tez confirmed both halves working as tested below.
- **Verified live** (Tez, manual): (1) opened Wordless in Scroll mode
  (default), scrolled a few pages, closed the reader, confirmed the issue
  now appears under the web UI's "Reading" left-nav filter — previously
  empty. (2) Reopened the same issue in Scroll mode, confirmed it resumed
  roughly where it left off instead of restarting at page 1. (3) Confirmed
  Page mode unaffected (no regression). `flutter analyze` and `flutter
  build windows --debug` both clean before Tez's manual pass.
- **Docs:** `INBOX.md` line struck through and filed as BUG-024 in
  `archive/bugs-fixed-archive.md` (found and fixed same session, never
  spent time as a live `BUGS.md` open entry — same pattern as BUG-023).
  `SPEC.md` Reader screen section corrected — it previously said "Progress
  saved to server on every page turn," which implied this already worked
  uniformly across both modes.

## Session — 2026-07-17 — Multi-select: shift-click range select, deselect-last-card no longer navigates

- Tez reported two related multi-select issues: (1) shift-clicking a card
  after selecting an earlier one didn't select the range between them —
  there was no shift-click handling in `frontend/js/app.js`'s selection
  code at all; (2) deselecting the *last* remaining selected card both
  deselected it and navigated to that card's issue/series page, instead of
  just exiting selection mode cleanly.
- **Root cause of (2):** `makeSelectable()`'s `pointerup` handler calls
  `toggleSelected()`, which calls `exitSelectionMode()` (setting
  `selectionActive = false`) the moment the last id is removed from
  `selectedIds`. The delegated capture-phase `click` listener that
  normally suppresses the `<a>`'s navigation checks the *live*
  `selectionActive` flag — but by the time the browser's synthetic `click`
  event fires (after `pointerup`), `selectionActive` had already flipped
  false, so the suppression check silently passed the click through to the
  underlying link.
- **Fix:** added a `suppressNextClick` flag, set `true` inside the
  `pointerup` handler whenever selection mode was active *at pointerup
  time* (before any toggle can exit it), consumed and cleared by the click
  listener on the very next `click` event (plus a `setTimeout(...,0)`
  safety-net reset in case the click never fires, e.g. `pointercancel`).
  The click listener checks this flag before falling back to the live
  `selectionActive` check, so the suppression decision is now pinned to
  the gesture that triggered it rather than state that can change mid-flight.
- **Shift-click range select:** added `selectionAnchorId` (the most
  recently individually-selected card) and a new `selectRange(anchorId,
  targetId)` helper that walks all `[data-issue-id]` elements in DOM order
  and selects everything between the two indices (inclusive), in either
  direction, without touching cards already selected outside the range —
  same behaviour as typical file-explorer shift-click. Wired into
  `makeSelectable()`'s `pointerup` short-tap branch: a shift-held tap while
  selection mode is active calls `selectRange()` instead of
  `toggleSelected()`. Each card element now also carries `__selectId`/
  `__selectKind` (the original, non-stringified id/kind passed to
  `makeSelectable()`) so range selection can key into `selectedIds`
  consistently with every other call site — `dataset.issueId` coerces to a
  string, which would otherwise create duplicate Map entries for numeric ids.
- **Verified live** against the running dev server (`localhost:9424`, Tez's
  tray-app instance) via `javascript_tool`, dispatching real
  `pointerdown`/`pointerup`/`click` event sequences (not calling the
  selection functions directly) so the actual event-handling fix was
  exercised, not just the selection-math helpers: (1) bootstrapped
  selection mode on a card, shift-clicked a card 3 positions later —
  confirmed all 4 cards in between got the `.selected` class and the
  toolbar read "4 selected", with `location.href` unchanged (no
  navigation). (2) Deselected down to a single remaining card, then
  deselected that last card — confirmed the toolbar hid, all `.selected`
  classes cleared, and `location.href` stayed on the browse page instead of
  navigating to the issue page (the reported bug). (3) Re-tested range
  select in the reverse direction (anchor after target in DOM order) —
  confirmed the same inclusive range regardless of click order. No
  scan/library data touched — purely client-side selection state.
- No spec doc describes multi-select gesture behaviour in this level of
  detail, so nothing else needed updating.

## Session — 2026-07-17 — Issue Detail page: live read-state sync, Read/Continue Reading button, backdrop full-bleed

Three small UI fixes to the Issue Detail page (`/issue/{id}`), all in
`buildIssueDetail()`/`buildStatusToggle()` (`frontend/js/app.js`) and the
`.issue-backdrop*`/`.issue-actions` rules (`frontend/css/style.css`).

- **Live read-state sync (behaviour fix):** clicking Mark as Read/✓ Read
  previously only updated the button itself — the collector-card frame's
  mat colour (blue = unread / green = reading·read) and the progress bar
  under the cover were computed once at initial render and stayed stale
  until a manual page refresh. Refactored `buildIssueDetail()` to build the
  cover frame and progress track once, then drive both from a new
  `syncReadState()` closure that recomputes them from `data.read_status`/
  `data.current_page`. `buildStatusToggle()` now takes an `onChange`
  callback and calls it after a successful mark-read/unread fetch, so
  `syncReadState()` re-runs and every dependent visual updates in place —
  no refresh needed.
- **"Read"/"Continue Reading" button:** added a filled accent-coloured
  `.btn-read-action` pill above Mark as Read in `.issue-actions`, linking
  to the same `comicvault://read/{id}` URI as the cover art. Label is
  "Read" by default, "Continue Reading" while `read_status === 'reading'`
  (kept "Read" for the fully-read state too — not asked to special-case
  it). Label is also driven by `syncReadState()`, so it flips immediately
  if Mark as Read changes the status.
- **Backdrop full-bleed + lighter fade:** `.issue-backdrop` was inset by
  `.container`'s 30px side padding, leaving a visible gap before the
  sidebar/viewport edge. Changed to `left: -30px; right: -30px` (mirrors
  `.page-bg`'s full-content-width approach) so it now spans edge-to-edge.
  Shortened `.issue-backdrop-fade`'s top transition (was solid `var(--bg)`
  through 8%, transparent by 55%; now transparent by 30%, no flat solid
  band) so more of the cover art reads through near the top. Added
  `filter: blur(2px)` to `.issue-backdrop-img` (image had no blur before);
  opacity left unchanged at 0.18 per the request.
- **Verified live** against the running dev server (`localhost:9424`,
  Tez's tray-app instance) via `claude-in-chrome`: loaded issue 4318
  (unread), clicked Mark as Read — confirmed the frame ring flipped
  blue→green, the progress track appeared, and the button changed to
  "✓ Read", all without a page reload. Set the issue to `reading` via
  `POST /api/progress/4318` and reloaded — confirmed the button read
  "Continue Reading" and the progress bar reflected the real page
  fraction. Reset the issue back to `unread`/`current_page: 0` via
  `POST /api/progress/4318/mark-unread` afterward — real library data
  left as found. No console errors.
- No spec doc describes the Issue Detail page's read-state visuals at this
  level of detail, so nothing else needed updating.
- **Follow-up same session:** the progress bar was showing for the `read`
  state too (a carry-over from the pre-existing `state-part-read ||
  state-read` condition, not something introduced by the sync refactor
  above). Tez asked for it to only appear while `reading`. Narrowed
  `syncReadState()`'s condition to `coverState === 'state-part-read'`
  only. Verified live: `read` state now shows no progress bar, `reading`
  still shows it correctly at the real page fraction. Reset issue 4318
  back to `unread`/`current_page: 0` afterward.
- **Second follow-up same session:** Tez asked for Edit XML and Flag for
  Review to share a row at equal width, and for the 🏷 emoji before Flag
  for Review's label to go. Wrapped both buttons in a new
  `.issue-actions-row` (`display:flex; gap:8px`) and gave both
  `.btn-edit-xml`/`.btn-flag-review-toggle` `flex:1; min-width:0` so they
  split the row evenly; dropped the `🏷 ` prefix from
  `buildFlagReviewToggle()`'s `sync()` text (both the flagged and
  unflagged label). Verified live — buttons now sit side by side at equal
  width, no icon, "Flag for Review" wraps to two lines at the narrower
  width which reads fine. No console errors.

## Session — 2026-07-17 — Cover-card resting shadow rework (Home vs Grid), Issue Detail button sizing

Tez noticed Home strip cards showed a "permanent" shadow at the base that
looked like the Grid library cards' hover glow, and asked whether it was
actually the same effect. Traced `.cover-card.cover-card--redesign`'s
resting box-shadow (`style.css` ~1165) — confirmed via `getComputedStyle`
in the running app that Home strip cards and Grid cards render byte-
identical box-shadow values; the "permanent vs hover-only" read was a
context illusion (a couple of Home cards floating in open space make a
constant low-intensity shadow obvious, the same shadow packed into a dense
multi-row grid just blends into the grid's own darkness).

- **Split the single box-shadow into two layers, one resting one hover:**
  the old rule combined a white glow ring + dark drop shadow, always on,
  intensifying further on `:hover`. Tez asked to keep the white glow
  permanent but move the dark drop-shadow layer to hover-only, so it stays
  subtle at rest on Home specifically. Split `.cover-card.cover-card--redesign`
  (and its `.is-flagged-review` specificity-override twin, same file ~1178)
  down to just the glow layer; the drop shadow now lives solely in the
  existing `.cover-card.cover-card--redesign:hover` rule (~1319), stacking
  with hover's own intensified glow for the lift effect. Existing
  `transition: box-shadow` on `.cover-card--redesign` already animates it
  in smoothly — no new transition needed.
- **Root-caused a hard clip line on the glow ring:** the original 5px-blur
  glow was bleeding past `.strip-track .continue-strip`'s 5px top / 10px
  bottom padding and getting a flat-cut edge instead of fading out. Found
  why: that container is `overflow-x: auto` with no explicit `overflow-y`
  — per the CSS overflow spec, a non-`visible` x-axis forces the y-axis to
  compute to `auto` too (confirmed via `getComputedStyle`, `overflowY:
  "auto"` despite only `overflow-x` being set in the stylesheet), so
  anything bleeding past the padding box gets hard-clipped rather than
  soft-fading. Tightened the glow's blur radius and raised its alpha so it
  reads at the same intensity within the existing headroom instead of
  reaching past it.
- **Follow-up, Tez's own manual edits:** after the above, Tez took over
  directly in the CSS to finish dialing in the pixel-level values —
  further tightened the resting glow, bumped `.strip-track .continue-strip`
  padding-top 5px→8px for more hover headroom, reduced the hover lift from
  `translateY(-4px)` to `-3px`, zeroed the hover drop-shadow's alpha, and
  changed `.btn-read-action`'s text colour from black to white. Left as
  Tez's own working state — not re-verified by Claude beyond confirming
  the file diff, since these were Tez's direct pixel-perfect adjustments
  made hands-on rather than through a described requirement. Worth noting
  the flagged-review twin rule (`.is-flagged-review`, ~1178) wasn't touched
  in this manual pass and may now differ slightly from the base rule's
  glow value — flag if that divergence wasn't intentional.
- **Issue Detail — Edit XML / Flag for Review pill sizing:** Tez asked for
  smaller text on both buttons since "Flag for Review" filling one line
  was forcing both equal-width pills wider than needed. Reduced
  `.btn-edit-xml`/`.btn-flag-review-toggle` `font-size` 13px→11px and
  `padding` `8px 18px`→`7px 14px`. Verified live on `/issue/4439` — both
  pills now sit noticeably thinner, text still legible.
- **Verified live** throughout via `claude-in-chrome` against the running
  dev server (`localhost:9424`, Tez's tray-app instance): compared Home
  strip vs Singles-grid resting/hover states side by side, zoomed on card
  edges to confirm the clip line was gone, and screenshotted the Issue
  Detail button row before/after the font-size change. No real library
  data touched (visual-only change, nothing read/write-path related).
- Purely cosmetic (shadow timing/intensity, button text size) — no
  `DECISIONS.md` entry or build-queue item per `CLAUDE.md` §5's
  structural/cosmetic threshold.

## Session — 2026-07-17 — List View redesign

- Scoped explicitly to the library List View (`#coverGrid.list-view`) only,
  since it shares `buildCoverCard()` and most CSS classes with Grid View —
  every change below was written to require `.list-view` (or an equivalent
  guard) so Grid View's appearance and behaviour stay untouched.
- **Two-column layout:** `.cover-grid.list-view` (`style.css` ~769) changed
  from a fixed single column to `grid-template-columns: repeat(2, 1fr)` with
  `column-gap: 50px`, plus a `@media (max-width: 1100px)` fallback back to
  one column on narrow windows. 1100px is a first-pass breakpoint, not a
  measured value — easy to hand-tune once lived with.
- **Row/column spacing:** added `padding-top: 10px` to `.cover-grid.list-view
  .cover-card` for breathing room at the top of each row; `row-gap` stayed
  at the existing 6px, only `column-gap` changed.
- **Genre tags → links:** `buildCoverCard()`'s list-genres block
  (`app.js` ~1621) now renders each genre as its own `<a class="list-genre-tag">`
  linking to `/?surface=fieldview&field=genre&value=...` (same fieldview
  pattern the Series/Issue Detail pages already use), joined by ' · ' text
  nodes, instead of one plain joined string. New `.list-genre-tag` CSS is
  deliberately its own lightweight class, not a reuse of the existing
  `.genre-tag` pill style (too heavy for a compact single-line row).
  Because the row itself (`.cover-card`) is an `<a>`, each genre link calls
  `e.stopPropagation()` on click (same guard pattern as `buildSelectDot`) so
  clicking a genre navigates to the filter instead of also triggering the
  row's own series/issue navigation.
- **Read/unread emphasis swap (List View only):** the pre-existing
  `.state-read`/`.state-part-read` text-colour rules (shared with Grid View,
  `style.css` ~992) made read issues appear bolder/brighter than unread ones.
  Added new `.cover-grid.list-view .cover-card.state-read ...` /
  `.state-part-read ...` overrides (higher specificity via the extra
  `.cover-grid.list-view` prefix, so they only apply in List View) that
  invert this — read/part-read rows now render muted (~0.55 opacity, lighter
  weight, no text-shadow), unread rows keep/gain the stronger look. Grid
  View's cards are unaffected — confirmed live that a `state-read` card's
  title colour/weight in Grid View is unchanged from before this session
  (Grid View's `.cover-card--redesign` rule for title colour already wins
  over the shared read-state rule regardless of this session's changes, a
  pre-existing quirk, not something introduced here).
- Grid View's page-level "cloud" background (`#pageBg`) needed no change —
  confirmed it's already page-scoped (sits behind `#browseView` regardless
  of grid/list mode) and was already visible behind List View before this
  session.
- **Verified live** via `claude-in-chrome` against the running dev server
  (`localhost:9424`, Tez's tray-app instance, port already owned so no
  second server started): confirmed the 2-column layout, 50px column gap,
  and row padding render correctly on the Browse/All surface; clicked a
  genre tag and confirmed it navigates to the fieldview genre filter (not
  the card's own series/issue page); compared computed styles for a
  `state-read` card's title/count/year between the Read and Unread filter
  tabs in List View (read: `rgba(255,255,255,0.55)`/weight 500, unread:
  `rgb(243,236,224)`/weight 700 — confirms the swap); re-checked the same
  card in Grid View (unchanged `rgb(243,236,224)`/weight 700 regardless of
  read state, matching pre-session behaviour). No console errors. Did not
  get a reliable real-window resize to visually confirm the 1100px
  collapse-to-one-column breakpoint — `resize_window` didn't change the
  automation viewport in this environment — but the media query itself is
  the same well-established technique already used elsewhere in this file
  (`--card-min` breakpoints at ~1766); worth a quick manual resize check by
  Tez to confirm the exact px feels right in practice.
- Cosmetic under `CLAUDE.md` §5's structural/cosmetic threshold (colour,
  spacing, and link-ifying existing text within the same layout) — no
  `DECISIONS.md` entry or build-queue item.
- **Follow-up, same session:** Tez asked for two further tweaks after
  reviewing the above live. Both confirmed working: (1) row-gap on
  `.cover-grid.list-view` bumped 6px → 25px (space below each row), column-gap
  unchanged at 50px. (2) Unread rows' `.list-summary` text set to
  `rgba(255, 255, 255, 0.9)` (`.cover-grid.list-view .cover-card:not(.state-read):not(.state-part-read)
  .list-summary`), scoped the same way as the rest of the emphasis-swap
  rules above — List View only, Grid View untouched.

## Session — 2026-07-17 — Series View: List View card layout applied to issue rows

Tez asked for the new List View design/layout (this session's own prior entry
above) to carry over to the Series Detail issue list, so each issue gets its
own formatted card in a 2-column grid, matching Item 9's design language
instead of Item 9's original "explicitly out of scope, same as list view"
call on `buildIssueRow()` (see Item 9's build note in
`comicvault-changes-v2.6.md`) — that call predates List View's own redesign
and is superseded by this session's explicit ask.

- **2-column card grid:** `.arc-group` (`style.css` ~1697, the direct parent
  `buildIssueList()` wraps issue rows in — confirmed via `app.js` there is
  currently always exactly one `.arc-group` per series, arc-label grouping is
  present in CSS but not yet wired up in JS) changed from a plain vertical
  stack to `grid-template-columns: repeat(2, 1fr)`, `column-gap: 50px`,
  `row-gap: 25px` — same values as `.cover-grid.list-view`. Same
  `@media (max-width: 1100px)` collapse-to-one-column fallback. Added
  `grid-column: 1 / -1` to the (currently unused) `.arc-label` rule so an
  arc heading will span both columns correctly whenever arc grouping is
  wired up in JS.
- **`.issue-row` restyled as a permanent card**, mirroring
  `.cover-card.cover-card--redesign`'s resting-glow/hover-lift treatment
  (`style.css` ~1231/1379): `background: var(--surface)`,
  `border-radius: var(--radius-lg)`, permanent white glow ring at rest
  (`box-shadow: 0 0 2px 1px rgba(255,255,255,0.5)`), lift + intensified glow
  on hover. Thumbnail bumped 65px → 115px to match List View's card
  prominence; grid-template-columns simplified from `65px 44px 1fr auto` to
  `115px 1fr auto` (thumb / detail / status button) — the issue-number
  column was folded into the title line as an inline `.issue-num` span
  (`#12 Title`) rather than kept as its own grid column, since a portrait
  card reads better with the number inline than as a separate centred
  column. Existing left-border read-state colour (green/blue) kept —
  wasn't part of the ask, low risk to leave as-is.
- **Genre tags added to each issue card** — new, since `buildIssueRow()`
  previously had no genre display at all (only the series header showed an
  aggregate). Required a small backend addition:
  `backend/routers/library.py`'s `GET /api/series/{issue_id}` issue_list
  entries (~line 473-491) gained `"genres": [g.genre_name for g in
  iss.genres]` — free, since `selectinload(Issue.genres)` was already
  applied to the query for the existing series-wide genre aggregate.
  `buildIssueRow()` (`app.js` ~2202) renders these the same way List View's
  `.list-genre-tag` does: each genre its own `<a>` into
  `/?surface=fieldview&field=genre&value=...`, `e.stopPropagation()` guarded
  since the row itself is a link. New `.issue-genres`/`.issue-genre-tag` CSS,
  same lightweight underline-on-hover treatment as `.list-genres`/
  `.list-genre-tag`.
- **Read/reading emphasis swap** added to issue cards, matching List View's
  swap: `.issue-row.state-read`/`.state-reading` now dim `.issue-title`
  (0.55 opacity, weight 500) and `.issue-sub`/`.issue-genres`/`.issue-summary`
  (0.5 opacity), so unread issues stand out and already-read/in-progress
  ones go quiet — same intent as the List View entry above, adapted to
  issue-row's own two states (no "part-read" concept at single-issue
  granularity).
- **Backend server needed a restart** to pick up the new `genres` field —
  `backend/main.py` runs `uvicorn.run(..., reload=False)`, so the change sat
  inert (empty `genres` key absent from the live API response) until Tez
  restarted the tray app's server process mid-session.
- **Verified live** via `claude-in-chrome` against the running dev server
  (`localhost:9424`, Tez's tray-app instance): 2000 AD series
  (`/series/5546`, 2,484 issues) — confirmed 2-column card grid, resting
  glow ring, hover lift, `#46`-`#50` (real `read` issues in the library)
  render with dimmed title/sub/summary text and a green left border +
  checkmark button versus bright/bold unread neighbours, genre tags
  ("Action · Adventure · Sci-Fi") render as real `<a>` links to the
  fieldview genre filter after the backend restart. No console errors.
  **Accidentally toggled issue #43 to `read` while testing the status
  button** (pre-existing click behaviour, not touched this session) —
  caught immediately via a direct `/api/series/5546` fetch and reverted by
  clicking the same button again; confirmed back to `unread` before moving
  on. Did not get a reliable real-window resize to visually confirm the
  1100px collapse-to-one-column breakpoint (same `resize_window` limitation
  as the List View session above) — same well-established media-query
  technique already proven elsewhere, worth a quick manual resize check by
  Tez.
- Cosmetic under `CLAUDE.md` §5's structural/cosmetic threshold (layout/
  spacing/colour change to an existing page, no nav/routing/IA change) — no
  `DECISIONS.md` entry or build-queue item, same precedent as the List View
  session above. The one non-cosmetic piece (`genres` added to an API
  response) is a pure additive field, no existing behaviour changed.

## Session — 2026-07-17 — Folder View subfolder cards: match redesigned cover-card border/image padding

- Folder View's subfolder cards (`.folder-card`, `buildFolderCard()` in
  `app.js`) still carried the pre-redesign chrome — a flat `1px solid
  var(--border)` border, and (for subfolders with a representative cover,
  which is effectively all non-empty ones per
  `get_tab_folder_contents()`/`backend/routers/library.py`) the cover image
  sitting flush against the card edge with no inset. Folder View's loose-file
  issue cards (`buildFolderFileCard()`) already use `.cover-card.cover-card--
  redesign`, so the two card types in the same grid looked visually
  inconsistent.
- `frontend/css/style.css`: `.folder-card` now uses the same resting glow
  ring / hover lift+glow `box-shadow` treatment as `.cover-card--redesign`
  (`border: none` + `box-shadow: 0 0 2px 1px rgba(255,255,255,0.5)` at rest,
  brighter glow + lift on hover) instead of a flat border. `.folder-card.has-
  cover` gets the same `5px 5px 7px` image-inset padding as the redesigned
  card, with a new `.folder-card.has-cover .cover-img-wrap { border-radius:
  var(--radius); }` rule so the now-inset cover keeps rounded corners.
  Deliberately left unchanged: `.folder-card`'s background (`var(--surface)`,
  stays theme-aware) and `.folder-card-info` (name/count block) — only the
  outer chrome and image inset were asked to match, not the info layout.
- Verified live via `claude-in-chrome` against the running dev server
  (`localhost:9424`, Tez's tray-app instance): a Custom Tab's Folder View top
  level (`2000 AD` decade subfolders) — resting glow ring and inset cover
  image confirmed via zoomed screenshot, hover lift + brighter glow confirmed
  on the first card. Drilled into a leaf folder to confirm the loose-file
  `.cover-card--redesign` cards read as visually consistent with the
  subfolder cards above them in the same grid. No console errors either
  level.
- Cosmetic under `CLAUDE.md` §5 (border/spacing/hover-effect change within an
  existing layout, no nav/routing/IA impact) — no `DECISIONS.md` entry or
  build-queue item.

## Session — 2026-07-17 — Folder View: removed in-page "← Back" / "Mark all read" row

- Same session, follow-up ask: Tez wanted the `folder-view-nav` row (the
  "← Back" link + "Mark all read" button sitting above the Folder View grid)
  removed outright so the card grid pushes up flush under the menu bar,
  matching Browse's (`#coverGrid`) layout.
- This one *is* navigation-touching, so treated as structural per `CLAUDE.md`
  §5 rather than waved through as cosmetic — see the new `DECISIONS.md` entry
  for the "is anything actually lost" check done before removing it (short
  version: no — `folderBackBtn` duplicated the browser's own back button,
  `folderMarkAllBtn` duplicated the existing multi-select toolbar's "Mark
  Read" action).
- `frontend/index.html`: `<nav class="back-nav folder-view-nav">` and its two
  buttons removed from `#folderView`; `#folderSearchLabel` (still needed —
  shows "Search results for…" during folder search) kept as a stand-alone
  element.
- `frontend/js/app.js`: removed the `folderBackBtn` history-back wiring and
  the `folderMarkAllBtn` show/hide/`onclick` lines from `renderFolderView()`
  and `startFolderViewSearch()`; deleted the now-unused `markFolderViewRead()`
  function entirely. Backend `/library/tab/{id}/folder/mark-read` endpoint
  left in place (not asked to remove it).
- `frontend/css/style.css`: dropped the dead `.folder-view-nav` rule;
  `.folder-search-label` now carries its own `padding: 14px 0 12px` so it
  still reads clearly when a search is active, and (via the `hidden`
  attribute already toggled in JS) takes zero space otherwise.
- Verified live via `claude-in-chrome` against the running dev server: grid
  now sits flush under the menu bar on a Folder View top level, matching
  Browse's spacing. Confirmed folder search still shows the "Search results
  for…" label with correct spacing and clears back to the normal grid.
  Drilled into a leaf folder and used the browser's native back navigation to
  confirm it still lands back on the parent folder listing with no in-page
  Back button. No console errors at any step.

## Session — 2026-07-18 — Move Series Folders / Move Singles Folders (v2.6 Item 10)

Two new Processing Tools built, sharing the existing Folder Processing card
alongside Sort by Filename (§11.5): `backend/library_move.py` (core logic,
also runnable standalone via `python -m backend.library_move series|singles
<folder>` per Tez's "port scripts in" intent), `backend/series_move_log.py`
/ `backend/singles_move_log.py`, `backend/routers/library_move.py`
(`browse`/`drives`/`run`/`status`, one progress singleton per group so a
Series run and a Singles run can't collide). Frontend: `fsScriptSelect`
enabled as a real 3-option dropdown, `processingTools.js` dispatches
Run/poll by selection.

**Scope changed twice mid-session before any code was written**, both times
because checking the real library against the proposed rule surfaced a
problem the plan hadn't accounted for:
- Article-stripping alpha rule (`The`/`A`/`An` stripped before bucketing)
  was picked after finding the literal-first-char rule contradicted
  `SPEC.md` §5's own examples and most of the real library.
- 2000 AD was originally going to need a hardcoded root-level exception
  (`20000AD` sat outside the A–Z/`#` scheme entirely, holding progs *and*
  megazines *and* one-shots). Tez restructured the actual folder instead —
  renamed to `2000 AD`, moved under `#\Series\2000 AD`, years unchanged —
  which meant the mover needed zero special-casing for it, so long as
  merging worked correctly at that nested depth.

**Two follow-up fixes came out of Tez's manual test pass**, not the
automated checks:
1. **Recursive merge.** First real Series run put a `2000 AD - 2026` Stage 3
   folder directly under `#\Series` as a wrong sibling of `2000 AD`, instead
   of merging into the existing `#\Series\2000 AD\2000 AD - 2026`. The old
   flat merge treated every entry as opaque — a same-named subfolder at the
   destination just failed instead of being merged into. Rewrote
   `_merge_series_folder` → `_merge_into_existing`, now recursive: a
   same-named folder at the destination merges one level deeper instead of
   failing; a same-named plain file still fails individually as before.
   Purely structural, no name-based logic — generalizes to any
   container-style series, not just 2000 AD. Re-verified with a new nested
   test case matching the real shape (existing dated sub-folder gets new
   issues merged in, a brand-new dated sub-folder gets added inside the
   container, an untouched sibling year stays untouched, a duplicate issue
   fails individually without blocking the rest).
2. **Exact-duplicate blocking.** Tez flagged that some older folders use
   `[YYYY]` where newer ones use `(YYYY)` — an unprocessed Stage 3 folder
   under the new convention could duplicate an existing folder under the
   old one. Split near-miss detection into two tiers: a folder that
   normalizes *identically* to an existing one (same letters/digits once
   the year suffix and all punctuation are stripped, regardless of bracket
   style) is now blocked outright — not moved, left in Stage 3, logged as a
   failure with the exact existing path it matched. Genuinely-similar-but-
   different names still only get the softer near-miss warning and still
   move. Verified against both a Singles (`Barbarella [1964]` vs `(1964)`)
   and a Series (`Tale of Sand  [2011]` vs `(2011)` — also caught a stray
   double-space) case.

**Also mid-session, unrelated to the build itself:** Code wrote an
unprompted entry into `INBOX.md` (a note about the DB-relink gap found
while investigating the 2000 AD move) — a direct violation of the
entry-only rule already stated in `working-rules.md`. Tez caught it and
clarified `INBOX.md` is his personal scratchpad, not something Code should
factor into its own work. Entry reverted; `working-rules.md` and
`CLAUDE.md`'s doc table both tightened to make the rule harder to miss
next time (see `DECISIONS.md`).

**Verified:** 18 automated checks (article stripping, `#`/`T`/`E` bucketing,
flat and nested Series merge, Singles collision, missing-folder error,
near-miss detection incl. the containment fix needed to actually catch the
motivating Judge Dredd Megazine case, exact-duplicate blocking for both
groups) against scratch library/Stage 3 copies in an isolated sandbox —
`L:\Comic Archives` never touched by any test run. Manually tested live by
Tez against real Stage 3 content afterward, including the real 2000 AD
nested-merge case, confirmed working after the two fixes above.

**Not done this session:** the library scan Tez deferred until all
Processing Tools work is complete — done 2026-07-18, see the performance
re-baseline entry below

---

## Performance Re-Baseline After the 2000 AD Move (2026-07-18)

Tez asked for a fresh performance pass, since the 2000 AD series had been
moved and ~2,500 new issues added — neither covered by the 2026-07-09
baseline. Run via the `perf-diagnostics` skill. **No application code was
changed at any point**; every measurement came from read-only scratchpad
scripts outside the repo, and `L:\Comic Archives` was verified byte-identical
before and after (5,452 files / 562.47 GB, zero added, removed or resized).

**The pre-flight check stopped the plan before it started.** The DB still had
all 2,484 2000 AD rows pointing at `L:\Comic Archives\20000AD\...`, a
directory that no longer existed — 44% of a random 400-issue sample was dead
paths. Reading `scanner.py` settled what a rescan would do:
`scan_single_file()` matches existing rows by exact `file_path` only, with no
hash or filename fallback, so the moved files would have been INSERTed as
2,490 new issues while the 2,484 originals got swept to `missing=True`. Tez's
assumption that the scan would detect the move and relink was wrong, and
finding that out before running it avoided a duplicated library. Logged as
**BUG-025**.

**Decision: wipe and rebuild, and make the rebuild the measurement.** Only 33
issues were marked read and 2 had a saved page position, so the DB held almost
nothing irreplaceable — and a from-scratch scan of ~5,450 files was exactly
the "scanner at real scale" number `PERFORMANCE.md` §3 had carried as an open
follow-up since 2026-07-09. Tez cleared the DB via the Admin page; verified
afterwards that all library tables were at 0 rows while `custom_tabs` and
`home_strips` survived.

**Results are written up in full in `PERFORMANCE.md` §1B.** Headlines:

- **Scanner, first real measurement:** 5,452 files in **21.5 min** (4.23
  files/s). Thumbnail generation is **53%** of that, per-file `db.commit()`
  **18%** (5,452 commits, one per file), metadata parse 24%. **4 archive opens
  per file**, not the 3 that code inspection had estimated. Cost is near-flat
  against file size (189ms to 289ms across a 25x size range), so the scanner
  is bound by fixed per-file overhead, not I/O.
- **Both N+1 fixes held** at the larger scale: `/api/library` 7,508 to 13
  queries, `/api/series` (2000 AD, now 2,490 issues) 4,969 to 9.
- **Cold-start follow-up closed with a negative result** — cold/warm ratio
  0.9-1.2x across all eight endpoints, i.e. no measurable first-request
  penalty. Measured on the true first request after Tez restarted the tray
  app.
- **A third instance of the `Issue.genres` N+1** in `home.py` —
  `/api/home/strips` went 7 to 39-52 queries, fingerprinted as 32 identical
  `issue_genres` selects across two 15-item strips. `library.py` got this fix
  in v2.6 Phase 1/2; `home.py` was never touched.
- Phase 3 (reader page cache) and Phase 4 (cover ETag/304) fixes both
  confirmed still working.

**Correctness problems found along the way**, all logged rather than fixed,
per the skill's hard rule that diagnostics don't change code:

- **BUG-025** — series move doesn't update `issues.file_path` or
  `custom_tabs.folder_path`.
- **BUG-026** — Clear Database leaves orphaned thumbnails (2,516 files,
  354MB) and doesn't `VACUUM`.
- **BUG-027** — no safe DB-reset sequence, since Clear Database lives on the
  Admin page the server must be up to serve. Raised by Tez as a flaw in the
  session plan; it's a real product gap, not just a planning one.
- **BUG-028** — macOS resource-fork entries (`._*.jpg`) inside archives break
  cover extraction *and* double `page_count` (64 reported vs 32 real), while
  the scan still reports `errors=0`. A full-library sweep found **22 of 5,452
  issues affected**. Started as "21 covers failed"; chasing it turned up the
  page-count effect and one further affected issue whose cover happened to
  succeed, so it showed no visible symptom at all.

**Two harness mistakes worth recording**, both caught before they reached the
doc: the cover conditional-GET check first reported 0/15 Cache-Control and
0/15 304s, which looked like a regression of the 2026-07-13 fix — it was a
case-sensitive header lookup against uvicorn's lowercase header names (real
answer: 15/15 and 15/15). And this run's archive-level "cold" timings are not
cold, because the instrumented scan had just warmed the OS cache across the
whole library; `PERFORMANCE.md` §1B flags this rather than claiming a 60x
improvement over the 2026-07-09 figure.

**Not done this session:** the browser-waterfall phase (Phase 6 of the plan) —
the HTTP-level numbers are solid and the Folder View tab was broken for most
of the session, so it was left for a follow-up. Cold-idle drive probe skipped
by Tez's call (10-15 min wall-clock per rep); finding #9 stays inconclusive.
No scanner optimisation attempted — findings #13/#14/#15 say where the time
goes, but deciding what to fix is a separate triage step.

**Still pending on Tez:** recreate the 2000 AD Folder View custom tab against
the new path (the old one was removed mid-session, since it pointed at the
deleted directory).

## Session — 2026-07-18 — BUG-028 fixed (macOS junk entries)

Two-part fix, per Tez's ask: (1) clean up the 22 already-affected issues,
(2) catch it at the processing stage so it doesn't recur with new batches.

**Root cause, confirmed by reading every "list image entries in an archive"
call site in `backend/`:** every one filtered by file extension only, with
no guard against macOS AppleDouble sidecars (`._foo.jpg`) or `__MACOSX/`
folder entries — except `reader.py`'s `_sorted_pages()`, which already had
an inline dot-prefix check. No centralized helper existed anywhere.

**Code fix — new shared predicate `archive_formats.is_macos_junk_entry()`,
applied at every read and write site:**
- Read sites (exclude junk when counting/picking): `scanner.py`
  `_generate_thumbnail()` (cover picker) and `_parse_cbz()` (page count),
  `reader.py` `_sorted_pages()` (deduped its own inline check against the
  shared one), `editor/archive_io.py` `get_archive_page_count()` /
  `read_xml_and_page_count()`, `editor_full.py` `_cached_image_list()` — the
  last three per Tez's go-ahead to extend past BUG-028's literal scope,
  since it's the same root cause and the Basic/Full Editor would otherwise
  keep showing wrong page counts for the same issues.
- Write sites (drop junk so a rebuild doesn't reintroduce it): `editor/archive_io.py`
  `flatten_and_zip()` — the single shared rebuild function behind Convert
  Images, CT Auto-Tag, XML Tagging, and every Editor save, so one fix covers
  all of them — and `archive_convert.py` `_convert_cbr()`, which does its
  own separate extract+rezip. `image_convert.py`'s `_extract_all()` also
  needed the same filter applied to its returned entry list, not just
  extraction: `flatten_and_zip()` dropping junk but `expected_count` (used
  by post-conversion validation) still counting it would have made
  validation fail on every archive containing junk — caught this before it
  shipped by tracing how `expected_count` flows through `_validate()`.
- Also fixed `_convert_images_in_dir()` so a `._` sidecar isn't
  Pillow-decode-attempted and counted into `images_skipped` (it was junk,
  not a real conversion failure).

**BUGS.md's fix #2 (scan errors) and #3 (cover endpoint) also done:**
- `scan_single_file()` now increments `scan_progress.errors` and logs
  `THUMBNAIL ERROR: <filename>` when `_generate_thumbnail()` fails, at all
  three call sites (new/updated/skip-branch backfill) — without
  reclassifying the row's own `"new"`/`"updated"` result, since the row
  itself scanned fine. `GET /api/scan/status` now returns `error_files`;
  `admin.js`'s scan-completion text appends `, N errors` when non-zero
  (previously nothing surfaced this at all, not even a count field existed).
- `GET /api/cover/{issue_id}` now looks up the `Issue` row first and only
  trusts the on-disk `{id}.jpg` when `cover_path` is set — previously it
  trusted a bare filename match, so a failed cover generation served
  whatever stale file happened to sit at that ID (BUG-026 territory) instead
  of falling through to live extraction.

**Remediation (the 22 affected issues):** new script,
`.claude/skills/perf-diagnostics/scripts/10_macos_junk_rebuild.py`,
companion to the existing read-only `8_macos_junk_sweep.py`. Confirmed via
that sweep script first that a plain rescan would **not** have fixed these —
`scan_single_file()` skips re-parsing a file whose mtime hasn't changed, and
this code fix doesn't touch any archive's mtime. The new script bypasses
that gate entirely: re-derives the affected list live from the DB, recomputes
`page_count` and regenerates the cover thumbnail via the now-fixed scanner
logic, writes both directly to the DB row. Took a `.bak` copy of the dev DB
first. Ran it: all 22 fixed (21× 2000 AD 64→32 pages, two of those at
104→52, plus Judge Dredd - One-Eyed Jacks 232→116) — exact match to BUGS.md's
predicted numbers. Archive files on `L:\Comic Archives` were never opened for
writing; only DB rows and thumbnail cache files changed.

**One wrinkle found during verification, logged in `DECISIONS.md`:**
`8_macos_junk_sweep.py`'s headline "issues containing macOS junk entries"
count stays at 22 even after the fix — it means "archive physically contains
a `._` entry," and these 22 archives still do (only files that pass through
Convert Archives/Convert Images/CT Auto-Tag get the junk physically stripped
on rebuild; direct-to-library files keep the junk bytes but the app now
correctly ignores them everywhere). The sweep's other number, "page_count is
wrong," is the real fixed-or-not signal — that one dropped from 22 to 0.

**Verified:** every fix checked by direct execution against the real
affected archives (not mocks) — `_sorted_pages()`, `get_archive_page_count()`,
`read_xml_and_page_count()`, and `_cached_image_list()` all confirmed
returning 32 (not 64) for issue 2491 post-fix. Built a scratch CBZ with
injected `._`/`__MACOSX/` junk entries, ran it through
`convert_images_in_archive()` live — rebuilt archive contained zero junk
entries, `images_skipped: 0` (junk didn't inflate that count), validation
passed. Forced a thumbnail failure with a scratch all-undecodable CBZ,
called `scan_single_file()` against a throwaway DB row (cleaned up after) —
confirmed `scan_progress.errors` incremented and the log line appeared,
result stayed `"new"`. Simulated the cover endpoint's `cover_path`-check
logic against both states (set and forced-None, rolled back, never
persisted). CBR-path fix (`archive_convert.py` `_convert_cbr()`) verified by
code reading only — fabricating a real RAR file isn't practical without
paid WinRAR, and the project deliberately never writes RAR anywhere. **Then
restarted the live server** (`POST /api/admin/restart`, the existing
sanctioned restart path — Tez confirmed this was fine) and re-checked live
in the browser: issue 2491's detail page shows "32 pages" (not 64), cover
loads 200 OK; `/api/issue/2491/pages` returns exactly 32 real page URLs,
`/api/page/2491/0` and `/31` both serve real `image/jpeg` bytes, `/32`
404s; issues 2503 and 4077 (the Judge Dredd one) spot-checked the same way,
both matching the remediation script's output (52 and 116 pages).

**Follow-up question from Tez, same session:** does opening an archive in
the Full (or Basic) Editor and saving also strip macOS junk, on top of the
ingest-time fix? Yes — both Editors' Save action calls
`write_comicinfo_to_cbz()`, which rebuilds via the same `_rebuild_archive()`
→ `flatten_and_zip()` path already fixed. Confirmed live: built a scratch
CBZ with 2 real pages + injected `._page.jpg`/`__MACOSX/._page.jpg` entries,
ran it through `write_comicinfo_to_cbz()` directly (the exact function the
Save button calls) — rebuilt archive contained only `ComicInfo.xml` + the 2
real pages, junk gone.

## Session — 2026-07-18 (BUG-025 follow-up)

Scoped BUG-025 first per Tez's instruction (highest-impact of the three bugs
open at session start — BUG-026, BUG-027 untouched, still open). Investigated
the Move Series/Singles Folders tool (`backend/library_move.py`,
`backend/routers/library_move.py`, `backend/series_move_log.py`,
`backend/singles_move_log.py` — all uncommitted new code from the same day)
and confirmed the bug's own description: the tool moves files on disk and
logs `[OK]`, but never touches `Issue.file_path` / `CustomTab.folder_path`.

**Built and scratch-tested a fix:** `_merge_into_existing()` now returns the
exact `(src, dst)` pairs it actually moved (a merge isn't always a clean
single-prefix rename — some entries can fail on a destination clash and stay
put); `LibraryMoveFolderResult` gained `moved_paths` and `db_sync_error`; new
`sync_moved_paths_to_db(db, result)` rewrites `Issue.file_path`/
`CustomTab.folder_path`/`HomeStrip.folder_path` per successfully-moved folder,
committing per-folder so a blocked/failed folder's rows stay untouched and a
DB-write failure on one folder can't roll back another's already-good update.
`routers/library_move.py`'s `_run()` opens/closes its own `SessionLocal()`
(mirrors `admin.py`'s `_run_scan_background` pattern). Move log `[OK]` lines
now show `N issue(s) re-pointed`, or a distinct `[OK, DB SYNC FAILED — rescan
and check logs]` suffix if the sync step itself fails (kept separate from a
real disk-move `FAILED:` line). Verified via an isolated scratch script —
temp dirs, temp SQLite DB, temp log dir, nothing real touched — covering the
plain-move case, the merge-into-existing case, and the exact-duplicate-blocked
partial-failure case (confirmed that folder's `Issue` row is correctly left
unchanged). Also unit-tested the DB-sync-failure branch in isolation.

**Re-diagnosed as not a bug, same session, before docs were written.** Tez
tried a real-world test — renamed `'68 Homefron [2014]` → `'68 Homefront
(2014)` and ran a Scan — and got 4 new + 4 missing rows, which looked like
the bug reproducing. Checking `logs/series_move_log.md` showed no entry for
that rename at all: it was done outside the Move tool (a plain on-disk
rename), so the code above was never exercised — this is `scanner.py`'s
exact-path-match blind spot instead, i.e. **BUG-013**, not BUG-025. That
prompted a closer look at BUG-025's actual trigger: the tool's intended
workflow is Stage 3 Processing → Move → manual Scan, and
`config.json`'s `scan_exclude: ["Processing"]` means Processing content is
never scanned before the move — so in the normal flow there's no DB row at
the source path to desync in the first place. The original 2000 AD report
was the tool being pointed at content **already inside** `L:\Comic Archives`
(already scanned) to reorganize it — an atypical use, not the designed one.

**Resolution:** closed BUG-025 as not-a-bug in the intended workflow — moved
to `docs/archive/bugs-fixed-archive.md` with the full writeup (not left open,
not logged as a genuine fix). The sync code was kept rather than reverted: it's
a no-op on the normal path and correctly covers the 2000-AD-style edge case if
the tool is ever pointed at already-in-library content again. Reasoning logged
in `docs/DECISIONS.md`. BUG-013 remained open at the time, separately, as the
bug covering "a folder changed location while already in the library" — on
BUG-013's own 2026-07-18 closeout (later the same day, see below), that
rename/move blind spot was split out into its own entry, **BUG-029**, since
BUG-013 itself only ever covered the narrower same-path mtime/size case.

**Verified:** scratch script only (see above) — no live manual test of the
kept sync code was run this session, since the bug it targets doesn't occur
in the tool's normal, intended use. If the tool is ever deliberately pointed
at already-in-library content again, that would be the moment to manually
verify the sync path end-to-end.

## Session — 2026-07-18 — BUG-013 fixed (scanner mtime/size change detection)

Tez asked whether BUG-013 was connected to the rename/dead-entry concern
raised earlier the same day. Explored `scanner.py`, `models.py`, `database.py`
to answer precisely: they're related but distinct — an in-place content edit
(same path) already worked correctly (mtime changes, scanner reprocesses); the
narrow BUG-013 gap is only a re-save that *preserves* mtime while changing
content; the rename/move case (no content-hash or path-independent matching
at all) is a separate, previously-undocumented blind spot. Tez initially
declined logging that second one — then, once BUG-013's fix was implemented
and a dead `'68 Homefront [2014]`/`(2014)` row-pair turned up as a live
example during migration testing, agreed to split it out as its own bug on
BUG-013's closeout (see below) rather than leave BUG-025's "still open, see
BUG-013" cross-reference pointing at a bug that had just been closed for
something narrower.

**Built:** added `Issue.file_size` (`models.py`); `_add_missing_issue_columns()`
(`database.py`) now adds the column and backfills it from disk for every
existing row (stat-only, avoids a mass "changed" storm on the first scan
after upgrading — confirmed cheap per the 2026-07-18 performance baseline,
~0.4s to stat the whole library). `scan_single_file()`'s skip check
(`scanner.py`) now reads mtime and size from a single `os.stat()` call and
requires both to match to skip; `_apply_metadata()` writes `file_size`
alongside `date_modified` on both insert and update paths.

**Verified:** scratch-tested first, in full isolation (temp DB, temp
thumbnail dir, synthetic CBZ, nothing real touched) — built a CBZ, scanned it
in, rewrote its contents with a different size while forcing the mtime back
to its original value (`os.utime`), rescanned, and confirmed the scanner now
reports "updated" instead of "skipped"; also confirmed a genuinely unchanged
file still skips (no fast-path regression). Also ran the migration itself
against a throwaway copy of the real dev DB: schema updated, 5,439/5,443 rows
backfilled correctly; the 4 that didn't (IDs 1-4, `'68 Homefront`) turned out
to be a real dead-entry example on disk — the folder was renamed from
`[2014]` to `(2014)` at some point outside the app, and the DB never caught
up (`missing` still `False`). That confirmed BUG-025's "still open, see
BUG-013" note was pointing at a real, reproducing gap — just not the one this
fix addresses.

Then Tez restarted the live server (picking up the migration + code against
the real dev DB) and ran a manual scan across various areas of the real
library — no issues, sign-off given.

**Closeout:** moved BUG-013 to `archive/bugs-fixed-archive.md`, scoped
strictly to the mtime/size fix actually built. Opened **BUG-029** in
`BUGS.md` for the rename/move blind spot (scanner's only match key is exact
`file_path`; no hash or move detection), citing the live `'68 Homefront`
example as confirmed real-world evidence, and updated BUG-025's stale
"BUG-013" cross-reference to point at BUG-029 instead. Corrected
`ADMIN_SPEC.md`'s "Changed" definition and `SPEC.md`'s incremental-rescan
table/`Issue` schema table to describe the mtime-or-size check and the new
`file_size` column.

## Session — 2026-07-18 — BUG-016 fixed (Restore Database doesn't revert DB state)

Asked which of the 4 open bugs to fix next; recommended BUG-016 over
BUG-026/027/029 — it's the only one marked high impact, it's the safety net
BUG-026/027's future DB-reset work will depend on, and unlike those two
(which explicitly need their own scoping session) BUG-016 already had a
confirmed root cause and a concrete recommended fix written into its
`BUGS.md` entry from the 2026-06-28 investigation. Read `backend/database.py`
and `backend/routers/admin.py` to confirm the diagnosis still held before
proposing the fix.

**Built:** added `checkpoint_wal()` (`database.py`) — runs `PRAGMA
wal_checkpoint(TRUNCATE)` on the live engine, folding pending WAL writes into
the main `.db` file and emptying the `-wal` sidecar. `run_database_backup()`
(`admin.py`) now calls it right before its `shutil.copy2`, so every backup
(manual, scheduled, and the pre-restore snapshot) captures fully-flushed
state — closes the "may affect backups too" risk BUG-016 flagged as
unconfirmed. `restore_database()` calls it, then `engine.dispose()`, then
deletes any remaining `-wal`/`-shm` sidecars next to `db_path` before copying
the chosen backup over it.

The `engine.dispose()` step wasn't part of the original plan — added after a
scratch test showed the app's `QueuePool`-backed engine still holds an
OS-level file handle on the `-wal`/`-shm` sidecars even after `TRUNCATE`,
which threw `PermissionError` on Windows when the fix tried to delete them.
Disposing the pool first releases the handle; safe here specifically because
restore already tears the process down via `_schedule_delayed_exit()` right
after (see `DECISIONS.md`).

**Verified:** scratch-tested in two stages outside the repo (throwaway
SQLite DB in the session scratchpad, nothing real touched) — first
reproduced the original bug mechanism directly (a post-backup write survived
a bare `copy2`-only restore), then re-ran the exact fixed sequence
(checkpoint → dispose → delete sidecars → copy) through a real SQLAlchemy
engine with `QueuePool` matching `database.py`'s setup, confirming the
post-backup write was correctly discarded. Then Tez ran the real repro live:
took a backup, made a change, ran Restore Database, confirmed the change was
reverted, and confirmed the server restarts and the library browses
normally afterward — sign-off given.

**Closeout:** moved BUG-016 to `archive/bugs-fixed-archive.md`. Updated
`ADMIN_SPEC.md` §9.2's mechanism description and status block (both
previously pointed at the open bug). Added a `DECISIONS.md` entry for the
`engine.dispose()` call, since the Windows file-lock behaviour behind it
isn't obvious from reading the fix alone.

## Session — 2026-07-18 — BUG-026/BUG-027 fixed (Clear Database orphaned thumbnails/no VACUUM; no safe DB-reset path)

Asked which bug to fix next; recommended tackling BUG-026 and BUG-027
together rather than as separate sessions — BUG-027's own scope note already
said its fix should "dispose derived data (BUG-026)," so they're one design
problem (a proper Clear Database reset), not two. Two Explore agents plus
direct reads of `admin.py`, `database.py`, `scan_logs.py`, `config.py`,
`admin.js`, `ADMIN_SPEC.md`, and the BUG-016 archive entry found the fix
surface was smaller than BUG-027's note assumed: Restore Database had
already solved "safely touch the DB file from a live server" via
`checkpoint_wal()` → `engine.dispose()` → sidecar delete →
`_schedule_delayed_exit()`. Confirmed with Tez: reuse that pattern
(restart-after-clear) rather than inventing a quiesce mode, and expand the
reset scope to also cover scan logs and `config.json` timestamps, not just
thumbnails — see `DECISIONS.md`.

**Built:** `clear_database()` (`backend/routers/admin.py`) now, in order:
deletes `Issue`/`Person` rows in a single commit (previously two separate
commits); sweeps every file in `backend/thumbnails/` (new
`_clear_all_thumbnails()` helper — unconditional, since everything is
orphaned once `Issue` is empty); resets the four scan log files (new
`scan_logs.clear_all_logs()`); clears `log_last_viewed`/
`next_processing_run` in `config.json`; runs `checkpoint_wal()` →
`engine.dispose()` → a fresh raw `sqlite3` connection to `VACUUM` and
re-checkpoint (new `_vacuum_database()` helper — VACUUM can't run inside a
transaction, and the SQLAlchemy engine is already disposed by this point) →
deletes any remaining `-wal`/`-shm` sidecars → `_schedule_delayed_exit()`.
Frontend (`admin.js`) `clearDatabase()` now mirrors `doRestore()`'s UX:
expanded confirm text, disabled/relabelled button while in flight, toast +
`window.location.reload()` after ~4s instead of `loadStats()`.

**Bug found during verification, fixed same session:** the first live test
returned a 500. `clear_database()` was a plain `def`, so FastAPI ran it in a
worker thread with no event loop, and `_schedule_delayed_exit()`'s
`asyncio.create_task()` requires one. Changed to `async def` (matching
`restart_server()`/`restore_database()`, which were already async for this
exact reason) — see `DECISIONS.md`. A second, unrelated snag during testing:
the running dev server process pre-dated these code edits, so the first
click exercised the *old* endpoint (only issues/people deleted, no restart)
— had to trigger `/api/admin/restart` manually once to load the new code
before the real test could run.

**Verified:** live against the real dev DB (disposable per `CLAUDE.md` §6).
Before: 5,452 issues, 7,968 thumbnail files, 19.2MB DB, 98KB `-wal`,
`log_last_viewed` populated, four scan logs present. After: 0 issues, 0
thumbnail files, 98KB DB (VACUUM reclaimed ~19MB), 0-byte `-wal`, scan logs
gone, `log_last_viewed` cleared, Processing Tools logs (Convert, Rename, CT
Auto-Tag, etc.) confirmed untouched. Confirmed via `Get-CimInstance
Win32_Process` that the server process actually exited and a new one started
with no manual tray interaction (closing BUG-027). Tez then ran the full
click-through UI flow (Unlock → Clear Database → confirm dialog) directly
and confirmed no errors and a clean automatic restart.

**Closeout:** moved BUG-026 and BUG-027 to `archive/bugs-fixed-archive.md`,
correcting both entries' stale `ADMIN_SPEC.md §9` citation to §7.4 (Clear
Database, not Database Backup) along the way. Updated `ADMIN_SPEC.md` §7.4
with the full reset scope and restart mechanism, and added a `DECISIONS.md`
entry for the quiesce-vs-restart call and the `async def` fix. BUG-029
(scanner rename/move detection) remains the only open bug.

## Session — 2026-07-18 — BUG-029 fixed: content-hash rename/move detection (forward-only)

Tez asked for a cost/impact analysis of using content hashing to fix
BUG-029 before deciding whether to build it: what full-file hashing costs
versus the scanner's current ZIP-directory-only reads, whether it introduces
new problems, and whether it helps performance elsewhere. Findings (see
`DECISIONS.md` for the full write-up): the scanner is deliberately not
I/O-bound today (`PERFORMANCE.md` finding #16), so hashing breaks that
property; a one-time backfill across the whole library was estimated at
~75-95 minutes of continuous USB HDD reads (~430GB at the drive's measured
77-95MB/s), while hashing only new/changed files going forward is nearly
free (real scans typically touch 0-2 files, `PERFORMANCE.md` finding #7).
Tez confirmed the dev DB will be wiped at least once more before
production, so there's no reason to spend that backfill time on data that
won't survive — decided to go **forward-only**: hash new/updated files from
here on, don't retroactively backfill the existing ~5,427 issues. The 4
already-orphaned rows from the original bug report are unaffected by this
fix and still need the existing manual `cleanup-missing` cleanup.

**Built:**
- `backend/models.py` — added `Issue.content_hash` (nullable `Text`).
- `backend/database.py` — `_add_missing_issue_columns()` adds the column via
  a plain guarded `ALTER TABLE`, deliberately with **no backfill loop**
  (unlike the `file_size` column a few lines above it, which backfills
  because a stat call is cheap — a full-file hash read is not).
- `backend/scanner.py` — new `_hash_file()` (chunked `blake2b`, so large
  compendiums don't load fully into memory), called from `_apply_metadata()`
  so it only runs on INSERT/UPDATE, never on the unchanged/"skipped" fast
  path. New `_detect_renames()` pre-pass in `scan_library()`: before the
  per-file loop, matches on-disk paths with no DB row against DB rows
  currently off-disk (by `file_size` prefilter, then `content_hash` exact
  match) — this includes rows already flagged `missing=True` from an earlier
  scan, not just ones going missing in the current run, so a rename is still
  caught even if the move happened between two scans. On a match, the
  existing row's `file_path`/`date_modified`/`file_size` are updated in
  place (id, `content_hash`, `cover_path`, and reading progress all
  untouched) instead of inserting a new row and flagging the old one
  missing; logged via `scan_logs.append_changed_files_entry(...,
  "moved (renamed from <old_path>)")` and a new `ScanProgress.moved` counter
  surfaced in the scan summary line.

**Verified:** scratch-only, isolated temp DB + temp library + temp
thumbnails/logs dirs (never the real `backend/comicvault_v2.db` or
`L:\Comic Archives`) — confirmed a plain on-disk rename updates the existing
row (id/progress preserved, no duplicate, `moved` counter incremented,
"moved" line written to the changed-files log) while a genuinely new file
still INSERTs, a same-path content change still hits the BUG-013 mtime/size
UPDATE path (not the rename path), and a genuine delete still flags
`missing=True`. Separately smoke-tested the migration itself against a
throwaway copy of the real dev DB: `init_db()` completed in ~0.04s, row
count unchanged, and every existing row's `content_hash` confirmed `NULL`
(proof the no-backfill guarantee holds against real data, not just a fresh
test DB).

## Session — 2026-07-19 — Three UI tweaks: genre ribbon link, Admin page width, Home Strip arrow bleed

Three small cosmetic/behavioural UI fixes, tested and passed one at a time,
docs/commit batched at the end per Tez's request.

**1. Genre ribbon on grid/strip cards now links to the genre filter.**
`frontend/js/app.js` — the `card-genre-ribbon` shown on strip cards
(`buildStripCard`), series/singles grid cards (`buildSeriesCard`), and
folder-view cards (`buildFolderFileCard`) was a plain non-interactive
`<span>`. Replaced with a new shared `buildGenreRibbon()` helper that
renders it as a real `<a href="/?surface=fieldview&field=genre&value=...">`,
same fieldview route the Series/Issue Detail page's genre tags and the
list-view `list-genre-tag` already use. Since each card is itself an `<a>`
wrapping the whole cover, the ribbon's click handler calls
`stopPropagation()` — same guard `list-genre-tag` already uses — so
clicking it opens the genre filter instead of also navigating into the
card's series/issue. `frontend/css/style.css` `.card-genre-ribbon` gained
`text-decoration: none` and a `:hover` accent-colour cue now that it's a
link.

**2. Admin page: content sections narrowed and centred.** Per-section
settings blocks (`.admin-content-block`, one shown at a time under
`#adminContentPane`/the Advanced Settings fieldset) were stretching to the
full unconstrained `.container` width on wide viewports. Capped at
`max-width: 640px; margin: 0 auto`, so every settings form — Auto Scan
Settings, DB Backup Schedule, Library Folders, Home Page Strips,
Genre/Format List, Password Protection, etc. — is now a narrow centred
column. Filename Editor (`data-subitem="filename-editor"`) was called out
by Tez as needing more room for its 3-column `pt-rename-row` layout;
initially left at full width, then Tez asked for it narrowed too —
settled at `max-width: 75%` (still centred via the same rule), rather than
the 640px every other section gets.

**3. Home strip scroll arrows pushed to the true page edge.** The
left/right arrow buttons (`.strip-arrow`) are positioned `left:0`/`right:0`
against `.strip-track`, which sat inside `.container`'s 30px gutter (10px
at ≤640px) — leaving a visible gap between the arrow and the actual
browser edge. `.strip-track` now bleeds full-width past that gutter
(negative margin cancelling it, matching padding added back so the
scrollable card row itself still lines up with the rest of the page) —
same full-bleed technique as any edge-to-edge carousel row. Mobile
breakpoint (`@media max-width: 640px`) gets the matching ±10px override so
the bleed amount always matches `.container`'s actual padding at that
width.

**Verified:** all three manually tested live in-browser by Tez, one at a
time, each confirmed passing before moving to the next.

## Session — 2026-07-19 — Admin Logs modal defaults to most recent scan only

Tez's complaint: after a scan, clicking a log card's **Logs** button showed the
*entire* accumulated log file — as the file grows over many scans, the entries just
written end up buried at the bottom, requiring scroll-through of old history to find
them. Fix: the modal now defaults to showing only the entries from the scan that was
just run; the underlying log file's full history is untouched and still reachable
via a text editor (same as before).

**Design problem:** `changed_files_log.md`, `new_files_log.md`, and
`missing_log.md` accumulate zero or more lines *per scan* (one per changed/new/
missing file), with no per-line timestamp or scan-boundary marker — so there was no
way to tell, from file content alone, which lines belonged to which scan run.
(`last_scan_log.md` didn't have this problem — it's already exactly one line per
scan.)

**Solution — scan-boundary marker lines.** `backend/scan_logs.py` gained
`write_scan_markers(started_at)`, which appends a `## Scan — DD/MM/YYYY HH:MM` line
to those three logs. `backend/scanner.py`'s `scan_library()` calls it once, right
after the `library_root` existence check and before the disk-walk begins — so every
scan that actually runs writes its marker first, before any of that scan's entries,
including scans that find zero changes (a lone marker with nothing under it usefully
confirms "ran, found nothing" rather than looking broken). `read_recent_log()` (new,
alongside the existing `read_log()`) finds the last marker line and returns it plus
everything after; `last_scan_log.md` just returns its last line. `GET
/admin/logs/{log_name}` (`backend/routers/admin.py`) switched from `read_log()` to
`read_recent_log()` — same response shape, so no frontend contract change.

**Legacy fallback:** log files that predate this change have no marker yet;
`read_recent_log()` falls back to full content until the next scan adds one. No
backfill — forward-only, consistent with how this project already treats
accumulated log/DB state.

**Frontend:** no functional changes — same endpoint, same `{content, exists}`
shape. Added one static hint line under the modal title (`frontend/admin.html`,
`.log-viewer-hint` in `style.css`) pointing to Settings → Library Management →
Access Logs for the full-history folder path, since the modal no longer shows it by
default.

**Verified:** ran a real scan via the Admin page (5,452 files, 0 changes) — each of
the four Logs modals showed only that scan's marker/line, not the accumulated
history; confirmed the full `new_files_log.md` on disk (474KB, pre-existing) was
untouched apart from the new marker appended at the end. Separately verified the
multi-entry-per-scan slicing logic (two simulated scans, several lines each) against
an isolated scratch log directory — recent view correctly isolated only the second
scan's lines while the full file retained both. No real library files or Processing
folder touched — verification scan was read-only against the archives, as scans
always are.

**Follow-on, same session — BUG-030 fixed.** Tez's own verification of the above
surfaced a real, separate bug: a folder rename he'd made (`4 Kids Walk Into A Bank
v1 [2016]` → `(2016)`) showed "Changed Files: 6" on the stat tile with an empty log
underneath. Root cause traced to `_since_scan_count` (the counter behind that tile)
incrementing on new-file inserts as well as genuine updates, while
`changed_files_log.md` only ever logs genuine updates/moves — so a rename that
BUG-029's forward-only content-hash matching couldn't catch (these rows predated
that fix) fell back to new-insert-plus-missing-row handling, inflating the tile
while leaving the log correctly empty. Fixed in `backend/scanner.py`: removed the
insert-branch increment, added one to `_detect_renames()`'s match branch instead —
tile and log now driven by the same two events (updated, moved). Full writeup in
`archive/bugs-fixed-archive.md` BUG-030. Verified via code review of the small diff
plus a real no-op rescan (tile and log both correctly zero); the positive case
wasn't exercised with a synthetic new file per this project's real-library-only
testing convention — will show correctly on Tez's next real scan with actual
changes.

## Session — 2026-07-19 — Full XML Editor pre-fills Series/Number/Year from filename when no XML exists

Full Editor's `get_file_xml()` (`backend/routers/editor_full.py`) used to return
every field blank when a loaded archive had no `ComicInfo.xml` at all, leaving Tez
to type at least a Series name by hand before "Search ComicVine" would fire (its
existing guard: *"Need to enter a series name to search"*). The Filename Editor
(Admin → File Rename, `ADMIN_SPEC.md` §11.1) already solves the same problem for
its own use case via `backend/rename_tool.py::parse_comic_filename()` — a
well-tested, scene-release-tolerant regex parser, also reused by CT Auto-Tag
(`ct_bridge.py::identify_file()`).

Found a dormant, purpose-built shim already sitting unused for exactly this:
`backend/editor/xml_parser.py::parse_filename_for_comicinfo()` did the
Series/Number/Year/Title field-remapping needed, but was wired to
`backend/scanner.py::_parse_filename()` — the simpler fallback the library scanner
uses internally — and was never actually called from anywhere. Repointed it to
`rename_tool.parse_comic_filename()` instead (updated the import, the field-key
remap to match that parser's `series`/`issue_num`/`year` return shape, and the
docstring), rather than writing new remapping code. `scanner._parse_filename()`
itself is untouched — its own internal callers (`scanner.py` lines ~304, ~352) are
unaffected.

`editor_full.py::get_file_xml()`'s no-XML branch now calls this shim to seed
`fields` before returning. No frontend changes needed — `populateForm()`
(`frontend/js/editor_full.js`) already writes `fields.Series`/`Number`/`Year`
straight into the form inputs, and `openSearchOnline()`'s existing series-required
guard just naturally passes once Series is pre-filled (or still shows the same
manual-entry prompt if a filename doesn't parse to anything useful).

**Verified live** via the actual Full Editor UI (`/editor`) against three synthetic
scratch `.cbz` files added under a temporary `_claude_test_scratch` folder inside
`L:\Comic Archives` (removed immediately after testing, real library otherwise
untouched):
- No XML, well-formed filename (`Amazing Test-Man 003 (2019).cbz`) → Series/Number/
  Year auto-populated correctly on load, Title stayed blank; clicked "Search
  ComicVine" and it fired immediately using the parsed series, returning real
  ComicVine matches, no manual typing required.
- Existing `ComicInfo.xml` present (`Already Tagged Comic 001 (2020).cbz`, embedded
  Series "Existing Series"/Number 5) → fields loaded from the XML unchanged,
  filename-derived values ("Already Tagged Comic"/001/2020) were not used —
  confirms the XML-present path is untouched by this change.
- No XML, filename with no clean series pattern (`zzz garbage_%%%.cbz`) → degraded
  gracefully, no crash; the parser's whole-string fallback filled Series with the
  cleaned filename text rather than leaving it blank or erroring.

## Session — 2026-07-19 — BUG-031: Full Editor Process All wrote Increment # numbers out of order

Tez reported live, loading the real `Empire of the Dead [2014-2015]` folder for a
genre change with Increment # + Process All: displayed issue #2 came back tagged
`<Number>8</Number>`, #3 as 9, and so on — the written numbers didn't track the
issues shown in the Column 1 tree.

**Root cause:** `renderFileTree()` (`frontend/js/editor_full.js`) sorts a *copy* of
each series' issues with `naturalCompare` (numeric-aware) purely for display. The
underlying `loadedFiles` array driving `processBatch('all')`'s `file_ids` was never
reordered to match — it kept whatever order the files arrived in, which is
non-numeric from either intake path: `add_folder`'s `os.walk()` (raw filesystem
enumeration order) or the folder-browse picker's own list (sorted with plain
`localeCompare`, no `numeric: true`). The backend's `apply_increment()`
(`backend/editor/batch.py`) just assigns `Number = start + idx` sequentially over
whatever order it's handed, trusting the caller.

This is why it only surfaced now: pre-v2.6-Item-7 the list was flat and
drag-and-drop reorder *was* `loadedFiles`'s order, so display order and processing
order were the same array by construction. The four-column tree redesign
(2026-07-14) correctly dropped drag-and-drop (no meaning in a grouped tree, see
`DECISIONS.md`) but nothing replaced it to keep `loadedFiles`'s actual order in
sync with the natural-sorted render — small batches (or names where lexicographic
and numeric order happen to coincide) never exposed the gap; a 15-issue folder did.

**Fix:** added `treeOrderedFileIds()` — walks the same grouped folder→series→issue
structure `buildFileTree()`/`renderFileTree()` already use, natural-sorted the same
way, and returns just the ids in that order. `processBatch('all')` now sends
`payload.file_ids = treeOrderedFileIds(loadedFiles)` instead of raw `loadedFiles`
order, so Process All's numbering is derived from the tree at request time and can
no longer diverge from what's displayed, regardless of arrival order. Also fixed
the picker's own list sort (`renderPickerTree`) from plain `localeCompare` to
`naturalCompare`, so Select All in the folder-browse modal is numeric-aware too —
same bug class, same feature area. Updated `editor_full.py`'s `process_batch()`
docstring, which still claimed file_ids "respects drag-and-drop reorder" (stale
since the v2.6 Item 7 redesign).

**Verified live** against 10 synthetic scratch `.cbz` files (`Empire Test 1.cbz` …
`Empire Test 10.cbz`, no zero-padding) under a temporary `_bug031_test` folder
inside `L:\Comic Archives\Processing` (scan-excluded, removed after testing) —
chosen specifically because plain string sort/filesystem order splits `10` away
from `2`–`9`, exactly the divergence that caused the bug. Loaded via **Add Selected
Folder** (exercises `os.walk`, the real repro's intake path), tree displayed
correctly natural-sorted (1–10) as before. First Process All attempt (against the
already-fixed code) still showed the bug — turned out to be the browser serving a
cached pre-fix `editor_full.js` (`EDITOR_SPEC.md`'s own deploy note: `/editor`'s
static assets have no `cache-control`, need a hard refresh). After Ctrl+Shift+R and
regenerating fresh scratch files, reran Process All (Genre=Crime/Format=Series/Age
Rating=Teen all "Apply to All", Increment # from 1): every archive's
`<ComicInfo><Number>` now matches its tree position exactly (`Empire Test 1.cbz` →
1 … `Empire Test 10.cbz` → 10), Genre applied to all ten. Scratch folder deleted
afterward; real `Empire of the Dead` folder was never touched — its working set was
cleared from the Full Editor's in-memory list (not from disk) before testing and
left empty afterward for Tez to reload and redo his actual batch.

## Session — 2026-07-19 — Full Editor: consolidated the three "Clear" buttons into one Clear Queue

Tez reported the Column 2 "Clear" button (bottom of "Edit ComicInfo.xml", next to
"+ Queue") "appears broken and no longer clears the queue." Investigating found no
code-level bug there: that button (`feClearFormBtn`) only ever called `resetForm()` —
it reset the form fields and was never wired to the queue at all. It just sat directly
below "+ Queue" and read as if it should be queue-related. (Initial pass mis-flagged
`clearQueue()`'s fetch URL as having a backslash/forward-slash bug — that was an
artifact of how the Grep tool rendered the string in this session, not an actual defect;
`backend/routers/editor_full.py`'s `/api/editor/full/queue/clear` handler and its
frontend caller were already correct.)

**Fix, per Tez's direction:** removed `feClearFormBtn` from Column 2 entirely (only
"+ Queue" remains in that panel's foot). Removed the old "🗑 Clear Queue" button from
Column 4's top toolbar and relocated it into the Queue Actions row, between Process
Queue and Process All. Restyled it from the ghost-button look to the same `btn-primary`
blue-pill class as its two siblings, added `disabled` (tied to `queueFiles.length === 0`,
same condition already driving Process Queue) so all three buttons now share identical
enable/disable behaviour. Per a follow-up request, added `color: #fff` (including on
`:hover`) scoped to `.fe-queue-actions .btn-primary` so all three queue-action buttons
render white text instead of `btn-primary`'s default black-on-blue.

Files touched: `frontend/editor_full.html` (button removal/move/restyle),
`frontend/js/editor_full.js` (dropped the dead `feClearFormBtn` wiring line, added
`feClearQueueBtn` to `updateActionButtonStates()`), `frontend/css/style.css`
(white-text override for the queue action row).

**Verified live** at `http://localhost:9424/editor` (dev server already running under
Tez's tray app, port 9424) via Claude-in-Chrome: hard-refreshed past the static-asset
cache (same caching quirk noted in the 2026-07-18 BUG-031 session), confirmed Column 2's
foot shows only "+ Queue", confirmed Column 4's Queue Actions row reads Process Queue /
🗑 Clear Queue / Process All as matching white-text blue pills, all three disabled with
an empty queue. No console errors on load. Did not click Process Queue/Process All or
run a full queue→clear round-trip against real library files — the Explorer/file-picker
modal was opened once against the real `L:\Comic Archives` tree to inspect the folder
browser but no files were selected or added, so nothing on disk was touched.

## Session — 2026-07-19 — Auto Processing Schedule row: disable irrelevant fields, auto-save on change

Tez flagged the Schedule/Time/Day row (Admin → Processing Tools → Auto Processing,
`ADMIN_SPEC.md` §11.4.5) as confusing: the Day dropdown stayed active even when
Schedule was Off or Daily, where it's meaningless. Bundled in a second, already-known
gap from the same row: unlike every other control on this page, Schedule/Time/Day
required an explicit **Save** click with no unsaved-changes indicator — flagged as a
`ROADMAP.md` candidate and documented in §11.4.5 as the *actual root cause* of a past
"scheduled runs weren't firing" report (someone changed Day/Time, assumed it was live
like the rest of the page, never clicked Save).

**Fix:** `frontend/js/processingTools.js` — added `updatePfScheduleFieldStates()`
(same `.disabled = ` pattern already used for `convertImagesQuality`/Lossless), called
on load and whenever Schedule changes: Time disabled only when Schedule is Off, Day
disabled unless Schedule is Weekly. Replaced the explicit `pfSaveScheduleBtn` click
handler with a `saveSchedule()` helper wired to `change` on all three fields
(Schedule/Time/Day), matching the auto-save-on-change pattern every other Processing
Folder Automation control already uses — reuses the existing `savePfSetting()` helper
and its "Saved" toast, no backend changes needed (`POST /processing-folder/config`
already accepted partial payloads and already nulled `next_processing_run` on any
schedule/time/day change). `frontend/admin.html` — removed the now-unneeded
`pfSaveScheduleBtn` button.

**Verified live** at `http://localhost:9424/admin` via Claude-in-Chrome, against the
real Processing Folder config (`L:\Comic Archives\Processing\Stage 1`, real ComicVine
key, Schedule=Daily/01:00/Thursday — same static-asset caching quirk as the 2026-07-18/19
Editor sessions, needed a hard refresh before the new JS took effect). Confirmed via
direct DOM inspection: Off → both Time and Day disabled; Daily → Time enabled, Day
disabled; Weekly → both enabled. Cycled Schedule through weekly → off → daily via
real `change` events (not just calling the handler directly) to exercise the actual
event wiring, then confirmed via `GET /api/admin/processing-folder/config` that the
real config settled back to its original `daily`/`01:00`/`3` (only `next_processing_run`
went `null`, which is expected — the endpoint already nulls it on any schedule/time/day
change, and the scheduler loop recomputes it on its next poll). No console errors.

## Session — 2026-07-19 — File Rename: field order + output format changed

Tez asked to change the File Rename tool's field order/output format so Issue #
sits right after Series instead of after Title.

**Fix:** `backend/rename_tool.py`'s `build_filename()` — reordered parts from
`Series - Title #Issue (Year)` to `Series #Issue - Title (Year)`. Edit Panel row
order in `frontend/admin.html` swapped to match (Series, Issue, Title, Year — the
table previously read Series, Title, Issue, Year despite `ADMIN_SPEC.md` §11.1.4
already describing the Series/Issue/Title/Year order, a pre-existing doc/code
mismatch this also resolves). `frontend/js/processingTools.js`'s `RENAME_FIELDS`
array reordered to match, including the one positional reference
(`RENAME_FIELDS[1]` for Issue, used by `updateRenameAutoIncrementAvailability()`).

**Verified:** sanity-checked `build_filename()` output via a scratch Python call
(`Series #Issue - Title (Year)`, and correctly degrading when Title/Issue/Year
are blank), then Tez manually tested with a sample file in the live Admin UI —
confirmed field order and generated filename both correct.
Real Processing Folder path, checkboxes, and ComicVine key were never touched.
