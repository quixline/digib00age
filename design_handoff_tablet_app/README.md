# Handoff: digib00age Flutter Tablet App — Options 2a (portrait) & 2b (landscape)

## Overview
Redesign of the ComicVault Flutter tablet app (`flutter_app/`) to match the digib00age web UI. Two approved mockups from the design session:

- **2a — Portrait tablet (810×1080 logical px)**: collapsed nav rail, custom libraries shown as blue circles with initials.
- **2b — Landscape tablet (1080×810 logical px)**: expanded nav rail, custom libraries shown as text.

Same app, one responsive layout: the rail collapses/expands via the toggle button; default to **collapsed in portrait, expanded in landscape**.

## About the Design Files
The files in this bundle are **design references created in HTML** — interactive prototypes showing intended look and behaviour, **not production code**. The task is to recreate them in the existing **Flutter** app (`comicvault_v2/flutter_app/`) using its established patterns (screens in `lib/screens/`, models in `lib/models/`, `api_service.dart` for data). Open `Flutter App Redesign.dc.html` in a browser and use sections **2a / 2b** (top of the canvas) as the source of truth; ignore turn 1 (superseded).

## Fidelity
**High-fidelity.** Colors, typography, spacing, radii and interactions are final. Recreate pixel-perfectly with Flutter widgets.

## App Structure
Persistent left **nav rail** + content area. Screens: Home, Browse (filtered library, grid/list), Series detail, Issue detail. Existing `library_screen.dart` / `series_screen.dart` are the starting points; the reader (`reader_screen.dart`) is unchanged.

### Nav rail (matches web UI side menu)
Width 64px collapsed / 196px expanded (animate 180ms). Background `surface-card #16181C`, right hairline border `#2C3038`, 14px 8px padding, 2px gap. Top: rail-toggle icon button.

Items, in order (icon 19px + label 14px, semibold; active = accent color + 12% accent tint bg, radius 6px; row padding 10px 14px expanded, centered when collapsed):
1. **Home** (house icon)
2. **All** (2×2 grid icon)
3. **Singles** (book icon)
4. **Series** (layers icon)
5. — divider (hairline) —
6. **Unread** — glyph `○`
7. **Reading** — glyph `◐`
8. **Read** — glyph `✓`
9. — divider —
10. **LIBRARIES** eyebrow label (11px, bold, 0.08em tracking, uppercase, muted `#5E6470`) — expanded only
11. One row per custom library (from the server's custom tabs/folders API):
    - **Expanded**: library name as plain text (truncate with ellipsis).
    - **Collapsed**: **26px blue circle (`#0A5FFF`), white bold 12px first character** of the library name — `#` for names starting with a digit (e.g. "2000 AD" → `#`), else the first letter A–Z (e.g. "Favourites" → `F`). Active library circle gets a 2px accent ring offset by the surface color.

Items 2–8 and libraries all navigate to Browse with the corresponding filter. Read-state filters: Unread / Reading / Read map to `unread` / `progress` / `read`.

### Home
Header: digib00age lockup logo (24px high) left; search `⌕` and settings `⚙` 38px round icon buttons right; bottom hairline. Body: horizontal cover strips (Recently Added, Random Unread, genre strip…), each with an eyebrow heading and 150px-wide cover cards.

### Browse (grid + list)
Header row: eyebrow of active filter (e.g. `UNREAD`, `2000 AD`) above a **22px, weight 800, accent-blue count** (`5,427 Titles` format); grid/list toggle buttons (40×40, radius 8, active = raised bg) on the right.

**Grid**: 150px cover cards, 14px gap. Card = 2:3 cover, 10px radius, hairline border, title (bold, 1–2 lines) + meta below. Read-state treatments (locked): unread = default surface; part-read = black card, green gradient rising from bottom, 3px green progress bar over cover, "NN% Read"; read = 50% green fill; favourite = gold ring around card + gold `★` badge top-left (1px black border). Unread series show a blue count badge top-right.

**List** (this is the changed card — note the field order): row card, 96px-wide 2:3 thumbnail left, info column 10px 14px padding, 3px gap:
1. Title — 14px bold, 1 line ellipsis
2. Year · count — `2025 · 353 pages` / `2026 · 20 issues` (12px muted)
3. **Summary — 12px muted, max 2 lines, ellipsis** ← inserted between the count and genres
4. Genres — `Action · Adventure · Sci-Fi` (12px secondary)
5. Publisher · Writer (12px muted)
6. `NN% Read` when part-read (white, semibold)

Same read-state/favourite treatments as grid. Hover/press: 3px lift + accent border.

### Series detail (mirrors web `series.html`)
- Backdrop: first-issue cover, ~28% opacity, 3–4px blur, dark overlay, gradient fade to canvas.
- Top bar: `← Back` (accent pill, sm) left, `Mark all read` (accent pill, sm) right.
- Title 30px/800; `Publisher · Year` 14px secondary; genre tag chips; `N issues` 13px muted.
- Issue rows (cards, radius 8, hairline border, 10px 12px padding, 14px gap, tappable → issue detail):
  56px cover thumb (3px radius) · `#n` (13px bold secondary) · column: title (14px bold), `Year · NN pages` (12px muted), **summary (12px muted, 2-line clamp)** · circular status button right (○ unread / ◐ reading / ✓ read, toggles state).
  Left border 3px: green = read, blue = reading, hairline = unread. Reading row gets an 8% blue tint background.

### Issue detail (mirrors web `issue.html` — **NO "Edit XML" button**)
- Same backdrop treatment. `← Back` accent pill top-left.
- Left column (190px portrait / 210px landscape): cover (2:3, radius 8, hairline border, modal shadow), then stacked **secondary** (bordered, raised-surface) full-width buttons:
  1. `Mark as Read` ↔ `✓ Read`
  2. `★ Add to Favourites` ↔ `★ In Favourites`
  3. Row of five 22px `★` rating stars (empty = `#2A2E36`, filled = gold `#F0C419`), tap to set/clear.
  **The web UI's "Edit XML" button is intentionally omitted on the app.**
- Right column: title 32px/800; badge row — `#19` (raised pill, hairline border) shown for series issues only + type pill (`Series`/`Single`, accent bg, white text); `Publisher · Year · English` 14px secondary; genre tag chips; hairline divider; `SUMMARY` eyebrow + body (15px, 1.7 line-height); divider; `CREDITS` eyebrow + `Writer  <name>` (label muted, name accent-blue underlined link); `Rated: Teen+ · NN pages` 13px muted.
- Bottom bar: `← Previous` (flex-grow, bordered card button) · current title (13px muted) · `Next →`. Disabled state = 35% opacity. For a series issue prev/next steps through issues; for a single it steps through the current browse list.

## Interactions & Behavior
- Rail toggle animates width 180ms `cubic-bezier(0.4,0,0.2,1)`; labels hide when collapsed.
- Card hover/press: translate up 3px + accent border, 180ms. No bounces, no loops. Honour reduced-motion.
- Back stack: issue (from series) → series → browse/home; series/single → wherever opened.
- Mark-as-read, favourite, and rating update state immediately (optimistic) and persist via the API.
- Portrait/landscape: same widget tree; rail default collapsed in portrait, expanded in landscape; issue-detail left column 190→210px.

## State Management
- Nav: active section/filter, rail collapsed, grid|list view mode.
- Library: item list per filter (all / singles / series / unread / reading / read / custom library).
- Detail: current series, current issue index; read-state marks, favourites, ratings.

## Design Tokens (dark theme — default)
Colors: canvas `#0D0E10` · card `#16181C` · raised `#1F2228` · sunken `#2A2E36` · border `#2C3038` · border-strong `#3A3F49` · text primary `#F2F4F7` · secondary `#9BA1AC` · muted `#5E6470` · **accent `#0A5FFF`** (hover `#2E72FF`, press `#0048D6`) · read/progress green `#3FB877` · "reading" row blue `#0A5FFF` · favourite gold `#F0C419`. No red in the read system. Light theme values in `tokens/colors.css`.

Type: **Hanken Grotesk** everywhere (JetBrains Mono only for technical strings). 15px UI base; eyebrows 11px/700/0.08em uppercase; titles 30–32px/800, -0.02em.

Spacing/radii: radii 3 (thumbs) / 6 (controls) / 8–10 (cards) / pill 999. Hairline 1px borders; depth from the 4 surface steps, not shadows.

## Assets
- Logo lockup + OO icon: project `assets/logo/` (copy `lockup-light.png`, `icon-oo.png`, `favicon.png` into Flutter assets).
- Cover art in the prototype is placeholder; the app loads real covers from the ComicVault server thumbnails API.
- Icons: minimal Unicode glyph set (`★ ⚙ ✓ ◐ ○ ← → ⌕`) + simple outline icons (house/grid/book/layers, 2px stroke — Lucide equivalents are fine in Flutter, e.g. `lucide_icons` package).

## Files
- `Flutter App Redesign.dc.html` — interactive prototype; **use sections 2a and 2b only** (turn 1 is superseded). Open in a browser from the design project root (it references `_ds/`, `assets/`, `support.js`).
- `data.js` — the fake catalogue data driving the prototype (shows expected fields: title, year, type, pages/issues, genres, publisher, writer, summary, state, progress, favourite).
- `tokens/` — `colors.css`, `typography.css`, `spacing.css`, `elevation.css` copied from the digib00age design system: authoritative token values.

## Suggested Claude Code prompt
> Read `design_handoff_tablet_app/README.md`. Implement options 2a/2b in `flutter_app/` — restructure `lib/screens/` into a rail-based scaffold (nav rail + Home/Browse/Series/Issue screens) per the spec, mapping data through the existing `api_service.dart` and models. Dark theme first, tokens from the README.
