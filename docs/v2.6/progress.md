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
