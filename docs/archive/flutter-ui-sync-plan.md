# Flutter UI Sync Plan — Library Card Components

**Source files read:**
- `frontend/css/tokens-base.css`, `tokens-dark.css`, `tokens-light.css`, `style.css`
- `frontend/js/app.js` — `buildCoverCard()`, `buildStripCard()`, `buildFolderCard()`, `buildFolderFileCard()`
- `flutter_app/lib/theme/tokens.dart`
- `flutter_app/lib/widgets/cover_card.dart` — `CoverCard`, `CoverListRow`
- `flutter_app/lib/screens/browse_screen.dart`, `home_screen.dart`
- `flutter_app/lib/models/series.dart`, `custom_tab.dart`

**Target device:** 10" tablet (landscape)  
**Flutter project location:** `comicvault_v2/flutter_app/`  
**Generated:** 2026-07-23

---

## Closing status (2026-07-28)

Closed out — reviewed against the actual current `flutter_app/` source rather
than resumed as a build queue. Most of what mattered shipped, largely via
Tez's own direct ask (`mobile-reader-changes.txt`, closed in `INBOX.md`
2026-07-24) rather than by working this document's priority list in order —
so treat the checkmarks below as "confirmed present in code," not "built
from this plan."

**Shipped, differently than this doc proposed** (matches Tez's actual ask,
not this doc's web-parity guess):
- Card frame: plain 1px border (white dark / black light), not the
  gradient-background-plus-glow-ring this doc recommended (§1.1/1.2/6.2).
- Card size widened to fit 4/row instead of 5 (`AppSpacing.cardMin` 150→188).
- Grid card's full green read-state overlay dropped in favour of the small
  corner badge (§2.1); unread-count pill field still exists but nothing
  renders it (§2.5); favourite badge is now a heart, border no longer gold
  (§2.4, though the circle itself stayed black/bordered rather than the
  white/no-border this doc specified — never flagged as wrong, left as-is).
- **Folder View (§4, the largest item in this doc) — fully built**:
  `getFolderContents()` wired, `FolderEntry` with the year-range calc
  (`1979–2000`) Tez asked for, `FolderScreen` with drill-down nav, routed
  from `shell_screen.dart` off `viewMode == 'folder'`. Reuses `CoverCard`
  directly for folder tiles instead of a separate `FolderCard` widget.
- Page-background blur built, but as a fixed blur rather than a live
  cover-cloud — a deliberate switch, already logged in `INBOX.md`.

**Fixed during this closeout session** (found while reviewing, not
pre-existing in this doc's checklist):
- `CoverListRow` (list view) still had the full-image green read overlay
  the grid card had already dropped — now uses the same small corner badge.
- `Series.progressPercent` (`flutter_app/lib/models/series.dart`) used
  `read_count/issue_count` for every card, which can only ever read 0% or
  100% for a Singles card (one issue). The web already special-cases this
  (`frontend/js/app.js:1812-1821`) using real page-level progress
  (`current_page/page_count`) for Singles — the backend already sends
  `current_page` for exactly this reason (`backend/routers/library.py:242`).
  Flutter's `Series` model never parsed it. Now mirrors the web's branch.

**Never built — not actually requested, this doc's own web-parity ideas**:
genre ribbon (§1.3), rating stars on cards (§3), flag-for-review badge
(§2.6), compact card tier (§6.1), two-column list view (§5.3), 115px list
thumbnail width (§5.1, still 96px), progress shown as a bar rather than a
text pill (§2.2/5.2). None of these came up in Tez's own ask or `INBOX.md` —
if any becomes wanted later, scope it as its own item rather than resuming
this document.

---

## 1. Current Web Card Styles

The web library grid uses `.cover-card.cover-card--redesign` — a "physical card" design with a fixed dark face regardless of site theme.

### Card Container

| Property | Value |
|----------|-------|
| Background (dark theme) | `linear-gradient(160deg, #1b2028 0%, #12161d 100%)` — always applied, overrides all read-state colour rules |
| Background (light theme) | `var(--surface-card)` = `#d8e3ef` |
| Border | None (dark); `1px solid #96b7d1` (light) |
| Box-shadow at rest (dark) | `0 0 2px 1px rgba(255,255,255,0.5)` — white glow ring |
| Box-shadow at rest (light) | `0 0 0 1px #454566` |
| Border-radius | `10px` (`--radius-lg`) |
| Inner padding (matte gap) | `5px 5px 7px` — creates a visible inset gap between cover edge and card edge |

### Cover Image

| Property | Value |
|----------|-------|
| Aspect ratio | `2 / 3` |
| Image border-radius | `6px` (`--radius`) — slightly inset from card edge |
| Lazy load | Yes |
| Placeholder | `📖` emoji centred in `var(--surface-2)` bg |

### Info Block (below image)

| Property | Value |
|----------|-------|
| Padding | `10px 0 0` — no sides (text aligns with cover inset) |
| Gap between elements | `5px` |
| Title layout | Anchors to bottom of info block via `margin-top: auto` on first meta row |

### Typography

| Element | Size | Weight | Color | Notes |
|---------|------|--------|-------|-------|
| Title | 12px | 600 | `#f3ece0` (`--rc-title`) | 2-line clamp, line-height 1.3 |
| Year | 11px | 400 | `#c9b79f` (`--rc-meta`) | Row 1, left |
| Issue count / page count | 11px | 400 | `#c9b79f` (`--rc-meta`) | Row 2, left |
| Genre ribbon | 10px | 400 | `#F2F4F7` | Uppercase, letter-spacing 0.04em; Row 1, right |
| Rating stars | 11px | — | `#F0C419` (gold) | Row 2, right; only shown if rated |

### Meta Row Layout (grid view)

```
[Title — 2 lines, 12px]
[Year 11px] .............. [Genre ribbon 10px]
[Issue count 11px] ........ [★★★ rating 11px]
```

Both meta rows use `justify-content: space-between`. If no rating exists, issue count sits left and right side is empty.

### Genre Ribbon

Displayed as a left-partial pill — `border-radius: 3px 0 0 3px`. Dark semi-transparent fill (`rgba(0,0,0,0.4)`). The bottom border carries the **read-state colour signal**:

| State | Border-bottom colour |
|-------|---------------------|
| Unread | `#0A5FFF` (blue) |
| Part-read / Read | `#3FB877` (green) |

Compact card tier (set by admin card-size control): ribbon font shrinks to 8px, tighter padding.

### Cover Overlays and Badges

| Badge | Position | Size | Appearance |
|-------|----------|------|------------|
| Read badge (state-read only) | top-right, 6px inset | 14×14px circle | Green fill `#3FB877`, 2px white border |
| Favourite heart | top-left, 6px inset | 20×20px circle | `rgba(255,255,255,0.6)` bg, red `♥` glyph (24px), no border |
| Flag-for-review | bottom-right, 6px inset | 20×20px circle | `rgba(255,255,255,0.6)` bg, danger-red SVG flag |
| Select dot | bottom-left, 11px↑ 8px← | 14×14px circle | Hover-reveal only; white border; filled+checkmark when selected |
| Unread count pill | — | — | **Dropped on redesigned card** — read badge replaces it |

### Progress Indicator

A **floating pill** overlaid on the cover image (shown for state-part-read and state-read):

- Track: `position: absolute; left: 28px; right: 28px; bottom: 9px; height: 5px` — inset from badge corners
- Track background: `rgba(0,0,0,0.55)` (dark tinted)
- Fill: `#3FB877` (green), `border-radius: 999px`

There is **no** "XX% Read" text in grid view — text label appears in list view only (`.list-progress-text`).

### Read State Signals (redesigned card)

Because the fixed dark gradient overrides all `.state-read` / `.state-part-read` background rules, the **only visual read signals on the redesigned card are**:

- The **green circle badge** (top-right) for fully read
- The **genre ribbon bottom border colour** (blue = unread, green = read/progress)
- The **progress pill** for part-read/read

The card background colour does **not** change with read state.

### Grid Layout

```css
grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
gap: 24px;  /* #coverGrid specific */
```

Card minimum width: 120px (100px on mobile ≤640px). Cards grow to fill available columns.

### List View (web)

Two-column grid; cover thumbnail 115px wide × 2/3 aspect ratio. Info shows: title (14px, 700), meta (12px), genres row, publisher·writer row, summary (2-line), "X% Read" text (part-read only), rating stars. Genre ribbon and read/flag badges are hidden in list view.

### Folder Cards (web)

Folder tiles share the same dark gradient background and hover treatment as series cards.

**Without cover (icon variant):**
- `aspect-ratio: 2/3`, `padding: 18px 16px`, flex column centred
- `📁` icon (32px), name (14px, 700, `--text`), count (12px, `--text-3`)

**With cover (has-cover variant):**
- Same structure as a series card: cover image at top, `folder-card-info` below
- Info block: `padding: 10px`, shows name (font-size 14px, 700) + issue count (12px)
- No genre ribbon, no rating, no read-state badges

---

## 2. Current Flutter Card Styles

### Grid Card (`CoverCard`)

The `CoverCard` widget is a bare **`Column`** — there is no card-level container, no background decoration, no shadow, and no padding around the cover.

```
Column:
  AspectRatio(2/3):
    Container(borderRadius: 10px, border: 1px border-color):
      Stack:
        CachedNetworkImage
        [if read]     → Container(color: readGreen @ alpha 0.5)
        [if progress] → green gradient (56px, bottom) + 3px green bar + "XX% Read" text overlay
        [if favourite] → ★ star badge (top-left, 13px glyph, dark-circle bg)
        [if unreadCount > 0] → blue pill (top-right, "N" label, 10px)
  SizedBox(height: 6)
  Text(title)        → 13px, w700, textPrimary, 2-line clamp
  SizedBox(height: 2)
  Text(meta)         → 12px, w400, textMuted, 1-line ("YEAR · N issues" or "YEAR · N pages")
```

| Property | Value |
|----------|-------|
| Card background | **None** — no container behind the cover |
| Box-shadow | None |
| Card padding (matte gap) | None |
| Cover border | `1px solid colors.border` at rest; `colors.accent` on hover; `2px solid colours.favouriteGold` if favourite |
| Cover border-radius | `10px` |
| Title size | 13px (web: 12px) |
| Title weight | w700 (web: 600) |
| Meta size | 12px (matching web) |
| Meta content | Combined "YEAR · N issues" string — no separate year/count rows |

### Grid Layout (Flutter)

```dart
SliverGridDelegateWithMaxCrossAxisExtent(
  maxCrossAxisExtent: 150.0,   // web: minmax(120px, 1fr)
  childAspectRatio: 0.5,
  crossAxisSpacing: 14.0,      // web: 24px
  mainAxisSpacing: 14.0,       // web: 24px
)
```

### Read-state Handling (Flutter)

| State | Visual |
|-------|--------|
| `unread` | Plain cover, blue badge if unreadCount > 0 |
| `progress` | Green gradient fade (56px bottom) + 3px full-width green bar + "XX% Read" text in image |
| `read` | `rgba(green, 0.5)` overlay on entire cover image |

The progress bar is a **full-width 3px line at the very bottom edge** of the cover — no track, no inset.

"XX% Read" text appears **inside** the image overlay in grid view (at bottom-left, inside the progress state). The web does not show this text in grid view at all.

### Favourite Badge (Flutter vs Web)

| Attribute | Flutter | Web |
|-----------|---------|-----|
| Icon | `★` star glyph | `♥` heart glyph |
| Size | 13px | 24px (heart only; circle stays 20px) |
| Circle bg | `Colors.black @ 0.35` | `rgba(255,255,255,0.6)` |
| Border | `1px black` | None |
| Position | `top: 6, left: 6` | `top: 6, left: 6` ✓ |

### List Row (`CoverListRow`)

Has a proper card decoration: `surfaceCard` background, `8px` border-radius, border. Thumbnail width 96px (web: 115px). Shows title, meta, summary, genresLabel, credLabel, and "XX% Read" text. Progress indicator is only a dark thumbnail overlay (`Container(height: 32, opacity: 0.35)`) — **no progress bar**.

### What the Flutter App Does Not Know About Tabs

`CustomTabInfo.viewMode` is parsed (`"flat"` or `"folder"`), but the shell screen and browse screen **ignore `viewMode` entirely** — all library tabs load via `getLibrary(tabId:)` and render as a flat series grid. The `viewMode: "folder"` flag is stored but never acted on.

---

## 3. Gap Analysis

### A — Card Visual Frame

| Property | Web | Flutter | Gap |
|----------|-----|---------|-----|
| Card-level dark gradient background | ✅ `linear-gradient(160deg, #1b2028, #12161d)` | ❌ No card container | Missing entirely |
| Inner padding / matte gap | ✅ `5px 5px 7px` | ❌ None | Missing |
| White glow ring at rest | ✅ `box-shadow: 0 0 2px 1px rgba(255,255,255,0.5)` | ❌ None | Missing |
| Card border-radius | ✅ 10px | ✅ 10px | ✓ Match |
| Cover image inner radius | ✅ 6px (inset from 5px matte) | ✅ 10px (no matte gap, so flush) | Different — Flutter cover fills edge |

### B — Typography

| Property | Web | Flutter | Gap |
|----------|-----|---------|-----|
| Title size | 12px | 13px | Minor mismatch |
| Title weight | w600 | w700 | Minor mismatch |
| Title color | `#f3ece0` (fixed warm off-white) | `textPrimary` (themed) | Semantic vs fixed |
| Title line clamp | 2 | 2 | ✓ |
| Meta size | 11px | 12px | Minor mismatch |
| Meta color | `#c9b79f` (fixed warm grey) | `textMuted` (themed) | Semantic vs fixed |
| Meta content | Two separate rows (year / count) | Single combined string | Structural difference |
| Year as distinct field | ✅ Own `cover-year` div, 11px | Embedded in `meta` string | No separate visual treatment |

### C — Metadata Shown on Grid Card

| Field | Web | Flutter |
|-------|-----|---------|
| Title | ✅ | ✅ |
| Year | ✅ (own row, bottom-aligned) | ✅ (in meta string) |
| Issue count / page count | ✅ (own row) | ✅ (in meta string) |
| Genre ribbon (1st genre, read-state border) | ✅ | ❌ Missing |
| Rating stars | ✅ (if rated) | ❌ Missing (`Series.personalRating` is in model but never passed to `CoverCardData`) |
| Progress % text | ❌ (grid only — no text) | ✅ (inside image — different from web intent) |

### D — Cover Badges and States

| Badge | Web | Flutter | Gap |
|-------|-----|---------|-----|
| Read state badge (green circle) | ✅ top-right | ❌ Missing | Missing |
| Unread count pill | ❌ Dropped in redesign | ✅ Still present | Flutter kept the dropped badge |
| Favourite badge | ✅ `♥` heart, white circle | ✅ `★` star, black circle | Wrong glyph + wrong circle colour |
| Flag-for-review badge | ✅ flag SVG, white circle | ❌ Missing | Missing — model has no flag field either |
| Select dot | ✅ hover-reveal | ❌ Missing | Missing (not critical for tablet) |

### E — Progress Indicator

| Property | Web | Flutter | Gap |
|----------|-----|---------|-----|
| Style | Inset pill track (28px margins, 5px) | Full-width 3px bar flush to bottom | Different appearance |
| Track background | `rgba(0,0,0,0.55)` dark tinted | None (bare colour bar) | No track |
| Fill colour | `#3FB877` | `colors.readGreen` (`#3FB877`) | ✓ Match |
| Position | `bottom: 9px`, inset from edges | `bottom: 0`, flush | Different |
| "XX% Read" text in grid | ❌ Not shown | ✅ Inside image overlay | Flutter shows text the web doesn't |

### F — Read-State Colour Signals

| Signal | Web | Flutter | Gap |
|--------|-----|---------|-----|
| Genre ribbon border colour (blue/green) | ✅ Key signal | ❌ No ribbon | Biggest signal is missing |
| Card background change | ❌ Overridden by gradient | ❌ N/A | N/A |
| Green overlay on read | ❌ Not present on redesigned card | ✅ Full green overlay | Flutter over-signals (dark gradient prevents this on web) |
| Green circle badge | ✅ Shown when read | ❌ Missing | Missing |

### G — Grid Spacing

| Property | Web | Flutter | Gap |
|----------|-----|---------|-----|
| Card gap | 24px | 14px | Cards too close together in Flutter |
| Card min width | 120px (`auto-fill minmax`) | 150px max per cell | Different sizing model |

### H — List View

| Property | Web | Flutter | Gap |
|----------|-----|---------|-----|
| Thumbnail width | 115px | 96px | 19px narrower |
| Progress bar in list | ✅ Full-width 2px bar in info | ❌ Dark overlay only, no bar | Missing |
| Rating in list | ✅ Star row after summary | ❌ Missing | Missing |
| Two-column layout | ✅ (at large widths) | ❌ Single column always | Missing |

---

## 4. Missing Folder View

### Current State

`CustomTabInfo.viewMode` field exists and is parsed, but is ignored at runtime. All custom library tabs — including "2000 AD" (which is configured with `view_mode: "folder"`) — load and display as a flat series grid via `BrowseScreen`. There is no `FolderScreen` or `FolderCard` widget.

### What a Folder View Needs

On the web, a folder-view tab (`view_mode: "folder"`) navigates a directory hierarchy. Each level shows:

1. **Folder cards** — represent subdirectories (publishers/groups)
2. **File cards** — represent individual issues (`.cover-card--redesign` style)

For the Flutter implementation of 2000 AD and similar tabs:

**Folder card widget (new — `FolderCard`):**

```
Container(
  aspect-ratio: 2/3,               // same shape as series card
  background: dark gradient,        // matches cover-card--redesign
  border-radius: 10px,
  glow ring,
):
  if hasCover:
    [cover image]
    [folder-info block]
      name: 14px, w700
      count: 12px, textMuted — "N issues"
  else (icon variant):
    centred column:
      📁 icon (48px — slightly larger than web's 32px for touch targets)
      name: 14px, w700
      count: 12px, textMuted
```

**Key visual differences from a series card:**
- No genre ribbon (folders don't have genres)
- No read-state badge or progress bar
- No favourite/flag badges
- Info block shows only name + count (no year, no rating)

**Distinguishing folders from series cards visually:**
The web uses `aspect-ratio: 2/3` plus the 📁 icon to distinguish an icon-only folder from a series card. With a cover image (`has-cover`), it's visually identical to a series card. On tablet, consider:
- Icon folders: large emoji, no cover — clearly a folder
- Cover folders: add a small 📁 badge overlay (top-right, similar to the read badge) so the user knows tapping drills down rather than opening a single series
- Alternatively: a subtle "folder badge" label in the info block: `"14 series"` or `"42 issues"` worded differently

**Data the folder API returns:**  
The web hits `/library/tab/{id}/folder?path={path}`. The response includes `folders[]` (name, issue_count, cover_path) and `files[]` (individual issues). The Flutter `ApiService` does not currently have this endpoint wired.

**2000 AD specifically:**
2000 AD is a weekly anthology. Its `view_mode` is `"folder"` with subdirectories for individual prog numbering or story arcs. Currently in Flutter it shows as a single series card labelled "2000 AD" with a cumulative issue count — the folder navigation that gives it context is entirely missing.

---

## 5. Tablet Adaptation Notes

Target: 10" tablet (landscape, ~1280×800 logical px). Available library width after nav rail (collapsed 64px + gutter): **~1180px**. At 150px card max + 14px gaps: **7 cards per row**. Cards are approximately **155px wide**.

At 155px wide, a 2/3 cover is **233px tall**. The info block below adds approximately 55–65px (title 2 lines + meta). Total card height ≈ 295px.

For each web card property, the tablet verdict:

| Property | Tablet verdict | Notes |
|----------|---------------|-------|
| Dark gradient card background | **INCLUDE** | Works at any size; essential for "physical card" feel |
| White glow ring | **INCLUDE** | Subtle, works at any size |
| Inner padding / matte gap | **INCLUDE** | Reduce to `4px 4px 5px` (slightly smaller than web's `5px 5px 7px`) to preserve space |
| Title (2-line, 12px) | **INCLUDE** | Web's 12px is fine on tablet; match it (Flutter has 13px — reduce) |
| Year field | **INCLUDE** | 11px, fits on a single line alongside genre ribbon |
| Issue count / page count | **INCLUDE** | 11px, same row as rating stars |
| Genre ribbon (1st genre only) | **INCLUDE** | At 155px card width, genre ribbon has ~80px after year text. Truncate if needed. 10px text is legible |
| Genre ribbon read-state border | **INCLUDE** | Critical visual signal; no extra space needed (it's a bottom border) |
| Rating stars | **INCLUDE** | 11px stars, 1–5 stars. At 155px, 5 stars = ~55px max. Fine |
| Read badge (green circle, top-right) | **INCLUDE** | 14×14px, negligible |
| Favourite heart badge | **INCLUDE** | 20×20px, top-left; replace ★ with ♥ and white circle |
| Flag-for-review badge | **INCLUDE** | 20×20px, bottom-right |
| Select dot | **EXCLUDE** | Hover-reveal on web; no hover on tablet. Multi-select is touch-long-press only — implement separately if needed |
| Progress pill track (inset) | **INCLUDE** | Reduce inset: `left: 20px, right: 20px` (web 28px) to use more of the 155px width |
| "XX% Read" text inside grid card | **EXCLUDE** | Clutters the cover image; web deliberately doesn't show it in grid. Move to list view only |
| Unread count pill | **EXCLUDE** | Dropped from web redesign. Remove from Flutter too |
| Card gap | **REDUCE** | 20px (between web's 24px and Flutter's 14px) |
| Two-column list view | **INCLUDE** | At 1180px, two columns of ~545px each with 90px gap is comfortable |
| List thumbnail width | **INCLUDE at 115px** | Match web (Flutter currently 96px — too narrow) |
| Folder card icon size | **REDUCE to 40px** | Web's 32px is for desktop; 40px for touch affordance |
| Folder navigation path breadcrumb | **INCLUDE** | Needed for hierarchical nav; doesn't exist on web either but essential for tablet UX |

---

## 6. Prioritised Change List

Tasks are ordered by user-visible impact. Effort: **S** ≈ 1–3h, **M** ≈ half-day, **L** ≈ 1–2 days.

### Priority 1 — Card Visual Overhaul (high impact, foundation for everything else)

| # | Task | Effort |
|---|------|--------|
| 1.1 | **Add card-level container with dark gradient background and matte inner padding** — wrap `CoverCard`'s `Column` in a `Container` with `decoration: BoxDecoration(gradient: ..., borderRadius: 10px)` and `padding: EdgeInsets.fromLTRB(4, 4, 4, 5)`. Remove border from inner cover container (border moves to card level as glow). | M |
| 1.2 | **Add white glow ring** — add `BoxShadow(color: Colors.white.withValues(alpha: 0.5), blurRadius: 2, spreadRadius: 1)` to the card-level container's `BoxDecoration`. | S |
| 1.3 | **Add genre ribbon widget** — new `GenreRibbon` widget: dark-bg pill with left-side border-radius, the state-colour bottom border (blue/green), 10px uppercase text. Add to `CoverCardData` (a `genreLabel` field — the first genre string). Wire in `_cardFor()` from `s.genres.isNotEmpty ? s.genres.first : null`. Place in the first meta row, `Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [yearText, if genreLabel != null GenreRibbon(...)])`. | M |
| 1.4 | **Fix title and meta typography to match web** — title: 12px, w600, fixed cream `Color(0xFFF3ECE0)`. Meta year: 11px, fixed warm grey `Color(0xFFC9B79F)`. Break meta into two separate `Row` widgets (year+ribbon / count+rating) rather than a single string. | S |
| 1.5 | **Fix card grid gap to 20px** — change both `crossAxisSpacing` and `mainAxisSpacing` in `BrowseScreen._buildGrid()` from `AppSpacing.cardGap` (14px) to 20. Update `AppSpacing.cardGap` or use a dedicated `cardGridGap` constant. | S |

### Priority 2 — Read-State and Badge Alignment

| # | Task | Effort |
|---|------|--------|
| 2.1 | **Add green circle read badge** — when `state == 'read'`, show a 14×14px filled circle (`colors.readGreen`, 2px white border) at `top: 6, right: 6` on the cover stack. Remove the green full-image overlay (which the web's dark gradient makes invisible — Flutter's lack of card gradient currently makes it the only visible signal, which will be wrong once the gradient is added). | S |
| 2.2 | **Fix progress bar to inset pill style** — replace the `Container(height: 3, color: colors.readGreen)` flush bar with a `Positioned(left: 20, right: 20, bottom: 9, child: ClipRRect(borderRadius: pill, child: Stack([track, fill])))`. Track colour: `Colors.black.withValues(alpha: 0.55)`, height: 5px. | S |
| 2.3 | **Remove "XX% Read" text from grid card image overlay** — this text only belongs in list view. Delete the `Text('${d.progressPercent}% Read', ...)` from the `CoverCard` progress stack. | S |
| 2.4 | **Fix favourite badge: ♥ heart, white circle, correct size** — change glyph from `★` to `♥`, circle background from `Colors.black @ 0.35` to `Colors.white.withValues(alpha: 0.6)`, remove `Border.all(black)`, increase glyph size to 18–20px. | S |
| 2.5 | **Remove unread count pill** — the web redesign dropped it. Delete the `if (d.unreadCount > 0)` block from `CoverCard`. Remove `unreadCount` from `CoverCardData` or keep but stop rendering (field can stay for potential future use). | S |
| 2.6 | **Add flag-for-review badge** — add `flaggedForReview` bool to `CoverCardData`, wire from `s.flaggedForReview` (check if `Series` model has this field — if not, add to API response and model). Show 20×20px circle (white @ 0.6 bg, danger-red flag icon) at `bottom: 6, right: 6`. | M |

### Priority 3 — Rating Stars

| # | Task | Effort |
|---|------|--------|
| 3.1 | **Add `personalRating` (0–5) to `CoverCardData`** — `Series` model already has `personalRating`. Pass it from `_cardFor()`. | S |
| 3.2 | **Build `CardRatingRow` widget** — up to 5 `★` glyphs at 11px in `#F0C419`. In light theme: wrap in dark pill background. Show in second meta row, right-aligned, only when `personalRating > 0`. | S |
| 3.3 | **Show rating in list row** — add rating stars after summary in `CoverListRow`. | S |

### Priority 4 — Folder View (new feature)

| # | Task | Effort |
|---|------|--------|
| 4.1 | **Wire `/library/tab/{id}/folder` endpoint in `ApiService`** — new method `getFolderContents(tabId, path)` returning `{folders: [...], files: [...]}`. | M |
| 4.2 | **Build `FolderCard` widget** — icon variant (📁 at 40px, name, count, centred in 2:3 card matching dark gradient frame) and cover variant (image top, name+count below, same frame as `CoverCard`). Add folder-distinguishing visual: small 📁 overlay badge on cover variant at top-right. | L |
| 4.3 | **Build `FolderScreen`** — stateful screen that loads folder contents, renders `FolderCard`s + file `CoverCard`s in a grid, handles drill-down navigation (push new `FolderScreen` with updated path), provides a breadcrumb bar at top. | L |
| 4.4 | **Route `viewMode == "folder"` custom tabs to `FolderScreen`** — in `ShellScreen._buildContent()` (or wherever `NavKind.library` is handled), check `tab.viewMode == "folder"` and push `FolderScreen` instead of `BrowseScreen`. | S |
| 4.5 | **2000 AD folder structure validation** — once 4.1–4.4 are in, confirm that 2000 AD's prog/series hierarchy renders correctly. The root level likely shows subdirectory folder cards; drilling into a prog shows its issues as file cards. | M |

### Priority 5 — List View Fixes

| # | Task | Effort |
|---|------|--------|
| 5.1 | **Widen list thumbnail from 96px to 115px** — matches web. Update `SizedBox(width: 96)` to `SizedBox(width: 115)` in `CoverListRow`. | S |
| 5.2 | **Add progress bar to list row** — currently list row only shows a dark thumbnail overlay. Add a `LinearProgressIndicator` or custom bar in the info column when `state == 'progress'`. | S |
| 5.3 | **Two-column list view on tablet** — wrap `ListView.separated` in a `GridView` with 2 columns when screen width > 900px. | M |

### Priority 6 — Polish and Edge Cases

| # | Task | Effort |
|---|------|--------|
| 6.1 | **Compact card tier** — mirror the web's `data-card-tier="compact"` admin setting: at smaller card sizes, reduce genre ribbon font to 8px and tighten padding. Can be driven by a `SettingsService` card-size value. | M |
| 6.2 | **Light theme card overrides** — in light mode the web swaps the fixed dark gradient for `--surface-card` with a thin border. Add `MediaQuery.of(context).platformBrightness == Brightness.light` branch in `CoverCard` to swap gradient for `colors.surfaceCard` background, and swap fixed cream/warm-grey text colours for `colors.textPrimary` / `colors.textSecondary`. | M |
| 6.3 | **Cover placeholder icon** — web uses `📖` emoji; Flutter uses `Icons.menu_book_outlined`. Acceptable difference, but harmonise if desired. | S |
| 6.4 | **Page-bg cloud field** — web library views have a blurred multi-cover background. Flutter has nothing. Low priority but adds atmosphere. | L |

---

### Summary Table

| Task | Effort | Priority |
|------|--------|----------|
| 1.1 Card gradient + matte padding | M | P1 |
| 1.2 Glow ring | S | P1 |
| 1.3 Genre ribbon widget | M | P1 |
| 1.4 Fix title/meta typography and layout | S | P1 |
| 1.5 Fix grid gap to 20px | S | P1 |
| 2.1 Green circle read badge | S | P2 |
| 2.2 Progress pill track style | S | P2 |
| 2.3 Remove "% Read" text from grid overlay | S | P2 |
| 2.4 Fix favourite badge (♥, white circle) | S | P2 |
| 2.5 Remove unread count pill | S | P2 |
| 2.6 Flag-for-review badge | M | P2 |
| 3.1–3.3 Rating stars (grid + list) | S+S+S | P3 |
| 4.1 Folder API endpoint | M | P4 |
| 4.2 FolderCard widget | L | P4 |
| 4.3 FolderScreen | L | P4 |
| 4.4 Route folder tabs to FolderScreen | S | P4 |
| 4.5 2000 AD validation | M | P4 |
| 5.1 List thumbnail 115px | S | P5 |
| 5.2 List progress bar | S | P5 |
| 5.3 Two-column list on tablet | M | P5 |
| 6.1 Compact card tier | M | P6 |
| 6.2 Light theme card overrides | M | P6 |
| 6.3 Cover placeholder harmonise | S | P6 |
| 6.4 Page-bg cloud field | L | P6 |
