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
