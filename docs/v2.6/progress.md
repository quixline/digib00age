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
